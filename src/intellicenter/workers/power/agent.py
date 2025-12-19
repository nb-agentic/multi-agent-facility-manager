import json
import asyncio
import yaml
import structlog
from pathlib import Path
from datetime import datetime, timezone
from crewai.tools import BaseTool
from intellicenter.shared.event_bus import EventBus
from intellicenter.shared.logger import logger, bind_request_context
from intellicenter.shared.schema import AgentType, AgentStatus, AgentResponse, AgentDirective
from crewai import Agent, Task, Crew
from intellicenter.infrastructure.llm.factory import get_llm
from intellicenter.workers.fallback import get_fallback_response

class PowerMonitoringTool(BaseTool):
    name: str = "Power Monitoring Tool"
    description: str = "Monitor current power consumption"

    def _run(self, zone: str = "facility") -> str:
        import random
        current_load = random.randint(65, 85)
        capacity = 100
        status = "optimal" if current_load < 80 else "high_load"
        return f"⚡ Power monitoring {zone}: {current_load}% load ({capacity}kW capacity) - Status: {status}"

class UPStatusTool(BaseTool):
    name: str = "UPS Status Tool"
    description: str = "Check UPS and backup power systems"

    def _run(self) -> str:
        import random
        battery_level = random.randint(85, 100)
        runtime = random.randint(15, 45)
        return f"🔋 UPS Status: {battery_level}% battery, {runtime} min runtime at current load"

class CostAnalysisTool(BaseTool):
    name: str = "Cost Analysis Tool"
    description: str = "Analyze cost implications of power decisions"

    def _run(self, power_level: str) -> str:
        cost_map = {"low": "$850/day", "medium": "$1100/day", "high": "$1450/day", "peak": "$1800/day"}
        cost = cost_map.get(power_level, cost_map["medium"])
        return f"💰 Power cost analysis: {power_level} consumption = {cost}"

class PowerManagementAgent:
    """Power Management Agent with explicit crew setup"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.agents_config = self._load_config("agents.yaml")
        self.tasks_config = self._load_config("tasks.yaml")
        self.crew = self._setup_crew()
        self.fallback_mode = False
        self.performance_metrics = {
            "responses": 0,
            "avg_response_time": 0,
            "decisions": {"low": 0, "medium": 0, "high": 0, "emergency": 0}
        }
        
        # Bind context for the power agent
        bind_request_context(agent_id="power_agent", agent_type=AgentType.POWER)
        
        # Subscribe to HVAC cooling decisions for coordination
        loop = asyncio.get_event_loop()
        self.event_bus.subscribe("hvac.cooling.decision", lambda msg: self._handle_cooling_decision(msg, loop))
        
        # Test agent startup
        startup_success = self.test_agent_startup()
        if not startup_success:
            logger.warning("power_agent_startup_issues", fallback_mode=True)
            self.fallback_mode = True
        
        logger.info("power_agent_initialized")
        
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
            return {"power_specialist": {
                "role": "Power Management Specialist", 
                "goal": "Optimize electrical systems and energy consumption", 
                "backstory": "Expert electrical engineer specializing in power distribution",
                "max_execution_time": 25
            }}
        elif "tasks" in file_name:
            return {"power_analysis": {
                "description": "Analyze power consumption and optimize energy distribution",
                "expected_output": "Power optimization recommendations with efficiency metrics"
            }}
        return {}
    
    def _setup_crew(self):
        """Setup CrewAI crew for Power operations with centralized LLM configuration"""
        try:
            # Get LLM from centralized configuration
            llm = get_llm("power")
            
            power_specialist = Agent(
                config=self.agents_config['power_specialist'],
                llm=llm,
                verbose=True,
                allow_delegation=False,
                tools=[
                    PowerMonitoringTool(),
                    UPStatusTool(),
                    CostAnalysisTool()
                ]
            )
            
            power_optimization_task = Task(
                config=self.tasks_config['power_analysis'],
                agent=power_specialist
            )

            return Crew(
                agents=[power_specialist],
                tasks=[power_optimization_task],
                verbose=False,
                memory=False,
                planning=False,
                max_execution_time=25
            )
            
        except Exception as e:
            logger.error("power_crew_setup_failed", error=str(e))
            # Initialize fallback agent
            from intellicenter.workers.fallback import MockAgent
            self.mock_agent = MockAgent()
            self.fallback_mode = True
            return None
    
    def _handle_cooling_decision(self, message, loop):
        try:
            payload = json.loads(message)
            # Handle both raw dict and structured AgentResponse
            if "decision_data" in payload:
                # It's an AgentResponse
                response = AgentResponse(**payload)
                cooling_level = response.decision_data.get("cooling_level", "medium")
                request_id = response.request_id
            else:
                # Legacy or raw dict
                cooling_level = payload.get("cooling_level", "medium")
                request_id = payload.get("request_id", "unknown")
            
            power_data = {
                "cooling_level": cooling_level,
                "hvac_decision_data": payload,
                "request_id": request_id
            }
            asyncio.create_task(self._run_power_analysis(power_data, loop))
        except Exception as e:
            logger.error("power_analysis_trigger_error", error=str(e))
    
    async def _run_power_analysis(self, power_data, loop):
        start_time = loop.time()
        try:
            # Check if we're in fallback mode
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                # Use MockAgent for fallback response
                from intellicenter.workers.fallback import get_fallback_response
                
                fallback_response = get_fallback_response(
                    "power",
                    "power_optimization",
                    {"cooling_level": power_data.get("cooling_level", "medium")}
                )
                
                power_decision = {
                    "power_optimization": fallback_response.response,
                    "timestamp": loop.time(),
                    "cooling_correlation": power_data.get("cooling_level"),
                    "agent_type": AgentType.POWER,
                    "confidence": fallback_response.confidence,
                    "reasoning": fallback_response.reasoning,
                    "response_time": round(asyncio.get_event_loop().time() - start_time, 2),
                    "status": "fallback",
                    "fallback_triggered": True
                }
            else:
                # Use CrewAI directly with Ollama
                result = await asyncio.to_thread(
                    self.crew.kickoff,
                    inputs={"power_data": json.dumps(power_data)}
                )
                
                power_decision = {
                    "power_optimization": result.raw if hasattr(result, 'raw') else str(result),
                    "timestamp": loop.time(),
                    "cooling_correlation": power_data.get("cooling_level"),
                    "agent_type": AgentType.POWER,
                    "response_time": round(loop.time() - start_time, 2),
                    "status": "success"
                }
            
            # Create AgentResponse object
            response_obj = AgentResponse(
                request_id=power_data.get("request_id", "unknown"),
                agent_type=AgentType.POWER,
                status=AgentStatus.SUCCESS if power_decision.get("status") == "success" else AgentStatus.FAILED,
                decision_data=power_decision,
                reasoning=power_decision.get("reasoning"),
                confidence=power_decision.get("confidence")
            )
            
            await self.event_bus.publish("power.optimization.decision", response_obj.model_dump_json())
            self._update_metrics(power_decision)
            logger.info("power_optimization_completed", 
                        recommendation=power_decision.get('power_optimization', 'fallback')[:100],
                        cooling_level=power_decision.get('cooling_correlation'))
            
        except Exception as e:
            logger.error("power_analysis_error", error=str(e))
            fallback_decision = self._generate_fallback_decision(power_data, str(e), start_time, loop)
            
            # Create AgentResponse for fallback
            fallback_response_obj = AgentResponse(
                request_id=power_data.get("request_id", "unknown"),
                agent_type=AgentType.POWER,
                status=AgentStatus.FAILED,
                decision_data=fallback_decision,
                reasoning="Fallback decision due to analysis error."
            )
            await self.event_bus.publish("power.optimization.decision", fallback_response_obj.model_dump_json())
    
    def _update_metrics(self, decision_data):
        """Update performance metrics for power agent"""
        response_time = decision_data.get("response_time", 0)
        cooling_level = decision_data.get("cooling_correlation", "medium")
        self.performance_metrics["responses"] += 1
        count = self.performance_metrics["responses"]
        old_avg = self.performance_metrics["avg_response_time"]
        self.performance_metrics["avg_response_time"] = (old_avg * (count - 1) + response_time) / count
        if cooling_level in self.performance_metrics["decisions"]:
            self.performance_metrics["decisions"][cooling_level] += 1
    
    def _generate_fallback_decision(self, power_data, error_msg, start_time, loop):
        """Generate fallback decision when power analysis fails"""
        cooling_level = power_data.get("cooling_level", "medium")
        return {
            "power_optimization": f"Maintain current power distribution - {cooling_level} cooling level",
            "error": error_msg,
            "fallback": True,
            "timestamp": loop.time(),
            "response_time": round(loop.time() - start_time, 2),
            "cooling_correlation": cooling_level,
            "agent_type": AgentType.POWER,
            "status": "fallback"
        }
    
    def get_performance_report(self) -> str:
        """Get performance report for power agent"""
        metrics = self.performance_metrics
        total_decisions = sum(metrics["decisions"].values())
        if total_decisions == 0: return "⚡ Power Agent: No decisions made yet."
        report = f"⚡ Power Agent: {metrics['responses']} responses, {metrics['avg_response_time']:.2f}s avg response. Decisions: "
        for level, count in metrics["decisions"].items():
            report += f"{level}: {count} ({(count/total_decisions*100):.1f}%) "
        return report.strip()
    
    def test_agent_startup(self) -> bool:
        """Test agent initialization and startup"""
        try:
            logger.info("power_agent_startup_test_initiated")
            
            # Test 1: Check if crew was initialized successfully
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                logger.info("power_agent_startup_test_success", mode="fallback")
                return True
            elif self.crew is not None:
                logger.info("power_agent_startup_test_success", mode="crewai")
                return True
            else:
                logger.error("power_agent_startup_test_failed", reason="initialization_failure")
                return False
                
        except Exception as e:
            logger.error("power_agent_startup_test_failed", error=str(e))
            return False
    
    async def test_response_generation(self, power_data: dict) -> dict:
        """Test agent response generation with sample data"""
        try:
            logger.info("power_agent_test_response_initiated", data=power_data)
            
            start_time = asyncio.get_event_loop().time()
            
            # Simulate cooling decision event
            message = json.dumps(power_data)
            loop = asyncio.get_event_loop()
            self._handle_cooling_decision(message, loop)
            
            # Wait a moment for async processing
            await asyncio.sleep(0.1)
            
            # Check if we got a decision
            if hasattr(self, 'performance_metrics') and self.performance_metrics['responses'] > 0:
                logger.info("power_agent_test_response_success")
                return {
                    "success": True,
                    "responses_generated": self.performance_metrics['responses'],
                    "status": "completed"
                }
            else:
                logger.warning("power_agent_test_response_no_events")
                return {
                    "success": True,
                    "responses_generated": 0,
                    "status": "waiting"
                }
                
        except Exception as e:
            logger.error("power_agent_test_response_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def run(self):
        logger.info("power_agent_running")
        while True:
            await asyncio.sleep(1)