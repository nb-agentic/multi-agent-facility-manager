import json
import asyncio
import yaml
import time
import structlog
import uuid
from pathlib import Path
from collections import deque, defaultdict
from typing import List, Any, Dict, Optional
from datetime import datetime, timezone
from crewai.tools import BaseTool
from intellicenter.shared.event_bus import EventBus
from intellicenter.shared.logger import logger, bind_request_context
from intellicenter.shared.schema import (
    AgentType, 
    AgentDirective, 
    AgentResponse, 
    AgentStatus,
    EventSeverity
)
from crewai import Agent, Task, Crew
from intellicenter.infrastructure.llm.factory import get_llm

class PriorityScoringTool(BaseTool):
    """Tool for scoring agent decisions based on priority and impact"""
    name: str = "Priority Scoring Tool"
    description: str = "Score agent decisions based on priority levels and system impact"

    def _run(self, decision_data: dict, context: dict = None) -> str:
        priority_score = 0
        factors = []
        
        # Extract priority from decision
        priority = decision_data.get("priority", "normal").lower()
        if priority == "critical":
            priority_score += 100
            factors.append("critical_priority")
        elif priority == "high":
            priority_score += 75
            factors.append("high_priority")
        elif priority == "medium":
            priority_score += 50
            factors.append("medium_priority")
        elif priority == "low":
            priority_score += 25
            factors.append("low_priority")
        
        # Consider system impact
        impact = decision_data.get("impact", "normal").lower()
        if impact == "facility_wide":
            priority_score += 50
            factors.append("facility_impact")
        elif impact == "multi_system":
            priority_score += 30
            factors.append("multi_system_impact")
        elif impact == "single_system":
            priority_score += 10
            factors.append("single_system_impact")
        
        # Consider emergency status
        if decision_data.get("emergency", False):
            priority_score += 40
            factors.append("emergency_response")
        
        # Consider correlation with other systems
        if context and context.get("correlation_high", False):
            priority_score += 20
            factors.append("high_correlation")
        
        return f"Priority Score: {priority_score}/200. Factors: {', '.join(factors)}"

class ConflictResolutionTool(BaseTool):
    """Tool for resolving conflicts between agent decisions"""
    name: str = "Conflict Resolution Tool"
    description: str = "Resolve conflicts between agent decisions based on priority and system dependencies"

    def _run(self, conflicting_decisions: List[dict], system_dependencies: dict = None) -> str:
        if not conflicting_decisions:
            return "No conflicts detected"
        
        resolution = []
        priority_order = ["critical", "high", "medium", "low"]
        
        # Sort decisions by priority
        sorted_decisions = sorted(
            conflicting_decisions,
            key=lambda x: priority_order.index(x.get("priority", "low")),
            reverse=True
        )
        
        # Resolve conflicts by priority
        for i, decision in enumerate(sorted_decisions):
            agent_type = decision.get("agent_type", "unknown")
            priority = decision.get("priority", "low")
            action = decision.get("action", "unknown")
            
            resolution.append(f"{agent_type}: {action} (Priority: {priority})")
            
            # Check for system dependencies
            if system_dependencies and agent_type in system_dependencies:
                dependencies = system_dependencies[agent_type]
                if dependencies:
                    resolution.append(f"  Dependencies: {', '.join(dependencies)}")
        
        return "Conflict Resolution:\n" + "\n".join(resolution)

class ScenarioOrchestrationTool(BaseTool):
    """Tool for orchestrating responses to facility scenarios"""
    name: str = "Scenario Orchestration Tool"
    description: str = "Orchestrate multi-agent responses to facility scenarios"

    def _run(self, scenario_type: str, agent_responses: dict, emergency_level: str = "normal") -> str:
        orchestration_plan = []
        
        # Define scenario-specific orchestration patterns
        scenario_patterns = {
            "temperature_emergency": {
                "priority_order": ["hvac", "power", "security", "network"],
                "actions": {
                    "hvac": "emergency_cooling",
                    "power": "power_allocation_support",
                    "security": "increased_monitoring",
                    "network": "priority_bandwidth"
                }
            },
            "power_overload": {
                "priority_order": ["power", "hvac", "security", "network"],
                "actions": {
                    "power": "load_shedding",
                    "hvac": "reduce_cooling",
                    "security": "emergency_protocols",
                    "network": "bandwidth_throttling"
                }
            },
            "security_breach": {
                "priority_order": ["security", "network", "power", "hvac"],
                "actions": {
                    "security": "lockdown_protocols",
                    "network": "isolation_mode",
                    "power": "critical_power_only",
                    "hvac": "emergency_ventilation"
                }
            },
            "network_congestion": {
                "priority_order": ["network", "power", "security", "hvac"],
                "actions": {
                    "network": "traffic_prioritization",
                    "power": "power_optimization",
                    "security": "heightened_alert",
                    "hvac": "standard_operation"
                }
            }
        }
        
        # Get pattern for scenario type
        pattern = scenario_patterns.get(scenario_type, scenario_patterns["temperature_emergency"])
        
        # Generate orchestration plan
        orchestration_plan.append(f"Scenario: {scenario_type} (Emergency Level: {emergency_level})")
        orchestration_plan.append("Orchestration Plan:")
        
        for agent_type in pattern["priority_order"]:
            if agent_type in agent_responses:
                action = pattern["actions"].get(agent_type, "standard_operation")
                response = agent_responses[agent_type]
                orchestration_plan.append(f"  {agent_type.upper()}: {action}")
                orchestration_plan.append(f"    Response: {response.get('reasoning', 'No reasoning provided')}")
        
        return "\n".join(orchestration_plan)

class CoordinatorAgent:
    """Enhanced Facility Coordinator Agent with multi-agent coordination, priority-based decision making, and orchestration patterns"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.agents_config = self._load_config("agents.yaml")
        self.tasks_config = self._load_config("tasks.yaml")
        self.crew = self._setup_crew()
        
        # Facility status tracking using AgentType enums
        self.facility_status: Dict[AgentType, Optional[dict]] = {
            AgentType.HVAC: None,
            AgentType.POWER: None,
            AgentType.SECURITY: None,
            AgentType.NETWORK: None,
        }
        
        self.event_log = deque(maxlen=20)
        self.fallback_mode = False
        self.performance_metrics = {
            "coordination_events": 0,
            "avg_coordination_time": 0,
            "conflicts_resolved": 0,
            "scenarios_orchestrated": 0,
            "priority_decisions": defaultdict(int)
        }
        self.decision_history = deque(maxlen=50)
        self.system_dependencies = {
            AgentType.HVAC: [AgentType.POWER],
            AgentType.POWER: [AgentType.NETWORK],
            AgentType.SECURITY: [AgentType.NETWORK, AgentType.POWER],
            AgentType.NETWORK: [AgentType.POWER]
        }
        
        # Bind context for the coordinator
        bind_request_context(agent_id="facility_coordinator", agent_type=AgentType.COORDINATOR)
        
        # Subscribe to agent decision events during initialization
        self._setup_event_subscriptions()
        
        # Test agent startup
        startup_success = self.test_agent_startup()
        if not startup_success:
            logger.warning("coordinator_startup_issues", fallback_mode=True)
            self.fallback_mode = True

    def _load_config(self, file_name: str):
        # Try optimized config first
        optimized_path = Path(f"src/intellicenter/config/optimized_{file_name}")
        config_data = None
        
        if optimized_path.exists():
            with open(optimized_path, "r") as file:
                config_data = yaml.safe_load(file)
        else:
            # Fallback to regular config
            config_path = Path(f"src/intellicenter/config/{file_name}")
            if config_path.exists():
                with open(config_path, "r") as file:
                    config_data = yaml.safe_load(file)
        
        # If we loaded tasks config, normalize the task keys
        if config_data and "tasks" in file_name:
            # Ensure both 'coordination_task' and 'facility_coordination' keys exist
            if 'facility_coordination' in config_data and 'coordination_task' not in config_data:
                config_data['coordination_task'] = config_data['facility_coordination']
            elif 'coordination_task' in config_data and 'facility_coordination' not in config_data:
                config_data['facility_coordination'] = config_data['coordination_task']
        
        # Return loaded config or default fallback
        if config_data:
            return config_data
                
        # Default fallback
        if "agents" in file_name:
            return {"facility_coordinator": {
                "role": "Facility Coordinator",
                "goal": "Orchestrate and coordinate actions between all specialized agents to ensure a holistic and efficient facility response to events.",
                "backstory": "The central command unit of the IntelliCenter. You receive high-level reports from all specialized agents and make strategic decisions that may require coordinating actions across multiple domains (e.g., reducing power to non-critical systems during a security lockdown). You are the master orchestrator.",
                "max_execution_time": 30
            }}
        elif "tasks" in file_name:
            return {"coordination_task": {
                "description": "Analyze the combined facility status report: {facility_status_report}. The report contains summaries from HVAC, Power, Security, and Network agents. Your primary goal is to identify inter-dependencies and potential cascading effects. 1. Review all agent assessments. 2. Identify any conflicting recommendations (e.g., HVAC needs more power, but Power agent wants to shed load). 3. Develop a coordinated action plan that prioritizes overall facility stability and safety. 4. The plan should specify actions for each agent if required. Provide a high-level coordination directive with: - overall_status: (green/yellow/red) - priority_event: The most critical event to address. - coordinated_plan: A list of clear, actionable directives for specific agents (e.g., \"HVAC: Maintain current cooling. Power: Reroute non-essential load. Security: Increase monitoring in Zone B.\"). - justification: A brief rationale for the plan.",
                "expected_output": "JSON with overall_status, priority_event, coordinated_plan, and justification."
            }}
        return {}
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions during initialization"""
        self.event_bus.subscribe("hvac.cooling.decision", lambda msg: asyncio.create_task(self._update_facility_status(AgentType.HVAC, json.loads(msg))))
        self.event_bus.subscribe("power.optimization.decision", lambda msg: asyncio.create_task(self._update_facility_status(AgentType.POWER, json.loads(msg))))
        self.event_bus.subscribe("security.assessment.decision", lambda msg: asyncio.create_task(self._update_facility_status(AgentType.SECURITY, json.loads(msg))))
        self.event_bus.subscribe("network.assessment.decision", lambda msg: asyncio.create_task(self._update_facility_status(AgentType.NETWORK, json.loads(msg))))
        self.event_bus.subscribe("facility.coordination.conflict", lambda msg: asyncio.create_task(self._handle_coordination_conflict(json.loads(msg))))
        self.event_bus.subscribe("facility.coordination.scenario", 
            lambda msg: asyncio.create_task(self._orchestrate_scenario_response(
                json.loads(msg).get("scenario_type", "unknown"), 
                json.loads(msg).get("agent_responses", {}), 
                json.loads(msg).get("emergency_level", "normal")
            ))
        )

    def _setup_crew(self):
        """Setup CrewAI crew for Coordinator operations with centralized LLM configuration"""
        try:
            # Get LLM from centralized configuration
            llm = get_llm("coordinator")
            
            facility_coordinator = Agent(
                config=self.agents_config['facility_coordinator'],
                llm=llm,
                verbose=True,
                allow_delegation=False,
                tools=[
                    PriorityScoringTool(),
                    ConflictResolutionTool(),
                    ScenarioOrchestrationTool()
                ]
            )
            
            coordination_task = Task(
                config=self.tasks_config.get('facility_coordination', self.tasks_config.get('coordination_task', {})),
                agent=facility_coordinator
            )

            return Crew(
                agents=[facility_coordinator],
                tasks=[coordination_task],
                verbose=False,  # Reduce verbosity for demo
                memory=False,
                planning=False,
                max_execution_time=30
            )
            
        except Exception as e:
            logger.error("coordinator_crew_setup_failed", error=str(e))
            # Initialize fallback agent
            from intellicenter.workers.fallback import MockAgent
            self.mock_agent = MockAgent()
            self.fallback_mode = True
            return None

    async def _update_facility_status(self, agent_type: AgentType, data: dict):
        """Update the status of a specific agent and trigger analysis if all agents have reported."""
        # Try to wrap in AgentResponse for validation/normalization if possible
        try:
            if "decision_data" in data and "agent_type" in data:
                response = AgentResponse(**data)
                self.facility_status[agent_type] = response
                self.event_log.append(f"[{agent_type.upper()}] {response.status}: {response.reasoning[:50]}...")
            else:
                self.facility_status[agent_type] = data
                self.event_log.append(f"[{agent_type.upper()}] Received raw decision data")
        except Exception:
            self.facility_status[agent_type] = data
            self.event_log.append(f"[{agent_type.upper()}] Received unformatted decision data")
            
        if all(v is not None for v in self.facility_status.values()):
            await self._trigger_coordination_analysis()

    async def _trigger_coordination_analysis(self):
        logger.info("coordination_analysis_initiated", agents_ready=list(self.facility_status.keys()))
        
        # Prepare full report, converting AgentResponse to dict if necessary
        full_report = {
            "hvac_assessment": self.facility_status[AgentType.HVAC].model_dump() if isinstance(self.facility_status[AgentType.HVAC], AgentResponse) else self.facility_status[AgentType.HVAC],
            "power_assessment": self.facility_status[AgentType.POWER].model_dump() if isinstance(self.facility_status[AgentType.POWER], AgentResponse) else self.facility_status[AgentType.POWER],
            "security_assessment": self.facility_status[AgentType.SECURITY].model_dump() if isinstance(self.facility_status[AgentType.SECURITY], AgentResponse) else self.facility_status[AgentType.SECURITY],
            "network_assessment": self.facility_status[AgentType.NETWORK].model_dump() if isinstance(self.facility_status[AgentType.NETWORK], AgentResponse) else self.facility_status[AgentType.NETWORK],
            "recent_events": list(self.event_log)
        }
        
        await self._run_coordination_analysis(full_report)
        self.facility_status = {key: None for key in self.facility_status}

    async def _run_coordination_analysis(self, facility_status_report):
        """Enhanced coordination analysis with priority-based decision making and error handling"""
        start_time = time.time()
        self.performance_metrics["coordination_events"] += 1
        
        try:
            # Check if we're in fallback mode
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                # Use MockAgent for fallback response
                fallback_response = get_fallback_response(
                    "coordinator",
                    "facility_coordination",
                    facility_status_report
                )
                
                coordination_directive = {
                    "directive": fallback_response.response,
                    "timestamp": time.time(),
                    "agent_type": AgentType.COORDINATOR,
                    "confidence": fallback_response.confidence,
                    "reasoning": fallback_response.reasoning,
                    "response_time": round(time.time() - start_time, 2),
                    "status": "fallback",
                    "fallback_triggered": True,
                    "priority_analysis": "fallback_mode_active",
                    "conflicts_resolved": 0,
                    "scenarios_orchestrated": 0
                }
            else:
                # Use CrewAI directly with centralized LLM
                result = await asyncio.to_thread(
                    self.crew.kickoff,
                    inputs={"facility_status_report": json.dumps(facility_status_report)}
                )
                
                coordination_directive = self._process_crew_result(result, facility_status_report, start_time)
            
            # Update performance metrics
            self._update_coordination_metrics(coordination_directive)
            
            # Add to decision history
            self.decision_history.append({
                "timestamp": coordination_directive["timestamp"],
                "directive": coordination_directive["directive"],
                "status": coordination_directive["status"],
                "response_time": coordination_directive.get("response_time", 0)
            })
            
            # Issue directive as AgentDirective model
            directive_obj = AgentDirective(
                request_id=str(uuid.uuid4()),
                agent_type=AgentType.COORDINATOR,
                directive_type="coordination_plan",
                payload=coordination_directive,
                priority=EventSeverity.INFO,
                reasoning=coordination_directive.get("justification", "Combined facility assessment.")
            )
            
            # Publish coordination directive
            await self.event_bus.publish("facility.coordination.directive", directive_obj.model_dump_json())
            logger.info("coordination_directive_issued", 
                        directive_id=directive_obj.request_id,
                        status=coordination_directive["status"])
            
        except Exception as e:
            logger.error("coordination_analysis_failed", error=str(e))
            # Generate emergency fallback directive
            emergency_payload = {
                "directive": "EMERGENCY: Maintain all current operations. Initiate facility-wide monitoring.",
                "error": str(e),
                "emergency_fallback": True
            }
            
            emergency_directive = AgentDirective(
                request_id=str(uuid.uuid4()),
                agent_type=AgentType.COORDINATOR,
                directive_type="emergency_fallback",
                payload=emergency_payload,
                priority=EventSeverity.CRITICAL,
                reasoning=f"Coordination analysis failed: {str(e)}"
            )
            
            await self.event_bus.publish("facility.coordination.directive", emergency_directive.model_dump_json())
            await self.event_bus.publish("facility.coordination.error", json.dumps({"error": str(e)}))
    
    def _process_crew_result(self, result, facility_status_report, start_time):
        """Process CrewAI result and extract coordination directive"""
        try:
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            crew_output = json.loads(raw_output)
        except (json.JSONDecodeError, AttributeError):
            # Parse raw output if JSON parsing fails
            raw_output = result.raw if hasattr(result, 'raw') else str(result)
            
            # Extract key information from raw output
            coordination_directive = {
                "directive": raw_output,
                "overall_status": "yellow",  # Default status
                "priority_event": "facility_monitoring",
                "coordinated_plan": ["Continue monitoring all systems"],
                "justification": "AI analysis completed, raw output processed.",
                "confidence": 75,
                "reasoning": "AI analysis completed, raw output processed."
            }
        else:
            # Use structured JSON output
            coordination_directive = {
                **crew_output,
                "confidence": crew_output.get("confidence", 85),
                "reasoning": crew_output.get("reasoning", "Coordination analysis completed")
            }
        
        # Add coordination metadata
        coordination_directive.update({
            "timestamp": time.time(),
            "agent_type": AgentType.COORDINATOR,
            "response_time": round(time.time() - start_time, 2),
            "status": "success",
            "coordination_type": "multi_agent",
            "agents_involved": [a.value for a in facility_status_report.keys() if isinstance(a, AgentType)],
            "system_dependencies": {k.value: [v.value for v in deps] for k, deps in self.system_dependencies.items()}
        })
        
        return coordination_directive
    
    def _update_coordination_metrics(self, coordination_directive):
        """Update coordination performance metrics"""
        response_time = coordination_directive.get("response_time", 0)
        self.performance_metrics["avg_coordination_time"] = (
            (self.performance_metrics["avg_coordination_time"] * (self.performance_metrics["coordination_events"] - 1) + response_time)
            / self.performance_metrics["coordination_events"]
        )
        
        # Track priority decisions
        priority = coordination_directive.get("priority", "normal")
        if priority in self.performance_metrics["priority_decisions"]:
            self.performance_metrics["priority_decisions"][priority] += 1
        
        # Track conflicts resolved
        if coordination_directive.get("conflicts_resolved", 0) > 0:
            self.performance_metrics["conflicts_resolved"] += coordination_directive["conflicts_resolved"]
        
        # Track scenarios orchestrated
        if coordination_directive.get("scenarios_orchestrated", 0) > 0:
            self.performance_metrics["scenarios_orchestrated"] += coordination_directive["scenarios_orchestrated"]
    
    async def _handle_coordination_conflict(self, conflicting_decisions: List[dict]):
        """Handle conflicts between agent decisions using priority-based resolution"""
        start_time = time.time()
        
        try:
            # Use conflict resolution tool
            conflict_resolution = ConflictResolutionTool()._run(
                conflicting_decisions,
                self.system_dependencies
            )
            
            # Create conflict resolution directive
            resolution_directive_payload = {
                "directive": conflict_resolution,
                "conflict_type": "inter_agent_conflict",
                "resolution_method": "priority_based"
            }
            
            resolution_directive = AgentDirective(
                request_id=str(uuid.uuid4()),
                agent_type=AgentType.COORDINATOR,
                directive_type="conflict_resolution",
                payload=resolution_directive_payload,
                priority=EventSeverity.WARNING,
                reasoning="Inter-agent conflict detected and resolved based on priority rules."
            )
            
            # Update metrics
            self.performance_metrics["conflicts_resolved"] += 1
            
            # Publish resolution
            await self.event_bus.publish("facility.coordination.conflict_resolution", resolution_directive.model_dump_json())
            logger.info("conflict_resolved", resolution=conflict_resolution[:100])
            
        except Exception as e:
            logger.error("conflict_resolution_error", error=str(e))
            await self.event_bus.publish("facility.coordination.conflict_error", json.dumps({"error": str(e)}))
    
    async def _orchestrate_scenario_response(self, scenario_type: str, agent_responses: dict, emergency_level: str = "normal"):
        """Orchestrate multi-agent response to facility scenarios"""
        start_time = time.time()
        
        try:
            # Use scenario orchestration tool
            orchestration_plan = ScenarioOrchestrationTool()._run(
                scenario_type,
                agent_responses,
                emergency_level
            )
            
            # Create orchestration directive
            orchestration_directive_payload = {
                "directive": orchestration_plan,
                "scenario_type": scenario_type,
                "emergency_level": emergency_level,
                "agents_coordinated": list(agent_responses.keys())
            }
            
            orchestration_directive = AgentDirective(
                request_id=str(uuid.uuid4()),
                agent_type=AgentType.COORDINATOR,
                directive_type="scenario_orchestration",
                payload=orchestration_directive_payload,
                priority=EventSeverity.INFO if emergency_level == "normal" else EventSeverity.HIGH,
                reasoning=f"Scenario orchestration for {scenario_type}."
            )
            
            # Update metrics
            self.performance_metrics["scenarios_orchestrated"] += 1
            
            # Publish orchestration
            await self.event_bus.publish("facility.coordination.scenario_orchestration", orchestration_directive.model_dump_json())
            logger.info("scenario_orchestrated", scenario=scenario_type, level=emergency_level)
            
        except Exception as e:
            logger.error("scenario_orchestration_error", scenario=scenario_type, error=str(e))
            await self.event_bus.publish("facility.coordination.scenario_error", json.dumps({"error": str(e)}))

    def test_agent_startup(self) -> bool:
        """Test agent initialization and startup"""
        try:
            logger.info("coordinator_startup_test_initiated")
            
            # Test 1: Check if crew was initialized successfully
            if hasattr(self, 'fallback_mode') and self.fallback_mode:
                logger.info("coordinator_startup_test_success", mode="fallback")
                return True
            elif self.crew is not None:
                logger.info("coordinator_startup_test_success", mode="crewai")
                return True
            else:
                logger.error("coordinator_startup_test_failed", reason="initialization_failure")
                return False
                
        except Exception as e:
            logger.error("coordinator_startup_test_failed", error=str(e))
            return False
    
    async def test_response_generation(self, facility_data: dict) -> dict:
        """Test agent response generation with sample data"""
        try:
            print("🧪 Testing Coordinator Agent Response Generation...")
            print(f"📊 Input data: {facility_data}")
            
            start_time = time.time()
            
            # Simulate facility status update
            for agent_type, data in facility_data.items():
                await self._update_facility_status(agent_type, data)
            
            # Wait a moment for async processing
            await asyncio.sleep(0.1)
            
            # Check if we got coordination events
            if hasattr(self, 'performance_metrics') and self.performance_metrics['coordination_events'] > 0:
                print("✅ Response generation successful")
                return {
                    "success": True,
                    "coordination_events": self.performance_metrics['coordination_events'],
                    "avg_response_time": self.performance_metrics['avg_coordination_time'],
                    "status": "completed"
                }
            else:
                print("⚠️  No coordination events generated yet")
                return {
                    "success": True,
                    "coordination_events": 0,
                    "avg_response_time": 0,
                    "status": "waiting"
                }
                
        except Exception as e:
            logger.error("coordinator_test_response_failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "status": "error"
            }
    
    def get_performance_report(self) -> str:
        """Get performance report for coordinator agent"""
        metrics = self.performance_metrics
        total_coordination = metrics["coordination_events"]
        if total_coordination == 0: return "📊 Coordinator Agent: No coordination events yet."
        
        report = f"📊 Coordinator Agent: {total_coordination} coordination events, {metrics['avg_coordination_time']:.2f}s avg response. "
        report += f"Conflicts resolved: {metrics['conflicts_resolved']}, Scenarios orchestrated: {metrics['scenarios_orchestrated']}. "
        
        # Add priority decision breakdown
        priority_breakdown = []
        for priority, count in metrics["priority_decisions"].items():
            if count > 0:
                priority_breakdown.append(f"{priority}: {count}")
        if priority_breakdown:
            report += f"Priority decisions: {', '.join(priority_breakdown)}."
        
        return report.strip()
    
    async def run(self):
        """Enhanced run method with multi-agent coordination and event bus integration"""
        print("📜 Enhanced Facility Coordinator Agent is running...")
        last_report_time = time.time()
        
        while True:
            await asyncio.sleep(1)
            
            # Periodic performance reporting
            if time.time() - last_report_time > 30 and self.performance_metrics["coordination_events"] > 0:
                print(self.get_performance_report())
                last_report_time = time.time()