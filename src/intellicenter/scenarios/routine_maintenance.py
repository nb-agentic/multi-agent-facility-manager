"""
Routine Maintenance Scenario for Demo Scenarios

This module provides a simple and lightweight routine maintenance scenario
that demonstrates basic HVAC-Network agent coordination with quick completion
for demonstration purposes.

Features:
- Simple trigger: scheduled maintenance window detection
- Basic coordination: HVAC system check + Network connectivity validation
- Lightweight operations: status checks rather than complex decision-making
- Quick completion: 60-second maximum duration
- Clear success indicators for demo purposes
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Callable

from intellicenter.shared.event_bus import EventBus
from intellicenter.shared.logger import logger
from intellicenter.shared.schema import (
    AgentType,
    MaintenancePhase,
    ScenarioResult,
    ScenarioState,
    ScenarioStepRuntime,
    ScenarioType,
)


# Removed local Enum and dataclass definitions as they are now in shared.schema


class RoutineMaintenanceScenario:
    """
    Simple and lightweight routine maintenance scenario.
    
    Demonstrates basic HVAC-Network agent coordination with quick completion
    for demonstration purposes.
    """
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.logger = logger.bind(scenario="routine_maintenance")
        
        # Scenario state management
        self.current_phase = MaintenancePhase.DETECTION
        self.maintenance_steps: List[MaintenanceStep] = []
        self.maintenance_result: Optional[MaintenanceResult] = None
        
        # Execution tracking
        self.start_time: Optional[datetime] = None
        self.current_step_index: int = 0
        self.step_start_time: Optional[datetime] = None
        self.agent_responses: Dict[str, List[Dict[str, Any]]] = {}
        self.maintenance_events: List[Dict[str, Any]] = []
        
        # Event handlers and subscriptions
        self.event_handlers: Dict[str, Callable] = {}
        self.active_subscriptions: List[str] = []
        
        # Timing constraints
        self.max_duration_seconds = 60.0  # 1 minute max for quick demo
        self.step_timeout_task: Optional[asyncio.Task] = None
        
        # Initialize maintenance steps
        self._create_maintenance_steps()
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
    
    def _create_maintenance_steps(self):
        """Create routine maintenance steps"""
        self.maintenance_steps = [
            ScenarioStepRuntime(
                step_id="maintenance_detection",
                description="Detect scheduled maintenance window",
                event_type="demo.scenario.start",
                event_data={"scenario": "routine_maintenance", "phase": "detection"},
                delay_seconds=1.0
            ),
            ScenarioStepRuntime(
                step_id="hvac_system_check",
                description="Perform HVAC system status check",
                event_type="hvac.system.status",
                event_data={"system": "hvac", "status": "check", "location": "server_room_main"},
                delay_seconds=5.0,
                timeout_seconds=15.0,
                expected_responses=["hvac.system.status"],
                required_agents=[AgentType.HVAC]
            ),
            ScenarioStepRuntime(
                step_id="network_connectivity_check",
                description="Validate network connectivity and performance",
                event_type="network.connectivity.status",
                event_data={"system": "network", "status": "validation", "location": "server_room_main"},
                delay_seconds=5.0,
                timeout_seconds=15.0,
                expected_responses=["network.connectivity.status"],
                required_agents=[AgentType.NETWORK]
            ),
            ScenarioStepRuntime(
                step_id="coordination_completion",
                description="Complete coordination and verification",
                event_type="facility.maintenance.completion",
                event_data={"scenario_complete": True, "location": "server_room_main"},
                delay_seconds=3.0,
                timeout_seconds=15.0,
                expected_responses=["facility.maintenance.completion"],
                required_agents=[AgentType.COORDINATOR]
            )
        ]
    
    def _setup_event_subscriptions(self):
        """Setup event subscriptions for routine maintenance"""
        # Subscribe to maintenance-related events
        maintenance_events = [
            "hvac.system.status",
            "network.connectivity.status",
            "facility.maintenance.response",
            "facility.maintenance.completion"
        ]
        
        for event_type in maintenance_events:
            handler = self._create_event_handler(event_type)
            self.event_bus.subscribe(event_type, handler)
            self.event_handlers[event_type] = handler
            self.active_subscriptions.append(event_type)
    
    def _create_event_handler(self, event_type: str) -> Callable:
        """Create an event handler for a specific event type"""
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
                
                # Extract agent type from event
                agent_type = self._extract_agent_type(event_type, data)
                
                # Store response with timestamp
                response_record = {
                    **data,
                    "received_at": datetime.now(timezone.utc),
                    "timestamp": time.time(),
                    "event_type": event_type,
                    "agent_type": agent_type
                }
                
                if agent_type not in self.agent_responses:
                    self.agent_responses[agent_type] = []
                
                self.agent_responses[agent_type].append(response_record)
                
                # Log coordination event
                self.maintenance_events.append({
                    "type": "agent_response",
                    "agent_type": agent_type,
                    "timestamp": datetime.now(timezone.utc),
                    "phase": self.current_phase.value,
                    "data": data
                })
                
                self.logger.debug(f"📨 Agent response received: {agent_type} for {self.current_phase.value}")
                
            except Exception as e:
                self.logger.error(f"Error handling event {event_type}: {e}")
        
        return handler
    
    def _extract_agent_type(self, event_type: str, data: Dict[str, Any]) -> str:
        """Extract and normalize agent type from event type or data"""
        # Try to get from data first
        raw_agent_type = data.get("agent_type", "")
        
        # Determine base agent type
        if "hvac" in raw_agent_type or "hvac" in event_type:
            return str(AgentType.HVAC)
        elif "network" in raw_agent_type or "network" in event_type:
            return str(AgentType.NETWORK)
        elif "coordinator" in raw_agent_type or "facility.maintenance" in event_type:
            return str(AgentType.COORDINATOR)
        elif "power" in raw_agent_type or "power" in event_type:
            return str(AgentType.POWER)
        elif "security" in raw_agent_type or "security" in event_type:
            return str(AgentType.SECURITY)
        
        return raw_agent_type or "unknown_agent"
    
    async def start_maintenance(self) -> ScenarioResult:
        """
        Start routine maintenance execution.
        
        Returns:
            MaintenanceResult containing execution results
        """
        try:
            self.logger.info("🔧 Starting routine maintenance scenario")
            
            # Initialize maintenance execution
            await self._initialize_maintenance()
            
            # Execute maintenance steps
            result = await self._execute_maintenance()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error starting routine maintenance: {e}")
            
            # Create error result
            error_result = ScenarioResult(
                scenario_id="routine_maintenance_error",
                scenario_type=ScenarioType.ROUTINE_MAINTENANCE,
                state=ScenarioState.FAILED,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                success=False,
                error_message=str(e),
                steps_total=0
            )
            
            self.maintenance_result = error_result
            return error_result
    
    async def _initialize_maintenance(self):
        """Initialize routine maintenance for execution"""
        self.logger.info("Initializing routine maintenance scenario")
        
        # Set initial phase
        self.current_phase = MaintenancePhase.DETECTION
        self.start_time = datetime.now(timezone.utc)
        self.current_step_index = 0
        
        # Reset tracking data
        self.agent_responses.clear()
        self.maintenance_events.clear()
        
        # Initialize result tracking
        self.maintenance_result = ScenarioResult(
            scenario_id="routine_maintenance_demo",
            scenario_type=ScenarioType.ROUTINE_MAINTENANCE,
            state=ScenarioState.INITIALIZING,
            start_time=self.start_time,
            steps_total=len(self.maintenance_steps)
        )
        
        # Publish start event
        await self.event_bus.publish(
            "demo.scenario.initialized",
            json.dumps({
                "scenario_id": "routine_maintenance_demo",
                "scenario_type": "routine_maintenance",
                "name": "Routine Maintenance",
                "timestamp": self.start_time.isoformat()
            })
        )
        
        self.logger.info("✅ Routine maintenance scenario initialized")
    
    async def _execute_maintenance(self) -> ScenarioResult:
        """Execute the routine maintenance steps"""
        if not self.maintenance_steps:
            raise RuntimeError("No maintenance steps defined for execution")
        
        self.logger.info(f"Executing routine maintenance: {len(self.maintenance_steps)} steps")
        
        try:
            # Initialize start_time if not set (for direct calls from tests)
            if not self.start_time:
                self.start_time = datetime.now(timezone.utc)
            
            # Initialize maintenance result if not already set
            if not self.maintenance_result:
                self.maintenance_result = ScenarioResult(
                    scenario_id="routine_maintenance_demo",
                    scenario_type=ScenarioType.ROUTINE_MAINTENANCE,
                    state=ScenarioState.RUNNING,
                    start_time=self.start_time,
                    steps_total=len(self.maintenance_steps)
                )
            
            # Execute each step
            for step_index, step in enumerate(self.maintenance_steps):
                if self.current_phase != MaintenancePhase.COMPLETION:
                    self.current_step_index = step_index
                    self.step_start_time = datetime.now(timezone.utc)
                    
                    # Execute step
                    step_success = await self._execute_step(step)
                    
                    if step_success:
                        self.maintenance_result.steps_completed += 1
                    else:
                        self.logger.warning(f"Step failed: {step.step_id}")
                    
                    # Record step completion
                    self.maintenance_events.append({
                        "type": "step_completed",
                        "timestamp": datetime.now(timezone.utc),
                        "step_id": step.step_id,
                        "success": step_success,
                        "step_index": step_index
                    })
                    
                    # Update current phase (mock phase update since ScenarioStep doesn't have it directly)
                    # We can infer it from step_id for this specific scenario
                    if "detection" in step.step_id: self.current_phase = MaintenancePhase.DETECTION
                    elif "hvac" in step.step_id: self.current_phase = MaintenancePhase.HVAC_CHECK
                    elif "network" in step.step_id: self.current_phase = MaintenancePhase.NETWORK_CHECK
                    elif "completion" in step.step_id: self.current_phase = MaintenancePhase.COMPLETION
            
            # Evaluate maintenance success
            success = await self._evaluate_maintenance_success()
            
            # Complete maintenance
            await self._complete_maintenance(success)
            
            return self.maintenance_result
            
        except Exception as e:
            self.logger.error(f"Error executing routine maintenance: {e}")
            await self._fail_maintenance(str(e))
            return self.maintenance_result
    
    async def _execute_step(self, step: ScenarioStepRuntime) -> bool:
        """Execute a single maintenance step"""
        self.logger.info(f"🔄 Executing step: {step.step_id} - {step.description}")
        
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
                "scenario_id": "routine_maintenance_demo",
                "step_id": step.step_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            await self.event_bus.publish(step.event_type, json.dumps(event_data))
            
            # Wait for expected responses if specified
            if step.expected_responses:
                responses_received = await self._wait_for_step_responses(step)
                step_success = len(responses_received) >= len(step.expected_responses) * 0.8  # 80% response rate
            else:
                step_success = True
            
            # Cancel step timeout
            if self.step_timeout_task:
                self.step_timeout_task.cancel()
                self.step_timeout_task = None
            
            self.logger.info(f"✅ Step completed: {step.step_id} - Success: {step_success}")
            return step_success
            
        except Exception as e:
            self.logger.error(f"Error executing step {step.step_id}: {e}")
            return False
    
    async def _wait_for_step_responses(self, step: ScenarioStepRuntime) -> List[Dict[str, Any]]:
        """Wait for expected responses to a maintenance step"""
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
                        if resp.get("timestamp", 0) >= self.step_start_time.timestamp() and
                        agent_type not in [r.get("agent_type") for r in responses_received]
                    ]
                    
                    if new_responses:
                        responses_received.extend(new_responses)
            
            # Short sleep to avoid busy waiting
            await asyncio.sleep(0.1)
        
        return responses_received
    
    async def _evaluate_maintenance_success(self) -> bool:
        """Evaluate overall maintenance success based on criteria"""
        if not self.maintenance_result or not self.start_time:
            return False
        
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate success metrics
        success = (
            total_duration <= self.max_duration_seconds and  # Within time constraint
            self.maintenance_result.steps_completed >= self.maintenance_result.steps_total * 0.8 and  # 80% steps completed
            len(self.agent_responses) >= 2  # At least 2 agents responded (HVAC and Network)
        )
        
        # Update result with final metrics
        self.maintenance_result.end_time = end_time
        self.maintenance_result.duration_seconds = total_duration
        self.maintenance_result.success = success
        
        # Log success evaluation
        self.logger.info(
            f"🔍 Maintenance success evaluation: "
            f"Duration: {total_duration:.1f}s (max: {self.max_duration_seconds}s), "
            f"Steps: {self.maintenance_result.steps_completed}/{self.maintenance_result.total_steps}, "
            f"Agents: {len(self.agent_responses)}, "
            f"Success: {success}"
        )
        
        return success
    
    async def _complete_maintenance(self, success: bool):
        """Complete routine maintenance execution"""
        if not self.maintenance_result:
            return
        
        # Update result
        self.maintenance_result.end_time = datetime.now(timezone.utc)
        self.maintenance_result.duration_seconds = (
            self.maintenance_result.end_time - self.maintenance_result.start_time
        ).total_seconds()
        self.maintenance_result.success = success
        self.maintenance_result.agent_responses = dict(self.agent_responses)
        self.maintenance_result.events = list(self.maintenance_events)
        
        # Publish completion event
        await self.event_bus.publish(
            "demo.scenario.completed",
            json.dumps({
                "scenario_id": "routine_maintenance_demo",
                "success": success,
                "duration_seconds": self.maintenance_result.duration_seconds,
                "steps_completed": self.maintenance_result.steps_completed,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        )
        
        self.logger.info(
            f"🏁 Routine maintenance completed: Success: {success} - "
            f"Duration: {self.maintenance_result.duration_seconds:.1f}s - "
            f"Steps: {self.maintenance_result.steps_completed}/{self.maintenance_result.steps_total}"
        )
    
    async def _fail_maintenance(self, error_message: str):
        """Fail routine maintenance execution"""
        if not self.maintenance_result:
            return
        
        # Update result
        self.maintenance_result.end_time = datetime.now(timezone.utc)
        self.maintenance_result.duration_seconds = (
            self.maintenance_result.end_time - self.maintenance_result.start_time
        ).total_seconds()
        self.maintenance_result.success = False
        self.maintenance_result.error_message = error_message
        self.maintenance_result.agent_responses = dict(self.agent_responses)
        self.maintenance_result.events = list(self.maintenance_events)
        
        # Publish failure event
        await self.event_bus.publish(
            "demo.scenario.failed",
            json.dumps({
                "scenario_id": "routine_maintenance_demo",
                "error_message": error_message,
                "duration_seconds": self.maintenance_result.duration_seconds,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        )
        
        self.logger.error(f"❌ Routine maintenance failed: {error_message}")
    
    async def _step_timeout_handler(self, timeout_seconds: float, step_id: str):
        """Handle step timeout"""
        try:
            await asyncio.sleep(timeout_seconds)
            self.logger.warning(f"⏰ Step timeout: {step_id} after {timeout_seconds} seconds")
        except asyncio.CancelledError:
            pass
    
    def get_maintenance_status(self) -> Dict[str, Any]:
        """Get current maintenance status"""
        if not self.start_time:
            return {
                "active": False,
                "status": "idle",
                "phase": None
            }
        
        current_time = datetime.now(timezone.utc)
        elapsed_time = (current_time - self.start_time).total_seconds()
        remaining_time = max(0, self.max_duration_seconds - elapsed_time)
        
        return {
            "active": True,
            "status": "active",
            "phase": self.current_phase.value,
            "elapsed_seconds": elapsed_time,
            "remaining_seconds": remaining_time,
            "completion_percentage": min(100, (elapsed_time / self.max_duration_seconds) * 100),
            "steps_completed": self.maintenance_result.steps_completed if self.maintenance_result else 0,
            "steps_total": len(self.maintenance_steps),
            "agents_responded": len(self.agent_responses),
            "current_step": self.current_step_index,
            "current_step_id": self.maintenance_steps[self.current_step_index].step_id if self.current_step_index < len(self.maintenance_steps) else None
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for routine maintenance"""
        metrics = {
            "max_duration_seconds": self.max_duration_seconds,
            "current_phase": self.current_phase.value,
            "total_steps": len(self.maintenance_steps),
            "steps_completed": self.maintenance_result.steps_completed if self.maintenance_result else 0,
            "agents_responded": len(self.agent_responses),
            "total_events": len(self.maintenance_events)
        }
        
        if self.maintenance_result:
            metrics.update({
                "success": self.maintenance_result.success,
                "duration_seconds": self.maintenance_result.duration_seconds,
                "completion_rate": self.maintenance_result.steps_completed / self.maintenance_result.steps_total
            })
        
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
        
        return metrics
    
    async def reset_maintenance(self) -> bool:
        """Reset maintenance state for next scenario"""
        try:
            self.logger.info("🔄 Resetting maintenance state...")
            
            # Cancel any running timeouts
            if self.step_timeout_task:
                self.step_timeout_task.cancel()
                self.step_timeout_task = None
            
            # Reset all state variables
            self.current_phase = MaintenancePhase.DETECTION
            self.maintenance_steps.clear()
            self.maintenance_result = None
            self.start_time = None
            self.current_step_index = 0
            self.step_start_time = None
            self.agent_responses.clear()
            self.maintenance_events.clear()
            
            # Recreate maintenance steps
            self._create_maintenance_steps()
            
            # Publish reset event
            await self.event_bus.publish(
                "demo.scenario.reset",
                json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "completed"
                })
            )
            
            self.logger.info("✅ Maintenance reset completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting maintenance: {e}")
            return False
    
    async def integrate_with_orchestrator(self) -> bool:
        """Integrate with the scenario orchestrator"""
        try:
            self.logger.info("🔗 Integrating routine maintenance with orchestrator")
            
            # Subscribe to orchestrator events (this is in addition to existing subscriptions)
            self.event_bus.subscribe(
                "demo.scenario.start",
                self._handle_orchestrator_event
            )
            self.active_subscriptions.append("demo.scenario.start")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error integrating with orchestrator: {e}")
            return False
    
    async def _handle_orchestrator_event(self, message: str):
        """Handle events from the scenario orchestrator"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            if data.get("scenario") == "routine_maintenance":
                self.logger.info("🎭 Orchestrator routine maintenance scenario detected")
                
                # Start our routine maintenance implementation
                await self.start_maintenance()
                
        except Exception as e:
            self.logger.error(f"Error handling orchestrator event: {e}")