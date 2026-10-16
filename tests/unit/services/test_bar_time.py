"""Unit tests for BarTime, DateTimeSeries, and TimeConditions in app.services.include.bar_time."""

from datetime import UTC, datetime

import numpy as np
import pytest
from app.services.include.bar_time import (
    BarTime,
    DateTimeSeries,
    TimeConditions,
    format_timestamp,
    normalize_timestamps,
)


def test_normalize_timestamps() -> None:
    """Test timestamp normalization across various input formats."""
    # Milliseconds array vs seconds array
    ms_arr = np.array([1704110400000, 1704153600000], dtype=np.int64)
    sec_arr = normalize_timestamps(ms_arr)
    assert sec_arr.dtype == np.int64
    assert list(sec_arr) == [1704110400, 1704153600]

    # Mixed python list
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    raw = [1704110400, 1704153600000, dt, "2024-01-01T15:00:00+00:00"]
    norm = normalize_timestamps(raw)
    assert len(norm) == 4
    assert norm[0] == 1704110400
    assert norm[1] == 1704153600
    assert norm[2] == int(dt.timestamp())


def test_format_timestamp() -> None:
    """Test timestamp string formatting."""
    assert format_timestamp(None) == "N/A"

    ts = 1704110400  # 2024-01-01 12:00:00 UTC
    formatted = format_timestamp(ts, include_tz=False)
    assert "2024-01-01 12:00:00" in formatted

    iso = format_timestamp(ts, fmt="iso", include_tz=True)
    assert "2024-01-01T12:00:00" in iso

    local_fmt = format_timestamp(ts, use_local_tz=True)
    assert len(local_fmt) > 0

    with pytest.raises(TypeError):
        format_timestamp("invalid")  # type: ignore[arg-type]


def test_datetime_series() -> None:
    """Test DateTimeSeries shift indexing and boundaries."""
    timestamps = [1704110400, 1704153600, 1704196800]  # newest is 1704196800
    series = DateTimeSeries(timestamps, name="TestTS")

    assert series.name == "TestTS"
    assert len(series) == 3
    assert len(series.timestamps) == 3

    # shift 0 is newest, shift 2 is oldest
    assert series.get_timestamp(shift=0) == 1704196800
    assert series.get_timestamp(shift=1) == 1704153600
    assert series.get_timestamp(shift=2) == 1704110400
    assert series.get_timestamp(shift=3) == -1
    assert series.get_timestamp(shift=-1) == -1

    dt0 = series.get_datetime(shift=0)
    assert dt0 is not None
    assert dt0 == datetime.fromtimestamp(1704196800, tz=UTC)
    assert series.get_datetime(shift=99) is None

    with pytest.raises(ValueError):
        DateTimeSeries([])


def test_bar_time_extractors() -> None:
    """Test BarTime component extraction via HQTime delegation."""
    # 2024-01-01 12:30:45 UTC (Monday)
    # 2024-01-02 15:45:00 UTC (Tuesday)
    t1 = int(datetime(2024, 1, 1, 12, 30, 45, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 2, 15, 45, 0, tzinfo=UTC).timestamp())

    bt = BarTime([t1, t2])
    assert len(bt) == 2

    # Shift 0 is t2 (Jan 2, 15:45:00)
    assert bt.bar_hour(shift=0) == 15
    assert bt.bar_minute(shift=0) == 45
    assert bt.bar_day_of_week(shift=0) == 2  # Tuesday
    assert bt.bar_day_of_month(shift=0) == 2
    assert bt.bar_month(shift=0) == 1
    assert bt.bar_date(shift=0) == 20240102
    assert bt.bar_time(shift=0) == 154500
    assert bt.bar_week_of_month(shift=0) == 1
    assert bt.current_bar(shift=0) == 1
    assert bt.current_bar(shift=1) == 0

    # Shift 1 is t1 (Jan 1, 12:30:45)
    assert bt.bar_hour(shift=1) == 12
    assert bt.bar_minute(shift=1) == 30
    assert bt.bar_day_of_week(shift=1) == 1  # Monday
    assert bt.bar_time(shift=1) == 123045

    # Out of bounds
    assert bt.bar_hour(shift=5) == -1
    assert bt.bar_time(shift=5) == -1

    # Aliases
    assert bt.current_date() == 20240102
    assert bt.current_time() == 154500
    assert bt.current_hour() == 15
    assert bt.current_minute() == 45
    assert bt.current_day_of_week() == 2
    assert bt.current_month() == 1
    assert bt.current_week_of_month() == 1

    # Series generation
    hs = bt.hour_series()
    assert list(hs.values) == [12, 15]
    ms = bt.minute_series()
    assert list(ms.values) == [30, 45]
    dows = bt.day_of_week_series()
    assert list(dows.values) == [1, 2]
    months = bt.month_series()
    assert list(months.values) == [1, 1]


def test_time_conditions() -> None:
    """Test TimeConditions rule predicates."""
    t1 = int(datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 28, 14, 30, 0, tzinfo=UTC).timestamp())

    cond = TimeConditions([t1, t2])
    assert cond.always_true() is True
    assert cond.always_false() is False
    assert cond.is_bar_open() is True

    # Shift 0 is t2 (14:30)
    assert cond.bar_hour_is(14, shift=0) is True
    assert cond.bar_hour_is(10, shift=0) is False
    assert cond.bar_hour_is_bigger(12, shift=0) is True
    assert cond.bar_hour_is_smaller(15, shift=0) is True
    assert cond.bar_minute_is(30, shift=0) is True
    assert cond.bar_day_of_week_is(7, shift=0) is True  # Sunday
    assert cond.bar_day_of_week_is_not(1, shift=0) is True
    assert cond.bar_month_is(1, shift=0) is True
    assert cond.bar_month_is_not(2, shift=0) is True
    assert cond.bar_time_is(1430, shift=0) is True
    assert cond.bar_time_is(143000, shift=0) is True

    # Aliases
    assert cond.current_hour_is(14) is True
    assert cond.current_minute_is(30) is True
    assert cond.current_day_of_week_is(7) is True
    assert cond.current_month_is(1) is True
    assert cond.current_time_is(1430) is True

    # Month trading days & cycle predicates
    assert cond.first_week_of_month(shift=1) is True  # Jan 1
    assert cond.first_week_of_month(shift=0) is False  # Jan 28
    assert cond.last_week_of_month(shift=0) is True  # Jan 28 >= 25
    assert cond.last_week_of_month(shift=1) is False

    assert cond.is_month_first_trading_day(shift=1) is True  # Jan 1 is first
    assert cond.is_month_first_trading_day(shift=0) is False
    assert cond.is_month_last_trading_day(shift=0) is True  # Jan 28 is last
    assert cond.is_month_last_trading_day(shift=1) is False
