"""Shift, reserve, change callback and integer-precision series regression tests."""

import pytest
from app.core.data.series import DataSeries, TimeDataSeries


def test_reverse_history_and_missing_bars() -> None:
    data = DataSeries("close")
    data.add(1.0)
    data.add(2.0)
    assert data.name == "close"
    assert data.get(0) == 2.0
    assert data.get(1) == 1.0
    assert data.get(2) == 0.0
    with pytest.raises(ValueError, match="Index cannot be smaller"):
        data.get(-1)
    data.set(0, 0.0000000000000000001)
    assert data.get(0) == 0.0
    data.set(100, 44.0)
    assert data.size() == 2


def test_shift_and_listeners() -> None:
    data = DataSeries()
    bars: list[tuple[int, int]] = []
    ticks: list[tuple[int, int]] = []
    data.on_bar_change(lambda a, b: bars.append((a, b)))
    data.on_tick_change(lambda a, b: ticks.append((a, b)))
    data.add_values(3)
    data.set_shift(1)
    data.set(0, 5.0)
    assert data.size() == 2
    assert data.special_size() == 3
    assert data.get(0) == 5.0
    assert (1, 3) in bars and (1, 3) in ticks
    with pytest.raises(ValueError, match="Shift must be 0"):
        data.add(7.0)
    data.add_values(2)
    assert data.size() == 4
    with pytest.raises(ValueError):
        data.set_shift(-1)


def test_long_timestamps_not_converted_to_float() -> None:
    series = TimeDataSeries("time")
    precise = 2**53 + 13
    series.add(precise)
    assert series.get(0) == precise
    with pytest.raises(TypeError):
        series.add(1.5)  # type: ignore[arg-type]
