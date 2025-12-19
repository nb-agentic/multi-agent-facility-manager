"""
IntelliCenter Shared Kernel.

This module provides common utilities shared across all agents:
- Structured logging (logger)
- Pydantic data contracts (schema)
- Resilience utilities (retries)
- Custom exceptions (exceptions)
"""

from intellicenter.shared.exceptions import (
    AgentInitializationError,
    ConfigurationError,
    FatalError,
    IntelliCenterError,
    LLMTimeoutError,
    RateLimitError,
    SchemaValidationError,
    StateCorruptionError,
    TransientError,
    ValidationFailure,
)
from intellicenter.shared.logger import (
    bind_request_context,
    clear_request_context,
    get_logger,
    log_token_usage,
    logger,
)
from intellicenter.shared.retries import (
    CircuitBreaker,
    ReflexionLoop,
    retry_on_transient_error,
    retry_on_validation_error,
)
from intellicenter.shared.schema import (
    AgentDecision,
    AgentMetrics,
    AgentState,
    AgentStatus,
    AgentType,
    EventPriority,
    FacilityEvent,
    LLMTokenUsage,
    ScenarioConfig,
    ScenarioResult,
    ScenarioState,
    ScenarioStep,
    ScenarioType,
)

__all__ = [
    # Exceptions
    "IntelliCenterError",
    "TransientError",
    "RateLimitError",
    "LLMTimeoutError",
    "ValidationFailure",
    "SchemaValidationError",
    "FatalError",
    "ConfigurationError",
    "AgentInitializationError",
    "StateCorruptionError",
    # Logging
    "logger",
    "get_logger",
    "bind_request_context",
    "clear_request_context",
    "log_token_usage",
    # Retries
    "retry_on_transient_error",
    "retry_on_validation_error",
    "ReflexionLoop",
    "CircuitBreaker",
    # Schema
    "AgentStatus",
    "AgentType",
    "AgentMetrics",
    "AgentState",
    "EventPriority",
    "FacilityEvent",
    "LLMTokenUsage",
    "AgentDecision",
    "ScenarioState",
    "ScenarioType",
    "ScenarioStep",
    "ScenarioConfig",
    "ScenarioResult",
]
