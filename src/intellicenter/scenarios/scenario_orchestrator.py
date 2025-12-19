"""
Scenario Orchestrator for Demo Scenarios

This module provides orchestration capabilities for demo scenarios including:
- Cooling Crisis Response
- Security Breach Response  
- Energy Optimization

Features:
- Scenario state management
- Reset functionality between demos
- Event bus integration for coordination
- Timing constraints and completion tracking
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Callable

from intellicenter.shared.event_bus import EventBus
from intellicenter.shared.logger import logger
from intellicenter.shared.schema import (
    AgentType,
    ScenarioConfig,
    ScenarioResult,
    ScenarioState,
    ScenarioStep,
    ScenarioType,
)


# Removed local Enum and dataclass definitions as they are now in shared.schema


class ScenarioOrchestrator:
    """
    Orchestrates demo scenarios for IntelliCenter system.
    
    Provides comprehensive scenario management including state tracking,
    event coordination, timing constraints, and reset functionality.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logger.bind(component="scenario_orchestrator")
        
        # Scenario state management
        self.current_scenario: Optional[ScenarioConfig] = None
        self.scenario_state: ScenarioState = ScenarioState.IDLE
        self.scenario_result: Optional[ScenarioResult] = None
        
        # Execution tracking
        self.start_time: Optional[datetime] = None
        self.current_step: int = 0
        self.step_start_time: Optional[datetime] = None
        self.agent_responses: Dict[str, List[Dict[str, Any]]] = {}
        self.scenario_events: List[Dict[str, Any]] = []
        
        # Event handlers and subscriptions
        self.event_handlers: Dict[str, Callable] = {}
        self.active_subscriptions: List[str] = []
        
        # Timing and constraints
        self.scenario_timeout_task: Optional[asyncio.Task] = None
        self.step_timeout_task: Optional[asyncio.Task] = None
        
        # Built-in scenario definitions
        self.scenario_definitions = self._create_scenario_definitions()
        
        # Import routine maintenance scenario
        from .routine_maintenance import RoutineMaintenanceScenario
        self.RoutineMaintenanceScenario = RoutineMaintenanceScenario
        
        # Setup base event subscriptions
        self._setup_base_subscriptions()
    
    def _create_scenario_definitions(self) -> Dict[ScenarioType, ScenarioConfig]:
        """Create built-in demo scenario definitions"""
        scenarios = {}
        
        # Cooling Crisis Scenario
        scenarios[ScenarioType.COOLING_CRISIS] = ScenarioConfig(
            scenario_id="cooling_crisis_demo",
            name="Cooling Crisis Response",
            description="Demonstrates coordinated response to cooling system failure",
            scenario_type=ScenarioType.COOLING_CRISIS,
            max_duration_seconds=120.0,  # 2 minutes
            steps=[
                ScenarioStep(
                    step_id="normal_operation",
                    description="Normal facility operation",
                    event_type="demo.scenario.start",
                    event_data={"scenario": "cooling_crisis", "phase": "normal"},
                    delay_seconds=2.0
                ),
                ScenarioStep(
                    step_id="temperature_rise",
                    description="Initial temperature increase detected",
                    event_type="hvac.temperature.changed",
                    event_data={"temperature": 26.5, "trend": "rising", "rate": 0.5, "location": "server_room_main"},
                    delay_seconds=3.0,
                    expected_responses=["hvac.cooling.decision"],
                    required_agents=[AgentType.HVAC]
                ),
                ScenarioStep(
                    step_id="cooling_failure",
                    description="Primary cooling system failure",
                    event_type="hvac.system.failure",
                    event_data={"system": "primary_cooling", "severity": "critical", "backup_available": True},
                    delay_seconds=2.0,
                    expected_responses=["hvac.cooling.decision", "facility.coordination.directive"],
                    required_agents=[AgentType.HVAC, AgentType.COORDINATOR]
                ),
                ScenarioStep(
                    step_id="emergency_temperature",
                    description="Emergency temperature threshold reached",
                    event_type="hvac.temperature.changed",
                    event_data={"temperature": 30.0, "trend": "rising", "rate": 1.2, "emergency": True},
                    delay_seconds=5.0,
                    expected_responses=["hvac.cooling.decision", "power.optimization.decision", "facility.coordination.directive"],
                    required_agents=[AgentType.HVAC, AgentType.POWER, AgentType.COORDINATOR],
                    timeout_seconds=15.0
                ),
                ScenarioStep(
                    step_id="coordination_response",
                    description="Multi-agent coordination response",
                    event_type="facility.coordination.scenario",
                    event_data={"scenario_type": "temperature_emergency", "emergency_level": "critical", "agent_responses": {}},
                    delay_seconds=1.0,
                    expected_responses=["facility.coordination.scenario_orchestration"],
                    required_agents=[AgentType.COORDINATOR]
                )
            ],
            success_criteria={
                "max_response_time": 15.0,
                "required_agents_responded": [AgentType.HVAC, AgentType.POWER, AgentType.COORDINATOR],
                "coordination_achieved": True,
                "temperature_stabilized": True
            },
            cleanup_steps=[
                ScenarioStep(
                    step_id="reset_temperature",
                    description="Reset temperature to normal",
                    event_type="hvac.temperature.changed",
                    event_data={"temperature": 22.0, "trend": "stable", "status": "normal"},
                    delay_seconds=1.0
                ),
                ScenarioStep(
                    step_id="reset_systems",
                    description="Reset all systems to normal operation",
                    event_type="demo.scenario.reset",
                    event_data={"scenario": "cooling_crisis", "status": "reset"},
                    delay_seconds=1.0
                )
            ]
        )
        
        # Security Breach Scenario
        scenarios[ScenarioType.SECURITY_BREACH] = ScenarioConfig(
            scenario_id="security_breach_demo",
            name="Security Breach Response",
            description="Demonstrates coordinated lockdown response to security breach",
            scenario_type=ScenarioType.SECURITY_BREACH,
            max_duration_seconds=90.0,  # 1.5 minutes
            steps=[
                ScenarioStep(
                    step_id="normal_security",
                    description="Normal security operation",
                    event_type="demo.scenario.start",
                    event_data={"scenario": "security_breach", "phase": "normal"},
                    delay_seconds=2.0
                ),
                ScenarioStep(
                    step_id="suspicious_access",
                    description="Suspicious access attempt detected",
                    event_type="security.access.suspicious",
                    event_data={"location": "server_room_a", "severity": "medium", "user_id": "unknown_user_001", "attempts": 3},
                    delay_seconds=3.0,
                    expected_responses=["security.assessment.decision"],
                    required_agents=[AgentType.SECURITY]
                ),
                ScenarioStep(
                    step_id="breach_confirmed",
                    description="Security breach confirmed",
                    event_type="security.breach.detected",
                    event_data={"location": "server_room_a", "severity": "high", "breach_type": "unauthorized_access"},
                    delay_seconds=2.0,
                    expected_responses=["security.assessment.decision", "network.assessment.decision"],
                    required_agents=[AgentType.SECURITY, AgentType.NETWORK]
                ),
                ScenarioStep(
                    step_id="lockdown_initiated",
                    description="Facility lockdown initiated",
                    event_type="security.lockdown.initiated",
                    event_data={"scope": "facility_wide", "duration": "indefinite", "reason": "security_breach"},
                    delay_seconds=1.0,
                    expected_responses=["security.assessment.decision", "network.assessment.decision", "facility.coordination.directive"],
                    required_agents=[AgentType.SECURITY, AgentType.NETWORK, AgentType.COORDINATOR],
                    timeout_seconds=10.0
                ),
                ScenarioStep(
                    step_id="coordination_lockdown",
                    description="Coordinated lockdown response",
                    event_type="facility.coordination.scenario",
                    event_data={"scenario_type": "security_breach", "emergency_level": "high", "agent_responses": {}},
                    delay_seconds=1.0,
                    expected_responses=["facility.coordination.scenario_orchestration"],
                    required_agents=[AgentType.COORDINATOR]
                )
            ],
            success_criteria={
                "max_response_time": 10.0,
                "required_agents_responded": ["security_agent", "network_agent", "coordinator_agent"],
                "lockdown_coordinated": True,
                "access_denied": True
            },
            cleanup_steps=[
                ScenarioStep(
                    step_id="lift_lockdown",
                    description="Lift security lockdown",
                    event_type="security.lockdown.lifted",
                    event_data={"scope": "facility_wide", "reason": "demo_complete"},
                    delay_seconds=1.0
                ),
                ScenarioStep(
                    step_id="reset_security",
                    description="Reset security systems to normal",
                    event_type="demo.scenario.reset",
                    event_data={"scenario": "security_breach", "status": "reset"},
                    delay_seconds=1.0
                )
            ]
        )
        
        # Energy Optimization Scenario
        scenarios[ScenarioType.ENERGY_OPTIMIZATION] = ScenarioConfig(
            scenario_id="energy_optimization_demo",
            name="Energy Optimization",
            description="Demonstrates proactive energy cost optimization",
            scenario_type=ScenarioType.ENERGY_OPTIMIZATION,
            max_duration_seconds=180.0,  # 3 minutes
            steps=[
                ScenarioStep(
                    step_id="energy_analysis",
                    description="Energy consumption analysis and optimization opportunity identification",
                    event_type="power.consumption.changed",
                    event_data={"consumption": 85.0, "trend": "high", "optimization_opportunity": True, "threshold_exceeded": True},
                    delay_seconds=2.0,
                    expected_responses=["power.optimization.decision"],
                    required_agents=["power_agent"]
                ),
                ScenarioStep(
                    step_id="pre_cooling_strategy",
                    description="Pre-cooling strategy implementation for energy arbitrage",
                    event_type="hvac.temperature.changed",
                    event_data={"temperature": 20.0, "trend": "decreasing", "rate": -0.5, "pre_cooling": True, "strategy": "energy_arbitrage"},
                    delay_seconds=3.0,
                    expected_responses=["hvac.cooling.decision"],
                    required_agents=["hvac_agent"]
                ),
                ScenarioStep(
                    step_id="power_coordination",
                    description="Power system optimization and load balancing",
                    event_type="power.optimization.decision",
                    event_data={"optimization_level": "aggressive", "reasoning": "Energy cost optimization required", "agent_type": "power_specialist", "price_based": True},
                    delay_seconds=2.0,
                    expected_responses=["power.optimization.decision"],
                    required_agents=["power_agent"]
                ),
                ScenarioStep(
                    step_id="coordination_response",
                    description="Coordinated response between power and HVAC systems",
                    event_type="facility.coordination.scenario",
                    event_data={"scenario_type": "power_overload", "emergency_level": "normal", "agent_responses": {}},
                    delay_seconds=1.0,
                    expected_responses=["facility.coordination.directive"],
                    required_agents=[AgentType.COORDINATOR]
                ),
                ScenarioStep(
                    step_id="optimization_verification",
                    description="Verify optimization success and system stabilization",
                    event_type="hvac.temperature.changed",
                    event_data={"temperature": 22.0, "trend": "stable", "rate": 0.0, "verification_required": True, "optimization_complete": True},
                    delay_seconds=2.0,
                    expected_responses=["hvac.cooling.decision", "power.optimization.decision", "facility.coordination.directive"],
                    required_agents=["power_agent", "hvac_agent", "coordinator_agent"],
                    timeout_seconds=15.0
                )
            ],
            success_criteria={
                "max_response_time": 15.0,
                "required_agents_responded": ["power_agent", "hvac_agent", "coordinator_agent"],
                "coordination_achieved": True,
                "energy_savings_achieved": True,
                "optimization_complete": True
            },
            cleanup_steps=[
                ScenarioStep(
                    step_id="system_stabilization",
                    description="System stabilization completed",
                    event_type="hvac.temperature.changed",
                    event_data={"temperature": 22.0, "trend": "stable", "rate": 0.0, "stabilization_status": "All systems operating at optimal efficiency"},
                    delay_seconds=1.0
                ),
                ScenarioStep(
                    step_id="reset_energy",
                    description="Reset energy systems to normal",
                    event_type="demo.scenario.reset",
                    event_data={"scenario": "energy_optimization", "status": "reset"},
                    delay_seconds=1.0
                )
            ]
        )
        
        # Routine Maintenance Scenario
        scenarios[ScenarioType.ROUTINE_MAINTENANCE] = ScenarioConfig(
            scenario_id="routine_maintenance_demo",
            name="Routine Maintenance",
            description="Demonstrates simple HVAC-Network coordination for routine maintenance",
            scenario_type=ScenarioType.ROUTINE_MAINTENANCE,
            max_duration_seconds=60.0,  # 1 minute - quick completion for demo
            steps=[
                ScenarioStep(
                    step_id="maintenance_detection",
                    description="Detect scheduled maintenance window",
                    event_type="demo.scenario.start",
                    event_data={"scenario": "routine_maintenance", "phase": "detection"},
                    delay_seconds=1.0
                ),
                ScenarioStep(
                    step_id="hvac_system_check",
                    description="Perform HVAC system status check",
                    event_type="hvac.system.status",
                    event_data={"system": "hvac", "status": "check", "location": "server_room_main"},
                    delay_seconds=5.0,
                    expected_responses=["hvac.system.status"],
                    required_agents=["hvac_agent"]
                ),
                ScenarioStep(
                    step_id="network_connectivity_check",
                    description="Validate network connectivity and performance",
                    event_type="network.connectivity.status",
                    event_data={"system": "network", "status": "validation", "location": "server_room_main"},
                    delay_seconds=5.0,
                    expected_responses=["network.connectivity.status"],
                    required_agents=["network_agent"]
                ),
                ScenarioStep(
                    step_id="coordination_completion",
                    description="Complete coordination and verification",
                    event_type="facility.maintenance.completion",
                    event_data={"scenario_complete": True, "location": "server_room_main"},
                    delay_seconds=3.0,
                    expected_responses=["facility.maintenance.completion"],
                    required_agents=[AgentType.COORDINATOR]
                )
            ],
            success_criteria={
                "maintenance_completed": True,
                "systems_validated": True,
                "coordination_achieved": True
            },
            cleanup_steps=[
                ScenarioStep(
                    step_id="reset_maintenance_state",
                    description="Reset maintenance state",
                    event_type="facility.maintenance.reset",
                    event_data={"reset": True},
                    delay_seconds=1.0
                )
            ]
        )
        
        return scenarios
    
    def _setup_base_subscriptions(self):
        """Setup base event subscriptions for scenario coordination"""
        # Subscribe to agent response events
        agent_events = [
            "hvac.cooling.decision",
            "power.optimization.decision",
            "security.assessment.decision",
            "network.assessment.decision",
            "facility.coordination.directive",
            "facility.coordination.scenario_orchestration",
            "energy_optimization.energy_optimization_initiated",
            "energy_optimization.energy_optimization_completed",
            "energy_optimization.energy_optimization_resolving",
            "hvac.system.status",
            "network.connectivity.status",
            "facility.maintenance.response"
        ]
        
        for event_type in agent_events:
            handler = self._create_response_handler(event_type)
            self.event_bus.subscribe(event_type, handler)
            self.event_handlers[event_type] = handler
    
    def _create_response_handler(self, event_type: str) -> Callable:
        """Create a response handler for a specific event type"""
        async def handler(message: str):
            try:
                # Parse message
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        data = {"raw_message": message}
                else:
                    data = message
                
                # Extract agent type from event or data
                agent_type = self._extract_agent_type(event_type, data)
                
                # Record response
                response_record = {
                    "event_type": event_type,
                    "timestamp": datetime.now(timezone.utc),
                    "agent_type": agent_type,
                    "data": data,
                    "scenario_step": self.current_step if self.current_scenario else None
                }
                
                # Store agent response
                if agent_type not in self.agent_responses:
                    self.agent_responses[agent_type] = []
                self.agent_responses[agent_type].append(response_record)
                
                # Store scenario event
                self.scenario_events.append({
                    "type": "agent_response",
                    "timestamp": datetime.now(timezone.utc),
                    "event_type": event_type,
                    "agent_type": agent_type,
                    "data": data
                })
                
                self.logger.debug(f"Recorded response: {event_type} from {agent_type}")
                
            except Exception as e:
                self.logger.error(f"Error in response handler for {event_type}: {e}")
        
        return handler
    
    def _extract_agent_type(self, event_type: str, data: Dict[str, Any]) -> str:
        """Extract agent type from event type or data"""
        # Try to get from data first
        if "agent_type" in data:
            return data["agent_type"]
        
        # Extract from event type
        if "hvac." in event_type:
            return "hvac_agent"
        elif "power." in event_type:
            return "power_agent"
        elif "security." in event_type:
            return "security_agent"
        elif "network." in event_type:
            return "network_agent"
        elif "facility.coordination." in event_type or "facility.maintenance." in event_type:
            return "coordinator_agent"
        else:
            return "unknown_agent"
    
    async def trigger_scenario(self, scenario_type: ScenarioType) -> ScenarioResult:
        """
        Trigger execution of a demo scenario.
        
        Args:
            scenario_type: Type of scenario to execute
            
        Returns:
            ScenarioResult containing execution results
        """
        try:
            # Check if scenario is already running
            if self.scenario_state not in [ScenarioState.IDLE, ScenarioState.COMPLETED, ScenarioState.FAILED]:
                raise RuntimeError(f"Cannot start scenario: current state is {self.scenario_state}")
            
            # Get scenario configuration
            if scenario_type not in self.scenario_definitions:
                raise ValueError(f"Unknown scenario type: {scenario_type}")
            
            scenario_config = self.scenario_definitions[scenario_type]
            
            # Initialize scenario execution
            await self._initialize_scenario(scenario_config)
            
            # Execute scenario steps
            result = await self._execute_scenario()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error triggering scenario {scenario_type}: {e}")
            
            # Create error result
            error_result = ScenarioResult(
                scenario_id=f"{scenario_type.value}_error",
                scenario_type=scenario_type,
                state=ScenarioState.FAILED,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                success=False,
                error_message=str(e),
                steps_total=0  # Map total_steps to steps_total if needed, but schema has steps_total
            )
            
            self.scenario_result = error_result
            self.scenario_state = ScenarioState.FAILED
            
            return error_result
    
    async def _initialize_scenario(self, scenario_config: ScenarioConfig):
        """Initialize scenario for execution"""
        self.logger.info(f"Initializing scenario: {scenario_config.name}")
        
        # Set scenario state
        self.scenario_state = ScenarioState.INITIALIZING
        self.current_scenario = scenario_config
        self.start_time = datetime.now(timezone.utc)
        self.current_step = 0
        
        # Reset tracking data
        self.agent_responses.clear()
        self.scenario_events.clear()
        
        # Initialize result tracking
        self.scenario_result = ScenarioResult(
            scenario_id=scenario_config.scenario_id,
            scenario_type=scenario_config.scenario_type,
            state=ScenarioState.INITIALIZING,
            start_time=self.start_time,
            steps_total=len(scenario_config.steps)
        )
        
        # Setup scenario timeout
        if self.scenario_timeout_task:
            self.scenario_timeout_task.cancel()
        
        self.scenario_timeout_task = asyncio.create_task(
            self._scenario_timeout_handler(scenario_config.max_duration_seconds)
        )
        
        # Publish scenario start event
        await self.event_bus.publish(
            "demo.scenario.initialized",
            json.dumps({
                "scenario_id": scenario_config.scenario_id,
                "scenario_type": scenario_config.scenario_type.value,
                "name": scenario_config.name,
                "timestamp": self.start_time.isoformat()
            })
        )
        
        self.scenario_state = ScenarioState.RUNNING
        self.logger.info(f"Scenario initialized: {scenario_config.name}")
    
    async def _execute_scenario(self) -> ScenarioResult:
        """Execute the current scenario steps"""
        if not self.current_scenario:
            raise RuntimeError("No scenario initialized for execution")
        
        self.logger.info(f"Executing scenario: {self.current_scenario.name}")
        
        try:
            # Execute each step
            for step_index, step in enumerate(self.current_scenario.steps):
                if self.scenario_state != ScenarioState.RUNNING:
                    break
                
                self.current_step = step_index
                self.step_start_time = datetime.now(timezone.utc)
                
                # Execute step
                step_success = await self._execute_step(step)
                
                if step_success:
                    self.scenario_result.steps_completed += 1
                else:
                    self.logger.warning(f"Step failed: {step.step_id}")
                
                # Record step completion
                self.scenario_events.append({
                    "type": "step_completed",
                    "timestamp": datetime.now(timezone.utc),
                    "step_id": step.step_id,
                    "success": step_success,
                    "step_index": step_index
                })
            
            # Evaluate scenario success
            success = await self._evaluate_scenario_success()
            
            # Complete scenario
            await self._complete_scenario(success)
            
            return self.scenario_result
            
        except Exception as e:
            self.logger.error(f"Error executing scenario: {e}")
            await self._fail_scenario(str(e))
            return self.scenario_result
    
    async def _execute_step(self, step: ScenarioStep) -> bool:
        """Execute a single scenario step"""
        self.logger.info(f"Executing step: {step.step_id} - {step.description}")
        
        try:
            # Apply delay if specified
            if step.delay_seconds > 0:
                await asyncio.sleep(step.delay_seconds)
            
            # Setup step timeout
            if self.step_timeout_task:
                self.step_timeout_task.cancel()
            
            self.step_timeout_task = asyncio.create_task(
                self._step_timeout_handler(step.timeout_seconds, step.step_id)
            )
            
            # Publish step event
            event_data = step.event_data.copy()
            event_data.update({
                "scenario_id": self.current_scenario.scenario_id,
                "step_id": step.step_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            await self.event_bus.publish(step.event_type, json.dumps(event_data))
            
            # Wait for expected responses if specified
            if step.expected_responses:
                responses_received = await self._wait_for_responses(step)
                step_success = len(responses_received) >= len(step.expected_responses) * 0.8  # 80% response rate
            else:
                step_success = True
            
            # Cancel step timeout
            if self.step_timeout_task:
                self.step_timeout_task.cancel()
                self.step_timeout_task = None
            
            self.logger.info(f"Step completed: {step.step_id} - Success: {step_success}")
            return step_success
            
        except Exception as e:
            self.logger.error(f"Error executing step {step.step_id}: {e}")
            return False
    
    async def _wait_for_responses(self, step: ScenarioStep) -> List[Dict[str, Any]]:
        """Wait for expected responses to a scenario step"""
        responses_received = []
        timeout_time = datetime.now(timezone.utc) + timedelta(seconds=step.timeout_seconds)
        
        while datetime.now(timezone.utc) < timeout_time and len(responses_received) < len(step.expected_responses):
            # Check for new responses from required agents
            for agent_type in step.required_agents:
                if agent_type in self.agent_responses:
                    agent_responses = self.agent_responses[agent_type]
                    
                    # Find responses that occurred after step start
                    new_responses = [
                        resp for resp in agent_responses
                        if resp["timestamp"] >= self.step_start_time and
                        resp["event_type"] in step.expected_responses and
                        resp not in responses_received
                    ]
                    
                    responses_received.extend(new_responses)
            
            # Short sleep to avoid busy waiting
            await asyncio.sleep(0.1)
        
        return responses_received
    
    async def _evaluate_scenario_success(self) -> bool:
        """Evaluate overall scenario success based on criteria"""
        if not self.current_scenario or not self.scenario_result:
            return False
        
        success_criteria = self.current_scenario.success_criteria
        
        # Check completion rate
        completion_rate = self.scenario_result.steps_completed / self.scenario_result.steps_total
        if completion_rate < 0.8:  # 80% completion required
            return False
        
        # Check response time if specified
        if "max_response_time" in success_criteria:
            max_allowed = success_criteria["max_response_time"]
            scenario_duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            if scenario_duration > max_allowed:
                return False
        
        # Check required agents responded
        if "required_agents_responded" in success_criteria:
            required_agents = set(success_criteria["required_agents_responded"])
            responding_agents = set(self.agent_responses.keys())
            if not required_agents.issubset(responding_agents):
                return False
        
        # Check coordination achieved
        if success_criteria.get("coordination_achieved", False):
            coordination_events = [
                event for event in self.scenario_events
                if "coordination" in event.get("event_type", "") or
                event.get("agent_type") == "coordinator_agent"
            ]
            if len(coordination_events) == 0:
                return False
        
        return True
    
    async def _complete_scenario(self, success: bool):
        """Complete scenario execution"""
        if not self.scenario_result:
            return
        
        # Update result
        self.scenario_result.state = ScenarioState.COMPLETED
        self.scenario_result.end_time = datetime.now(timezone.utc)
        self.scenario_result.duration_seconds = (
            self.scenario_result.end_time - self.scenario_result.start_time
        ).total_seconds()
        self.scenario_result.success = success
        self.scenario_result.agent_responses = dict(self.agent_responses)
        self.scenario_result.events = list(self.scenario_events)
        
        # Calculate performance metrics
        self.scenario_result.performance_metrics = {
            "total_agent_responses": sum(len(responses) for responses in self.agent_responses.values()),
            "unique_agents_responded": len(self.agent_responses),
            "total_events": len(self.scenario_events),
            "completion_rate": self.scenario_result.steps_completed / self.scenario_result.steps_total,
            "average_step_time": self.scenario_result.duration_seconds / max(self.scenario_result.steps_completed, 1)
        }
        
        # Update state
        self.scenario_state = ScenarioState.COMPLETED
        
        # Cancel timeouts
        if self.scenario_timeout_task:
            self.scenario_timeout_task.cancel()
        if self.step_timeout_task:
            self.step_timeout_task.cancel()
        
        # Publish completion event
        await self.event_bus.publish(
            "demo.scenario.completed",
            json.dumps({
                "scenario_id": self.scenario_result.scenario_id,
                "success": success,
                "duration_seconds": self.scenario_result.duration_seconds,
                "steps_completed": self.scenario_result.steps_completed,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        )
        
        self.logger.info(f"Scenario completed: {self.current_scenario.name} - Success: {success}")
    
    async def _fail_scenario(self, error_message: str):
        """Fail scenario execution"""
        if not self.scenario_result:
            return
        
        # Update result
        self.scenario_result.state = ScenarioState.FAILED
        self.scenario_result.end_time = datetime.now(timezone.utc)
        self.scenario_result.duration_seconds = (
            self.scenario_result.end_time - self.scenario_result.start_time
        ).total_seconds()
        self.scenario_result.success = False
        self.scenario_result.error_message = error_message
        self.scenario_result.agent_responses = dict(self.agent_responses)
        self.scenario_result.events = list(self.scenario_events)
        
        # Update state
        self.scenario_state = ScenarioState.FAILED
        
        # Cancel timeouts
        if self.scenario_timeout_task:
            self.scenario_timeout_task.cancel()
        if self.step_timeout_task:
            self.step_timeout_task.cancel()
        
        # Publish failure event
        await self.event_bus.publish(
            "demo.scenario.failed",
            json.dumps({
                "scenario_id": self.scenario_result.scenario_id,
                "error_message": error_message,
                "duration_seconds": self.scenario_result.duration_seconds,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        )
        
        self.logger.error(f"Scenario failed: {self.current_scenario.name} - Error: {error_message}")
    
    async def _scenario_timeout_handler(self, timeout_seconds: float):
        """Handle scenario timeout"""
        try:
            await asyncio.sleep(timeout_seconds)
            if self.scenario_state == ScenarioState.RUNNING:
                await self._fail_scenario(f"Scenario timeout after {timeout_seconds} seconds")
        except asyncio.CancelledError:
            pass
    
    async def _step_timeout_handler(self, timeout_seconds: float, step_id: str):
        """Handle step timeout"""
        try:
            await asyncio.sleep(timeout_seconds)
            self.logger.warning(f"Step timeout: {step_id} after {timeout_seconds} seconds")
            # Step timeout doesn't fail the entire scenario, just logs the timeout
        except asyncio.CancelledError:
            pass
    
    async def reset_scenario(self) -> bool:
        """
        Reset scenario state and clean up resources between demos.
        
        Returns:
            bool: True if reset successful, False otherwise
        """
        try:
            self.logger.info("Resetting scenario state...")
            
            # Set resetting state
            self.scenario_state = ScenarioState.RESETTING
            
            # Cancel any running timeouts
            if self.scenario_timeout_task:
                self.scenario_timeout_task.cancel()
                self.scenario_timeout_task = None
            
            if self.step_timeout_task:
                self.step_timeout_task.cancel()
                self.step_timeout_task = None
            
            # Execute cleanup steps if current scenario exists
            if self.current_scenario and self.current_scenario.cleanup_steps:
                await self._execute_cleanup_steps()
            
            # Reset all state variables
            self.current_scenario = None
            self.scenario_result = None
            self.start_time = None
            self.current_step = 0
            self.step_start_time = None
            self.agent_responses.clear()
            self.scenario_events.clear()
            
            # Publish reset event
            await self.event_bus.publish(
                "demo.scenario.reset",
                json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "completed"
                })
            )
            
            # Set idle state
            self.scenario_state = ScenarioState.IDLE
            
            self.logger.info("Scenario reset completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting scenario: {e}")
            self.scenario_state = ScenarioState.FAILED
            return False
    
    async def _execute_cleanup_steps(self):
        """Execute cleanup steps for current scenario"""
        if not self.current_scenario or not self.current_scenario.cleanup_steps:
            return
        
        self.logger.info("Executing scenario cleanup steps...")
        
        for step in self.current_scenario.cleanup_steps:
            try:
                # Apply delay if specified
                if step.delay_seconds > 0:
                    await asyncio.sleep(step.delay_seconds)
                
                # Publish cleanup event
                event_data = step.event_data.copy()
                event_data.update({
                    "cleanup": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                await self.event_bus.publish(step.event_type, json.dumps(event_data))
                
                self.logger.debug(f"Executed cleanup step: {step.step_id}")
                
            except Exception as e:
                self.logger.error(f"Error executing cleanup step {step.step_id}: {e}")
    
    def get_scenario_state(self) -> Dict[str, Any]:
        """
        Get current scenario state and progress information.
        
        Returns:
            Dict containing current scenario state information
        """
        state_info = {
            "state": self.scenario_state.value,
            "current_scenario": None,
            "progress": {
                "current_step": self.current_step,
                "total_steps": 0,
                "completion_percentage": 0.0
            },
            "timing": {
                "start_time": None,
                "elapsed_seconds": 0.0,
                "estimated_remaining_seconds": None
            },
            "agent_responses": {
                "total_responses": sum(len(responses) for responses in self.agent_responses.values()),
                "responding_agents": list(self.agent_responses.keys()),
                "response_count_by_agent": {
                    agent: len(responses) for agent, responses in self.agent_responses.items()
                }
            },
            "events": {
                "total_events": len(self.scenario_events),
                "recent_events": self.scenario_events[-5:] if self.scenario_events else []
            }
        }
        
        # Add current scenario information
        if self.current_scenario:
            state_info["current_scenario"] = {
                "scenario_id": self.current_scenario.scenario_id,
                "name": self.current_scenario.name,
                "type": self.current_scenario.scenario_type.value,
                "description": self.current_scenario.description
            }
            
            # Update progress information
            state_info["progress"]["total_steps"] = len(self.current_scenario.steps)
            if len(self.current_scenario.steps) > 0:
                state_info["progress"]["completion_percentage"] = (
                    self.current_step / len(self.current_scenario.steps) * 100.0
                )
        
        # Add timing information
        if self.start_time:
            elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
            state_info["timing"]["start_time"] = self.start_time.isoformat()
            state_info["timing"]["elapsed_seconds"] = elapsed
            
            # Estimate remaining time based on current progress
            if self.current_scenario and self.current_step > 0:
                avg_step_time = elapsed / self.current_step
                remaining_steps = len(self.current_scenario.steps) - self.current_step
                state_info["timing"]["estimated_remaining_seconds"] = avg_step_time * remaining_steps
        
        return state_info
    
    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """
        Get list of available demo scenarios.
        
        Returns:
            List of available scenario information
        """
        scenarios = []
        
        for scenario_type, config in self.scenario_definitions.items():
            scenarios.append({
                "scenario_type": scenario_type.value,
                "scenario_id": config.scenario_id,
                "name": config.name,
                "description": config.description,
                "max_duration_seconds": config.max_duration_seconds,
                "total_steps": len(config.steps),
                "required_agents": list(set(
                    agent for step in config.steps for agent in step.required_agents
                ))
            })
        
        return scenarios
    
    def get_scenario_result(self) -> Optional[ScenarioResult]:
        """
        Get the result of the last executed scenario.
        
        Returns:
            ScenarioResult if available, None otherwise
        """
        return self.scenario_result
    
    async def pause_scenario(self) -> bool:
        """
        Pause the currently running scenario.
        
        Returns:
            bool: True if paused successfully, False otherwise
        """
        if self.scenario_state != ScenarioState.RUNNING:
            return False
        
        try:
            self.scenario_state = ScenarioState.PAUSED
            
            # Cancel timeouts while paused
            if self.scenario_timeout_task:
                self.scenario_timeout_task.cancel()
            if self.step_timeout_task:
                self.step_timeout_task.cancel()
            
            # Publish pause event
            await self.event_bus.publish(
                "demo.scenario.paused",
                json.dumps({
                    "scenario_id": self.current_scenario.scenario_id if self.current_scenario else None,
                    "current_step": self.current_step,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            )
            
            self.logger.info("Scenario paused")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing scenario: {e}")
            return False
    
    async def resume_scenario(self) -> bool:
        """
        Resume a paused scenario.
        
        Returns:
            bool: True if resumed successfully, False otherwise
        """
        if self.scenario_state != ScenarioState.PAUSED:
            return False
        
        try:
            self.scenario_state = ScenarioState.RUNNING
            
            # Restart timeouts
            if self.current_scenario:
                remaining_time = self.current_scenario.max_duration_seconds
                if self.start_time:
                    elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
                    remaining_time = max(0, self.current_scenario.max_duration_seconds - elapsed)
                
                if remaining_time > 0:
                    self.scenario_timeout_task = asyncio.create_task(
                        self._scenario_timeout_handler(remaining_time)
                    )
            
            # Publish resume event
            await self.event_bus.publish(
                "demo.scenario.resumed",
                json.dumps({
                    "scenario_id": self.current_scenario.scenario_id if self.current_scenario else None,
                    "current_step": self.current_step,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            )
            
            self.logger.info("Scenario resumed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming scenario: {e}")
            return False
    
    async def stop_scenario(self) -> bool:
        """
        Stop the currently running scenario.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if self.scenario_state not in [ScenarioState.RUNNING, ScenarioState.PAUSED]:
            return False
        
        try:
            # Cancel timeouts
            if self.scenario_timeout_task:
                self.scenario_timeout_task.cancel()
            if self.step_timeout_task:
                self.step_timeout_task.cancel()
            
            # Mark as completed (but not successful)
            if self.scenario_result:
                self.scenario_result.state = ScenarioState.COMPLETED
                self.scenario_result.end_time = datetime.now(timezone.utc)
                self.scenario_result.duration_seconds = (
                    self.scenario_result.end_time - self.scenario_result.start_time
                ).total_seconds()
                self.scenario_result.success = False
                self.scenario_result.error_message = "Scenario stopped by user"
            
            self.scenario_state = ScenarioState.COMPLETED
            
            # Publish stop event
            await self.event_bus.publish(
                "demo.scenario.stopped",
                json.dumps({
                    "scenario_id": self.current_scenario.scenario_id if self.current_scenario else None,
                    "current_step": self.current_step,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            )
            
            self.logger.info("Scenario stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping scenario: {e}")
            return False
    
    def is_scenario_running(self) -> bool:
        """
        Check if a scenario is currently running.
        
        Returns:
            bool: True if scenario is running, False otherwise
        """
        return self.scenario_state in [ScenarioState.RUNNING, ScenarioState.PAUSED]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for scenario execution.
        
        Returns:
            Dict containing performance metrics
        """
        metrics = {
            "current_state": self.scenario_state.value,
            "total_scenarios_executed": 1 if self.scenario_result else 0,
            "current_scenario_metrics": {}
        }
        
        if self.scenario_result:
            metrics["current_scenario_metrics"] = self.scenario_result.performance_metrics
        
        if self.start_time:
            metrics["current_execution_time"] = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        # Add agent response statistics
        metrics["agent_statistics"] = {
            "total_responses": sum(len(responses) for responses in self.agent_responses.values()),
            "unique_agents": len(self.agent_responses),
            "response_distribution": {
                agent: len(responses) for agent, responses in self.agent_responses.items()
            }
        }
        
        # Add event statistics
        metrics["event_statistics"] = {
            "total_events": len(self.scenario_events),
            "event_types": {}
        }
        
        # Count event types
        for event in self.scenario_events:
            event_type = event.get("type", "unknown")
            metrics["event_statistics"]["event_types"][event_type] = (
                metrics["event_statistics"]["event_types"].get(event_type, 0) + 1
            )
        
        return metrics