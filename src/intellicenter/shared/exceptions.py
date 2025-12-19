"""
Custom exceptions for IntelliCenter.

Provides a clear hierarchy for error handling and retry logic.
"""

from __future__ import annotations


class IntelliCenterError(Exception):
    """Base exception for all IntelliCenter errors."""

    pass


# ============================================
# Transient Errors (Retryable)
# ============================================


class TransientError(IntelliCenterError):
    """Base for transient, retryable errors."""

    pass


class RateLimitError(TransientError):
    """LLM API rate limit exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: float | None = None
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class LLMTimeoutError(TransientError):
    """LLM request timed out."""

    pass


# ============================================
# Validation Errors (Potentially Retryable via Reflexion)
# ============================================


class ValidationFailure(IntelliCenterError):
    """
    LLM output failed validation.

    This error triggers the Reflexion pattern for self-correction.
    """

    def __init__(
        self, message: str, validation_errors: list[str] | None = None
    ) -> None:
        super().__init__(message)
        self.validation_errors = validation_errors or []


class SchemaValidationError(ValidationFailure):
    """Output did not match expected Pydantic schema."""

    pass


# ============================================
# Fatal Errors (Non-Retryable)
# ============================================


class FatalError(IntelliCenterError):
    """Base for fatal, non-retryable errors."""

    pass


class ConfigurationError(FatalError):
    """Invalid system configuration."""

    pass


class AgentInitializationError(FatalError):
    """Failed to initialize an agent."""

    pass


class StateCorruptionError(FatalError):
    """Agent state is corrupted and unrecoverable."""

    pass
