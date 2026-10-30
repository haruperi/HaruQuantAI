"""Time formatting and conversion utilities.

Description:
    Provides canonical time formatting functions matching StrategyQuant runtime
    behavior. Formats elapsed durations into day, hour, minute, and second
    representations.

Purpose:
    FEAT-CORE-LIB: Provide verified shared runtime time utilities.

Key Capabilities:
    - FR-core-lib-format-duration: Format elapsed duration seconds into canonical
      time representation strings.

Python API Usage:
    ```python
    from app.core.lib.time import format_duration_seconds

    formatted = format_duration_seconds(125)  # "2m 5s"
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/core/lib/test_time.py -q
    ```
"""

from __future__ import annotations

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["format_duration_seconds"]


def format_duration_seconds(seconds: int) -> str:
    """Format elapsed seconds into canonical StrategyQuant duration notation.

    Branching rules:
        - If days > 0: returns '{days}d {hours}h {minutes}m'
        - Else if hours > 0: returns '{hours}h {minutes}m'
        - Else if minutes > 0: returns '{minutes}m {seconds}s'
        - Else: returns '{seconds}s'

    Args:
        seconds: Nonnegative integer elapsed seconds.

    Returns:
        Formatted duration string.
    """
    seconds = max(seconds, 0)

    days = seconds // 86400
    if days > 0:
        rem = seconds % 86400
        hours = rem // 3600
        minutes = (rem % 3600) // 60
        result = f"{days}d {hours}h {minutes}m"
    else:
        hours = seconds // 3600
        if hours > 0:
            minutes = (seconds % 3600) // 60
            result = f"{hours}h {minutes}m"
        else:
            minutes = seconds // 60
            if minutes > 0:
                secs = seconds % 60
                result = f"{minutes}m {secs}s"
            else:
                result = f"{seconds}s"

    logger.debug(
        "FR-core-lib-format-duration: formatted %d seconds as %r",
        seconds,
        result,
    )
    return result
