"""Unit tests for DateTime, BarTime, and TimeConditions in app.services.include.bar_time."""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest
from app.services.include.bar_time import (
    BarTime,
    DateTime,
    TimeConditions,
    format_timestamp,
    normalize_timestamps,
)


def test_datetime_constants_and_scalar_extractors() -> None:
    """Verify DateTime constants and scalar epoch-ms component extraction."""
    assert DateTime.DAY_MILLIS == 86_400_000
    assert DateTime.MONDAY == 1
    assert DateTime.FRIDAY == 5
    assert DateTime.SATURDAY == 6
    assert DateTime.SUNDAY == 7

    # 2026-10-14 15:30:45.123 UTC (Wednesday; Oct 1 2026 is Thursday -> Week 3)
    ms = DateTime.to_long(2026, 10, 14, 15, 30, 45) + 123
    assert DateTime.get_year(ms) == 2026
    assert DateTime.get_month(ms) == 10
    assert DateTime.get_month_original(ms) == 9
    assert DateTime.get_day(ms) == 14
    assert DateTime.get_hour(ms) == 15
    assert DateTime.get_minute(ms) == 30
    assert DateTime.get_second(ms) == 45
    assert DateTime.get_millis(ms) == 123
    assert DateTime.get_day_of_week(ms) == 3
    assert DateTime.get_day_of_week_original(ms) == 3
    assert DateTime.get_day_of_year(ms) == 287
    assert DateTime.get_days_in_month(ms) == 31
    assert DateTime.get_week_of_month(ms) == 3
    assert DateTime.get_week_of_year(ms) == 42

    # Sunday: ISO DOW is 7, original/terminal DOW is 0
    sun_ms = DateTime.to_long(2026, 10, 18, 12, 0, 0)
    assert DateTime.get_day_of_week(sun_ms) == 7
    assert DateTime.get_day_of_week_original(sun_ms) == 0

    assert DateTime.get_ymd(ms) == 20261014
    assert DateTime.get_ymd(2026, 10, 14) == 20261014
    assert DateTime.get_hhmm(ms) == 1530
    assert DateTime.get_hhmm("15:30") == 1530
    assert DateTime.get_hhmm("08:05") == 805
    assert abs(DateTime.get_hms(1, 30, 0) - 1.5) < 1e-6
    assert DateTime.to_hours(ms) == ms // 3_600_000


def test_datetime_day_boundaries_and_arithmetic() -> None:
    """Verify DateTime day boundaries, calendar arithmetic, and setters."""
    ms = DateTime.to_long(2026, 10, 14, 15, 30, 45) + 500
    start_ms = DateTime.correct_day_start(ms)
    assert DateTime.get_date_in_ms(ms) == start_ms
    assert (
        DateTime.get_hour(start_ms),
        DateTime.get_minute(start_ms),
        DateTime.get_second(start_ms),
        DateTime.get_millis(start_ms),
    ) == (0, 0, 0, 0)

    end_ms = DateTime.correct_day_end(ms)
    assert (
        DateTime.get_hour(end_ms),
        DateTime.get_minute(end_ms),
        DateTime.get_second(end_ms),
        DateTime.get_millis(end_ms),
    ) == (23, 59, 59, 999)

    mt_end_ms = DateTime.correct_day_end_mt(ms)
    assert (
        DateTime.get_hour(mt_end_ms),
        DateTime.get_minute(mt_end_ms),
        DateTime.get_second(mt_end_ms),
    ) == (23, 59, 0)

    jan31 = DateTime.to_long(2026, 1, 31, 10, 0, 0)
    feb_ms = DateTime.add_months(jan31, 1)
    assert (DateTime.get_month(feb_ms), DateTime.get_day(feb_ms)) == (2, 28)
    assert DateTime.get_year(DateTime.add_years(jan31, 2)) == 2028
    assert DateTime.add_days(jan31, 2) == jan31 + 2 * 86_400_000
    assert DateTime.add_weeks(jan31, 1) == jan31 + 7 * 86_400_000
    assert DateTime.add_hours(jan31, 5) == jan31 + 5 * 3_600_000
    assert DateTime.add_minutes(jan31, 30) == jan31 + 30 * 60_000
    assert DateTime.add_seconds(jan31, 45) == jan31 + 45 * 1_000

    assert DateTime.add(jan31, 5, 3) == DateTime.add_days(jan31, 3)
    assert DateTime.minus(jan31, 5, 3) == DateTime.add_days(jan31, -3)
    assert DateTime.add(jan31, 1, 1) == DateTime.add_years(jan31, 1)
    assert DateTime.add(jan31, 2, 2) == DateTime.add_months(jan31, 2)
    assert DateTime.add(jan31, 3, 1) == DateTime.add_weeks(jan31, 1)
    assert DateTime.add(jan31, 10, 2) == DateTime.add_hours(jan31, 2)
    assert DateTime.add(jan31, 12, 10) == DateTime.add_minutes(jan31, 10)
    assert DateTime.add(jan31, 13, 20) == DateTime.add_seconds(jan31, 20)
    assert DateTime.add(jan31, 99, 100) == jan31 + 100


def test_datetime_setters_differences_and_formatting() -> None:
    """Verify DateTime setters, differences, formatting, parsing, and helpers."""
    ms = DateTime.to_long(2026, 10, 14, 15, 30, 45)
    assert DateTime.get_hour(DateTime.set_hour(ms, 8)) == 8
    assert DateTime.get_minute(DateTime.set_minute(ms, 12)) == 12
    assert DateTime.get_second(DateTime.set_second(ms, 5)) == 5
    assert DateTime.get_millis(DateTime.set_milliseconds(ms, 789)) == 789
    assert DateTime.get_day(DateTime.set_day_of_month(ms, 20)) == 20
    assert DateTime.get_month(DateTime.set_month_of_year(ms, 11)) == 11

    t_fri = DateTime.set_day_of_week(ms, DateTime.FRIDAY)
    assert (DateTime.get_day_of_week(t_fri), DateTime.get_day(t_fri)) == (5, 16)
    t_mon = DateTime.set_first_day_of_week(ms)
    assert (
        DateTime.get_day_of_week(t_mon),
        DateTime.get_day(t_mon),
        DateTime.get_hour(t_mon),
    ) == (1, 12, 0)

    t_hhmm = DateTime.set_hhmm(ms, 945)
    assert (
        DateTime.get_hour(t_hhmm),
        DateTime.get_minute(t_hhmm),
        DateTime.get_second(t_hhmm),
    ) == (9, 45, 0)
    t_time = DateTime.set_time(ms, 11, 22, 33, 444)
    assert (
        DateTime.get_hour(t_time),
        DateTime.get_minute(t_time),
        DateTime.get_second(t_time),
        DateTime.get_millis(t_time),
    ) == (11, 22, 33, 444)

    t1 = DateTime.to_long(2026, 10, 14, 10, 0, 0)
    t2 = DateTime.to_long(2026, 10, 17, 12, 30, 0)
    t_next_year = DateTime.to_long(2027, 2, 14, 10, 0, 0)
    assert DateTime.get_diff_in_days(t1, t2) == 3
    assert DateTime.get_days_between(t1, t2) == 3
    assert DateTime.get_days_between(t2, t1) == -3
    assert DateTime.get_minutes_between(t1, t2) == 3 * 1440 + 150
    assert DateTime.get_weeks_between(t1, t1 + 14 * 86_400_000) == 2
    assert DateTime.get_months_between(t1, t_next_year) == 4
    assert DateTime.get_years_between(t1, t_next_year) == 1
    assert DateTime.is_same_day(t1, t1 + 3_600_000) is True
    assert DateTime.is_same_day(t1, t2) is False
    assert DateTime.is_same_month(t1, t2) is True
    assert DateTime.is_same_month(t1, t_next_year) is False
    assert DateTime.is_same_week(t1, t1 + 86_400_000) == 1
    assert DateTime.is_same_week(t1, t1 + 10 * 86_400_000) == 0

    assert DateTime.to_full_datetime_string(ms) == "2026.10.14 15:30:45"
    assert DateTime.to_date_minute_string(ms) == "2026.10.14 15:30"
    assert DateTime.to_date_string(ms) == "2026.10.14"
    assert DateTime.format_date(ms) == "2026.10.14"
    assert DateTime.format_time(ms) == "15:30:45"
    assert DateTime.to_hhmm_string(ms) == "15:30"
    assert DateTime.to_full_time(ms) == "15:30:45.000"
    assert len(DateTime.get_log_time(include_date=True, include_millis=True)) > 10

    assert DateTime.parse_date_to_millis("2026.10.14 15:30:45") == ms
    assert DateTime.parse_date_to_millis("2026-10-14") == DateTime.to_long(2026, 10, 14)
    assert DateTime.parse_to_millis("14/10/2026 15:30:45", "dd/MM/yyyy HH:mm:ss") == ms
    assert DateTime.to_date(ms) == datetime(2026, 10, 14, 15, 30, 45, tzinfo=UTC)

    assert DateTime.hhmm_to_minutes(1430) == 870
    assert DateTime.minutes_to_hhmm(870) == 1430
    ms_930 = DateTime.to_long(2026, 10, 14, 9, 30, 0)
    assert DateTime.get_hhmm(ms_930) == 930
    assert DateTime.get_ts_diff_in_minutes(930, 1015) == 45
    assert DateTime.dow_to_metatrader(DateTime.SUNDAY) == 0
    assert DateTime.dow_to_metatrader(DateTime.MONDAY) == 1
    assert DateTime.dow_to_metatrader(DateTime.SATURDAY) == 6
    assert DateTime.dow_to_string(DateTime.MONDAY) == "Monday"
    assert DateTime.dow_to_string(DateTime.FRIDAY) == "Friday"
    assert DateTime.dow_to_string(99) == ""
    assert DateTime.times_in_same_minute(ms_930, ms_930 + 15_000) is True
    assert DateTime.times_in_same_minute(ms_930, ms_930 + 65_000) is False
    assert DateTime.times_in_same_minute(10, 10) is True
    assert DateTime.get_datetime(ms_930) == 202610140930
    assert DateTime.get_local_current_time_in_ms() > 0
    text = DateTime.get_duration_text(90_061_000)
    assert "1d" in text and "1h" in text and "1m" in text and "1s" in text


def test_normalize_and_format_timestamps() -> None:
    """Test normalize_timestamps and format_timestamp across input types."""
    ms_arr = np.array([1704110400000, 1704153600000], dtype=np.int64)
    sec_arr = normalize_timestamps(ms_arr)
    assert list(sec_arr) == [1704110400, 1704153600]

    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    raw = [
        1704110400,
        1704153600000,
        dt,
        "2024-01-01T15:00:00+00:00",
        np.datetime64("2024-01-01T18:00:00"),
    ]
    norm = normalize_timestamps(raw)
    assert len(norm) == 5
    assert norm[0] == 1704110400
    assert norm[1] == 1704153600
    assert norm[2] == int(dt.timestamp())

    assert format_timestamp(None) == "N/A"
    assert "2024-01-01 12:00:00" in format_timestamp(1704110400, include_tz=False)
    assert "2024-01-01T12:00:00" in format_timestamp(
        1704110400, fmt="iso", include_tz=True
    )
    assert len(format_timestamp(1704110400, use_local_tz=True)) > 0
    assert "2024-01-01" in format_timestamp(dt, fmt="%Y-%m-%d", include_tz=False)
    with pytest.raises(TypeError):
        format_timestamp(True)
    with pytest.raises(TypeError):
        format_timestamp("invalid")  # type: ignore[arg-type]


def test_datetime_series() -> None:
    """Test DateTime series shift indexing and bounds."""
    timestamps = [1704110400, 1704153600, 1704196800]
    series = DateTime(timestamps, name="TestTS")
    assert series.name == "TestTS"
    assert len(series) == 3
    assert len(series.timestamps) == 3
    assert series.get_timestamp(shift=0) == 1704196800
    assert series.get_timestamp(shift=1) == 1704153600
    assert series.get_timestamp(shift=2) == 1704110400
    assert series.get_timestamp(shift=3) == -1
    assert series.get_timestamp(shift=-1) == -1
    assert series.get_datetime(shift=0) == datetime.fromtimestamp(1704196800, tz=UTC)
    assert series.get_datetime(shift=99) is None
    with pytest.raises(ValueError):
        DateTime([])


def test_bar_time_extractors_and_broker_clock() -> None:
    """Test BarTime extractors, HHMM format, Sunday=0 DOW, and current_time_ms."""
    # t1: 2024-01-01 00:00:00 UTC (Monday)
    # t2: 2024-01-07 15:45:30 UTC (Sunday -> DOW=0)
    t1 = int(datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 7, 15, 45, 30, tzinfo=UTC).timestamp())

    bt = BarTime([t1, t2])
    assert len(bt) == 2
    assert bt.get_dt(0) == datetime(2024, 1, 7, 15, 45, 30, tzinfo=UTC)

    # Shift 0 is t2 (Sunday Jan 7, 15:45:30)
    assert bt.bar_hour(shift=0) == 15
    assert bt.bar_minute(shift=0) == 45
    assert bt.bar_day_of_week(shift=0) == 0  # Sunday = 0
    assert bt.bar_day_of_month(shift=0) == 7
    assert bt.bar_month(shift=0) == 1
    assert bt.bar_date(shift=0) == 20240107
    assert bt.bar_time(shift=0) == 1545  # Gap 2: packed HHMM
    assert bt.bar_week_of_month(shift=0) == 1
    assert bt.current_bar(shift=0) == 1
    assert bt.current_bar(shift=1) == 0

    # Shift 1 is t1 (Monday Jan 1, 00:00:00)
    assert bt.bar_hour(shift=1) == 0
    assert bt.bar_minute(shift=1) == 0
    assert bt.bar_day_of_week(shift=1) == 1  # Monday = 1
    assert bt.bar_time(shift=1) == 0

    # Out of bounds
    assert bt.bar_hour(shift=5) == -1
    assert bt.bar_time(shift=5) == -1

    # Default current_* uses shift=0 when current_time_ms is None
    assert bt.current_time_ms is None
    assert bt.current_date() == 20240107
    assert bt.current_time() == 1545
    assert bt.current_hour() == 15
    assert bt.current_minute() == 45
    assert bt.current_day_of_week() == 0
    assert bt.current_month() == 1
    assert bt.current_week_of_month() == 1

    # Gap 8: Setting broker clock (current_time_ms) overrides current_* independently of shift=0
    broker_ms = DateTime.to_long(2024, 2, 14, 9, 15, 0)  # Wed Feb 14, 2024 09:15
    bt.current_time_ms = broker_ms
    assert bt.current_time_ms == broker_ms
    assert bt.current_date() == 20240214
    assert bt.current_time() == 915
    assert bt.current_hour() == 9
    assert bt.current_minute() == 15
    assert bt.current_day_of_week() == 3  # Wednesday = 3
    assert bt.current_month() == 2
    assert bt.current_week_of_month() == 3  # Feb 1 2024 is Thu -> Feb 14 is Week 3

    # Series exports
    assert list(bt.hour_series().values) == [0, 15]
    assert list(bt.minute_series().values) == [0, 45]
    assert list(bt.day_of_week_series().values) == [1, 0]
    assert list(bt.month_series().values) == [1, 1]


def test_time_conditions_and_all_8_gaps() -> None:
    """Test TimeConditions predicates and verify all 8 BarAndTime gap fixes."""
    # Build a realistic monthly transition sequence:
    # Bar 0 (shift=4): 2026-05-29 10:00 UTC (Friday - last weekday of May 2026; May 31 is Sunday!)
    # Bar 1 (shift=3): 2026-05-31 22:00 UTC (Sunday - calendar end of May 2026)
    # Bar 2 (shift=2): 2026-08-01 08:00 UTC (Saturday - first calendar day of Aug 2026)
    # Bar 3 (shift=1): 2026-08-03 00:00 UTC (Monday - first weekday trading day of Aug 2026, midnight 00:00)
    # Bar 4 (shift=0): 2026-08-19 14:30 UTC (Wednesday - mid-month bar at shift=0)
    bars = [
        int(datetime(2026, 5, 29, 10, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2026, 5, 31, 22, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2026, 8, 1, 8, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2026, 8, 3, 0, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2026, 8, 19, 14, 30, 0, tzinfo=UTC).timestamp()),
    ]
    cond = TimeConditions(bars, is_bar_open=False)
    assert cond.always_true() is True
    assert cond.always_false() is False

    # Gap 7: IsBarOpen state & overrides
    assert cond.is_bar_open() is False
    assert cond.is_bar_open(True) is True
    assert TimeConditions(bars).is_bar_open() is True
    assert cond.is_bar_open(False) is False

    # Hour, minute, month conditions on shift=0 (2026-08-19 14:30, Wednesday=3)
    assert cond.bar_hour_is(14, shift=0) is True
    assert cond.bar_hour_is_bigger(12, shift=0) is True
    assert cond.bar_hour_is_smaller(15, shift=0) is True
    assert cond.bar_minute_is(30, shift=0) is True
    assert cond.bar_month_is(8, shift=0) is True
    assert cond.bar_month_is_not(5, shift=0) is True

    # Gap 1: Day of week (0=Sunday..6=Saturday; 7 also normalized to 0)
    assert cond.bar_day_of_week_is(0, shift=3) is True  # May 31 is Sunday (0)
    assert cond.bar_day_of_week_is(7, shift=3) is True  # 7 normalized to 0
    assert cond.bar_day_of_week_is(6, shift=2) is True  # Aug 1 is Saturday (6)
    assert cond.bar_day_of_week_is(1, shift=1) is True  # Aug 3 is Monday (1)
    assert cond.bar_day_of_week_is_not(1, shift=0) is True

    # Gap 4: BarTimeIs & CurrentTimeIs with (hour, minute, shift), HHMM, and midnight 00:00
    assert cond.bar_time_is(14, 30, shift=0) is True
    assert cond.bar_time_is(14, 15, shift=0) is False
    assert cond.bar_time_is(1430, shift=0) is True
    assert cond.bar_time_is(143000, shift=0) is True
    assert cond.bar_time_is(0, 0, shift=1) is True  # Midnight (00:00) via (hour, min)
    assert cond.bar_time_is(0, shift=1) is True  # Midnight (00:00) via packed HHMM=0
    assert cond.current_time_is(14, 30) is True
    assert cond.current_time_is(1430) is True

    # Gap 3: FirstWeekOfMonth & LastWeekOfMonth (Monday-aligned weeks)
    # Aug 1 2026 (Saturday) is in Week 1; Aug 3 2026 (Monday) starts Week 2; Aug 31 2026 (Monday) starts Week 6
    assert cond.first_week_of_month(shift=2) is True  # Aug 1 -> Week 1
    assert cond.first_week_of_month(shift=1) is False  # Aug 3 -> Week 2
    assert cond.last_week_of_month(shift=3) is True  # May 31 -> last week of May
    assert (
        cond.last_week_of_month(shift=4) is True
    )  # May 29 -> same Monday-week as May 31
    assert cond.last_week_of_month(shift=0) is False  # Aug 19 -> mid-month

    # Gap 5: IsMonthFirstTradingDay (include_weekends=False vs True)
    # Bar at shift=2 is Saturday Aug 1; Bar at shift=1 is Monday Aug 3
    assert cond.is_month_first_trading_day(shift=2, include_weekends=False) is False
    assert cond.is_month_first_trading_day(shift=2, include_weekends=True) is True
    assert cond.is_month_first_trading_day(shift=1, include_weekends=False) is True
    assert cond.is_month_first_trading_day(shift=1, include_weekends=True) is False
    assert cond.is_month_first_trading_day(shift=0, include_weekends=False) is False

    # Gap 6: IsMonthLastTradingDay (calendar month-end rollback, no future lookahead bug!)
    # May 2026 has 31 days; May 31 is Sunday, so last weekday trading day is Friday May 29 (shift=4)
    assert cond.is_month_last_trading_day(shift=4, include_weekends=False) is True
    assert cond.is_month_last_trading_day(shift=4, include_weekends=True) is False
    assert cond.is_month_last_trading_day(shift=3, include_weekends=False) is False
    assert cond.is_month_last_trading_day(shift=3, include_weekends=True) is True
    # Shift=0 is Aug 19 (mid-month): must return False (previously returned True due to lookahead bug)
    assert cond.is_month_last_trading_day(shift=0, include_weekends=False) is False
    assert cond.is_month_last_trading_day(shift=0, include_weekends=True) is False
