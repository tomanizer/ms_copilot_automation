"""Retry utilities for handling transient failures.

This module provides decorators and utilities for automatically retrying
operations that may fail due to transient errors like network issues,
UI timing problems, or temporary service unavailability.
"""

import asyncio
from collections.abc import Callable
from functools import wraps
from typing import Any

from .logger import get_logger

logger = get_logger(__name__)



async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    delay_ms: int = 1000,
    exponential_backoff: bool = True,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    **kwargs: Any,
) -> Any:
    """Retry an async function with configurable backoff.

    :param func: The async function to retry
    :type func: Callable
    :param args: Positional arguments for the function
    :param max_retries: Maximum number of retry attempts
    :type max_retries: int
    :param delay_ms: Initial delay between retries in milliseconds
    :type delay_ms: int
    :param exponential_backoff: Whether to use exponential backoff
    :type exponential_backoff: bool
    :param retry_on: Tuple of exception types to retry on
    :type retry_on: tuple[type[Exception], ...]
    :param kwargs: Keyword arguments for the function
    :returns: Result from the function
    :raises: The last exception if all retries fail

    Example:
        >>> result = await retry_async(
        ...     page.click,
        ...     "button",
        ...     max_retries=3,
        ...     retry_on=(TimeoutError,)
        ... )
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except retry_on as exc:
            last_exception = exc
            if attempt == max_retries - 1:
                logger.warning(
                    "All %d retry attempts failed for %s",
                    max_retries,
                    func.__name__,
                )
                raise

            # Calculate delay with optional exponential backoff
            current_delay = delay_ms
            if exponential_backoff:
                current_delay = delay_ms * (2**attempt)

            logger.debug(
                "Retry %d/%d for %s after %dms (error: %s)",
                attempt + 1,
                max_retries,
                func.__name__,
                current_delay,
                type(exc).__name__,
            )

            await asyncio.sleep(current_delay / 1000)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError(f"Retry logic failed for {func.__name__}")


def retry_on_exception(
    max_retries: int = 3,
    delay_ms: int = 1000,
    exponential_backoff: bool = True,
    retry_on: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to automatically retry async functions.

    :param max_retries: Maximum number of retry attempts
    :type max_retries: int
    :param delay_ms: Initial delay between retries in milliseconds
    :type delay_ms: int
    :param exponential_backoff: Whether to use exponential backoff
    :type exponential_backoff: bool
    :param retry_on: Tuple of exception types to retry on
    :type retry_on: tuple[type[Exception], ...]
    :returns: Decorated function with retry logic
    :rtype: Callable

    Example:
        >>> @retry_on_exception(
        ...     max_retries=3,
        ...     retry_on=(UIInteractionError,)
        ... )
        ... async def click_button(page, selector):
        ...     await page.click(selector)
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await retry_async(
                func,
                *args,
                max_retries=max_retries,
                delay_ms=delay_ms,
                exponential_backoff=exponential_backoff,
                retry_on=retry_on,
                **kwargs,
            )

        return wrapper

    return decorator


async def wait_for_condition(
    condition: Callable[[], bool],
    timeout_ms: int = 10000,
    poll_interval_ms: int = 500,
    error_message: str = "Condition not met within timeout",
) -> None:
    """Wait for a condition to become true.

    :param condition: Function that returns True when condition is met
    :type condition: Callable[[], bool]
    :param timeout_ms: Maximum time to wait in milliseconds
    :type timeout_ms: int
    :param poll_interval_ms: Time between checks in milliseconds
    :type poll_interval_ms: int
    :param error_message: Error message if timeout occurs
    :type error_message: str
    :raises TimeoutError: If condition not met within timeout

    Example:
        >>> await wait_for_condition(
        ...     lambda: element.is_visible(),
        ...     timeout_ms=5000,
        ...     error_message="Element not visible"
        ... )
    """
    elapsed = 0
    while elapsed < timeout_ms:
        if await condition() if asyncio.iscoroutinefunction(condition) else condition():
            return
        await asyncio.sleep(poll_interval_ms / 1000)
        elapsed += poll_interval_ms

    raise TimeoutError(f"{error_message} (timeout: {timeout_ms}ms)")
