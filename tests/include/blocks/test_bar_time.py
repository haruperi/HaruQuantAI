"""Comprehensive unit tests for BarAndTime modular blocks and facades."""

from __future__ import annotations

import importlib
from datetime import UTC, datetime

import pytest
from app.include import (
    BarTime,
    DateTime,
    TimeConditions,
)
from app.include.blocks.bar_time import (
    always_false,
    always_false_spec,
    always_true,
    always_true_spec,
    bar_date,
    bar_date_spec,
    bar_day_of_month,
    bar_day_of_month_spec,
    bar_day_of_week,
    bar_day_of_week_is,
    bar_day_of_week_is_not,
    bar_day_of_week_is_not_spec,
    bar_day_of_week_is_spec,
    bar_day_of_week_spec,
    bar_hour,
    bar_hour_is,
    bar_hour_is_bigger,
    bar_hour_is_bigger_spec,
    bar_hour_is_smaller,
    bar_hour_is_smaller_spec,
    bar_hour_is_spec,
    bar_hour_spec,
    bar_minute,
    bar_minute_is,
    bar_minute_is_spec,
    bar_minute_spec,
    bar_month,
    bar_month_is,
    bar_month_is_not,
    bar_month_is_not_spec,
    bar_month_is_spec,
    bar_month_spec,
    bar_time,
    bar_time_is,
    bar_time_is_spec,
    bar_time_spec,
    bar_week_of_month,
    bar_week_of_month_spec,
    current_bar,
    current_bar_spec,
    current_date,
    current_date_spec,
    current_day_of_week,
    current_day_of_week_is,
    current_day_of_week_is_spec,
    current_day_of_week_spec,
    current_hour,
    current_hour_is,
    current_hour_is_spec,
    current_hour_spec,
    current_minute,
    current_minute_is,
    current_minute_is_spec,
    current_minute_spec,
    current_month,
    current_month_is,
    current_month_is_spec,
    current_month_spec,
    current_time,
    current_time_is,
    current_time_is_spec,
    current_time_spec,
    current_week_of_month_spec,
    first_week_of_month,
    first_week_of_month_spec,
    is_bar_open,
    is_bar_open_spec,
    is_month_first_trading_day,
    is_month_first_trading_day_spec,
    is_month_last_trading_day,
    is_month_last_trading_day_spec,
    last_week_of_month,
    last_week_of_month_spec,
)
from app.include.blocks.metadata import BlockSpec, ExecutionKind, PortType
from app.include.blocks.registry import block_registry


def _sample_timestamps() -> list[int]:
    """Generate 5 representative timestamps in Jan 2025."""
    # 2025-01-01 09:30:00 (Wednesday, week 1, first day of month)
    d1 = int(datetime(2025, 1, 1, 9, 30, 0, tzinfo=UTC).timestamp())
    # 2025-01-02 10:15:00 (Thursday)
    d2 = int(datetime(2025, 1, 2, 10, 15, 0, tzinfo=UTC).timestamp())
    # 2025-01-06 14:45:00 (Monday, week 2)
    d3 = int(datetime(2025, 1, 6, 14, 45, 0, tzinfo=UTC).timestamp())
    # 2025-01-30 15:00:00 (Thursday)
    d4 = int(datetime(2025, 1, 30, 15, 0, 0, tzinfo=UTC).timestamp())
    # 2025-01-31 16:30:00 (Friday, last trading day of month)
    d5 = int(datetime(2025, 1, 31, 16, 30, 0, tzinfo=UTC).timestamp())
    return [d1, d2, d3, d4, d5]


def test_legacy_monolith_removed() -> None:
    """Verify app.include.bar_time legacy file is eliminated."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.include.bar_time")


def test_datetime_utilities() -> None:
    """Verify static DateTime helper arithmetic and conversions."""
    # 2025-01-06 14:30:00 UTC
    dt = datetime(2025, 1, 6, 14, 30, 15, 500000, tzinfo=UTC)
    ms = int(dt.timestamp() * 1000)

    assert DateTime.get_year(ms) == 2025
    assert DateTime.get_month(ms) == 1
    assert DateTime.get_month_original(ms) == 0
    assert DateTime.get_day(ms) == 6
    assert DateTime.get_hour(ms) == 14
    assert DateTime.get_minute(ms) == 30
    assert DateTime.get_second(ms) == 15
    assert DateTime.get_millis(ms) == 500
    assert DateTime.get_day_of_week(ms) == 1  # Monday
    assert DateTime.get_day_of_week_original(ms) == 1
    assert DateTime.get_ymd(ms) == 20250106
    assert DateTime.get_hhmm(ms) == 1430
    assert DateTime.get_days_in_month(ms) == 31
    assert DateTime.hhmm_to_minutes(1430) == 870
    assert DateTime.minutes_to_hhmm(870) == 1430
    assert DateTime.get_ts_diff_in_minutes(1430, 1500) == 30

    # Arithmetic
    plus_one_day = DateTime.add_days(ms, 1)
    assert DateTime.get_day(plus_one_day) == 7
    minus_one_hour = DateTime.add_hours(ms, -1)
    assert DateTime.get_hour(minus_one_hour) == 13


def test_bar_time_facade() -> None:
    """Verify BarTime facade methods and series outputs."""
    times = _sample_timestamps()
    bt = BarTime(times)

    assert len(bt) == 5
    # Shift 0 = latest (2025-01-31 16:30)
    assert bt.bar_date(0) == 20250131
    assert bt.bar_time(0) == 1630
    assert bt.bar_hour(0) == 16
    assert bt.bar_minute(0) == 30
    assert bt.bar_day_of_month(0) == 31
    assert bt.bar_day_of_week(0) == 5  # Friday
    assert bt.bar_month(0) == 1
    assert bt.current_bar(0) == 4

    # Series outputs
    assert len(bt.hour_series()) == 5
    assert len(bt.minute_series()) == 5
    assert len(bt.day_of_week_series()) == 5
    assert len(bt.month_series()) == 5


def test_time_conditions_facade() -> None:
    """Verify TimeConditions condition predicates."""
    times = _sample_timestamps()
    bt = BarTime(times)
    tc = TimeConditions(bt, is_bar_open=True)

    assert tc.always_true() is True
    assert tc.always_false() is False
    assert tc.is_bar_open() is True
    assert tc.bar_hour_is(16, shift=0) is True
    assert tc.bar_hour_is_bigger(15, shift=0) is True
    assert tc.bar_hour_is_smaller(17, shift=0) is True
    assert tc.bar_minute_is(30, shift=0) is True
    assert tc.bar_day_of_week_is(5, shift=0) is True
    assert tc.bar_day_of_week_is_not(1, shift=0) is True
    assert tc.bar_month_is(1, shift=0) is True
    assert tc.bar_time_is(1630, shift=0) is True
    assert tc.bar_time_is(16, 30, shift=0) is True
    assert tc.last_week_of_month(shift=0) is True
    assert tc.first_week_of_month(shift=4) is True  # Shift 4 = 2025-01-01
    assert tc.is_month_last_trading_day(shift=0) is True
    assert tc.is_month_first_trading_day(shift=4) is True


def test_discrete_value_blocks() -> None:
    """Verify each discrete value block independently."""
    times = _sample_timestamps()

    # Shift 0 is 2025-01-31 16:30:00 (Friday)
    assert bar_date(times, 0) == 20250131
    assert bar_day_of_month(times, 0) == 31
    assert bar_day_of_week(times, 0) == 5
    assert bar_hour(times, 0) == 16
    assert bar_minute(times, 0) == 30
    assert bar_month(times, 0) == 1
    assert bar_time(times, 0) == 1630
    assert current_bar(times, 0) == 4
    assert bar_week_of_month(times, 4) == 1

    # Current value blocks with context
    assert current_date(times) == 20250131
    assert current_day_of_week(times) == 5
    assert current_hour(times) == 16
    assert current_minute(times) == 30
    assert current_month(times) == 1
    assert current_time(times) == 1630


def test_discrete_condition_blocks() -> None:
    """Verify each discrete condition block independently."""
    times = _sample_timestamps()

    assert always_true() is True
    assert always_false() is False
    assert is_bar_open(is_open=True) is True
    assert is_bar_open(is_open=False) is False

    assert bar_day_of_week_is(times, 5, 0) is True
    assert bar_day_of_week_is_not(times, 1, 0) is True
    assert bar_hour_is(times, 16, 0) is True
    assert bar_hour_is_bigger(times, 15, 0) is True
    assert bar_hour_is_smaller(times, 17, 0) is True
    assert bar_minute_is(times, 30, 0) is True
    assert bar_month_is(times, 1, 0) is True
    assert bar_month_is_not(times, 2, 0) is True
    assert bar_time_is(times, 1630, shift=0) is True
    assert bar_time_is(times, 16, 30, shift=0) is True

    assert current_day_of_week_is(times, 5) is True
    assert current_hour_is(times, 16) is True
    assert current_minute_is(times, 30) is True
    assert current_month_is(times, 1) is True
    assert current_time_is(times, 1630) is True

    assert first_week_of_month(times, 4) is True
    assert last_week_of_month(times, 0) is True
    assert is_month_first_trading_day(times, 4) is True
    assert is_month_last_trading_day(times, 0) is True


def test_block_specs_and_registry() -> None:
    """Verify all 37 block specs and their registration in BlockRegistry."""
    specs: list[BlockSpec] = [
        always_false_spec,
        always_true_spec,
        bar_date_spec,
        bar_day_of_month_spec,
        bar_day_of_week_spec,
        bar_day_of_week_is_spec,
        bar_day_of_week_is_not_spec,
        bar_hour_spec,
        bar_hour_is_spec,
        bar_hour_is_bigger_spec,
        bar_hour_is_smaller_spec,
        bar_minute_spec,
        bar_minute_is_spec,
        bar_month_spec,
        bar_month_is_spec,
        bar_month_is_not_spec,
        bar_time_spec,
        bar_time_is_spec,
        bar_week_of_month_spec,
        current_bar_spec,
        current_date_spec,
        current_day_of_week_spec,
        current_day_of_week_is_spec,
        current_hour_spec,
        current_hour_is_spec,
        current_minute_spec,
        current_minute_is_spec,
        current_month_spec,
        current_month_is_spec,
        current_time_spec,
        current_time_is_spec,
        current_week_of_month_spec,
        first_week_of_month_spec,
        is_bar_open_spec,
        is_month_first_trading_day_spec,
        is_month_last_trading_day_spec,
        last_week_of_month_spec,
    ]

    assert len(specs) == 37
    for spec in specs:
        assert isinstance(spec, BlockSpec)
        assert spec.category == "bar_time"
        assert spec.execution_kind in (
            ExecutionKind.EXPRESSION,
            ExecutionKind.CONDITION,
        )
        assert len(spec.outputs) == 1
        assert spec.outputs[0].port_type in (PortType.NUMBER, PortType.BOOLEAN)

    # Verify callable registration into block_registry
    desc = block_registry.register_block(bar_date)
    assert desc.spec.id == bar_date_spec.id
    assert block_registry.get(bar_date_spec.id) is not None
