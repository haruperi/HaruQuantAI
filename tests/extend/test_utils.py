"""Unit tests for SQ.Utils TimeDiffUtil and SQTime primitives."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from app.extend.utils import SQTime, TimeDiffUtil


class MockChart:
    """Mock ChartData object providing Time and optional TimeD sequences."""

    def __init__(
        self,
        times_ms: Sequence[int],
        daily_times_ms: Sequence[int] | None = None,
    ) -> None:
        self._times = list(times_ms)
        self._daily_times = list(daily_times_ms or [])

    def Time(self, shift: int = 0) -> int:  # noqa: N802
        """Return millisecond timestamp at shift."""
        if 0 <= shift < len(self._times):
            return self._times[shift]
        return 0

    def TimeD(self, shift: int = 0) -> int:  # noqa: N802
        """Return daily timestamp at shift."""
        if 0 <= shift < len(self._daily_times):
            return self._daily_times[shift]
        return 0


def _to_ms(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> int:
    """Convert UTC calendar date to epoch milliseconds."""
    dt = datetime(year, month, day, hour, minute, tzinfo=UTC)
    return int(dt.timestamp() * 1000)


def test_sq_time_day_diff() -> None:
    """Test SQTime calendar day difference calculation."""
    t1 = _to_ms(2026, 5, 10, 10, 0)
    t2 = _to_ms(2026, 5, 10, 22, 0)
    # Same calendar day
    assert SQTime.get_diff_in_days(t1, t2) == 0
    assert SQTime.getDiffInDays(t1, t2) == 0

    # 5 calendar days apart
    t3 = _to_ms(2026, 5, 15, 8, 0)
    assert SQTime.get_diff_in_days(t1, t3) == 5
    assert SQTime.get_diff_in_days(t3, t1) == 5


def test_sq_time_day_start() -> None:
    """Test SQTime calendar day start truncation."""
    t = _to_ms(2026, 5, 10, 14, 35)
    expected_start = _to_ms(2026, 5, 10, 0, 0)
    assert SQTime.correct_day_start(t) == expected_start
    assert SQTime.correctDayStart(t) == expected_start


def test_sq_time_day_of_week() -> None:
    """Test SQTime Java Calendar-compatible day-of-week (Sunday=1..Saturday=7)."""
    # 2026-05-10 is Sunday
    sunday_ms = _to_ms(2026, 5, 10, 12, 0)
    assert SQTime.get_day_of_week_original(sunday_ms) == 1
    assert SQTime.getDayOfWeekOriginal(sunday_ms) == 1

    # 2026-05-11 is Monday
    monday_ms = _to_ms(2026, 5, 11, 12, 0)
    assert SQTime.get_day_of_week_original(monday_ms) == 2

    # 2026-05-15 is Friday
    friday_ms = _to_ms(2026, 5, 15, 12, 0)
    assert SQTime.get_day_of_week_original(friday_ms) == 6

    # 2026-05-16 is Saturday
    saturday_ms = _to_ms(2026, 5, 16, 12, 0)
    assert SQTime.get_day_of_week_original(saturday_ms) == 7


def test_sq_time_year_and_month() -> None:
    """Test SQTime year and month extraction."""
    t = _to_ms(2026, 11, 2, 18, 30)
    assert SQTime.get_year(t) == 2026
    assert SQTime.getYear(t) == 2026
    assert SQTime.get_month_original(t) == 11
    assert SQTime.getMonthOriginal(t) == 11


def test_time_diff_in_days_shift_zero() -> None:
    """Ensure get_diff_in_days returns 0 when shift is 0."""
    chart = MockChart([_to_ms(2026, 5, 10, 12, 0)])
    assert TimeDiffUtil.get_diff_in_days(chart, 0) == 0
    assert TimeDiffUtil.getDiffInDays(chart, 0) == 0


def test_time_diff_in_days_same_day() -> None:
    """Ensure get_diff_in_days returns 0 when bars fall on the same calendar day."""
    t0 = _to_ms(2026, 5, 10, 16, 0)
    t1 = _to_ms(2026, 5, 10, 12, 0)
    chart = MockChart([t0, t1])
    assert TimeDiffUtil.get_diff_in_days(chart, 1) == 0


def test_time_diff_in_days_intraday_fallback() -> None:
    """Test get_diff_in_days stepping through intraday bars across days."""
    # 3 days: 2026-05-12, 2026-05-11, 2026-05-10
    t0 = _to_ms(2026, 5, 12, 14, 0)
    t1 = _to_ms(2026, 5, 12, 10, 0)
    t2 = _to_ms(2026, 5, 11, 15, 0)
    t3 = _to_ms(2026, 5, 10, 9, 0)
    chart = MockChart([t0, t1, t2, t3])

    assert TimeDiffUtil.get_diff_in_days(chart, 1) == 0  # same day
    assert TimeDiffUtil.get_diff_in_days(chart, 2) == 1  # 1 day diff
    assert TimeDiffUtil.get_diff_in_days(chart, 3) == 2  # 2 days diff


def test_time_diff_in_days_daily_chart() -> None:
    """Test get_diff_in_days when daily chart TimeD is present."""
    t0 = _to_ms(2026, 5, 12, 14, 0)
    t1 = _to_ms(2026, 5, 11, 10, 0)
    t2 = _to_ms(2026, 5, 10, 9, 0)

    daily_0 = _to_ms(2026, 5, 12, 0, 0)
    daily_1 = _to_ms(2026, 5, 11, 0, 0)
    daily_2 = _to_ms(2026, 5, 10, 0, 0)

    chart = MockChart([t0, t1, t2], [daily_0, daily_1, daily_2])
    # shift=1: shifted_time is 2026-05-11 10:00; daily_1 is 2026-05-11 00:00 <= shifted_time -> 1
    assert TimeDiffUtil.get_diff_in_days(chart, 1) == 1
    # shift=2: shifted_time is 2026-05-10 09:00; daily_2 is 2026-05-10 00:00 <= shifted_time -> 2
    assert TimeDiffUtil.get_diff_in_days(chart, 2) == 2

    # Case where loop finishes without dailyTime <= shiftedTime
    chart_unmatched = MockChart([t0, t1], [daily_0, _to_ms(2026, 5, 13, 0, 0)])
    assert TimeDiffUtil.get_diff_in_days(chart_unmatched, 1) == 0


def test_time_diff_in_weeks() -> None:
    """Test get_diff_in_weeks across same week, weekend rollover, and multi-week."""
    # shift=0
    chart = MockChart([_to_ms(2026, 5, 15, 12, 0)])
    assert TimeDiffUtil.get_diff_in_weeks(chart, 0) == 0
    assert TimeDiffUtil.getDiffInWeeks(chart, 0) == 0

    # Same day
    t0 = _to_ms(2026, 5, 15, 16, 0)  # Friday
    t1 = _to_ms(2026, 5, 15, 10, 0)  # Friday
    chart_same = MockChart([t0, t1])
    assert TimeDiffUtil.get_diff_in_weeks(chart_same, 1) == 0

    # Same week: Friday (2026-05-15) and Monday (2026-05-11)
    # dow1 = 6 (Friday), dow2 = 2 (Monday) -> dow1 not < dow2 -> 0 weeks
    t_fri = _to_ms(2026, 5, 15, 12, 0)
    t_mon = _to_ms(2026, 5, 11, 12, 0)
    chart_week = MockChart([t_fri, t_mon])
    assert TimeDiffUtil.get_diff_in_weeks(chart_week, 1) == 0

    # Cross week rollover: Wednesday (2026-05-13) and previous Friday (2026-05-08)
    # dow1 = 4 (Wed), dow2 = 6 (Fri) -> dow1 < dow2 -> diffWeeks += 1 -> 1 week
    t_wed = _to_ms(2026, 5, 13, 12, 0)
    t_prev_fri = _to_ms(2026, 5, 8, 12, 0)
    chart_rollover = MockChart([t_wed, t_prev_fri])
    assert TimeDiffUtil.get_diff_in_weeks(chart_rollover, 1) == 1

    # Exact 2 weeks (14 calendar days)
    t_two_weeks = _to_ms(2026, 4, 29, 12, 0)
    chart_14d = MockChart([t_wed, t_two_weeks])
    assert TimeDiffUtil.get_diff_in_weeks(chart_14d, 1) == 2


def test_time_diff_in_months() -> None:
    """Test get_diff_in_months across same year and multi-year ranges."""
    # shift=0
    chart = MockChart([_to_ms(2026, 5, 15, 12, 0)])
    assert TimeDiffUtil.get_diff_in_months(chart, 0) == 0
    assert TimeDiffUtil.getDiffInMonths(chart, 0) == 0

    # Same calendar day
    t0 = _to_ms(2026, 5, 15, 16, 0)
    t1 = _to_ms(2026, 5, 15, 10, 0)
    chart_same = MockChart([t0, t1])
    assert TimeDiffUtil.get_diff_in_months(chart_same, 1) == 0

    # Same year, different months: May 2026 vs Feb 2026 -> 3 months
    t_may = _to_ms(2026, 5, 15, 12, 0)
    t_feb = _to_ms(2026, 2, 10, 12, 0)
    chart_same_year = MockChart([t_may, t_feb])
    assert TimeDiffUtil.get_diff_in_months(chart_same_year, 1) == 3

    # Cross year: Jan 2026 vs Nov 2025 -> 2 months
    t_jan = _to_ms(2026, 1, 15, 12, 0)
    t_nov_prev = _to_ms(2025, 11, 20, 12, 0)
    chart_cross_year = MockChart([t_jan, t_nov_prev])
    assert TimeDiffUtil.get_diff_in_months(chart_cross_year, 1) == 2

    # Multi-year: Jan 2026 vs Jan 2024 -> 24 months
    t_two_years_prior = _to_ms(2024, 1, 15, 12, 0)
    chart_multi_year = MockChart([t_jan, t_two_years_prior])
    assert TimeDiffUtil.get_diff_in_months(chart_multi_year, 1) == 24


def test_chart_series_fallback() -> None:
    """Test TimeDiffUtil with object providing Time_series attribute."""

    class SeriesChart:
        def __init__(self, times: list[int]) -> None:
            self.Time_series = times

    t0 = _to_ms(2026, 5, 15, 12, 0)
    t1 = _to_ms(2026, 5, 10, 12, 0)

    class DummySeries:
        def __init__(self, values: list[int]) -> None:
            self._values = values

        def get(self, shift: int) -> int:
            return self._values[shift]

    chart = SeriesChart([t0, t1])
    chart.Time_series = DummySeries([t0, t1])  # type: ignore[assignment]
    assert TimeDiffUtil.get_diff_in_days(chart, 1) == 1

    # Empty object fallback
    assert TimeDiffUtil.get_diff_in_days(object(), 1) == 0
