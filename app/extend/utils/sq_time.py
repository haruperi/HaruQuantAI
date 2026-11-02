"""StrategyQuant time calculation primitives and calendar utilities.

Description:
    Provides datetime and timestamp conversion utilities matching StrategyQuant
    SQTime library primitives, including millisecond timestamp truncation,
    calendar day difference, and Java-compatible calendar day-of-week mapping.

Purpose:
    FEAT-UTILS-SQTIME: StrategyQuant donor-faithful time utility primitives.

Key Capabilities:
    - FR-UTILS-DAY-DIFF: Calculate calendar days difference between timestamps.
    - FR-UTILS-DAY-START: Truncate millisecond timestamp to calendar day start.
    - FR-UTILS-DOW: Extract Java Calendar-compatible day of week (Sunday=1).

Python API Usage:
    from app.extend.utils.sq_time import SQTime
    days = SQTime.get_diff_in_days(t1, t2)

CLI Usage:
    uv run pytest tests/extend/test_utils.py --no-cov
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class SQTime:
    """StrategyQuant time manipulation and calendar conversion utility."""

    DAY_MILLIS: ClassVar[int] = 86_400_000

    @classmethod
    def get_diff_in_days(cls, time1_ms: int, time2_ms: int) -> int:
        """Return the absolute calendar days difference between two timestamps.

        Args:
            time1_ms: First timestamp in epoch milliseconds.
            time2_ms: Second timestamp in epoch milliseconds.

        Returns:
            Number of calendar days between the two dates.
        """
        d1 = datetime.fromtimestamp(time1_ms / 1000.0, tz=UTC).date()
        d2 = datetime.fromtimestamp(time2_ms / 1000.0, tz=UTC).date()
        diff = abs((d1 - d2).days)
        logger.debug("FR-UTILS-DAY-DIFF: calculated day diff %d", diff)
        return diff

    @classmethod
    def correct_day_start(cls, time_ms: int) -> int:
        """Truncate millisecond timestamp to 00:00:00.000 UTC of that calendar day.

        Args:
            time_ms: Timestamp in epoch milliseconds.

        Returns:
            Timestamp at start of day in milliseconds.
        """
        truncated = time_ms - (time_ms % cls.DAY_MILLIS)
        logger.debug("FR-UTILS-DAY-START: truncated %d to %d", time_ms, truncated)
        return truncated

    @classmethod
    def get_day_of_week_original(cls, time_ms: int) -> int:
        """Return Java Calendar-compatible day of week (Sunday=1..Saturday=7).

        Args:
            time_ms: Timestamp in epoch milliseconds.

        Returns:
            Day of week: Sunday=1, Monday=2, ..., Saturday=7.
        """
        dt = datetime.fromtimestamp(time_ms / 1000.0, tz=UTC)
        dow = (dt.weekday() + 1) % 7 + 1
        logger.debug("FR-UTILS-DOW: extracted day-of-week %d", dow)
        return dow

    @classmethod
    def get_year(cls, time_ms: int) -> int:
        """Return calendar year (UTC) for millisecond timestamp."""
        return datetime.fromtimestamp(time_ms / 1000.0, tz=UTC).year

    @classmethod
    def get_month_original(cls, time_ms: int) -> int:
        """Return calendar month (1-12, UTC) for millisecond timestamp."""
        return datetime.fromtimestamp(time_ms / 1000.0, tz=UTC).month

    # Donor Java camelCase compatibility aliases
    getDiffInDays = get_diff_in_days  # noqa: N815
    correctDayStart = correct_day_start  # noqa: N815
    getDayOfWeekOriginal = get_day_of_week_original  # noqa: N815
    getYear = get_year  # noqa: N815
    getMonthOriginal = get_month_original  # noqa: N815
