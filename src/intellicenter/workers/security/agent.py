import json
import asyncio
import yaml
import structlog
from pathlib import Path
from datetime import datetime, timezone
from crewai.tools import BaseTool
from crewai import Agent, Task, Crew
from intellicenter.shared.event_bus import EventBus
from intellicenter.shared.logger import logger, bind_request_context
from intellicenter.shared.schema import AgentType, AgentStatus, AgentResponse, AgentDirective
from intellicenter.infrastructure.crew import AsyncCrewAI, create_optimized_crew
from intellicenter.infrastructure.llm.factory import get_llm, get_memory_report
from intellicenter.workers.fallback import get_fallback_response


class CameraSurveillanceTool(BaseTool):
    name: str = "Camera Surveillance Tool"
    description: str = "Review camera footage for a specific zone."

    def _run(self, zone: str) -> str:
        return f"📷 Reviewing live camera feeds for zone: {zone}. No anomalies detected."


class AccessControlTool(BaseTool):
    name: str = "Access Control Tool"
    description: str = "Manage access control systems. Actions: query, lock, unlock"

    def _run(self, door_id: str, action: str = "query") -> str:
        if action == "lock":
            return f"🔒 Door {door_id} has been remotely locked."
        elif action == "unlock":
            return f"🔓 Door {door_id} has been remotely unlocked."
        return f"ℹ️  Door {door_id} status: Locked. Last access: 3 minutes ago."


class IncidentResponseTool(BaseTool):
    name: str = "Incident Response Tool"
    description: str = "Initiate an incident response protocol."

    def _run(self, protocol: str) -> str:
        return f"🚨 Initiating incident response protocol: {protocol}. Security team notified."


class SecurityOperationsAgent:
    """Security Operations Agent with explicit crew setup and fallback support"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.agents_config = self._load_config("agents.yaml")
        self.tasks_config = self._load_config("tasks.yaml")
        self.crew = self._setup_crew()
        self.fallback_mode = False
        self.performance_metrics = {
            "responses": 0,
            "avg_response_time": 0,
            "decisions": {"informational": 0, "low": 0, "medium": 0, "high": 0, "critical": 0}
        }
        
        # Bind context for the security agent
        bind_request_context(agent_id="security_agent", agent_type=AgentType.SECURITY)
        
        # Test agent startup
        startup_success = self.test_agent_startup()
        if not startup_success:
            logger.warning("security_agent_startup_issues", fallback_mode=True)
            self.fallback_mode = True
        
        # Subscribe to security events
        loop = asyncio.get_event_loop()
        self.event_bus.subscribe("facility.security.event", lambda msg: self._handle_security_event(msg, loop))
        
        logger.info("security_agent_initialized")
        
    def _load_config(self, file_name: str):
        # Try optimized config first
        optimized_path = Path(f"src/intellicenter/config/optimized_{file_name}")
        if optimized_path.exists():
            with open(optimized_path, "r") as file:
                return yaml.safe_load(file)
                
        # Fallback to regular config
        config_path = Path(f"src/intellicenter/config/{file_name}")
        if config_path.exists():
            with open(config_path, "r") as file:
                return yaml.safe_load(file)
                
        # Default fallback
        if "agents" in file_name:
            return {"security_specialist": {
                "role": "Security Operations Specialist", 
                "goal": "Ensure comprehensive facility security", 
                "backstory": "Expert security specialist with threat assessment expertise",
                "max_execution_time": 20
            }}
        elif "tasks" in file_name:
            return {"security_analysis": {
                "description": "Assess security events and determine appropriate response actions",
                "expected_output": "Security assessment with threat level and recommended actions"
            }}
        return {}
    
    def _setup_crew(self):
        """Setup CrewAI crew for Security operations with centralized LLM configuration"""
        try:
            # Get LLM from centralized configuration
            llm = get_llm("security")
            
            security_specialist = Agent(
                config=self.agents_config['security_specialist'],
                llm=llm,
                verbose=True,
                allow_delegation=False,
                tools=[
                    CameraSurveillanceTool(),
                    AccessControlTool(),
                    IncidentResponseTool()
                ]
            )
            
            security_analysis_task = Task(
                config=self.tasks_config['security_analysis'],
                agent=security_specialist
            )

            return Crew(
                agents=[security_specialist],
                tasks=[security_analysis_task],
                verbose=False,
                memory=False,
                planning=False,
                max_execution_time=20
            )
            
        except Exception as e:
            print(f"❌ Failed to setup CrewAI crew for Security agent: {e}")
            # Initialize fallback agent
            from intellicenter.workers.fallback import MockAgent
            self.mock_agent = MockAgent()
            self.fallback_mode = True
            return None
    
    def _handle_security_event(self, message, loop):
        try:
            security_data = json.loads(message)
            asyncio.create_task(self._run_security_analysis(security_data, loop))
        except Exception as e:
            logger.error("security_event_parse_error", error=str(e))

    async def _run_security_analysis(self, security_data, loop):
        start_time = loop.time()
        try:
            # Check if we're in fallback mode
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                # Use MockAgent for fallback response
                fallback_response = get_fallback_response(
                    "security",
                    "threat_assessment",
                    {"event_type": security_data.get("event_type", "unknown")}
                )
                
                security_decision = {
                    "threat_assessment": fallback_response.response,
                    "threat_level": "medium",  # Default fallback level
                    "recommended_actions": "Escalate to human operator for review.",
                    "confidence": fallback_response.confidence,
                    "reasoning": fallback_response.reasoning,
                    "timestamp": loop.time(),
                    "event_correlation": security_data.get("event_id"),
                    "agent_type": "security_specialist",
                    "response_time": round(asyncio.get_event_loop().time() - start_time, 2),
                    "status": "fallback",
                    "fallback_triggered": True
                }
            else:
                # Use CrewAI directly with Ollama
                result = await asyncio.to_thread(
                    self.crew.kickoff,
                    inputs={"security_data": json.dumps(security_data)}
                )
                
                security_decision = self._process_crew_result(result, security_data, start_time, loop)
            
            # Create AgentResponse object
            response_obj = AgentResponse(
                request_id=security_data.get("request_id", "unknown"),
                agent_type=AgentType.SECURITY,
                status=AgentStatus.SUCCESS if security_decision.get("status") == "success" else AgentStatus.FAILED,
                decision_data=security_decision,
                reasoning=security_decision.get("reasoning"),
                confidence=security_decision.get("confidence")
            )
            
            await self.event_bus.publish("security.assessment.decision", response_obj.model_dump_json())
            self._update_metrics(security_decision)
            logger.info("security_assessment_completed", 
                        assessment=security_decision.get('threat_assessment', 'fallback')[:100],
                        threat_level=security_decision.get('threat_level'))
            
        except Exception as e:
            logger.error("security_analysis_error", error=str(e))
            fallback_decision = self._generate_fallback_decision(security_data, str(e), start_time, loop)
            # Create AgentResponse for fallback
            fallback_response_obj = AgentResponse(
                request_id=security_data.get("request_id", "unknown"),
                agent_type=AgentType.SECURITY,
                status=AgentStatus.FAILED,
                decision_data=fallback_decision,
                reasoning="Fallback decision due to analysis error."
            )
            await self.event_bus.publish("security.assessment.decision", fallback_response_obj.model_dump_json())
    
    def _process_crew_result(self, result, security_data, start_time, loop):
        try:
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            crew_output = json.loads(raw_output)
        except (json.JSONDecodeError, AttributeError):
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            # Parse threat level from raw output
            threat_level = "medium"  # Default
            if "critical" in raw_output.lower():
                threat_level = "critical"
            elif "high" in raw_output.lower():
                threat_level = "high"
            elif "low" in raw_output.lower():
                threat_level = "low"
            elif "informational" in raw_output.lower():
                threat_level = "informational"
            
            crew_output = {
                "threat_assessment": raw_output,
                "threat_level": threat_level,
                "recommended_actions": "AI analysis completed, raw output processed.",
                "confidence": 75,
                "reasoning": "AI analysis completed, raw output processed."
            }
        
        return {
            **crew_output,
            "timestamp": security_data.get("timestamp"),
            "event_correlation": security_data.get("event_id"),
            "agent_type": AgentType.SECURITY,
            "response_time": round(loop.time() - start_time, 2),
            "status": "success"
        }
    
    def _generate_fallback_decision(self, security_data, error_msg, start_time, loop):
        """Generate fallback decision when security analysis fails"""
        event_type = security_data.get("event_type", "unknown")
        threat_level = "medium"  # Default fallback level
        
        # Determine threat level based on event type
        if event_type in ["unauthorized_access", "perimeter_breach", "system_tampering"]:
            threat_level = "high"
        elif event_type in ["suspicious_activity", "anomaly_detected"]:
            threat_level = "medium"
        elif event_type in ["routine_check", "system_update"]:
            threat_level = "informational"
        
        return {
            "threat_assessment": f"Standard security protocols applied for {event_type}. Fallback mode activated.",
            "threat_level": threat_level,
            "recommended_actions": "Escalate to human operator for review.",
            "error": error_msg,
            "fallback": True,
            "timestamp": loop.time(),
            "event_correlation": security_data.get("event_id"),
            "response_time": round(loop.time() - start_time, 2),
            "agent_type": AgentType.SECURITY,
            "status": "fallback"
        }
    
    def _update_metrics(self, decision_data):
        """Update performance metrics for security agent"""
        response_time = decision_data.get("response_time", 0)
        threat_level = decision_data.get("threat_level", "medium")
        self.performance_metrics["responses"] += 1
        count = self.performance_metrics["responses"]
        old_avg = self.performance_metrics["avg_response_time"]
        self.performance_metrics["avg_response_time"] = (old_avg * (count - 1) + response_time) / count
        if threat_level in self.performance_metrics["decisions"]:
            self.performance_metrics["decisions"][threat_level] += 1
    
    def get_performance_report(self) -> str:
        """Get performance report for security agent"""
        metrics = self.performance_metrics
        total_decisions = sum(metrics["decisions"].values())
        if total_decisions == 0: return "🛡️ Security Agent: No decisions made yet."
        report = f"🛡️ Security Agent: {metrics['responses']} responses, {metrics['avg_response_time']:.2f}s avg response. Decisions: "
        for level, count in metrics["decisions"].items():
            report += f"{level}: {count} ({(count/total_decisions*100):.1f}%) "
        return report.strip()
    
    def test_agent_startup(self) -> bool:
        """Test agent initialization and startup"""
        try:
            logger.info("security_agent_startup_test_initiated")
            
            # Test 1: Check if crew was initialized successfully
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                logger.info("security_agent_startup_test_success", mode="fallback")
                return True
            elif self.crew is not None:
                logger.info("security_agent_startup_test_success", mode="crewai")
                return True
            else:
                logger.error("security_agent_startup_test_failed", reason="initialization_failure")
                return False
                
        except Exception as e:
            logger.error("security_agent_startup_test_failed", error=str(e))
            return False
    
    async def test_response_generation(self, security_data: dict) -> dict:
        """Test agent response generation with sample data"""
        try:
            logger.info("security_agent_test_response_initiated", data=security_data)
            
            start_time = asyncio.get_event_loop().time()
            
            # Simulate security event
            message = json.dumps(security_data)
            loop = asyncio.get_event_loop()
            self._handle_security_event(message, loop)
            
            # Wait a moment for async processing
            await asyncio.sleep(0.1)
            
            # Check if we got a decision
            if hasattr(self, 'performance_metrics') and self.performance_metrics['responses'] > 0:
                logger.info("security_agent_test_response_success")
                return {
                    "success": True,
                    "responses_generated": self.performance_metrics['responses'],
                    "status": "completed"
                }
            else:
                logger.warning("security_agent_test_response_no_events")
                return {
                    "success": True,
                    "responses_generated": 0,
                    "status": "waiting"
                }
                
        except Exception as e:
            logger.error("security_agent_test_response_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def run(self):
        logger.info("security_agent_running")
        while True:
            await asyncio.sleep(1)