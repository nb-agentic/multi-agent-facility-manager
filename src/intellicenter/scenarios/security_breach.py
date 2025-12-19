"""
Security Breach Scenario Implementation

This module implements the Security Breach scenario logic with:
- Unauthorized access triggers and detection
- Security-Network-Coordinator multi-agent coordination
- 90-second completion constraint
- Step-by-step scenario execution
- Integration with scenario orchestrator

Features:
- Suspicious access monitoring
- Multi-layered security response
- Network isolation protocols
- Timing constraints and completion tracking
- Emergency lockdown procedures
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Callable

from ..shared.event_bus import EventBus
from ..shared.logger import logger
from ..shared.schema import (
    AgentType,
    SecurityBreachEvent,
    EventPriority,
    EventSeverity,
    ScenarioResult,
    ScenarioState,
    ScenarioStepRuntime,
    ScenarioType
)


# Security threshold constants
MAX_ACCESS_ATTEMPTS = 3
SUSPICIOUS_THRESHOLD = 2
CRITICAL_THRESHOLD = 3
LOCKDOWN_DURATION_SECONDS = 90




class SecurityBreachScenario:
    """
    Security Breach Scenario Implementation
    
    Handles unauthorized access scenarios requiring coordination
    between Security, Network, and Coordinator agents within a 90-second timeframe.
    """
    
    def __init__(self, event_bus: EventBus, orchestrator: Any):
        self.event_bus = event_bus
        self.orchestrator = orchestrator
        self.logger = logger.bind(scenario="security_breach")
        
        # Scenario state
        self.active_breach: Optional[SecurityBreachEvent] = None
        self.breach_steps: List[ScenarioStepRuntime] = []
        self.start_time: Optional[datetime] = None
        self.completion_deadline: Optional[datetime] = None
        
        # Agent coordination tracking
        self.agent_responses: Dict[str, List[Dict[str, Any]]] = {}
        self.coordination_events: List[Dict[str, Any]] = []
        self.security_actions_taken: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics = {
            "total_breaches_handled": 0,
            "successful_resolutions": 0,
            "average_response_time": 0.0,
            "coordination_success_rate": 0.0,
            "lockdown_initiated": 0,
            "network_isolations": 0
        }
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions for security breach monitoring"""
        # Subscribe to security events
        self.event_bus.subscribe(
            "security.access.suspicious", 
            self._handle_suspicious_access
        )
        
        self.event_bus.subscribe(
            "security.breach.detected",
            self._handle_breach_detection
        )
        
        # Subscribe to agent responses
        agent_events = [
            "security.assessment.decision",
            "network.assessment.decision",
            "facility.coordination.directive",
            "facility.coordination.scenario_orchestration"
        ]
        
        for event_type in agent_events:
            self.event_bus.subscribe(event_type, self._handle_agent_response)
    
    async def _handle_suspicious_access(self, message: str):
        """Handle suspicious access attempts and trigger breach if threshold exceeded"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            # Extract security data
            location = data.get("location", "unknown")
            user_id = data.get("user_id", "unknown")
            attempts = data.get("attempts", 1)
            severity = data.get("severity", "medium")
            
            # Check if breach threshold is exceeded
            if attempts >= SUSPICIOUS_THRESHOLD:
                await self._trigger_security_breach(data, location, user_id, attempts, severity)
            elif self.active_breach:
                # Monitor ongoing breach
                await self._monitor_breach_progress(data, location, user_id, attempts)
                
        except Exception as e:
            self.logger.error("error_handling_suspicious_access", error=str(e))
    
    async def _handle_breach_detection(self, message: str):
        """Handle confirmed security breach detection"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            # Extract breach data
            location = data.get("location", "unknown")
            breach_type = data.get("breach_type", "unauthorized_access")
            severity = data.get("severity", "high")
            
            await self._trigger_confirmed_breach(data, location, breach_type, severity)
                
        except Exception as e:
            self.logger.error("error_handling_breach_detection", error=str(e))
    
    async def _trigger_security_breach(self, access_data: Dict[str, Any], location: str, user_id: str, attempts: int, severity: str):
        """Trigger a security breach scenario"""
        if self.active_breach:
            self.logger.warning("Breach already active, updating severity")
            return
        
        # Create breach event
        breach_event = SecurityBreachEvent(
            event_id=f"security_breach_{int(time.time())}",
            timestamp=datetime.now(timezone.utc),
            event_type="security.breach.detected",
            priority=EventPriority.CRITICAL,
            severity=EventSeverity.CRITICAL,
            location=location,
            breach_type="unauthorized_access",
            user_id=user_id,
            access_attempts=attempts,
            unauthorized_access=True,
            payload={
                "attempts": attempts,
                "user_id": user_id,
                "location": location
            }
        )
        
        self.active_breach = breach_event
        self.start_time = datetime.now(timezone.utc)
        self.completion_deadline = self.start_time + timedelta(seconds=LOCKDOWN_DURATION_SECONDS)
        
        self.logger.critical(
            "security_breach_triggered",
            user_id=user_id,
            location=location,
            attempts=attempts,
            duration=LOCKDOWN_DURATION_SECONDS
        )
        
        # Initialize breach response steps
        await self._initialize_breach_steps()
        
        # Start breach response execution
        await self._execute_breach_response()
    
    async def _trigger_confirmed_breach(self, breach_data: Dict[str, Any], location: str, breach_type: str, severity: str):
        """Trigger a confirmed security breach scenario"""
        if self.active_breach:
            self.logger.warning("Breach already active, updating with confirmed breach")
            return
        
        # Create breach event
        breach_event = SecurityBreachEvent(
            event_id=f"confirmed_breach_{int(time.time())}",
            timestamp=datetime.now(timezone.utc),
            event_type="security.breach.confirmed",
            priority=EventPriority.CRITICAL,
            severity=EventSeverity.CRITICAL,
            location=location,
            breach_type=breach_type,
            user_id=breach_data.get("user_id", "unknown"),
            access_attempts=breach_data.get("attempts", MAX_ACCESS_ATTEMPTS),
            unauthorized_access=True,
            network_anomaly=breach_data.get("network_anomaly", False),
            payload=breach_data
        )
        
        self.active_breach = breach_event
        self.start_time = datetime.now(timezone.utc)
        self.completion_deadline = self.start_time + timedelta(seconds=LOCKDOWN_DURATION_SECONDS)
        
        self.logger.critical(
            "confirmed_security_breach",
            breach_type=breach_type,
            location=location,
            severity=severity,
            duration=LOCKDOWN_DURATION_SECONDS
        )
        
        # Initialize breach response steps
        await self._initialize_breach_steps()
        
        # Start breach response execution
        await self._execute_breach_response()
    
    async def _initialize_breach_steps(self):
        """Initialize the step-by-step breach response plan"""
        if not self.active_breach:
            return
        
        current_time = datetime.now(timezone.utc)
        
        # Step 1: Immediate Security Assessment (0-15 seconds)
        self.breach_steps.append(ScenarioStepRuntime(
            step_id="security_assessment",
            description="Immediate security threat assessment and access control",
            start_time=current_time,
            timeout_seconds=15.0,
            required_agents=[AgentType.SECURITY],
            expected_responses=["security.assessment.decision"],
            event_type="security.access.suspicious",
            event_data={"actions": ["camera_surveillance", "access_control_check"]}
        ))
        
        # Step 2: Network Security Analysis (10-30 seconds)
        self.breach_steps.append(ScenarioStepRuntime(
            step_id="network_analysis",
            description="Network traffic analysis and anomaly detection",
            start_time=current_time + timedelta(seconds=10),
            timeout_seconds=20.0,
            required_agents=[AgentType.NETWORK],
            expected_responses=["network.assessment.decision"],
            event_type="facility.network.event",
            event_data={"actions": ["traffic_analysis", "security_scan"]}
        ))
        
        # Step 3: Facility Lockdown Initiation (20-45 seconds)
        self.breach_steps.append(ScenarioStepRuntime(
            step_id="lockdown_initiation",
            description="Facility-wide lockdown protocol activation",
            start_time=current_time + timedelta(seconds=20),
            timeout_seconds=25.0,
            required_agents=[AgentType.SECURITY, AgentType.NETWORK],
            expected_responses=["security.assessment.decision", "network.assessment.decision"],
            event_type="security.lockdown.initiated",
            event_data={"actions": ["door_lockdown", "network_isolation", "access_revocation"]}
        ))
        
        # Step 4: Multi-Agent Coordination (30-60 seconds)
        self.breach_steps.append(ScenarioStepRuntime(
            step_id="coordination_response",
            description="Coordinated response between security and network teams",
            start_time=current_time + timedelta(seconds=30),
            timeout_seconds=30.0,
            required_agents=[AgentType.COORDINATOR],
            expected_responses=["facility.coordination.directive"],
            event_type="facility.coordination.scenario",
            event_data={"actions": ["emergency_protocol_activation", "resource_allocation"]}
        ))
        
        # Step 5: Breach Containment and Verification (60-90 seconds)
        self.breach_steps.append(ScenarioStepRuntime(
            step_id="containment_verification",
            description="Breach containment and system verification",
            start_time=current_time + timedelta(seconds=60),
            timeout_seconds=30.0,
            required_agents=[AgentType.SECURITY, AgentType.NETWORK, AgentType.COORDINATOR],
            expected_responses=["security.assessment.decision", "network.assessment.decision", "facility.coordination.directive"],
            event_type="security.breach.containment",
            event_data={"actions": ["containment_verification", "system_integrity_check", "threat_elimination"]}
        ))
    
    async def _execute_breach_response(self):
        """Execute the breach response steps with timing coordination"""
        if not self.active_breach or not self.breach_steps:
            return
        
        self.logger.info("executing_breach_response_steps", step_count=len(self.breach_steps))
        
        # Publish breach initiation event
        await self._publish_breach_event("security_breach_initiated", {
            "breach_id": self.active_breach.event_id,
            "location": self.active_breach.location,
            "breach_type": self.active_breach.breach_type,
            "severity": self.active_breach.severity,
            "user_id": self.active_breach.user_id,
            "deadline": self.completion_deadline.isoformat(),
            "steps_planned": len(self.breach_steps)
        })
        
        # Execute steps with proper timing
        for step in self.breach_steps:
            if datetime.now(timezone.utc) >= self.completion_deadline:
                self.logger.error("breach_response_deadline_exceeded")
                break
            
            await self._execute_breach_step(step)
        
        # Evaluate breach resolution
        await self._evaluate_breach_completion()
    
    async def _execute_breach_step(self, step: ScenarioStepRuntime):
        """Execute a single breach response step"""
        self.logger.info("executing_step", step_id=step.step_id, description=step.description)
        
        # Wait for step start time if needed
        current_time = datetime.now(timezone.utc)
        if current_time < step.start_time:
            wait_time = (step.start_time - current_time).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # Trigger appropriate events based on step
        await self._trigger_step_events(step)
        
        # Execute security actions
        await self._execute_security_actions(step)
        
        # Wait for agent responses with timeout
        step_deadline = step.start_time + timedelta(seconds=step.timeout_seconds)
        await self._wait_for_step_responses(step, step_deadline)
        
        # Mark step as completed
        step.completed = True
        step.success = len(step.agent_responses) >= len(step.required_agents) * 0.8  # 80% success rate
        
        self.logger.info(
            "step_completed",
            step_id=step.step_id,
            success=step.success,
            response_count=len(step.agent_responses),
            required_count=len(step.required_agents)
        )
    
    async def _trigger_step_events(self, step: ScenarioStepRuntime):
        """Trigger appropriate events for a breach step"""
        if not self.active_breach:
            return
        
        base_event_data = {
            "breach_id": self.active_breach.event_id,
            "step_id": step.step_id,
            "location": self.active_breach.location,
            "breach_type": self.active_breach.breach_type,
            "user_id": self.active_breach.user_id,
            "emergency": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Trigger events based on step type
        if step.step_id == "security_assessment":
            await self.event_bus.publish("security.access.suspicious", json.dumps({
                **base_event_data,
                "attempts": self.active_breach.access_attempts,
                "suspicious_activity": True,
                "threat_level": "high"
            }))
        
        elif step.step_id == "network_analysis":
            await self.event_bus.publish("facility.network.event", json.dumps({
                **base_event_data,
                "event_type": "security_breach",
                "segment": "all",
                "anomaly_detected": True,
                "security_scan_required": True
            }))
        
        elif step.step_id == "lockdown_initiation":
            await self.event_bus.publish("security.lockdown.initiated", json.dumps({
                **base_event_data,
                "scope": "facility_wide",
                "duration": "indefinite",
                "reason": "security_breach_confirmed"
            }))
        
        elif step.step_id == "coordination_response":
            await self.event_bus.publish("facility.coordination.scenario", json.dumps({
                **base_event_data,
                "scenario_type": "security_breach",
                "emergency_level": "high",
                "agent_responses": dict(self.agent_responses)
            }))
        
        elif step.step_id == "containment_verification":
            await self.event_bus.publish("security.breach.containment", json.dumps({
                **base_event_data,
                "verification_required": True,
                "system_integrity_check": True
            }))
    
    async def _execute_security_actions(self, step: ScenarioStepRuntime):
        """Execute security actions for a breach step"""
        if not self.active_breach:
            return
        
        actions = step.event_data.get("actions", [])
        for action in actions:
            action_record = {
                "action": action,
                "step_id": step.step_id,
                "timestamp": datetime.now(timezone.utc),
                "breach_id": self.active_breach.event_id,
                "location": self.active_breach.location,
                "status": "initiated"
            }
            
            # Simulate action execution
            if action == "camera_surveillance":
                action_record["status"] = "completed"
                action_record["details"] = "Camera surveillance activated for breach location"
                self.logger.info("camera_surveillance_activated", location=self.active_breach.location)
            
            elif action == "access_control_check":
                action_record["status"] = "completed"
                action_record["details"] = "Access control systems verified and restricted"
                self.logger.info("access_control_restricted", location=self.active_breach.location)
            
            elif action == "traffic_analysis":
                action_record["status"] = "completed"
                action_record["details"] = "Network traffic analysis initiated"
                self.logger.info("network_traffic_analysis_initiated")
            
            elif action == "security_scan":
                action_record["status"] = "completed"
                action_record["details"] = "Deep security scan completed"
                self.logger.info("security_scan_completed")
            
            elif action == "door_lockdown":
                action_record["status"] = "completed"
                action_record["details"] = "All facility doors locked down"
                self.logger.info("facility_door_lockdown_initiated")
                self.metrics["lockdown_initiated"] += 1
            
            elif action == "network_isolation":
                action_record["status"] = "completed"
                action_record["details"] = "Network isolation protocols activated"
                self.logger.info("network_isolation_activated")
                self.metrics["network_isolations"] += 1
            
            elif action == "access_revocation":
                action_record["status"] = "completed"
                action_record["details"] = "All access credentials revoked"
                self.logger.info("access_credentials_revoked")
            
            elif action == "emergency_protocol_activation":
                action_record["status"] = "completed"
                action_record["details"] = "Emergency protocols activated"
                self.logger.info("emergency_protocols_activated")
            
            elif action == "resource_allocation":
                action_record["status"] = "completed"
                action_record["details"] = "Security resources allocated"
                self.logger.info("security_resources_allocated")
            
            elif action == "containment_verification":
                action_record["status"] = "completed"
                action_record["details"] = "Breach containment verified"
                self.logger.info("breach_containment_verified")
            
            elif action == "system_integrity_check":
                action_record["status"] = "completed"
                action_record["details"] = "System integrity check completed"
                self.logger.info("system_integrity_check_completed")
            
            elif action == "threat_elimination":
                action_record["status"] = "completed"
                action_record["details"] = "Threat elimination procedures completed"
                self.logger.info("threat_elimination_completed")
            
            self.security_actions_taken.append(action_record)
    
    async def _wait_for_step_responses(self, step: ScenarioStepRuntime, deadline: datetime):
        """Wait for agent responses to a breach step"""
        while datetime.now(timezone.utc) < deadline and len(step.agent_responses) < len(step.required_agents):
            # Check for new responses
            for agent_type in step.required_agents:
                agent_key = str(agent_type)
                if agent_key in self.agent_responses:
                    # Find responses that occurred after step start
                    recent_responses = [
                        resp for resp in self.agent_responses[agent_key]
                        if resp.get("timestamp", 0) >= step.start_time.timestamp() and
                        agent_key not in step.agent_responses
                    ]
                    
                    if recent_responses:
                        step.agent_responses[agent_key] = recent_responses[-1]  # Latest response
            
            await asyncio.sleep(0.1)  # Short polling interval
    
    async def _handle_agent_response(self, message: str):
        """Handle agent responses during breach"""
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
                "breach_active": self.active_breach is not None,
                "data": data
            })
            
            self.logger.debug("agent_response_received", agent_type=agent_type)
            
        except Exception as e:
            self.logger.error("error_handling_agent_response", error=str(e))
    
    async def _monitor_breach_progress(self, access_data: Dict[str, Any], location: str, user_id: str, attempts: int):
        """Monitor ongoing breach progress"""
        if not self.active_breach:
            return
        
        # Update breach data
        self.active_breach.location = location
        self.active_breach.user_id = user_id
        self.active_breach.access_attempts = attempts
        
        # Check if breach is escalating
        if attempts >= CRITICAL_THRESHOLD:
            self.active_breach.severity = EventSeverity.CRITICAL
            self.logger.warning("breach_severity_escalated", location=location, severity="CRITICAL")
    
    async def _evaluate_breach_completion(self):
        """Evaluate breach completion and update metrics"""
        if not self.active_breach or not self.start_time:
            return
        
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.active_breach.timestamp).total_seconds()
        
        # Calculate success metrics
        completed_steps = sum(1 for step in self.breach_steps if step.completed)
        successful_steps = sum(1 for step in self.breach_steps if step.success)
        
        success = (
            total_duration <= LOCKDOWN_DURATION_SECONDS and  # Within 90-second constraint
            completed_steps >= len(self.breach_steps) * 0.8 and  # 80% steps completed
            successful_steps >= len(self.breach_steps) * 0.6 and  # 60% steps successful
            len(self.agent_responses) >= 3 and  # All 3 agents responded
            self.metrics["lockdown_initiated"] > 0 and  # Lockdown was initiated
            self.metrics["network_isolations"] > 0  # Network isolation was performed
        )
        
        # Update metrics
        self.metrics["total_breaches_handled"] += 1
        if success:
            self.metrics["successful_resolutions"] += 1
        
        # Update average response time
        old_avg = self.metrics["average_response_time"]
        count = self.metrics["total_breaches_handled"]
        self.metrics["average_response_time"] = (old_avg * (count - 1) + total_duration) / count
        
        # Update coordination success rate
        coordination_success = len(self.agent_responses) / 3  # 3 required agents
        self.metrics["coordination_success_rate"] = (
            self.metrics["coordination_success_rate"] * (count - 1) + coordination_success
        ) / count
        
        # Publish completion event
        await self._publish_breach_event("security_breach_completed", {
            "breach_id": self.active_breach.event_id,
            "success": success,
            "duration_seconds": total_duration,
            "completed_steps": completed_steps,
            "successful_steps": successful_steps,
            "total_steps": len(self.breach_steps),
            "agents_responded": len(self.agent_responses),
            "security_actions": len(self.security_actions_taken),
            "lockdown_initiated": self.metrics["lockdown_initiated"],
            "network_isolations": self.metrics["network_isolations"],
            "final_location": self.active_breach.location,
            "final_severity": self.active_breach.severity
        })
        
        # Reset breach state
        self.logger.info(
            "breach_completed",
            breach_id=self.active_breach.event_id,
            success=success,
            duration_seconds=total_duration,
            successful_steps=successful_steps,
            total_steps=len(self.breach_steps)
        )
        
        # Reset breach state
        await self._reset_breach_state()
    
    async def _reset_breach_state(self):
        """Reset breach state for next scenario"""
        self.active_breach = None
        self.breach_steps.clear()
        self.start_time = None
        self.completion_deadline = None
        self.agent_responses.clear()
        self.coordination_events.clear()
        self.security_actions_taken.clear()
    
    async def _publish_breach_event(self, event_type: str, data: Dict[str, Any]):
        """Publish breach-related events to the event bus"""
        await self.event_bus.publish(f"security_breach.{event_type}", json.dumps({
            **data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario_type": ScenarioType.SECURITY_BREACH
        }))
    
    def get_breach_status(self) -> Dict[str, Any]:
        """Get current breach status"""
        if not self.active_breach:
            return {
                "active": False,
                "status": "idle",
                "metrics": self.metrics
            }
        
        current_time = datetime.now(timezone.utc)
        elapsed_time = (current_time - self.active_breach.timestamp).total_seconds()
        remaining_time = max(0, LOCKDOWN_DURATION_SECONDS - elapsed_time)
        
        return {
            "active": True,
            "breach_id": self.active_breach.event_id,
            "status": "active",
            "location": self.active_breach.location,
            "breach_type": self.active_breach.breach_type,
            "severity": self.active_breach.severity,
            "user_id": self.active_breach.user_id,
            "access_attempts": self.active_breach.access_attempts,
            "elapsed_seconds": elapsed_time,
            "remaining_seconds": remaining_time,
            "completion_percentage": min(100, (elapsed_time / LOCKDOWN_DURATION_SECONDS) * 100),
            "steps_completed": sum(1 for step in self.breach_steps if step.completed),
            "total_steps": len(self.breach_steps),
            "agents_responded": len(self.agent_responses),
            "coordination_events": len(self.coordination_events),
            "security_actions": len(self.security_actions_taken),
            "metrics": self.metrics
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for security breach scenarios"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_resolutions"] / max(self.metrics["total_breaches_handled"], 1) * 100
            ),
            "current_breach_active": self.active_breach is not None,
            "avg_actions_per_breach": (
                len(self.security_actions_taken) / max(self.metrics["total_breaches_handled"], 1)
            )
        }
    
    async def trigger_test_breach(self, location: str = "test_server_room", severity: str = "medium") -> bool:
        """Trigger a test security breach for demonstration purposes"""
        try:
            test_data = {
                "location": location,
                "user_id": "test_user_001",
                "attempts": SUSPICIOUS_THRESHOLD,
                "severity": severity,
                "timestamp": time.time(),
                "test_scenario": True
            }
            
            await self._handle_suspicious_access(json.dumps(test_data))
            return True
            
        except Exception as e:
            self.logger.error("error_triggering_test_breach", error=str(e))
            return False
    
    async def integrate_with_orchestrator(self) -> bool:
        """Integrate security breach with the scenario orchestrator"""
        try:
            # Check if orchestrator has security breach scenario
            if ScenarioType.SECURITY_BREACH in self.orchestrator.scenario_definitions:
                self.logger.info("orchestrator_integration_found", scenario=ScenarioType.SECURITY_BREACH)
                
                # Subscribe to orchestrator events
                self.event_bus.subscribe(
                    "demo.scenario.start",
                    self._handle_orchestrator_event
                )
                
                return True
            else:
                self.logger.warning("orchestrator_integration_not_found", scenario=ScenarioType.SECURITY_BREACH)
                return False
                
        except Exception as e:
            self.logger.error("orchestrator_integration_error", error=str(e))
            return False
    
    async def _handle_orchestrator_event(self, message: str):
        """Handle events from the scenario orchestrator"""
        try:
            data = json.loads(message) if isinstance(message, str) else message
            
            if data.get("scenario") == "security_breach":
                self.logger.info("orchestrator_scenario_detected", scenario="security_breach")
                
                # Trigger our security breach implementation
                await self.trigger_test_breach("server_room_a", "high")
                
        except Exception as e:
            self.logger.error("orchestrator_event_handler_error", error=str(e))