"""Unit test suite for BarAndTime building blocks (DateTimeSeries, BarTime, TimeConditions).

Description:
    Tests verification of timestamp indexing, calendar feature extraction,
    and temporal rule predicates matching StrategyQuant X BarAndTime blocks.

Purpose:
    FEAT-SERVICES-TIME-TESTS: Comprehensive test coverage for BarAndTime blocks.

Key Capabilities:
    - FR-SERVICES-TEST-TIME: Assert exact temporal calculations and condition logic.
      Associated: `test_date_time_series()`, `test_bar_time()`,
        `test_time_conditions()`, `test_format_timestamp()`.
      Logging: DEBUG on test execution.

Python API Usage:
    ```python
    uv run pytest tests/unit/services/test_time.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_time.py --no-cov
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.indicators.base import IndicatorSeries
from app.services.utils.bar_time import (
    BarTime,
    DateTimeSeries,
    TimeConditions,
    format_timestamp,
)


def test_date_time_series() -> None:
    """Verify DateTimeSeries timestamp storage, datetime conversion, and bounds."""
    # 2024-01-01 10:00:00 and 2024-01-01 11:30:00 UTC
    dt1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    dt2 = datetime(2024, 1, 1, 11, 30, 0, tzinfo=UTC)
    ts = [int(dt1.timestamp()), int(dt2.timestamp())]

    dts = DateTimeSeries(ts, name="TestDT")
    assert dts.name == "TestDT"
    assert len(dts) == 2
    assert len(dts.timestamps) == 2

    # Shift 0 (newest bar)
    assert dts.get_timestamp(0) == ts[1]
    res_dt = dts.get_datetime(0)
    assert res_dt is not None
    assert res_dt.hour == 11
    assert res_dt.minute == 30

    # Shift 1 (previous bar)
    assert dts.get_timestamp(1) == ts[0]
    res_dt1 = dts.get_datetime(1)
    assert res_dt1 is not None
    assert res_dt1.hour == 10
    assert res_dt1.minute == 0

    # Out of bounds
    assert dts.get_timestamp(5) == -1
    assert dts.get_timestamp(-1) == -1
    assert dts.get_datetime(5) is None

    # Error handling
    with pytest.raises(ValueError, match="cannot be empty"):
        DateTimeSeries([])


def test_bar_time() -> None:
    """Verify BarTime component extractors and IndicatorSeries generation."""
    # Monday, Jan 15, 2024 14:45:30 UTC
    dt1 = datetime(2024, 1, 15, 14, 45, 30, tzinfo=UTC)
    # Friday, Jan 26, 2024 09:15:00 UTC
    dt2 = datetime(2024, 1, 26, 9, 15, 0, tzinfo=UTC)

    ts = [dt1, dt2]
    bt = BarTime(ts)
    assert len(bt) == 2
    assert isinstance(bt.series, DateTimeSeries)

    # Shift 0 (dt2: Friday, Jan 26, 2024 09:15:00)
    assert bt.bar_hour(0) == 9
    assert bt.bar_minute(0) == 15
    assert bt.bar_day_of_week(0) == 5  # Friday
    assert bt.bar_day_of_month(0) == 26
    assert bt.bar_month(0) == 1
    assert bt.bar_date(0) == 20240126
    assert bt.bar_time(0) == 91500
    assert bt.bar_week_of_month(0) == 4  # (26-1)//7 + 1 = 4
    assert bt.current_bar(0) == 1

    # Shift 1 (dt1: Monday, Jan 15, 2024 14:45:30)
    assert bt.bar_hour(1) == 14
    assert bt.bar_minute(1) == 45
    assert bt.bar_day_of_week(1) == 1  # Monday
    assert bt.bar_date(1) == 20240115
    assert bt.bar_time(1) == 144530
    assert bt.current_bar(1) == 0

    # Current bar convenience aliases (evaluates shift=0)
    assert bt.current_date() == 20240126
    assert bt.current_time() == 91500
    assert bt.current_hour() == 9
    assert bt.current_minute() == 15
    assert bt.current_day_of_week() == 5
    assert bt.current_month() == 1
    assert bt.current_week_of_month() == 4

    # Out of bounds
    assert bt.bar_hour(5) == -1
    assert bt.bar_minute(5) == -1
    assert bt.bar_day_of_week(5) == -1
    assert bt.bar_day_of_month(5) == -1
    assert bt.bar_month(5) == -1
    assert bt.bar_date(5) == -1
    assert bt.bar_time(5) == -1
    assert bt.bar_week_of_month(5) == -1
    assert bt.current_bar(5) == -1

    # IndicatorSeries exports
    h_s = bt.hour_series()
    assert isinstance(h_s, IndicatorSeries)
    assert h_s.get(0) == 9.0
    assert h_s.get(1) == 14.0

    m_s = bt.minute_series()
    assert isinstance(m_s, IndicatorSeries)
    assert m_s.get(0) == 15.0

    dow_s = bt.day_of_week_series()
    assert isinstance(dow_s, IndicatorSeries)
    assert dow_s.get(0) == 5.0

    mon_s = bt.month_series()
    assert isinstance(mon_s, IndicatorSeries)
    assert mon_s.get(0) == 1.0


def test_time_conditions() -> None:
    """Verify TimeConditions predicate checks and temporal calendar rules."""
    # 3 bars: Jan 2 (Tuesday), Jan 15 (Monday), Jan 31 (Wednesday) 2024
    d1 = datetime(2024, 1, 2, 8, 30, 0, tzinfo=UTC)
    d2 = datetime(2024, 1, 15, 14, 45, 0, tzinfo=UTC)
    d3 = datetime(2024, 1, 31, 18, 0, 0, tzinfo=UTC)

    ts = [d1, d2, d3]
    tc = TimeConditions(ts)
    assert isinstance(tc.bar_time, BarTime)

    # Static predicates
    assert tc.always_true() is True
    assert tc.always_false() is False
    assert tc.is_bar_open() is True

    # Shift 0 (Jan 31, 18:00)
    assert tc.bar_hour_is(18, shift=0) is True
    assert tc.bar_hour_is(10, shift=0) is False
    assert tc.bar_hour_is_bigger(17, shift=0) is True
    assert tc.bar_hour_is_bigger(18, shift=0) is False
    assert tc.bar_hour_is_smaller(19, shift=0) is True
    assert tc.bar_hour_is_smaller(18, shift=0) is False
    assert tc.bar_minute_is(0, shift=0) is True
    assert tc.bar_day_of_week_is(3, shift=0) is True  # Wednesday
    assert tc.bar_day_of_week_is_not(1, shift=0) is True
    assert tc.bar_month_is(1, shift=0) is True
    assert tc.bar_month_is_not(2, shift=0) is True

    # bar_time_is (HHMM or HHMMSS)
    assert tc.bar_time_is(1800, shift=0) is True
    assert tc.bar_time_is(180000, shift=0) is True
    assert tc.bar_time_is(900, shift=0) is False

    # Current bar convenience aliases
    assert tc.current_hour_is(18) is True
    assert tc.current_minute_is(0) is True
    assert tc.current_day_of_week_is(3) is True
    assert tc.current_month_is(1) is True
    assert tc.current_time_is(1800) is True

    # First / Last week of month
    assert tc.first_week_of_month(shift=2) is True  # Jan 2 is in week 1
    assert tc.first_week_of_month(shift=0) is False  # Jan 31 is not week 1
    assert tc.last_week_of_month(shift=0) is True  # Jan 31 is in last week
    assert tc.last_week_of_month(shift=2) is False  # Jan 2 is not in last week

    # First / Last trading day of month in series
    assert tc.is_month_first_trading_day(shift=2) is True  # Jan 2
    assert tc.is_month_first_trading_day(shift=0) is False  # Jan 31
    assert tc.is_month_last_trading_day(shift=0) is True  # Jan 31
    assert tc.is_month_last_trading_day(shift=2) is False  # Jan 2

    # Out of bounds returns False safely
    assert tc.bar_hour_is(10, shift=10) is False
    assert tc.bar_hour_is_bigger(10, shift=10) is False
    assert tc.bar_hour_is_smaller(10, shift=10) is False
    assert tc.bar_time_is(1000, shift=10) is False
    assert tc.first_week_of_month(shift=10) is False
    assert tc.last_week_of_month(shift=10) is False
    assert tc.is_month_first_trading_day(shift=10) is False
    assert tc.is_month_last_trading_day(shift=10) is False

    # Initialization with BarTime and DateTimeSeries directly
    bt = BarTime(ts)
    tc2 = TimeConditions(bt)
    assert tc2.bar_hour_is(18, shift=0) is True

    dts = DateTimeSeries(ts)
    tc3 = TimeConditions(dts)
    assert tc3.bar_hour_is(18, shift=0) is True


def test_format_timestamp() -> None:
    """Verify format_timestamp with seconds, milliseconds, datetimes, and edge cases."""
    # 2024-01-01 12:00:00 UTC = 1704110400
    ts_sec = 1704110400.123456
    ts_int_sec = 1704110400
    ts_ms = 1704110400123

    # Default formatting (UTC with 3-digit ms precision)
    assert format_timestamp(ts_sec) == "2024-01-01 12:00:00.123 UTC"
    assert format_timestamp(ts_int_sec) == "2024-01-01 12:00:00.000 UTC"
    assert format_timestamp(ts_ms) == "2024-01-01 12:00:00.123 UTC"

    # None handling
    assert format_timestamp(None) == "N/A"

    # datetime instances (both naive and tz-aware)
    dt_aware = datetime(2024, 1, 1, 12, 0, 0, 500000, tzinfo=UTC)
    assert format_timestamp(dt_aware) == "2024-01-01 12:00:00.500 UTC"

    dt_naive = datetime.fromisoformat("2024-01-01T12:00:00.500000")
    assert format_timestamp(dt_naive) == "2024-01-01 12:00:00.500 UTC"

    # ISO format option
    iso_res = format_timestamp(ts_int_sec, fmt="iso")
    assert iso_res == "2024-01-01T12:00:00+00:00"

    # Custom format and precision options
    assert format_timestamp(ts_sec, precision=None) == "2024-01-01 12:00:00.123456 UTC"
    assert format_timestamp(ts_sec, precision=0) == "2024-01-01 12:00:00 UTC"
    assert format_timestamp(ts_sec, include_tz=False) == "2024-01-01 12:00:00.123"

    # Local timezone offset formatting
    local_expected = datetime.fromtimestamp(ts_sec, tz=UTC).astimezone()
    offset = local_expected.strftime("%:z")
    local_str = format_timestamp(ts_sec, use_local_tz=True)
    assert local_str.endswith(offset)
    assert local_expected.strftime("%Y-%m-%d %H:%M:%S.123") in local_str

    # Local ISO format
    local_iso = format_timestamp(ts_int_sec, fmt="iso", use_local_tz=True)
    assert local_iso == local_expected.replace(microsecond=0).isoformat()
    assert local_iso.endswith(offset)

    # Type validation rejections
    with pytest.raises(TypeError, match="Unsupported timestamp type: bool"):
        format_timestamp(True)

    with pytest.raises(TypeError, match="Unsupported timestamp type: str"):
        format_timestamp("2024-01-01")  # type: ignore[arg-type]
