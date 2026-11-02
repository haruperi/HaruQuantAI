"""Time difference calculation utility conforming to StrategyQuant TimeDiffUtil.

Description:
    Calculates calendar day, week, and month differences between the current
    bar (shift=0) and a historical bar at an arbitrary bar shift in ChartData.
    Conforms to StrategyQuant SQ.Utils.TimeDiffUtil snippet specifications.

Purpose:
    FEAT-UTILS-TIMEDIFF: StrategyQuant donor-faithful bar time difference utility.

Key Capabilities:
    - FR-UTILS-DIFF-DAYS: Compute calendar days difference across bars.
    - FR-UTILS-DIFF-WEEKS: Compute calendar weeks difference with rollover.
    - FR-UTILS-DIFF-MONTHS: Compute calendar months difference across years.

Python API Usage:
    from app.extend.utils.time_diff_util import TimeDiffUtil
    diff_days = TimeDiffUtil.get_diff_in_days(chart, shift=10)

CLI Usage:
    uv run pytest tests/extend/test_utils.py --no-cov
"""

from __future__ import annotations

from typing import Any, ClassVar

from app.core.host.logging import get_logger
from app.extend.utils.sq_time import SQTime

logger = get_logger(__name__)


def _chart_time(chart: Any, shift: int) -> int:
    """Retrieve timestamp in epoch milliseconds from chart at shift."""
    fn = getattr(chart, "Time", getattr(chart, "time", None))
    if callable(fn):
        return int(fn(shift))
    series = getattr(chart, "Time_series", None)
    if series is not None and hasattr(series, "get"):
        return int(series.get(shift))
    return 0


def _chart_daily_time(chart: Any, shift: int) -> int:
    """Retrieve daily chart timestamp if daily chart data is present."""
    fn = getattr(chart, "TimeD", getattr(chart, "time_d", None))
    if callable(fn):
        return int(fn(shift))
    return 0


def _diff_days_from_daily(chart: Any, shift: int, shifted_time: int) -> int:
    """Find calendar days offset using daily chart stream."""
    for i in range(shift + 1):
        daily_time = SQTime.correct_day_start(_chart_daily_time(chart, i))
        if daily_time <= shifted_time:
            return i
    return 0


def _diff_days_from_intraday(chart: Any, shift: int, current_time: int) -> int:
    """Calculate elapsed calendar days by stepping through intraday bars."""
    diff_days = 0
    day_start = current_time - (current_time % SQTime.DAY_MILLIS)
    for i in range(1, shift + 1):
        bar_time = _chart_time(chart, i)
        if bar_time <= day_start:
            diff_days += 1
            day_start = bar_time - (bar_time % SQTime.DAY_MILLIS)
    return diff_days


class TimeDiffUtil:
    """Calculates calendar days, weeks, and months difference for ChartData."""

    DAY_MILLIS: ClassVar[int] = SQTime.DAY_MILLIS

    @classmethod
    def get_diff_in_days(
        cls,
        chart: Any,
        shift: int,
        is_ts_engine: bool = False,  # noqa: ARG003
    ) -> int:
        """Return calendar days difference between current bar (0) and bar at shift.

        Args:
            chart: ChartData instance containing price/time streams.
            shift: Bar shift index (0 = current bar).
            is_ts_engine: TS engine flag matching donor method signature.

        Returns:
            Number of calendar days between bars.
        """
        if shift == 0:
            return 0

        current_time = _chart_time(chart, 0)
        shifted_time = _chart_time(chart, shift)
        days_offset = SQTime.get_diff_in_days(current_time, shifted_time)

        if days_offset == 0:
            return 0

        if _chart_daily_time(chart, 0) != 0:
            return _diff_days_from_daily(chart, shift, shifted_time)

        return _diff_days_from_intraday(chart, shift, current_time)

    @classmethod
    def get_diff_in_weeks(cls, chart: Any, shift: int) -> int:
        """Return calendar weeks difference between current bar (0) and bar at shift.

        Args:
            chart: ChartData instance.
            shift: Bar shift index.

        Returns:
            Number of calendar weeks between bars.
        """
        if shift == 0:
            return 0

        current_time = _chart_time(chart, 0)
        shifted_time = _chart_time(chart, shift)
        days_offset = SQTime.get_diff_in_days(current_time, shifted_time)

        if days_offset == 0:
            return 0

        diff_weeks = days_offset // 7
        rem_days = days_offset % 7

        if rem_days > 0:
            dow1 = SQTime.get_day_of_week_original(current_time)
            dow2 = SQTime.get_day_of_week_original(shifted_time)
            if dow1 < dow2:
                diff_weeks += 1

        logger.debug(
            "FR-UTILS-DIFF-WEEKS: calculated %d weeks (shift=%d)",
            diff_weeks,
            shift,
        )
        return diff_weeks

    @classmethod
    def get_diff_in_months(cls, chart: Any, shift: int) -> int:
        """Return calendar months difference between current bar (0) and bar at shift.

        Args:
            chart: ChartData instance.
            shift: Bar shift index.

        Returns:
            Number of calendar months between bars.
        """
        if shift == 0:
            return 0

        current_time = _chart_time(chart, 0)
        shifted_time = _chart_time(chart, shift)
        days_offset = SQTime.get_diff_in_days(current_time, shifted_time)

        if days_offset == 0:
            return 0

        year1 = SQTime.get_year(current_time)
        month1 = SQTime.get_month_original(current_time)
        year2 = SQTime.get_year(shifted_time)
        month2 = SQTime.get_month_original(shifted_time)

        if year1 == year2:
            return month1 - month2

        diff_months = month1
        year1 -= 1
        diff_months += (year1 - year2) * 12
        diff_months += 12 - month2

        logger.debug(
            "FR-UTILS-DIFF-MONTHS: calculated %d months (shift=%d)",
            diff_months,
            shift,
        )
        return diff_months

    # Donor Java camelCase compatibility aliases
    getDiffInDays = get_diff_in_days  # noqa: N815
    getDiffInWeeks = get_diff_in_weeks  # noqa: N815
    getDiffInMonths = get_diff_in_months  # noqa: N815
