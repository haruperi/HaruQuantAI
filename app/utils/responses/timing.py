"""Monotonic execution-duration calculation for standard responses."""

from __future__ import annotations

import time
from collections.abc import Callable


def get_execution_ms(
    start_time: int,
    *,
    clock: Callable[[], int] = time.perf_counter_ns,
) -> float:
    """Calculate monotonic elapsed milliseconds rounded to three decimals.

    Args:
        start_time: Starting value previously read from ``time.perf_counter_ns``.
        clock: Injectable monotonic nanosecond clock used for deterministic tests.

    Returns:
        Non-negative elapsed milliseconds rounded to three decimal places.

    Raises:
        TypeError: If the starting clock value is not an integer.
        ValueError: If the starting value is negative or after the ending value.
    """
    if isinstance(start_time, bool) or not isinstance(start_time, int):
        raise TypeError("start_time must be a monotonic nanosecond integer")
    if start_time < 0:
        raise ValueError("start_time must be non-negative")
    end_time = clock()
    if isinstance(end_time, bool) or not isinstance(end_time, int):
        raise TypeError("clock must return a monotonic nanosecond integer")
    if end_time < start_time:
        raise ValueError("start_time cannot be after the monotonic clock")
    return round((end_time - start_time) / 1_000_000, 3)


__all__ = ["get_execution_ms"]
