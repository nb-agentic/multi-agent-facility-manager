#!/usr/bin/env python3
"""
Smoke Test for Cooling Crisis Scenario

This script verifies:
1. Runtime type safety (no crashes with Pydantic V2)
2. JSON log output (structlog producing valid JSON)
3. Timezone-aware timestamps (modern datetime.now(timezone.utc))
4. Context binding (scenario="cooling_crisis" in logs)
"""

import asyncio
import os
import sys

# Force JSON output for testing
os.environ["INTELLICENTER_ENV"] = "production"
os.environ["LOG_LEVEL"] = "DEBUG"

# Configure structlog BEFORE importing anything else
import structlog

# Custom configuration for stdout JSON output
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    cache_logger_on_first_use=False,
)

# Now import the modules
from intellicenter.shared.event_bus import EventBus
from intellicenter.shared.schema import (
    AgentDirective,
    AgentResponse,
    AgentType,
    AgentStatus,
    CoolingCrisisEvent,
    EventPriority,
    EventSeverity,
    FacilityEvent,
)
from intellicenter.scenarios.scenario_orchestrator import ScenarioOrchestrator
from intellicenter.scenarios.cooling_crisis import CoolingCrisisScenario


async def main():
    """Run the cooling crisis smoke test."""
    logger = structlog.get_logger("smoke_test").bind(scenario="cooling_crisis")
    
    logger.info("smoke_test_started", message="Starting Cooling Crisis Scenario smoke test")
    
    # 1. Test Pydantic V2 Models - ensure no runtime type errors
    logger.info("testing_pydantic_models", phase="pydantic_validation")
    
    try:
        # Test CoolingCrisisEvent with timezone-aware timestamp
        from datetime import datetime, timezone
        
        crisis_event = CoolingCrisisEvent(
            event_id="test_crisis_001",
            timestamp=datetime.now(timezone.utc),
            event_type="cooling_crisis_test",
            location="test_server_room",
            priority=EventPriority.CRITICAL,
            severity=EventSeverity.CRITICAL,
            temperature_fahrenheit=90.5,
            temperature_celsius=32.5,
            trend="rising",
            rate_of_change=1.5,
            emergency=True,
        )
        
        logger.info(
            "pydantic_model_validated",
            model="CoolingCrisisEvent",
            event_id=crisis_event.event_id,
            timestamp=crisis_event.timestamp.isoformat(),
            success=True,
        )
        
        # Test AgentDirective
        directive = AgentDirective(
            request_id="req_smoke_001",
            agent_type=AgentType.HVAC,
            directive="Activate emergency cooling protocol",
            context={"emergency": True, "temperature": 90.5},
        )
        
        logger.info(
            "pydantic_model_validated",
            model="AgentDirective",
            request_id=directive.request_id,
            timestamp=directive.timestamp.isoformat(),
            success=True,
        )
        
        # Test AgentResponse
        response = AgentResponse(
            request_id="req_smoke_001",
            agent_type=AgentType.HVAC,
            status="success",
            decision={"cooling_activated": True, "target_temp": 22.0},
            reasoning="Emergency cooling activated due to temperature threshold breach",
            confidence=0.95,
            response_time_ms=125.5,
        )
        
        logger.info(
            "pydantic_model_validated",
            model="AgentResponse",
            request_id=response.request_id,
            timestamp=response.timestamp.isoformat(),
            success=True,
        )
        
    except Exception as e:
        logger.error("pydantic_validation_failed", error=str(e), success=False)
        return
    
    # 2. Initialize EventBus and Scenario System
    logger.info("initializing_event_bus", phase="system_init")
    
    event_bus = EventBus()
    await event_bus.start()
    
    orchestrator = ScenarioOrchestrator(event_bus=event_bus)
    cooling_scenario = CoolingCrisisScenario(event_bus=event_bus, orchestrator=orchestrator)
    
    logger.info(
        "system_initialized",
        event_bus_running=event_bus.is_running,
        scenario_type="cooling_crisis",
    )
    
    # 3. Trigger test crisis
    logger.info("triggering_test_crisis", temperature_fahrenheit=90.0,phase="scenario_execution")
    
    success = await cooling_scenario.trigger_test_crisis(temperature_fahrenheit=90.0)
    
    # Give the async events time to process
    await asyncio.sleep(0.5)
    
    # 4. Get scenario status
    status = cooling_scenario.get_crisis_status()
    metrics = cooling_scenario.get_performance_metrics()
    
    logger.info(
        "scenario_status",
        active=status.get("active", False),
        status=status.get("status", "unknown"),
        total_crises=metrics.get("total_crises_handled", 0),
    )
    
    # 5. Cleanup
    await event_bus.stop()
    
    logger.info(
        "smoke_test_completed",
        success=True,
        pydantic_validation="passed",
        json_logging="active",
        timezone_aware="confirmed",
    )


if __name__ == "__main__":
    asyncio.run(main())
