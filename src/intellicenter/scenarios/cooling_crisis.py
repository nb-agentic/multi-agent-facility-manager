"""
Cooling Crisis Scenario Implementation

This module implements the Cooling Crisis scenario logic with:
- 89.5°F (32°C) temperature event triggers
- HVAC-Power-Security coordination
- 2-minute completion constraint
- Step-by-step scenario execution
- Integration with scenario orchestrator

Features:
- Temperature threshold monitoring
- Multi-agent coordination
- Timing constraints and completion tracking
- Emergency response protocols
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
    CoolingCrisisEvent,
    EventPriority,
    EventSeverity,
    ScenarioResult,
    ScenarioState,
    ScenarioStepRuntime,
    ScenarioType,
)

from .scenario_orchestrator import ScenarioOrchestrator


def _json_default(obj: Any) -> Any:
    """Custom JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# Temperature conversion constants
FAHRENHEIT_THRESHOLD = 89.5  # °F
CELSIUS_THRESHOLD = 32.0     # °C (89.5°F converted)


# Removed local dataclass definitions as they are now in shared.schema


class CoolingCrisisScenario:
    """
    Cooling Crisis Scenario Implementation
    
    Handles temperature-triggered emergency scenarios requiring coordination
    between HVAC, Power, and Security agents within a 2-minute timeframe.
    """
    
    def __init__(self, event_bus: EventBus, orchestrator: ScenarioOrchestrator):
        self.event_bus = event_bus
        self.orchestrator = orchestrator
        self.logger = logger.bind(scenario="cooling_crisis")
        
        # Scenario state
        self.active_crisis: Optional[CoolingCrisisEvent] = None
        self.crisis_steps: List[CoolingCrisisStep] = []
        self.start_time: Optional[datetime] = None
        self.completion_deadline: Optional[datetime] = None
        
        # Agent coordination tracking
        self.agent_responses: Dict[str, List[Dict[str, Any]]] = {}
        self.coordination_events: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics = {
            "total_crises_handled": 0,
            "successful_completions": 0,
            "average_response_time": 0.0,
            "agent_coordination_success_rate": 0.0
        }
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions for cooling crisis monitoring"""
        # Subscribe to temperature events
        self.event_bus.subscribe(
            "hvac.temperature.changed", 
            self._handle_temperature_event
        )
        
        # Subscribe to agent responses
        agent_events = [
            "hvac.cooling.decision",
            "power.optimization.decision",
            "security.assessment.decision",
            "facility.coordination.directive"
        ]
        
        for event_type in agent_events:
            self.event_bus.subscribe(event_type, self._handle_agent_response)
    
    async def _handle_temperature_event(self, message: str):
        """Handle incoming temperature events and trigger crisis if threshold exceeded"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            # Extract temperature data
            temp_celsius = data.get("temperature", 22.0)
            temp_fahrenheit = self._celsius_to_fahrenheit(temp_celsius)
            
            # Check if crisis threshold is exceeded
            if temp_fahrenheit >= FAHRENHEIT_THRESHOLD:
                await self._trigger_cooling_crisis(data, temp_fahrenheit, temp_celsius)
            elif self.active_crisis:
                # Monitor ongoing crisis
                await self._monitor_crisis_progress(data, temp_fahrenheit, temp_celsius)
                
        except Exception as e:
            self.logger.error(f"Error handling temperature event: {e}")
    
    async def _trigger_cooling_crisis(self, temp_data: Dict[str, Any], temp_f: float, temp_c: float):
        """Trigger a cooling crisis scenario"""
        if self.active_crisis:
            self.logger.warning("Crisis already active, updating severity")
            return
        
        # Create crisis event using Pydantic model
        crisis_event = CoolingCrisisEvent(
            event_id=f"cooling_crisis_{int(time.time())}",
            timestamp=datetime.now(timezone.utc),
            event_type="cooling_crisis_triggered",
            location=temp_data.get("location", "server_room_main"),
            priority=EventPriority.CRITICAL,
            severity=EventSeverity.CRITICAL,
            temperature_fahrenheit=temp_f,
            temperature_celsius=temp_c,
            trend=temp_data.get("trend", "rising"),
            rate_of_change=temp_data.get("rate", 1.0),
            emergency=True,
            payload=temp_data
        )
        
        self.active_crisis = crisis_event
        self.start_time = datetime.now(timezone.utc)
        self.completion_deadline = self.start_time + timedelta(seconds=120)  # 2-minute constraint
        
        self.logger.critical(
            f"🚨 COOLING CRISIS TRIGGERED: {temp_f:.1f}°F ({temp_c:.1f}°C) "
            f"at {crisis_event.location} - 2-minute response window activated"
        )
        
        # Initialize crisis response steps
        await self._initialize_crisis_steps()
        
        # Start crisis response execution
        await self._execute_crisis_response()
    
    async def _initialize_crisis_steps(self):
        """Initialize the step-by-step crisis response plan"""
        if not self.active_crisis:
            return
        
        current_time = datetime.now(timezone.utc)
        
        # Step 1: Immediate HVAC Response (0-15 seconds)
        self.crisis_steps.append(ScenarioStepRuntime(
            step_id="hvac_emergency_response",
            description="HVAC emergency cooling activation",
            event_type="hvac.temperature.changed",
            start_time=current_time,
            timeout_seconds=15.0,
            required_agents=[AgentType.HVAC],
            expected_responses=["hvac.cooling.decision"]
        ))
        
        # Step 2: Power System Coordination (15-45 seconds)
        self.crisis_steps.append(ScenarioStepRuntime(
            step_id="power_coordination",
            description="Power optimization for emergency cooling",
            event_type="hvac.cooling.decision",
            start_time=current_time + timedelta(seconds=15),
            timeout_seconds=30.0,
            required_agents=[AgentType.POWER],
            expected_responses=["power.optimization.decision"]
        ))
        
        # Step 3: Security Protocol Activation (30-60 seconds)
        self.crisis_steps.append(ScenarioStepRuntime(
            step_id="security_lockdown",
            description="Security lockdown for environmental emergency",
            event_type="facility.security.event",
            start_time=current_time + timedelta(seconds=30),
            timeout_seconds=30.0,
            required_agents=[AgentType.SECURITY],
            expected_responses=["security.assessment.decision"]
        ))
        
        # Step 4: Coordinated Response (45-90 seconds)
        self.crisis_steps.append(ScenarioStepRuntime(
            step_id="multi_agent_coordination",
            description="Multi-agent coordination and status verification",
            event_type="facility.coordination.scenario",
            start_time=current_time + timedelta(seconds=45),
            timeout_seconds=45.0,
            required_agents=[AgentType.COORDINATOR],
            expected_responses=["facility.coordination.directive"]
        ))
        
        # Step 5: Crisis Resolution Verification (90-120 seconds)
        self.crisis_steps.append(ScenarioStepRuntime(
            step_id="crisis_resolution",
            description="Verify crisis resolution and system stabilization",
            event_type="hvac.temperature.changed",
            start_time=current_time + timedelta(seconds=90),
            timeout_seconds=30.0,
            required_agents=[AgentType.HVAC, AgentType.COORDINATOR],
            expected_responses=["hvac.cooling.decision", "facility.coordination.directive"]
        ))
    
    async def _execute_crisis_response(self):
        """Execute the crisis response steps with timing coordination"""
        if not self.active_crisis or not self.crisis_steps:
            return
        
        self.logger.info(f"🎯 Executing {len(self.crisis_steps)} crisis response steps")
        
        # Publish crisis initiation event
        await self._publish_crisis_event("cooling_crisis_initiated", {
            "crisis_id": self.active_crisis.event_id,
            "temperature_fahrenheit": self.active_crisis.temperature_fahrenheit,
            "temperature_celsius": self.active_crisis.temperature_celsius,
            "location": self.active_crisis.location,
            "deadline": self.completion_deadline.isoformat(),
            "steps_planned": len(self.crisis_steps)
        })
        
        # Execute steps with proper timing
        for step in self.crisis_steps:
            if datetime.now(timezone.utc) >= self.completion_deadline:
                self.logger.error("⏰ Crisis response deadline exceeded!")
                break
            
            await self._execute_crisis_step(step)
        
        # Evaluate crisis resolution
        await self._evaluate_crisis_completion()
    
    async def _execute_crisis_step(self, step: ScenarioStepRuntime):
        """Execute a single crisis response step"""
        self.logger.info(f"🔄 Executing step: {step.step_id} - {step.description}")
        
        # Wait for step start time if needed
        current_time = datetime.now(timezone.utc)
        if current_time < step.start_time:
            wait_time = (step.start_time - current_time).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # Trigger appropriate events based on step
        await self._trigger_step_events(step)
        
        # Wait for agent responses with timeout
        step_deadline = step.start_time + timedelta(seconds=step.timeout_seconds)
        await self._wait_for_step_responses(step, step_deadline)
        
        # Mark step as completed
        step.completed = True
        step.success = len(step.agent_responses) >= len(step.required_agents) * 0.8  # 80% success rate
        
        self.logger.info(
            f"✅ Step completed: {step.step_id} - Success: {step.success} "
            f"({len(step.agent_responses)}/{len(step.required_agents)} agents responded)"
        )
    
    async def _trigger_step_events(self, step: ScenarioStepRuntime):
        """Trigger appropriate events for a crisis step"""
        if not self.active_crisis:
            return
        
        base_event_data = {
            "crisis_id": self.active_crisis.event_id,
            "step_id": step.step_id,
            "temperature_fahrenheit": self.active_crisis.temperature_fahrenheit,
            "temperature_celsius": self.active_crisis.temperature_celsius,
            "location": self.active_crisis.location,
            "emergency": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Trigger events based on step type
        if step.step_id == "hvac_emergency_response":
            await self.event_bus.publish("hvac.temperature.changed", json.dumps({
                **base_event_data,
                "temperature": self.active_crisis.temperature_celsius,
                "trend": "rising",
                "rate": self.active_crisis.rate_of_change,
                "emergency": True
            }))
        
        elif step.step_id == "power_coordination":
            await self.event_bus.publish("hvac.cooling.decision", json.dumps({
                **base_event_data,
                "cooling_level": "emergency",
                "reasoning": "Emergency cooling required for crisis response",
                "agent_type": "hvac_specialist"
            }))
        
        elif step.step_id == "security_lockdown":
            await self.event_bus.publish("facility.security.event", json.dumps({
                **base_event_data,
                "event_type": "environmental_emergency",
                "severity": "critical",
                "event_id": f"security_{step.step_id}_{int(time.time())}"
            }))
        
        elif step.step_id == "multi_agent_coordination":
            await self.event_bus.publish("facility.coordination.scenario", json.dumps({
                **base_event_data,
                "scenario_type": "cooling_crisis",
                "emergency_level": "critical",
                "agent_responses": dict(self.agent_responses)
            }, default=_json_default))
        
        elif step.step_id == "crisis_resolution":
            await self.event_bus.publish("hvac.temperature.changed", json.dumps({
                **base_event_data,
                "temperature": max(22.0, self.active_crisis.temperature_celsius - 2.0),  # Simulated cooling
                "trend": "stabilizing",
                "rate": -0.5,
                "verification_required": True
            }))
    
    async def _wait_for_step_responses(self, step: ScenarioStepRuntime, deadline: datetime):
        """Wait for agent responses to a crisis step"""
        while datetime.now(timezone.utc) < deadline and len(step.agent_responses) < len(step.required_agents):
            # Check for new responses
            for agent_type in step.required_agents:
                if agent_type in self.agent_responses:
                    # Find responses that occurred after step start
                    recent_responses = [
                        resp for resp in self.agent_responses[agent_type]
                        if resp.get("timestamp", 0) >= step.start_time.timestamp() and
                        agent_type not in step.agent_responses
                    ]
                    
                    if recent_responses:
                        step.agent_responses[agent_type] = recent_responses[-1]  # Latest response
            
            await asyncio.sleep(0.1)  # Short polling interval
    
    async def _handle_agent_response(self, message: str):
        """Handle agent responses during crisis"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            # Extract and normalize agent type
            raw_agent_type = data.get("agent_type", "unknown_agent")
            agent_type = "unknown_agent"
            
            if "hvac" in raw_agent_type:
                agent_type = str(AgentType.HVAC)
            elif "power" in raw_agent_type:
                agent_type = str(AgentType.POWER)
            elif "security" in raw_agent_type:
                agent_type = str(AgentType.SECURITY)
            elif "network" in raw_agent_type:
                agent_type = str(AgentType.NETWORK)
            elif "coordinator" in raw_agent_type:
                agent_type = str(AgentType.COORDINATOR)
            else:
                agent_type = raw_agent_type
            
            # Store response with timestamp
            response_record = {
                **data,
                "received_at": datetime.now(timezone.utc),
                "timestamp": time.time()
            }
            
            if agent_type not in self.agent_responses:
                self.agent_responses[agent_type] = []
            
            self.agent_responses[agent_type].append(response_record)
            
            # Log coordination event
            self.coordination_events.append({
                "type": "agent_response",
                "agent_type": agent_type,
                "timestamp": datetime.now(timezone.utc),
                "crisis_active": self.active_crisis is not None,
                "data": data
            })
            
            self.logger.debug(f"📨 Agent response received: {agent_type}")
            
        except Exception as e:
            self.logger.error(f"Error handling agent response: {e}")
    
    async def _monitor_crisis_progress(self, temp_data: Dict[str, Any], temp_f: float, temp_c: float):
        """Monitor ongoing crisis progress"""
        if not self.active_crisis:
            return
        
        # Update crisis temperature data using model_copy (frozen model pattern)
        self.active_crisis = self.active_crisis.model_copy(update={
            "temperature_fahrenheit": temp_f,
            "temperature_celsius": temp_c,
            "trend": temp_data.get("trend", "stable"),
            "rate_of_change": temp_data.get("rate", 0.0),
        })
        
        # Check if crisis is resolving
        if temp_f < FAHRENHEIT_THRESHOLD and temp_data.get("trend") == "decreasing":
            await self._begin_crisis_resolution()
    
    async def _begin_crisis_resolution(self):
        """Begin crisis resolution process"""
        if not self.active_crisis:
            return
        
        self.logger.info("🎯 Temperature below threshold - beginning crisis resolution")
        
        await self._publish_crisis_event("cooling_crisis_resolving", {
            "crisis_id": self.active_crisis.event_id,
            "current_temperature_fahrenheit": self.active_crisis.temperature_fahrenheit,
            "current_temperature_celsius": self.active_crisis.temperature_celsius,
            "trend": self.active_crisis.trend
        })
    
    async def _evaluate_crisis_completion(self):
        """Evaluate crisis completion and update metrics"""
        if not self.active_crisis or not self.start_time:
            return
        
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate success metrics
        completed_steps = sum(1 for step in self.crisis_steps if step.completed)
        successful_steps = sum(1 for step in self.crisis_steps if step.success)
        
        success = (
            total_duration <= 120.0 and  # Within 2-minute constraint
            completed_steps >= len(self.crisis_steps) * 0.8 and  # 80% steps completed
            successful_steps >= len(self.crisis_steps) * 0.6 and  # 60% steps successful
            len(self.agent_responses) >= 3  # At least 3 agents responded
        )
        
        # Update metrics
        self.metrics["total_crises_handled"] += 1
        if success:
            self.metrics["successful_completions"] += 1
        
        # Update average response time
        old_avg = self.metrics["average_response_time"]
        count = self.metrics["total_crises_handled"]
        self.metrics["average_response_time"] = (old_avg * (count - 1) + total_duration) / count
        
        # Update coordination success rate
        coordination_success = len(self.agent_responses) / max(len(set(
            agent for step in self.crisis_steps for agent in step.required_agents
        )), 1)
        self.metrics["agent_coordination_success_rate"] = (
            self.metrics["agent_coordination_success_rate"] * (count - 1) + coordination_success
        ) / count
        
        # Publish completion event
        await self._publish_crisis_event("cooling_crisis_completed", {
            "crisis_id": self.active_crisis.event_id,
            "success": success,
            "duration_seconds": total_duration,
            "completed_steps": completed_steps,
            "successful_steps": successful_steps,
            "total_steps": len(self.crisis_steps),
            "agents_responded": len(self.agent_responses),
            "final_temperature_fahrenheit": self.active_crisis.temperature_fahrenheit,
            "final_temperature_celsius": self.active_crisis.temperature_celsius
        })
        
        self.logger.info(
            f"🏁 Crisis completed: {self.active_crisis.event_id} - "
            f"Success: {success} - Duration: {total_duration:.1f}s - "
            f"Steps: {successful_steps}/{len(self.crisis_steps)} - "
            f"Agents: {len(self.agent_responses)}"
        )
        
        # Reset crisis state
        await self._reset_crisis_state()
    
    async def _reset_crisis_state(self):
        """Reset crisis state for next scenario"""
        self.active_crisis = None
        self.crisis_steps.clear()
        self.start_time = None
        self.completion_deadline = None
        self.agent_responses.clear()
        self.coordination_events.clear()
    
    async def _publish_crisis_event(self, event_type: str, data: Dict[str, Any]):
        """Publish crisis-related events to the event bus"""
        await self.event_bus.publish(f"cooling_crisis.{event_type}", json.dumps({
            **data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario_type": "cooling_crisis"
        }))
    
    def _celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit"""
        return (celsius * 9/5) + 32
    
    def _fahrenheit_to_celsius(self, fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius"""
        return (fahrenheit - 32) * 5/9
    
    def get_crisis_status(self) -> Dict[str, Any]:
        """Get current crisis status"""
        if not self.active_crisis:
            return {
                "active": False,
                "status": "idle",
                "metrics": self.metrics
            }
        
        current_time = datetime.now(timezone.utc)
        elapsed_time = (current_time - self.start_time).total_seconds() if self.start_time else 0
        remaining_time = max(0, 120 - elapsed_time)
        
        return {
            "active": True,
            "crisis_id": self.active_crisis.event_id,
            "status": "active",
            "temperature_fahrenheit": self.active_crisis.temperature_fahrenheit,
            "temperature_celsius": self.active_crisis.temperature_celsius,
            "location": self.active_crisis.location,
            "elapsed_seconds": elapsed_time,
            "remaining_seconds": remaining_time,
            "completion_percentage": min(100, (elapsed_time / 120) * 100),
            "steps_completed": sum(1 for step in self.crisis_steps if step.completed),
            "total_steps": len(self.crisis_steps),
            "agents_responded": len(self.agent_responses),
            "coordination_events": len(self.coordination_events),
            "metrics": self.metrics
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for cooling crisis scenarios"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_completions"] / max(self.metrics["total_crises_handled"], 1) * 100
            ),
            "current_crisis_active": self.active_crisis is not None
        }
    
    async def trigger_test_crisis(self, temperature_fahrenheit: float = 90.0) -> bool:
        """Trigger a test cooling crisis for demonstration purposes"""
        try:
            test_data = {
                "temperature": self._fahrenheit_to_celsius(temperature_fahrenheit),
                "trend": "rising",
                "rate": 1.5,
                "location": "test_server_room",
                "timestamp": time.time()
            }
            
            await self._handle_temperature_event(json.dumps(test_data))
            return True
            
        except Exception as e:
            self.logger.error(f"Error triggering test crisis: {e}")
            return False
    
    async def integrate_with_orchestrator(self) -> bool:
        """Integrate cooling crisis with the scenario orchestrator"""
        try:
            # Check if orchestrator has cooling crisis scenario
            if ScenarioType.COOLING_CRISIS in self.orchestrator.scenario_definitions:
                self.logger.info("✅ Cooling crisis scenario found in orchestrator")
                
                # Subscribe to orchestrator events
                self.event_bus.subscribe(
                    "demo.scenario.start",
                    self._handle_orchestrator_event
                )
                
                return True
            else:
                self.logger.warning("⚠️ Cooling crisis scenario not found in orchestrator")
                return False
                
        except Exception as e:
            self.logger.error(f"Error integrating with orchestrator: {e}")
            return False
    
    async def _handle_orchestrator_event(self, message: str):
        """Handle events from the scenario orchestrator"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            if data.get("scenario") == "cooling_crisis":
                self.logger.info("🎭 Orchestrator cooling crisis scenario detected")
                
                # Trigger our cooling crisis implementation
                await self.trigger_test_crisis(89.5)
                
        except Exception as e:
            self.logger.error(f"Error handling orchestrator event: {e}")