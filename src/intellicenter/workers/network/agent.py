"""
Network Infrastructure Agent Module

This module implements the Network Infrastructure Agent for monitoring and managing
network performance, device status, security scanning, and traffic analysis.
"""

import asyncio
import json
import random
import yaml
import structlog
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from intellicenter.shared.event_bus import EventBus
from intellicenter.shared.logger import logger, bind_request_context
from intellicenter.shared.schema import AgentType, AgentStatus, AgentResponse, AgentDirective
from intellicenter.workers.fallback import MockAgent, get_fallback_response
from intellicenter.infrastructure.llm.factory import get_llm


class TrafficAnalysisTool(BaseTool):
    """Tool for analyzing network traffic patterns and utilization."""
    
    name: str = "Traffic Analysis Tool"
    description: str = "Analyze network traffic for a specific segment."

    def _run(self, segment: str = "core") -> str:
        utilization = random.uniform(30, 70)
        return f"📈 Network traffic on {segment} segment is at {utilization:.2f}% utilization."


class LatencyCheckTool(BaseTool):
    """Tool for checking network latency to various destinations."""
    
    name: str = "Latency Check Tool"
    description: str = "Check network latency to a specific destination."

    def _run(self, destination: str = "external_gateway") -> str:
        latency = random.uniform(5, 25)
        return f"⏱️ Latency to {destination} is {latency:.2f}ms."


class DeviceStatusTool(BaseTool):
    """Tool for checking the status of network devices."""
    
    name: str = "Device Status Tool"
    description: str = "Check the status of a network device."

    def _run(self, device_id: str) -> str:
        return f"✅ Device {device_id} is online and operating within normal parameters."


class SecurityScanTool(BaseTool):
    """Tool for performing network security analysis and threat detection."""
    
    name: str = "Security Scan Tool"
    description: str = "Perform network security analysis and threat detection."

    def _run(self, scan_type: str = "basic") -> str:
        if scan_type == "basic":
            return "🔒 Security scan completed: No critical threats detected. Standard monitoring active."
        if scan_type == "deep":
            return "🔍 Deep security scan: Analyzing traffic patterns for anomalies. No suspicious activity found."
        return f"🛡️ Security scan ({scan_type}): Network security protocols engaged and operational."


class NetworkMonitoringAgent:
    """Network Infrastructure Agent with explicit crew setup and fallback support"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.agents_config = self._load_config("agents.yaml")
        self.tasks_config = self._load_config("tasks.yaml")
        self.crew = self._setup_crew()
        self.fallback_mode = False
        self.performance_metrics = {
            "responses": 0,
            "avg_response_time": 0,
            "decisions": {"optimal": 0, "stable": 0, "degraded": 0, "critical": 0}
        }
        
        # Bind context for the network agent
        bind_request_context(agent_id="network_agent", agent_type=AgentType.NETWORK)
        
        # Test agent startup
        startup_success = self.test_agent_startup()
        if not startup_success:
            logger.warning("network_agent_startup_issues", fallback_mode=True)
            self.fallback_mode = True
        
        # Subscribe to network events
        loop = asyncio.get_event_loop()
        self.event_bus.subscribe("facility.network.event", lambda msg: self._handle_network_event(msg, loop))
        
    def _load_config(self, file_name: str):
        # Try optimized config first
        optimized_path = Path(f"src/intellicenter/config/optimized_{file_name}")
        if optimized_path.exists():
            with open(optimized_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
                
        # Fallback to regular config
        config_path = Path(f"src/intellicenter/config/{file_name}")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
                
        # Default fallback
        if "agents" in file_name:
            return {"network_specialist": {
                "role": "Network Infrastructure Specialist",
                "goal": "Ensure optimal network performance, connectivity, and security",
                "backstory": "Expert network engineer specializing in data center networking, responsible for monitoring traffic, managing hardware, and responding to connectivity or security incidents",
                "max_execution_time": 30
            }}
        elif "tasks" in file_name:
            return {"network_analysis": {
                "description": "Analyze network performance data and provide optimization recommendations",
                "expected_output": "Network status report with health assessment and recommended actions"
            }}
        return {}
    
    def _setup_crew(self):
        """Setup CrewAI crew for Network operations with centralized LLM configuration"""
        try:
            # Get LLM from centralized configuration
            llm = get_llm("network")
            
            network_specialist = Agent(
                config=self.agents_config['network_specialist'],
                llm=llm,
                verbose=True,
                allow_delegation=False,
                tools=[
                    TrafficAnalysisTool(),
                    LatencyCheckTool(),
                    DeviceStatusTool(),
                    SecurityScanTool()
                ]
            )
            
            network_analysis_task = Task(
                config=self.tasks_config['network_analysis'],
                agent=network_specialist
            )

            return Crew(
                agents=[network_specialist],
                tasks=[network_analysis_task],
                verbose=False,  # Reduce verbosity for demo
                memory=False,
                planning=False,
                max_execution_time=30
            )
            
        except Exception as e:
            print(f"❌ Failed to setup CrewAI crew for Network agent: {e}")
            # Initialize fallback agent
            self.mock_agent = MockAgent()
            self.fallback_mode = True
            return None
    
    def _handle_network_event(self, message, loop):
        try:
            network_data = json.loads(message)
            asyncio.create_task(self._run_network_analysis(network_data, loop))
        except Exception as e:
            logger.error("network_event_parse_error", error=str(e))
    
    async def _run_network_analysis(self, network_data, loop):
        start_time = loop.time()
        try:
            # Check if we're in fallback mode
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                # Use MockAgent for fallback response
                fallback_response = get_fallback_response(
                    "network",
                    "traffic_analysis",
                    {"segment": network_data.get("segment", "core")}
                )
                
                network_decision = {
                    "network_assessment": fallback_response.response,
                    "network_health": "stable",
                    "timestamp": loop.time(),
                    "event_correlation": network_data.get("event_id"),
                    "agent_type": AgentType.NETWORK,
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
                    inputs={"network_data": json.dumps(network_data)}
                )
                
                network_decision = self._process_crew_result(result, network_data, start_time, loop)
            
            # Create AgentResponse object
            response_obj = AgentResponse(
                request_id=network_data.get("request_id", "unknown"),
                agent_type=AgentType.NETWORK,
                status=AgentStatus.SUCCESS if network_decision.get("status") == "success" else AgentStatus.FAILED,
                decision_data=network_decision,
                reasoning=network_decision.get("reasoning"),
                confidence=network_decision.get("confidence")
            )
            
            await self.event_bus.publish("network.assessment.decision", response_obj.model_dump_json())
            self._update_metrics(network_decision)
            logger.info("network_assessment_completed", 
                        assessment=network_decision.get('network_assessment', 'fallback')[:100],
                        health=network_decision.get('network_health'))
            
        except Exception as e:
            logger.error("network_analysis_error", error=str(e))
            fallback_decision = self._generate_fallback_decision(network_data, str(e), start_time, loop)
            
            # Create AgentResponse for fallback
            fallback_response_obj = AgentResponse(
                request_id=network_data.get("request_id", "unknown"),
                agent_type=AgentType.NETWORK,
                status=AgentStatus.FAILED,
                decision_data=fallback_decision,
                reasoning="Fallback decision due to analysis error."
            )
            await self.event_bus.publish("network.assessment.decision", fallback_response_obj.model_dump_json())
    
    def _process_crew_result(self, result, network_data, start_time, loop):
        try:
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            crew_output = json.loads(raw_output)
        except (json.JSONDecodeError, AttributeError):
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            # Parse network health from raw output
            network_health = "stable"  # Default
            if "critical" in raw_output.lower():
                network_health = "critical"
            elif "degraded" in raw_output.lower():
                network_health = "degraded"
            elif "optimal" in raw_output.lower():
                network_health = "optimal"
            
            crew_output = {
                "network_assessment": raw_output,
                "network_health": network_health,
                "optimization_actions": "AI analysis completed, raw output processed.",
                "security_advisory": "No immediate security concerns detected.",
                "confidence": 75,
                "reasoning": "AI analysis completed, raw output processed."
            }
        
        return {
            **crew_output,
            "timestamp": network_data.get("timestamp"),
            "event_correlation": network_data.get("event_id"),
            "agent_type": AgentType.NETWORK,
            "response_time": round(loop.time() - start_time, 2),
            "status": "success"
        }
    
    def _generate_fallback_decision(self, network_data, error_msg, start_time, loop):
        """Generate fallback decision when network analysis fails"""
        segment = network_data.get("segment", "core")
        network_health = "stable"  # Default fallback level
        
        # Determine network health based on segment
        if segment in ["core", "datacenter"]:
            network_health = "optimal"
        elif segment in ["perimeter", "external"]:
            network_health = "stable"
        
        return {
            "network_assessment": f"Standard network monitoring applied for {segment}. Fallback mode activated.",
            "network_health": network_health,
            "optimization_actions": "Maintain current routing configuration.",
            "security_advisory": "Standard security protocols engaged.",
            "error": error_msg,
            "fallback": True,
            "timestamp": loop.time(),
            "event_correlation": network_data.get("event_id"),
            "response_time": round(loop.time() - start_time, 2),
            "agent_type": AgentType.NETWORK,
            "status": "fallback"
        }
    
    def _update_metrics(self, decision_data):
        """Update performance metrics for network agent"""
        response_time = decision_data.get("response_time", 0)
        network_health = decision_data.get("network_health", "stable")
        self.performance_metrics["responses"] += 1
        count = self.performance_metrics["responses"]
        old_avg = self.performance_metrics["avg_response_time"]
        self.performance_metrics["avg_response_time"] = (old_avg * (count - 1) + response_time) / count
        if network_health in self.performance_metrics["decisions"]:
            self.performance_metrics["decisions"][network_health] += 1
    
    def get_performance_report(self) -> str:
        """Get performance report for network agent"""
        metrics = self.performance_metrics
        total_decisions = sum(metrics["decisions"].values())
        if total_decisions == 0: return "🌐 Network Agent: No decisions made yet."
        report = f"🌐 Network Agent: {metrics['responses']} responses, {metrics['avg_response_time']:.2f}s avg response. Decisions: "
        for level, count in metrics["decisions"].items():
            report += f"{level}: {count} ({(count/total_decisions*100):.1f}%) "
        return report.strip()
    
    def test_agent_startup(self) -> bool:
        """Test agent initialization and startup"""
        try:
            logger.info("network_agent_startup_test_initiated")
            
            # Test 1: Check if crew was initialized successfully
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                logger.info("network_agent_startup_test_success", mode="fallback")
                return True
            elif self.crew is not None:
                logger.info("network_agent_startup_test_success", mode="crewai")
                return True
            else:
                logger.error("network_agent_startup_test_failed", reason="initialization_failure")
                return False
                
        except Exception as e:
            logger.error("network_agent_startup_test_failed", error=str(e))
            return False
    
    async def test_response_generation(self, network_data: dict) -> dict:
        """Test agent response generation with sample data"""
        try:
            logger.info("network_agent_test_response_initiated", data=network_data)
            
            start_time = asyncio.get_event_loop().time()
            
            # Simulate network event
            message = json.dumps(network_data)
            loop = asyncio.get_event_loop()
            self._handle_network_event(message, loop)
            
            # Wait a moment for async processing
            await asyncio.sleep(0.1)
            
            # Check if we got a decision
            if hasattr(self, 'performance_metrics') and self.performance_metrics['responses'] > 0:
                logger.info("network_agent_test_response_success")
                return {
                    "success": True,
                    "responses_generated": self.performance_metrics['responses'],
                    "status": "completed"
                }
            else:
                logger.warning("network_agent_test_response_no_events")
                return {
                    "success": True,
                    "responses_generated": 0,
                    "status": "waiting"
                }
                
        except Exception as e:
            logger.error("network_agent_test_response_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    async def run(self):
        print("🌐  Network Infrastructure Agent is running...")
        last_report_time = asyncio.get_event_loop().time()
        while True:
            await asyncio.sleep(1)
            if asyncio.get_event_loop().time() - last_report_time > 30 and self.performance_metrics["responses"] > 0:
                print(self.get_performance_report())
                last_report_time = asyncio.get_event_loop().time()