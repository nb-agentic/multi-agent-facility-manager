"""
Professional structured logging configuration for IntelliCenter.

Features:
- JSON output in production, colored text in development
- contextvars for request_id and agent_id correlation
- Token usage metrics capture
- OpenTelemetry-compatible span contexts
"""

from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from structlog.types import Processor


# ============================================
# Context Variables for Distributed Tracing
# ============================================

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
agent_id_var: ContextVar[str | None] = ContextVar("agent_id", default=None)
agent_type_var: ContextVar[str | None] = ContextVar("agent_type", default=None)


def bind_request_context(
    request_id: str,
    agent_id: str | None = None,
    agent_type: str | None = None,
) -> None:
    """Bind request context for the current async task."""
    request_id_var.set(request_id)
    if agent_id:
        agent_id_var.set(agent_id)
    if agent_type:
        agent_type_var.set(agent_type)

    # Also bind to structlog's context
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        agent_id=agent_id,
        agent_type=agent_type,
    )


def clear_request_context() -> None:
    """Clear the current request context."""
    request_id_var.set(None)
    agent_id_var.set(None)
    agent_type_var.set(None)
    structlog.contextvars.clear_contextvars()


# ============================================
# Token Usage Logging
# ============================================


def log_token_usage(
    model: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost: float | None = None,
    **extra: Any,
) -> None:
    """
    Log LLM token usage metrics.

    Args:
        model: The LLM model name (e.g., "gpt-4o", "mistral-nemo")
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
        estimated_cost: Estimated cost in USD (optional)
        **extra: Additional context to log
    """
    token_logger = structlog.get_logger("intellicenter.llm.tokens")
    token_logger.info(
        "llm_token_usage",
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        estimated_cost_usd=estimated_cost,
        **extra,
    )


# ============================================
# Custom JSON Serializer for datetime support
# ============================================


def _json_serializer(obj: Any, default: Any) -> Any:
    """
    Custom JSON serializer for objects not natively serializable by json.dumps.
    
    Handles:
    - datetime objects -> ISO 8601 format string with UTC timezone
    - Other types -> falls back to default serializer
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    return default(obj)


# ============================================
# Logger Configuration
# ============================================


def _get_environment() -> str:
    """Determine the current environment."""
    return os.getenv("INTELLICENTER_ENV", "development").lower()


def _get_log_level() -> int:
    """Get the configured log level."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


def _get_shared_processors() -> list[Processor]:
    """Get processors shared between dev and prod."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]


def configure_logging() -> structlog.BoundLogger:
    """
    Configure structlog for IntelliCenter.

    Returns:
        Configured logger instance

    Environment Variables:
        - INTELLICENTER_ENV: "production" or "development" (default)
        - LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)
    """
    env = _get_environment()
    is_production = env == "production"

    shared_processors = _get_shared_processors()

    if is_production:
        # Production: JSON output for log aggregators
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(default=_json_serializer),
        ]
    else:
        # Development: Colored, human-readable output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.RichTracebackFormatter(
                    show_locals=True,
                    max_frames=10,
                ),
            ),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(_get_log_level()),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to route through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=_get_log_level(),
    )

    return structlog.get_logger("intellicenter")


# Initialize logger on module import
logger = configure_logging()


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """
    Get a logger instance with optional name.

    Args:
        name: Logger name (e.g., "intellicenter.agents.hvac")

    Returns:
        Bound structlog logger
    """
    if name:
        return structlog.get_logger(name)
    return structlog.get_logger("intellicenter")
