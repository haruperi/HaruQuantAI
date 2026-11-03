"""Time formatting, constants, and temporal bucket models matching donor SQTime.

Description:
    Provides canonical time formatting functions and temporal period representations
    matching StrategyQuant SQTime and TimePeriod runtime behavior. Formats elapsed
    durations into day, hour, minute, and second representations and provides
    standard millisecond duration constants.

Purpose:
    FEAT-CORE-LIB-TIME: Provide verified shared runtime time utilities and models.

Key Capabilities:
    - FR-core-lib-format-duration: Format elapsed duration seconds into canonical
      time representation strings.
    - FR-core-lib-time-period: Temporal range bucket with bounds, metric values,
      and cloning semantics.

Python API Usage:
    ```python
    from app.core.lib.time import DAY_MILLIS, TimePeriod, format_duration_seconds

    formatted = format_duration_seconds(125)  # "2m 5s"
    period = TimePeriod(from_ms=0, to_ms=DAY_MILLIS, value=1.5)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/core/lib/test_time.py -q
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.core.host.logging import get_logger

logger = get_logger(__name__)

DAY_MILLIS: Final[int] = 86_400_000
HOUR_MILLIS: Final[int] = 3_600_000
MINUTE_MILLIS: Final[int] = 60_000
SECOND_MILLIS: Final[int] = 1_000

__all__ = [
    "DAY_MILLIS",
    "HOUR_MILLIS",
    "MINUTE_MILLIS",
    "SECOND_MILLIS",
    "TimePeriod",
    "format_duration_seconds",
]


@dataclass(slots=True)
class TimePeriod:
    """Represents a temporal period bucket with temporal bounds and metric value."""

    from_ms: int
    to_ms: int
    value: float = 0.0
    name: str = ""
    note: str = ""

    def clone(self) -> TimePeriod:
        """Create an independent clone of this time period.

        Returns:
            New TimePeriod instance with identical values.
        """
        return TimePeriod(
            from_ms=self.from_ms,
            to_ms=self.to_ms,
            value=self.value,
            name=self.name,
            note=self.note,
        )


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
