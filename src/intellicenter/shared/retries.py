"""
Resilience utilities for IntelliCenter agents.

Features:
- Exponential backoff with jitter
- Retry on specific exceptions only
- Circuit breaker pattern
- Reflexion (self-correction) loop skeleton
"""

from __future__ import annotations

from typing import Any, Callable, ParamSpec, TypeVar

import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from intellicenter.shared.exceptions import (
    LLMTimeoutError,
    RateLimitError,
    ValidationFailure,
)

logger = structlog.get_logger("intellicenter.resilience")

P = ParamSpec("P")
R = TypeVar("R")


# ============================================
# Retry Decorators
# ============================================


def retry_on_transient_error(
    max_attempts: int = 3,
    min_wait: float = 4.0,
    max_wait: float = 60.0,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Retry decorator for transient errors (rate limits, timeouts).

    Uses exponential backoff with jitter to avoid thundering herd.

    Args:
        max_attempts: Maximum retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Decorated function
    """
    return retry(
        retry=retry_if_exception_type((RateLimitError, LLMTimeoutError)),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=min_wait, max=max_wait, jitter=2),
        before_sleep=lambda retry_state: logger.warning(
            "retrying_after_transient_error",
            attempt=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception())
            if retry_state.outcome
            else None,
        ),
        reraise=True,
    )


def retry_on_validation_error(
    max_attempts: int = 3,
    min_wait: float = 2.0,
    max_wait: float = 10.0,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Retry decorator specifically for validation failures.

    Used when LLM output doesn't match expected schema.

    Args:
        max_attempts: Maximum retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Decorated function
    """
    return retry(
        retry=retry_if_exception_type(ValidationFailure),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=min_wait, max=max_wait),
        before_sleep=lambda retry_state: logger.warning(
            "retrying_after_validation_error",
            attempt=retry_state.attempt_number,
            exception=str(retry_state.outcome.exception())
            if retry_state.outcome
            else None,
        ),
        reraise=True,
    )


# ============================================
# Reflexion Pattern (Self-Correction)
# ============================================


class ReflexionLoop:
    """
    Implements the Reflexion pattern for LLM self-correction.

    When the LLM produces invalid output, the error is fed back
    as additional context, allowing the model to self-correct.

    Example:
        reflexion = ReflexionLoop(max_iterations=3)

        async def generate():
            output = await llm.generate(prompt)
            validate_output(output)  # raises ValidationFailure on error
            return output

        result = await reflexion.run(generate, error_context_builder=build_context)
    """

    def __init__(
        self,
        max_iterations: int = 3,
        error_context_builder: Callable[[Exception], str] | None = None,
    ) -> None:
        """
        Initialize the Reflexion loop.

        Args:
            max_iterations: Maximum correction attempts
            error_context_builder: Function to build error context string
        """
        self.max_iterations = max_iterations
        self.error_context_builder = error_context_builder or self._default_error_context
        self.error_history: list[str] = []

    @staticmethod
    def _default_error_context(error: Exception) -> str:
        """Build default error context string."""
        return f"Previous attempt failed with error: {type(error).__name__}: {error}"

    def get_error_history(self) -> list[str]:
        """Get the history of errors encountered during reflection."""
        return self.error_history.copy()

    async def run(
        self,
        coroutine_factory: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Run the coroutine with self-correction on failures.

        Args:
            coroutine_factory: Async function to execute
            *args: Positional arguments for the coroutine
            **kwargs: Keyword arguments for the coroutine

        Returns:
            Result from successful execution

        Raises:
            ValidationFailure: If all correction attempts fail
        """
        self.error_history = []
        last_error: Exception | None = None

        for iteration in range(self.max_iterations):
            try:
                # Inject error context if we have prior failures
                if self.error_history:
                    kwargs["_reflexion_context"] = "\n".join(self.error_history)

                result = await coroutine_factory(*args, **kwargs)

                if self.error_history:
                    logger.info(
                        "reflexion_succeeded",
                        iteration=iteration + 1,
                        corrections_made=len(self.error_history),
                    )

                return result

            except ValidationFailure as e:
                last_error = e
                error_context = self.error_context_builder(e)
                self.error_history.append(error_context)

                logger.warning(
                    "reflexion_iteration_failed",
                    iteration=iteration + 1,
                    max_iterations=self.max_iterations,
                    error=str(e),
                )

        # All iterations failed
        logger.error(
            "reflexion_exhausted",
            max_iterations=self.max_iterations,
            total_errors=len(self.error_history),
        )

        raise ValidationFailure(
            f"Reflexion failed after {self.max_iterations} attempts. "
            f"Last error: {last_error}"
        )


# ============================================
# Circuit Breaker (Skeleton)
# ============================================


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failures exceeded threshold, requests blocked
    - HALF_OPEN: Testing if service recovered

    TODO: Full implementation with async state management
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        """
        Initialize the circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        # TODO: Implement full async state machine

    def record_success(self) -> None:
        """Record a successful operation."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                "circuit_breaker_opened",
                failure_count=self.failure_count,
                threshold=self.failure_threshold,
            )

    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self.state == "OPEN"
