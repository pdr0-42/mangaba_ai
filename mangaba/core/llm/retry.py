"""
Retry logic with exponential back-off for LLM calls.
"""

from __future__ import annotations

import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Set, Type, TypeVar

from mangaba.core.exceptions import RetryableError, RateLimitError, LLMError
from mangaba.core.events import EventBus, Event, EventType

log = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Any])

_DEFAULT_RETRYABLE: Set[Type[Exception]] = {RetryableError, RateLimitError, ConnectionError, TimeoutError}


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Optional[Set[Type[Exception]]] = None,
) -> Callable[[F], F]:
    """Decorator that retries a function on transient errors.

    Uses exponential back-off with optional jitter to avoid thundering herd
    problems. Emits LLM_RETRY events to the EventBus on each retry attempt.

    Args:
        max_retries: Maximum number of retry attempts (0 = no retries, default: 3).
        backoff_factor: Multiplicative back-off factor between retries (default: 2.0).
        max_delay: Upper bound on delay in seconds (default: 60.0).
        jitter: Add random jitter to delay to avoid thundering herd (default: True).
        retryable_exceptions: Set of exception types that trigger a retry.
            Defaults to RetryableError, RateLimitError, ConnectionError, TimeoutError.

    Returns:
        A decorator function that wraps the target function with retry logic.

    Raises:
        LLMError: If all retry attempts are exhausted.
    """
    exceptions = retryable_exceptions or _DEFAULT_RETRYABLE

    def decorator(fn: F) -> F:
        """Decorator that applies retry logic to the function.

        Args:
            fn: The function to wrap with retry logic.

        Returns:
            The wrapped function with retry logic applied.
        """
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function that implements the retry logic.

            Args:
                *args: Positional arguments to pass to the wrapped function.
                **kwargs: Keyword arguments to pass to the wrapped function.

            Returns:
                The return value of the wrapped function on success.

            Raises:
                LLMError: If all retry attempts are exhausted.
            """
            last_exc: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except tuple(exceptions) as exc:
                    last_exc = exc
                    if attempt >= max_retries:
                        break

                    # Compute delay
                    delay = min(backoff_factor ** attempt, max_delay)
                    if isinstance(exc, RateLimitError) and exc.retry_after:
                        delay = max(delay, exc.retry_after)
                    if jitter:
                        delay *= 0.5 + random.random()

                    EventBus.emit(Event(
                        event_type=EventType.LLM_RETRY,
                        data={"attempt": attempt + 1, "max_retries": max_retries, "delay": round(delay, 2), "error": str(exc)},
                    ))
                    log.warning("Retry %d/%d after %.1fs – %s", attempt + 1, max_retries, delay, exc)
                    time.sleep(delay)

            raise LLMError(
                f"Failed after {max_retries} retries: {last_exc}",
                cause=last_exc,
            )

        return wrapper  # type: ignore[return-value]

    return decorator
