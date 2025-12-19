"""
Pydantic V2 data contracts for IntelliCenter.

These models replace dataclasses to provide:
- Strict runtime validation
- JSON schema generation for LLM structured outputs
- Immutability and type safety
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ============================================
# Agent State Models (Orchestrator-Worker)
# ============================================


class AgentStatus(StrEnum):
    """Agent operational status."""

    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


class AgentType(StrEnum):
    """Types of facility management agents."""

    COORDINATOR = "coordinator_agent"
    HVAC = "hvac_agent"
    POWER = "power_agent"
    SECURITY = "security_agent"
    NETWORK = "network_agent"


class AgentMetrics(BaseModel):
    """Performance metrics for an agent."""

    model_config = ConfigDict(strict=True, frozen=True)

    total_tasks: int = Field(default=0, ge=0, description="Total tasks processed")
    successful_tasks: int = Field(
        default=0, ge=0, description="Successfully completed tasks"
    )
    failed_tasks: int = Field(default=0, ge=0, description="Failed tasks")
    avg_response_time_ms: float = Field(
        default=0.0, ge=0, description="Average response time in milliseconds"
    )
    total_tokens_used: int = Field(
        default=0, ge=0, description="Cumulative LLM tokens consumed"
    )


class AgentState(BaseModel):
    """
    Centralized state passed between Orchestrator and Workers.

    This is the primary data contract for agent communication,
    ensuring type safety across async boundaries.
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",  # Prevent hallucinated fields from LLM
        validate_assignment=True,
    )

    # Identity
    agent_id: str = Field(..., min_length=1, description="Unique agent identifier")
    agent_type: AgentType = Field(..., description="Type of facility agent")

    # Status
    status: AgentStatus = Field(
        default=AgentStatus.IDLE, description="Current operational status"
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Last state update timestamp"
    )

    # State Data
    current_directive_id: str | None = Field(
        default=None, description="ID of the current directive being processed"
    )
    last_completed_task: str | None = Field(
        default=None, description="Last fully completed task"
    )
    state_data: dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific state data"
    )

    # Metrics
    metrics: AgentMetrics = Field(
        default_factory=AgentMetrics, description="Performance metrics"
    )

    # Versioning (for state consistency)
    version: int = Field(default=1, ge=1, description="State version for conflict resolution")
    checksum: str | None = Field(default=None, description="Integrity checksum")


# ============================================
# Event Priority & Severity (must be defined before usage)
# ============================================


class EventPriority(StrEnum):
    """Priority levels for facility events."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EventSeverity(StrEnum):
    """Severity levels for facility events."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


# ============================================
# Handoff & Communication Models
# ============================================

class AgentDirective(BaseModel):
    """A direct command or task sent from the coordinator to an agent."""
    model_config = ConfigDict(strict=True, frozen=True)
    
    request_id: str = Field(..., description="Unique request identifier for tracking")
    agent_type: AgentType = Field(..., description="Target agent type")
    directive: str = Field(..., description="High-level instruction for the agent")
    priority: EventPriority = Field(default=EventPriority.MEDIUM, description="Task priority")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context for the task")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Directive timestamp"
    )

class AgentResponse(BaseModel):
    """An agent's formal response to a directive or external event."""
    model_config = ConfigDict(strict=True, frozen=True)
    
    request_id: str = Field(..., description="Correlation ID matching the directive or event")
    agent_type: AgentType = Field(..., description="Responding agent type")
    status: str = Field(..., description="Response status (e.g., success, failure)")
    decision: dict[str, Any] = Field(..., description="Structured decision data")
    reasoning: str = Field(..., description="Detailed reasoning for the decision")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0 to 1")
    response_time_ms: float = Field(ge=0.0, description="Total processing time in milliseconds")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp"
    )


# ============================================
# Facility Event Models
# ============================================


class FacilityEvent(BaseModel):
    """Base model for facility events."""

    model_config = ConfigDict(strict=True, frozen=True)

    event_id: str = Field(..., min_length=1, description="Unique event identifier")
    event_type: str = Field(..., min_length=1, description="Type of facility event")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Event timestamp"
    )
    priority: EventPriority = Field(
        default=EventPriority.MEDIUM, description="Event priority"
    )
    severity: EventSeverity = Field(
        default=EventSeverity.INFO, description="Event severity level"
    )
    location: str = Field(..., description="Facility location")
    source_agent: AgentType | None = Field(
        default=None, description="Agent that generated the event"
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Event payload data"
    )


class CoolingCrisisEvent(FacilityEvent):
    """Event specifically for cooling crises."""

    temperature_fahrenheit: float
    temperature_celsius: float
    trend: str = "rising"
    rate_of_change: float = 0.0
    emergency: bool = True


class SecurityBreachEvent(FacilityEvent):
    """Event specifically for security breaches."""

    breach_type: str
    affected_zones: list[str]
    detected_by: str


class EnergyConsumptionEvent(FacilityEvent):
    """Event specifically for energy monitoring."""

    consumption_kw: float
    cost_per_kwh: float | None = None
    is_peak_hours: bool = False


# ============================================
# LLM Response Models
# ============================================


class LLMTokenUsage(BaseModel):
    """Token usage from an LLM call."""

    model_config = ConfigDict(strict=True, frozen=True)

    model: str = Field(..., description="LLM model name")
    input_tokens: int = Field(..., ge=0, strict=True, description="Input/prompt tokens")
    output_tokens: int = Field(
        ..., ge=0, strict=True, description="Output/completion tokens"
    )

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens


class AgentDecision(BaseModel):
    """Structured decision output from an agent."""

    model_config = ConfigDict(strict=True, extra="forbid")

    decision_id: str = Field(..., description="Unique decision identifier")
    agent_type: AgentType = Field(..., description="Agent making the decision")
    action: str = Field(..., min_length=1, description="Action to take")
    reasoning: str = Field(..., min_length=1, description="Reasoning behind the decision")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, strict=True, description="Confidence score (0-1)"
    )
    priority: EventPriority = Field(
        default=EventPriority.MEDIUM, description="Action priority"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )
    token_usage: LLMTokenUsage | None = Field(
        default=None, description="Token usage for this decision"
    )


# ============================================
# Scenario Models (Migrated from dataclasses)
# ============================================


class ScenarioState(StrEnum):
    """Scenario execution states."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RESETTING = "resetting"


class MaintenancePhase(StrEnum):
    """Routine maintenance execution phases."""

    DETECTION = "detection"
    HVAC_CHECK = "hvac_check"
    NETWORK_CHECK = "network_check"
    COMPLETION = "completion"


class ScenarioType(StrEnum):
    """Available demo scenario types."""

    COOLING_CRISIS = "cooling_crisis"
    SECURITY_BREACH = "security_breach"
    ENERGY_OPTIMIZATION = "energy_optimization"
    ROUTINE_MAINTENANCE = "routine_maintenance"


class ScenarioStep(BaseModel):
    """Defines a single step in a scenario execution."""

    model_config = ConfigDict(strict=True, frozen=True)

    step_id: str = Field(..., description="Unique step identifier")
    description: str = Field(..., description="Human-readable description")
    event_type: str = Field(..., description="Event type to trigger")
    event_data: dict[str, Any] = Field(default_factory=dict, description="Event payload")
    delay_seconds: float = Field(default=0.0, ge=0, description="Delay before step execution")
    timeout_seconds: float = Field(default=30.0, ge=0, description="Step timeout")
    expected_responses: list[str] = Field(
        default_factory=list, description="Expected response events"
    )
    required_agents: list[str] = Field(
        default_factory=list, description="Agents required for step"
    )


class ScenarioStepRuntime(ScenarioStep):
    """Runtime tracking for a scenario step (mutable)."""

    model_config = ConfigDict(strict=True, frozen=False)

    start_time: datetime | None = None
    end_time: datetime | None = None
    completed: bool = False
    success: bool = False
    agent_responses: dict[str, Any] = Field(default_factory=dict)


class ScenarioConfig(BaseModel):
    """Configuration for a demo scenario."""

    model_config = ConfigDict(strict=True)

    scenario_id: str = Field(..., description="Unique scenario identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Scenario description")
    scenario_type: ScenarioType = Field(..., description="Type of scenario")
    steps: list[ScenarioStep] = Field(default_factory=list, description="Execution steps")
    max_duration_seconds: float = Field(
        default=300.0, ge=0, description="Maximum execution time"
    )
    success_criteria: dict[str, Any] = Field(
        default_factory=dict, description="Success evaluation criteria"
    )
    cleanup_steps: list[ScenarioStep] = Field(
        default_factory=list, description="Cleanup steps"
    )


class ScenarioResult(BaseModel):
    """Results from scenario execution."""

    model_config = ConfigDict(strict=True)

    scenario_id: str = Field(..., description="Scenario identifier")
    scenario_type: ScenarioType = Field(..., description="Type of scenario")
    state: ScenarioState = Field(..., description="Final scenario state")
    start_time: datetime = Field(..., description="Execution start time")
    end_time: datetime | None = Field(default=None, description="Execution end time")
    duration_seconds: float = Field(default=0.0, ge=0, description="Total duration")
    steps_completed: int = Field(default=0, ge=0, description="Steps completed")
    steps_total: int = Field(default=0, ge=0, description="Total steps")
    success: bool = Field(default=False, description="Whether scenario succeeded")
    agent_responses: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict, description="Responses from each agent"
    )
    events: list[dict[str, Any]] = Field(
        default_factory=list, description="All events during execution"
    )
    error_message: str | None = Field(default=None, description="Error message if failed")
    performance_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Performance data"
    )
