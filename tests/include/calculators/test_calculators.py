"""Unit tests for streaming rolling calculators under app.include.calculators.

FEAT-INC-CALCULATORS: Stateful streaming window calculators.
FR-CALC-BUFFER, FR-CALC-AVERAGE, FR-CALC-EXTREMA, FR-CALC-RSI, FR-CALC-STDDEV, FR-CALC-SUM.
"""

from __future__ import annotations

import math
from typing import override

import pytest
from app.include.calculators import (
    AbstractCalculator,
    AverageCalculator,
    AverageType,
    CalculatorError,
    HighestCalculator,
    LowestCalculator,
    RSICalculator,
    StdDevCalculator,
    SumCalculator,
)


class DummyCalculator(AbstractCalculator):
    """Concrete calculator for testing base ring-buffer mechanics."""

    def __init__(self, period: int) -> None:
        super().__init__(period)
        self.recorded_updates: list[tuple[float, bool]] = []

    @override
    def _calculate(self, new_value: float, is_same_bar: bool) -> None:
        self.recorded_updates.append((new_value, is_same_bar))

    @override
    def get_value(self) -> float:
        return self.buffer_get(0)


def test_abstract_calculator_period_fallback() -> None:
    """Ensure period <= 0 defaults to 2."""
    calc_zero = DummyCalculator(0)
    assert calc_zero.period == 2
    assert calc_zero.buffer_length() == 2

    calc_neg = DummyCalculator(-5)
    assert calc_neg.period == 2


def test_abstract_calculator_buffer_and_lifecycle() -> None:
    """Test ring buffer indexing, intra-bar rewrite, and bar transitions."""
    calc = DummyCalculator(3)

    # Bar 0, first tick
    calc.on_bar_update(10.0, current_bar=0)
    assert calc.buffer_get(0) == 10.0
    assert calc.old_buffer_value == 0.0
    assert calc.average_buffer_get() == 10.0

    # Bar 0, second tick (intra-bar overwrite)
    calc.on_bar_update(12.0, current_bar=0)
    assert calc.buffer_get(0) == 12.0
    assert calc.average_buffer_get() == 12.0
    assert calc.recorded_updates[-1] == (12.0, True)

    # Bar 1 (new bar advance)
    calc.on_bar_update(20.0, current_bar=1)
    assert calc.buffer_get(0) == 20.0
    assert calc.buffer_get(1) == 12.0
    assert calc.average_buffer_get() == pytest.approx((12.0 + 20.0) / 2)
    assert calc.recorded_updates[-1] == (20.0, False)

    # Bar 2
    calc.on_bar_update(30.0, current_bar=2)
    assert calc.buffer_get(0) == 30.0
    assert calc.buffer_get(1) == 20.0
    assert calc.buffer_get(2) == 12.0
    assert calc.average_buffer_get() == pytest.approx((12.0 + 20.0 + 30.0) / 3)

    # Bar 3: pushes 12.0 out of period-3 buffer
    calc.on_bar_update(40.0, current_bar=3)
    assert calc.buffer_get(0) == 40.0
    assert calc.buffer_get(1) == 30.0
    assert calc.buffer_get(2) == 20.0
    assert calc.old_buffer_value == 12.0
    assert calc.average_buffer_get() == pytest.approx((20.0 + 30.0 + 40.0) / 3)


def test_average_calculator_sma() -> None:
    """Test SMA calculations across warmup, full window, and intra-bar updates."""
    sma = AverageCalculator(AverageType.SMA, period=3)

    sma.on_bar_update(10.0, 0)
    assert sma.get_value() == 10.0

    sma.on_bar_update(20.0, 1)
    assert sma.get_value() == pytest.approx(15.0)

    # Intra-bar correction on bar 1
    sma.on_bar_update(30.0, 1)
    assert sma.get_value() == pytest.approx(20.0)

    # Bar 2: window full
    sma.on_bar_update(50.0, 2)
    assert sma.get_value() == pytest.approx((10.0 + 30.0 + 50.0) / 3)

    # Bar 3: drops 10.0, adds 70.0 -> (30 + 50 + 70)/3 = 50.0
    sma.on_bar_update(70.0, 3)
    assert sma.get_value() == pytest.approx(50.0)


def test_average_calculator_sma_precision_reset() -> None:
    """Test SMA periodic drift reset using average_precision."""
    # period=10, precision=20 -> reset every (10 * 20)//100 = 2 bars
    sma = AverageCalculator(AverageType.SMA, period=3, average_precision=50)
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
    for bar_idx, val in enumerate(values):
        sma.on_bar_update(val, bar_idx)

    # Window of last 3: 40, 50, 60 -> mean 50.0
    assert sma.get_value() == pytest.approx(50.0)


def test_average_calculator_ema() -> None:
    """Test EMA calculation matching standard exponential decay."""
    period = 3
    ema = AverageCalculator(AverageType.EMA, period=period)

    ema.on_bar_update(10.0, 0)
    assert ema.get_value() == 10.0

    # bar 1: 20 * 0.5 + 10 * 0.5 = 15.0
    ema.on_bar_update(20.0, 1)
    assert ema.get_value() == pytest.approx(15.0)

    # bar 2: 40 * 0.5 + 15 * 0.5 = 27.5
    ema.on_bar_update(40.0, 2)
    assert ema.get_value() == pytest.approx(27.5)


def test_average_calculator_smma() -> None:
    """Test SMMA (Wilder's smoothing) lifecycle."""
    smma = AverageCalculator(AverageType.SMMA, period=3)

    smma.on_bar_update(10.0, 0)
    # At bar 1, SMMA sets currentValue = newValue
    smma.on_bar_update(20.0, 1)
    assert smma.get_value() == 20.0

    # bar 2: (20 * 2 + 50) / 3 = 90 / 3 = 30.0
    smma.on_bar_update(50.0, 2)
    assert smma.get_value() == pytest.approx(30.0)


def test_average_calculator_lwma() -> None:
    """Test LWMA linear weighted calculation matching donor window bounds."""
    lwma = AverageCalculator(AverageType.LWMA, period=3)

    lwma.on_bar_update(10.0, 0)
    assert lwma.get_value() == 10.0

    # bar 1: max = min(3, 1) = 1. Only lag 0 included -> weight 3 / divider 3 = 20.0
    lwma.on_bar_update(20.0, 1)
    assert lwma.get_value() == pytest.approx(20.0)

    # bar 2: max = min(3, 2) = 2. Lag 0 (30.0) * 3 + Lag 1 (20.0) * 2 = 130.0 / 5 = 26.0
    lwma.on_bar_update(30.0, 2)
    assert lwma.get_value() == pytest.approx((30.0 * 3 + 20.0 * 2) / 5)

    # bar 3: max = min(3, 3) = 3. Lag 0 (40.0)*3 + Lag 1 (30.0)*2 + Lag 2 (20.0)*1 = 200 / 6
    lwma.on_bar_update(40.0, 3)
    assert lwma.get_value() == pytest.approx((40.0 * 3 + 30.0 * 2 + 20.0 * 1) / 6)


def test_average_calculator_validation() -> None:
    """Test invalid MA types and negative precision handling."""
    with pytest.raises(CalculatorError):
        AverageCalculator(99, 14)

    # Negative precision clamped to 0
    calc = AverageCalculator(AverageType.SMA, 14, average_precision=-10)
    assert calc.average_precision == 0


def test_highest_calculator() -> None:
    """Test rolling highest value and index tracking."""
    highest = HighestCalculator(period=3)

    highest.on_bar_update(10.0, 0)
    assert highest.get_highest_value() == 10.0
    assert highest.get_highest_index() == 0

    highest.on_bar_update(25.0, 1)
    assert highest.get_highest_value() == 25.0
    assert highest.get_highest_index() == 0

    highest.on_bar_update(15.0, 2)
    assert highest.get_highest_value() == 25.0
    assert highest.get_highest_index() == 1

    # Bar 3: 5.0 added. 25.0 (at bar 1, lag 2) is still in period 3
    highest.on_bar_update(5.0, 3)
    assert highest.get_highest_value() == 25.0
    assert highest.get_highest_index() == 2

    # Bar 4: 8.0 added. 25.0 expires! Window is [15.0, 5.0, 8.0]. Max is 15.0 at lag 2
    highest.on_bar_update(8.0, 4)
    assert highest.get_highest_value() == 15.0
    assert highest.get_highest_index() == 2

    # Intra-bar rewrite: on bar 4, price spikes to 30.0
    highest.on_bar_update(30.0, 4)
    assert highest.get_highest_value() == 30.0
    assert highest.get_highest_index() == 0


def test_lowest_calculator() -> None:
    """Test rolling lowest value and index tracking."""
    lowest = LowestCalculator(period=3)

    lowest.on_bar_update(50.0, 0)
    assert lowest.get_lowest_value() == 50.0
    assert lowest.get_lowest_index() == 0

    lowest.on_bar_update(20.0, 1)
    assert lowest.get_lowest_value() == 20.0
    assert lowest.get_lowest_index() == 0

    lowest.on_bar_update(35.0, 2)
    assert lowest.get_lowest_value() == 20.0
    assert lowest.get_lowest_index() == 1

    # Bar 3: 40.0 added. 20.0 is at lag 2
    lowest.on_bar_update(40.0, 3)
    assert lowest.get_lowest_value() == 20.0
    assert lowest.get_lowest_index() == 2

    # Bar 4: 20.0 expires! Window is [35.0, 40.0, 60.0]. Min is 35.0 at lag 2
    lowest.on_bar_update(60.0, 4)
    assert lowest.get_lowest_value() == 35.0
    assert lowest.get_lowest_index() == 2


def test_rsi_calculator() -> None:
    """Test RSI streaming calculations including boundary values."""
    rsi = RSICalculator(period=3)

    # Bar 0: warmup
    rsi.on_bar_update(100.0, 0)
    assert rsi.get_value() == 0.0

    # Bar 1-3: strictly upward price movement
    rsi.on_bar_update(105.0, 1)
    rsi.on_bar_update(110.0, 2)
    rsi.on_bar_update(115.0, 3)  # current_bar == period -> triggers first SMA
    assert rsi.get_value() == pytest.approx(100.0)

    # Bar 4: slight drop
    rsi.on_bar_update(110.0, 4)
    val = rsi.get_value()
    assert 0.0 < val < 100.0


def test_std_dev_calculator() -> None:
    """Test rolling population standard deviation calculation."""
    std = StdDevCalculator(period=3)

    std.on_bar_update(10.0, 0)
    assert std.get_value() == 0.0

    # Window [10, 20]: mean 15. Deviations: -5, +5. variance = (25 + 25) / 2 = 25 -> std = 5.0
    std.on_bar_update(20.0, 1)
    assert std.get_value() == pytest.approx(5.0)

    # Window [10, 20, 30]: mean 20. Deviations: -10, 0, 10. variance = (100 + 0 + 100) / 3 = 66.666667 -> std = sqrt(200/3)
    std.on_bar_update(30.0, 2)
    assert std.get_value() == pytest.approx(math.sqrt(200.0 / 3.0))

    # Window [20, 30, 40]: mean 30. std = sqrt(200/3)
    std.on_bar_update(40.0, 3)
    assert std.get_value() == pytest.approx(math.sqrt(200.0 / 3.0))


def test_sum_calculator() -> None:
    """Test rolling sum with O(1) sliding window."""
    rolling_sum = SumCalculator(period=3)

    rolling_sum.on_bar_update(10.0, 0)
    assert rolling_sum.get_value() == 10.0

    rolling_sum.on_bar_update(20.0, 1)
    assert rolling_sum.get_value() == 30.0

    # Intra-bar rewrite
    rolling_sum.on_bar_update(25.0, 1)
    assert rolling_sum.get_value() == 35.0

    # Bar 2
    rolling_sum.on_bar_update(15.0, 2)
    assert rolling_sum.get_value() == 50.0  # 10 + 25 + 15

    # Bar 3: drops 10.0, adds 30.0 -> 50 - 10 + 30 = 70.0
    rolling_sum.on_bar_update(30.0, 3)
    assert rolling_sum.get_value() == 70.0
