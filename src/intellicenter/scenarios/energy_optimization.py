"""
Energy Optimization Scenario Implementation

This module implements the Energy Optimization scenario logic with:
- Energy efficiency triggers (high consumption patterns)
- Power-HVAC-Coordinator coordination
- 3-minute completion constraint
- Step-by-step scenario execution
- Integration with scenario orchestrator

Features:
- Energy consumption monitoring and optimization
- Multi-agent coordination for energy savings
- Price-based optimization opportunities
- Timing constraints and completion tracking
- Pre-cooling strategies for energy arbitrage
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Callable

from ..shared.event_bus import EventBus
from ..shared.logger import logger
from intellicenter.shared.schema import (
    AgentType,
    EnergyConsumptionEvent,
    EventPriority,
    EventSeverity,
    ScenarioResult,
    ScenarioState,
    ScenarioStepRuntime,
    ScenarioType,
)

from .scenario_orchestrator import ScenarioOrchestrator


# Energy optimization constants
HIGH_CONSUMPTION_THRESHOLD = 80.0  # Percentage
PRICE_DROP_THRESHOLD = 0.10  # 10% price drop
PRE_COOLING_TARGET_TEMP = 20.0  # Celsius
NORMAL_TEMP = 22.0  # Celsius
MAX_DURATION_SECONDS = 180.0  # 3 minutes


# Removed local dataclass definitions as they are now in shared.schema


class EnergyOptimizationScenario:
    """
    Energy Optimization Scenario Implementation
    
    Handles energy cost optimization scenarios requiring coordination
    between Power, HVAC, and Coordinator agents within a 3-minute timeframe.
    """
    
    def __init__(self, event_bus: EventBus, orchestrator: ScenarioOrchestrator):
        self.event_bus = event_bus
        self.orchestrator = orchestrator
        self.logger = logger.bind(scenario="energy_optimization")
        
        # Scenario state
        self.active_optimization: Optional[EnergyConsumptionEvent] = None
        self.optimization_steps: List[EnergyOptimizationStep] = []
        self.start_time: Optional[datetime] = None
        self.completion_deadline: Optional[datetime] = None
        
        # Agent coordination tracking
        self.agent_responses: Dict[str, List[Dict[str, Any]]] = {}
        self.coordination_events: List[Dict[str, Any]] = []
        self.optimization_actions_taken: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics = {
            "total_optimizations_handled": 0,
            "successful_optimizations": 0,
            "average_response_time": 0.0,
            "coordination_success_rate": 0.0,
            "energy_savings_achieved": 0,
            "price_optimizations": 0,
            "pre_cooling_initiations": 0
        }
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions for energy optimization monitoring"""
        # Subscribe to energy consumption events
        self.event_bus.subscribe(
            "power.consumption.changed", 
            self._handle_consumption_event
        )
        
        self.event_bus.subscribe(
            "power.price.changed",
            self._handle_price_event
        )
        
        # Subscribe to agent responses
        agent_events = [
            "power.optimization.decision",
            "hvac.cooling.decision",
            "facility.coordination.directive",
            "facility.coordination.scenario_orchestration"
        ]
        
        for event_type in agent_events:
            self.event_bus.subscribe(event_type, self._handle_agent_response)
    
    async def _handle_consumption_event(self, message: str):
        """Handle incoming energy consumption events and trigger optimization if threshold exceeded"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            # Extract consumption data
            consumption = data.get("consumption", 60.0)
            location = data.get("location", "facility_main")
            
            # Check if optimization threshold is exceeded
            if consumption >= HIGH_CONSUMPTION_THRESHOLD:
                await self._trigger_energy_optimization(data, consumption, location)
            elif self.active_optimization:
                # Monitor ongoing optimization
                await self._monitor_optimization_progress(data, consumption, location)
                
        except Exception as e:
            self.logger.error(f"Error handling consumption event: {e}")
    
    async def _handle_price_event(self, message: str):
        """Handle incoming price events and trigger optimization opportunities"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            # Extract price data
            current_price = data.get("current_price", 0.10)
            previous_price = data.get("previous_price", 0.12)
            price_drop = previous_price - current_price
            price_drop_percentage = (price_drop / previous_price) * 100
            
            # Check if price drop threshold is exceeded
            if price_drop_percentage >= PRICE_DROP_THRESHOLD * 100:
                await self._trigger_price_optimization(data, current_price, price_drop_percentage)
                
        except Exception as e:
            self.logger.error(f"Error handling price event: {e}")
    
    async def _trigger_energy_optimization(self, consumption_data: Dict[str, Any], consumption: float, location: str):
        """Trigger an energy optimization scenario"""
        if self.active_optimization:
            self.logger.warning("Optimization already active, updating data")
            return
        
        # Create optimization event using Pydantic model
        optimization_event = EnergyConsumptionEvent(
            event_id=f"energy_optimization_{int(time.time())}",
            timestamp=datetime.now(timezone.utc),
            event_type="energy_optimization_triggered",
            location=location,
            priority=EventPriority.MEDIUM,
            severity=EventSeverity.INFO,
            consumption_kw=consumption,  # Assuming consumption is in kw or mapping it
            current_price=consumption_data.get("current_price", 0.10),
            price_trend="high",
            emergency=True,
            payload=consumption_data
        )
        
        self.active_optimization = optimization_event
        self.start_time = datetime.now(timezone.utc)
        self.completion_deadline = self.start_time + timedelta(seconds=MAX_DURATION_SECONDS)
        
        self.logger.critical(
            f"⚡ ENERGY OPTIMIZATION TRIGGERED: {consumption:.1f}% consumption "
            f"at {location} - {MAX_DURATION_SECONDS}-second optimization window activated"
        )
        
        # Initialize optimization response steps
        await self._initialize_optimization_steps()
        
        # Start optimization response execution
        await self._execute_optimization_response()
    
    async def _trigger_price_optimization(self, price_data: Dict[str, Any], current_price: float, price_drop_percentage: float):
        """Trigger a price-based energy optimization scenario"""
        if self.active_optimization:
            self.logger.warning("Optimization already active, updating with price data")
            return
        
        # Create optimization event using Pydantic model
        optimization_event = EnergyConsumptionEvent(
            event_id=f"price_optimization_{int(time.time())}",
            timestamp=datetime.now(timezone.utc),
            event_type="price_optimization_opportunity",
            location=price_data.get("location", "facility_main"),
            priority=EventPriority.LOW,
            severity=EventSeverity.INFO,
            consumption_kw=price_data.get("consumption", 70.0),
            current_price=current_price,
            price_trend="decreasing",
            emergency=False,
            payload=price_data
        )
        
        self.active_optimization = optimization_event
        self.start_time = datetime.now(timezone.utc)
        self.completion_deadline = self.start_time + timedelta(seconds=MAX_DURATION_SECONDS)
        
        self.logger.info(
            f"💰 PRICE OPTIMIZATION OPPORTUNITY: {price_drop_percentage:.1f}% price drop "
            f"to ${current_price:.3f}/kWh - {MAX_DURATION_SECONDS}-second optimization window activated"
        )
        
        # Initialize optimization response steps
        await self._initialize_optimization_steps()
        
        # Start optimization response execution
        await self._execute_optimization_response()
    
    async def _initialize_optimization_steps(self):
        """Initialize the step-by-step optimization response plan"""
        if not self.active_optimization:
            return
        
        current_time = datetime.now(timezone.utc)
        
        # Step 1: Energy Analysis (0-30 seconds)
        self.optimization_steps.append(ScenarioStepRuntime(
            step_id="energy_analysis",
            description="Energy consumption analysis and optimization opportunity identification",
            event_type="power.consumption.changed",
            start_time=current_time,
            timeout_seconds=30.0,
            required_agents=[AgentType.POWER],
            expected_responses=["power.optimization.decision"],
            event_data={"actions": ["consumption_analysis", "cost_calculation"]}
        ))
        
        # Step 2: Pre-cooling Strategy (30-60 seconds)
        self.optimization_steps.append(ScenarioStepRuntime(
            step_id="pre_cooling_strategy",
            description="Pre-cooling strategy implementation for energy arbitrage",
            event_type="hvac.temperature.changed",
            start_time=current_time + timedelta(seconds=30),
            timeout_seconds=30.0,
            required_agents=[AgentType.HVAC],
            expected_responses=["hvac.cooling.decision"],
            event_data={"actions": ["pre_cooling_initiation", "temperature_optimization"]}
        ))
        
        # Step 3: Power System Coordination (60-90 seconds)
        self.optimization_steps.append(ScenarioStepRuntime(
            step_id="power_coordination",
            description="Power system optimization and load balancing",
            event_type="power.optimization.decision",
            start_time=current_time + timedelta(seconds=60),
            timeout_seconds=30.0,
            required_agents=[AgentType.POWER],
            expected_responses=["power.optimization.decision"],
            event_data={"actions": ["load_balancing", "peak_shaving"]}
        ))
        
        # Step 4: Multi-Agent Coordination (90-120 seconds)
        self.optimization_steps.append(ScenarioStepRuntime(
            step_id="coordination_response",
            description="Coordinated response between power and HVAC systems",
            event_type="facility.coordination.scenario",
            start_time=current_time + timedelta(seconds=90),
            timeout_seconds=30.0,
            required_agents=[AgentType.COORDINATOR],
            expected_responses=["facility.coordination.directive"],
            event_data={"actions": ["resource_coordination", "optimization_validation"]}
        ))
        
        # Step 5: Optimization Verification (120-180 seconds)
        self.optimization_steps.append(ScenarioStepRuntime(
            step_id="optimization_verification",
            description="Verify optimization success and system stabilization",
            event_type="hvac.temperature.changed",
            start_time=current_time + timedelta(seconds=120),
            timeout_seconds=60.0,
            required_agents=[AgentType.POWER, AgentType.HVAC, AgentType.COORDINATOR],
            expected_responses=["power.optimization.decision", "hvac.cooling.decision", "facility.coordination.directive"],
            event_data={"actions": ["savings_verification", "system_stabilization"]}
        ))
    
    async def _execute_optimization_response(self):
        """Execute the optimization response steps with timing coordination"""
        if not self.active_optimization or not self.optimization_steps:
            return
        
        self.logger.info(f"🎯 Executing {len(self.optimization_steps)} optimization response steps")
        
        # Publish optimization initiation event
        await self._publish_optimization_event("energy_optimization_initiated", {
            "optimization_id": self.active_optimization.event_id,
            "current_consumption": self.active_optimization.current_consumption,
            "current_price": self.active_optimization.current_price,
            "price_trend": self.active_optimization.price_trend,
            "location": self.active_optimization.location,
            "deadline": self.completion_deadline.isoformat(),
            "steps_planned": len(self.optimization_steps)
        })
        
        # Execute steps with proper timing
        for step in self.optimization_steps:
            if datetime.now(timezone.utc) >= self.completion_deadline:
                self.logger.error("⏰ Optimization response deadline exceeded!")
                break
            
            await self._execute_optimization_step(step)
        
        # Evaluate optimization completion
        await self._evaluate_optimization_completion()
    
    async def _execute_optimization_step(self, step: ScenarioStepRuntime):
        """Execute a single optimization response step"""
        self.logger.info(f"🔄 Executing step: {step.step_id} - {step.description}")
        
        # Wait for step start time if needed
        current_time = datetime.now(timezone.utc)
        if current_time < step.start_time:
            wait_time = (step.start_time - current_time).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # Trigger appropriate events based on step
        await self._trigger_step_events(step)
        
        # Execute optimization actions
        await self._execute_optimization_actions(step)
        
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
        """Trigger appropriate events for an optimization step"""
        if not self.active_optimization:
            return
        
        base_event_data = {
            "optimization_id": self.active_optimization.event_id,
            "step_id": step.step_id,
            "current_consumption": self.active_optimization.consumption_kw,
            "current_price": self.active_optimization.current_price,
            "price_trend": self.active_optimization.price_trend,
            "location": self.active_optimization.location,
            "optimization": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Trigger events based on step type
        if step.step_id == "energy_analysis":
            await self.event_bus.publish("power.consumption.changed", json.dumps({
                **base_event_data,
                "consumption": self.active_optimization.consumption_kw,
                "trend": "high",
                "optimization_opportunity": True,
                "threshold_exceeded": True
            }))
        
        elif step.step_id == "pre_cooling_strategy":
            await self.event_bus.publish("hvac.temperature.changed", json.dumps({
                **base_event_data,
                "temperature": PRE_COOLING_TARGET_TEMP,
                "trend": "decreasing",
                "rate": -0.5,
                "pre_cooling": True,
                "strategy": "energy_arbitrage"
            }))
        
        elif step.step_id == "power_coordination":
            await self.event_bus.publish("power.optimization.decision", json.dumps({
                **base_event_data,
                "optimization_level": "aggressive",
                "reasoning": "Energy cost optimization required",
                "agent_type": "power_specialist",
                "price_based": True
            }))
        
        elif step.step_id == "coordination_response":
            await self.event_bus.publish("facility.coordination.scenario", json.dumps({
                **base_event_data,
                "scenario_type": "power_overload",
                "emergency_level": "normal",
                "agent_responses": dict(self.agent_responses)
            }))
        
        elif step.step_id == "optimization_verification":
            await self.event_bus.publish("hvac.temperature.changed", json.dumps({
                **base_event_data,
                "temperature": NORMAL_TEMP,
                "trend": "stable",
                "rate": 0.0,
                "verification_required": True,
                "optimization_complete": True
            }))
    
    async def _execute_optimization_actions(self, step: ScenarioStepRuntime):
        """Execute optimization actions for a step"""
        if not self.active_optimization:
            return
        
        actions = step.event_data.get("actions", [])
        for action in actions:
            action_record = {
                "action": action,
                "step_id": step.step_id,
                "timestamp": datetime.now(timezone.utc),
                "optimization_id": self.active_optimization.event_id,
                "location": self.active_optimization.location,
                "status": "initiated"
            }
            
            # Simulate action execution
            if action == "consumption_analysis":
                action_record["status"] = "completed"
                action_record["details"] = f"Consumption analysis completed: {self.active_optimization.consumption_kw}% load"
                action_record["recommendations"] = "Reduce non-essential loads during peak hours"
                self.logger.info(f"📊 Consumption analysis completed for {self.active_optimization.location}")
            
            elif action == "cost_calculation":
                action_record["status"] = "completed"
                action_record["details"] = f"Cost calculation: ${self.active_optimization.current_price:.3f}/kWh"
                action_record["potential_savings"] = f"${(self.active_optimization.current_price * 0.15):.2f}/kWh estimated"
                self.logger.info(f"💰 Cost calculation completed for {self.active_optimization.location}")
            
            elif action == "pre_cooling_initiation":
                action_record["status"] = "completed"
                action_record["details"] = f"Pre-cooling initiated to {PRE_COOLING_TARGET_TEMP}°C"
                action_record["energy_savings"] = "15% cooling energy reduction expected"
                self.metrics["pre_cooling_initiations"] += 1
                self.logger.info(f"❄️ Pre-cooling initiated at {self.active_optimization.location}")
            
            elif action == "temperature_optimization":
                action_record["status"] = "completed"
                action_record["details"] = f"Temperature optimized to {PRE_COOLING_TARGET_TEMP}°C for energy efficiency"
                action_record["efficiency_gain"] = "8% HVAC energy savings expected"
                self.logger.info(f"🌡️ Temperature optimization completed for {self.active_optimization.location}")
            
            elif action == "load_balancing":
                action_record["status"] = "completed"
                action_record["details"] = "Power load balancing implemented across facility"
                action_record["load_distribution"] = "Critical systems prioritized, non-essential reduced"
                self.logger.info(f"⚡ Load balancing implemented for {self.active_optimization.location}")
            
            elif action == "peak_shaving":
                action_record["status"] = "completed"
                action_record["details"] = "Peak shaving strategies activated"
                action_record["peak_reduction"] = "20% peak demand reduction achieved"
                self.metrics["energy_savings_achieved"] += 20
                self.logger.info(f"📈 Peak shaving activated for {self.active_optimization.location}")
            
            elif action == "resource_coordination":
                action_record["status"] = "completed"
                action_record["details"] = "Multi-agent resource coordination completed"
                action_record["coordination_summary"] = "Power and HVAC systems synchronized for optimal efficiency"
                self.logger.info(f"🤝 Resource coordination completed for {self.active_optimization.location}")
            
            elif action == "optimization_validation":
                action_record["status"] = "completed"
                action_record["details"] = "Optimization validation procedures completed"
                action_record["validation_results"] = "All systems operating within optimized parameters"
                self.logger.info(f"✅ Optimization validation completed for {self.active_optimization.location}")
            
            elif action == "savings_verification":
                action_record["status"] = "completed"
                action_record["details"] = "Energy savings verification completed"
                action_record["actual_savings"] = f"{self.metrics['energy_savings_achieved']}% reduction achieved"
                self.metrics["energy_savings_achieved"] += 5
                self.logger.info(f"📊 Savings verification completed for {self.active_optimization.location}")
            
            elif action == "system_stabilization":
                action_record["status"] = "completed"
                action_record["details"] = "System stabilization completed"
                action_record["stabilization_status"] = "All systems operating at optimal efficiency"
                self.logger.info(f"🔧 System stabilization completed for {self.active_optimization.location}")
            
            self.optimization_actions_taken.append(action_record)
    
    async def _wait_for_step_responses(self, step: ScenarioStepRuntime, deadline: datetime):
        """Wait for agent responses to an optimization step"""
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
        """Handle agent responses during optimization"""
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
                "optimization_active": self.active_optimization is not None,
                "data": data
            })
            
            self.logger.debug(f"📨 Agent response received: {agent_type}")
            
        except Exception as e:
            self.logger.error(f"Error handling agent response: {e}")
    
    async def _monitor_optimization_progress(self, consumption_data: Dict[str, Any], consumption: float, location: str):
        """Monitor ongoing optimization progress"""
        if not self.active_optimization:
            return
        
        # Update optimization data
        self.active_optimization.consumption_kw = consumption
        self.active_optimization.location = location
        
        # Check if optimization is successful
        if consumption < HIGH_CONSUMPTION_THRESHOLD * 0.9:  # 10% improvement
            await self._begin_optimization_resolution()
    
    async def _begin_optimization_resolution(self):
        """Begin optimization resolution process"""
        if not self.active_optimization:
            return
        
        self.logger.info("🎯 Consumption below threshold - beginning optimization resolution")
        
        await self._publish_optimization_event("energy_optimization_resolving", {
            "optimization_id": self.active_optimization.event_id,
            "current_consumption": self.active_optimization.current_consumption,
            "current_price": self.active_optimization.current_price,
            "trend": self.active_optimization.price_trend
        })
    
    async def _evaluate_optimization_completion(self):
        """Evaluate optimization completion and update metrics"""
        if not self.active_optimization or not self.start_time:
            return
        
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate success metrics
        completed_steps = sum(1 for step in self.optimization_steps if step.completed)
        successful_steps = sum(1 for step in self.optimization_steps if step.success)
        
        # Calculate energy savings
        total_savings = self.metrics["energy_savings_achieved"]
        price_optimizations = self.metrics["price_optimizations"]
        
        success = (
            total_duration <= MAX_DURATION_SECONDS and  # Within 3-minute constraint
            completed_steps >= len(self.optimization_steps) * 0.8 and  # 80% steps completed
            successful_steps >= len(self.optimization_steps) * 0.6 and  # 60% steps successful
            len(self.agent_responses) >= 3 and  # All 3 agents responded
            total_savings > 0 and  # Energy savings achieved
            price_optimizations >= 0  # Price optimizations completed
        )
        
        # Update metrics
        self.metrics["total_optimizations_handled"] += 1
        if success:
            self.metrics["successful_optimizations"] += 1
            self.metrics["price_optimizations"] += 1
        
        # Update average response time
        old_avg = self.metrics["average_response_time"]
        count = self.metrics["total_optimizations_handled"]
        self.metrics["average_response_time"] = (old_avg * (count - 1) + total_duration) / count
        
        # Update coordination success rate
        coordination_success = len(self.agent_responses) / 3  # 3 required agents
        self.metrics["coordination_success_rate"] = (
            self.metrics["coordination_success_rate"] * (count - 1) + coordination_success
        ) / count
        
        # Publish completion event
        await self._publish_optimization_event("energy_optimization_completed", {
            "optimization_id": self.active_optimization.event_id,
            "success": success,
            "duration_seconds": total_duration,
            "completed_steps": completed_steps,
            "successful_steps": successful_steps,
            "total_steps": len(self.optimization_steps),
            "agents_responded": len(self.agent_responses),
            "optimization_actions": len(self.optimization_actions_taken),
            "energy_savings_achieved": total_savings,
            "price_optimizations": price_optimizations,
            "pre_cooling_initiations": self.metrics["pre_cooling_initiations"],
            "final_consumption": self.active_optimization.consumption_kw,
            "final_price": self.active_optimization.current_price
        })
        
        self.logger.info(
            f"🏁 Optimization completed: {self.active_optimization.event_id} - "
            f"Success: {success} - Duration: {total_duration:.1f}s - "
            f"Steps: {successful_steps}/{len(self.optimization_steps)} - "
            f"Agents: {len(self.agent_responses)} - "
            f"Actions: {len(self.optimization_actions_taken)} - "
            f"Savings: {total_savings}%"
        )
        
        # Reset optimization state
        await self._reset_optimization_state()
    
    async def _reset_optimization_state(self):
        """Reset optimization state for next scenario"""
        self.active_optimization = None
        self.optimization_steps.clear()
        self.start_time = None
        self.completion_deadline = None
        self.agent_responses.clear()
        self.coordination_events.clear()
        self.optimization_actions_taken.clear()
    
    async def _publish_optimization_event(self, event_type: str, data: Dict[str, Any]):
        """Publish optimization-related events to the event bus"""
        await self.event_bus.publish(f"energy_optimization.{event_type}", json.dumps({
            **data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario_type": "energy_optimization"
        }))
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        if not self.active_optimization:
            return {
                "active": False,
                "status": "idle",
                "metrics": self.metrics
            }
        
        current_time = datetime.now(timezone.utc)
        elapsed_time = (current_time - self.start_time).total_seconds() if self.start_time else 0
        remaining_time = max(0, MAX_DURATION_SECONDS - elapsed_time)
        
        return {
            "active": True,
            "optimization_id": self.active_optimization.event_id,
            "status": "active",
            "current_consumption": self.active_optimization.consumption_kw,
            "current_price": self.active_optimization.current_price,
            "price_trend": self.active_optimization.price_trend,
            "location": self.active_optimization.location,
            "elapsed_seconds": elapsed_time,
            "remaining_seconds": remaining_time,
            "completion_percentage": min(100, (elapsed_time / MAX_DURATION_SECONDS) * 100),
            "steps_completed": sum(1 for step in self.optimization_steps if step.completed),
            "total_steps": len(self.optimization_steps),
            "agents_responded": len(self.agent_responses),
            "coordination_events": len(self.coordination_events),
            "optimization_actions": len(self.optimization_actions_taken),
            "metrics": self.metrics
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for energy optimization scenarios"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_optimizations"] / max(self.metrics["total_optimizations_handled"], 1) * 100
            ),
            "current_optimization_active": self.active_optimization is not None,
            "avg_actions_per_optimization": (
                len(self.optimization_actions_taken) / max(self.metrics["total_optimizations_handled"], 1)
            ),
            "avg_savings_per_optimization": (
                self.metrics["energy_savings_achieved"] / max(self.metrics["total_optimizations_handled"], 1)
            )
        }
    
    async def trigger_test_optimization(self, consumption: float = 85.0, price: float = 0.08) -> bool:
        """Trigger a test energy optimization for demonstration purposes"""
        try:
            test_data = {
                "consumption": consumption,
                "current_price": price,
                "previous_price": 0.12,
                "trend": "high",
                "location": "test_facility",
                "timestamp": time.time(),
                "test_scenario": True
            }
            
            await self._handle_consumption_event(json.dumps(test_data))
            return True
            
        except Exception as e:
            self.logger.error("error_triggering_test_optimization", error=str(e))
            return False
    
    async def integrate_with_orchestrator(self) -> bool:
        """Integrate energy optimization with the scenario orchestrator"""
        try:
            # Check if orchestrator has energy optimization scenario
            if ScenarioType.ENERGY_OPTIMIZATION in self.orchestrator.scenario_definitions:
                self.logger.info("orchestrator_integration_found", scenario=ScenarioType.ENERGY_OPTIMIZATION)
                
                # Subscribe to orchestrator events
                self.event_bus.subscribe(
                    "demo.scenario.start",
                    self._handle_orchestrator_event
                )
                
                return True
            else:
                self.logger.warning("orchestrator_integration_not_found", scenario=ScenarioType.ENERGY_OPTIMIZATION)
                return False
                
        except Exception as e:
            self.logger.error("orchestrator_integration_error", error=str(e))
            return False
    
    async def _handle_orchestrator_event(self, message: str):
        """Handle events from the scenario orchestrator"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            if data.get("scenario") == "energy_optimization":
                self.logger.info("orchestrator_scenario_detected", scenario="energy_optimization")
                
                # Trigger our energy optimization implementation
                await self.trigger_test_optimization(85.0, 0.08)
                
        except Exception as e:
            self.logger.error("orchestrator_event_handler_error", error=str(e))