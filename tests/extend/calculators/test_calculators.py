"""Unit tests for streaming rolling calculators under app.extend.calculators.

FEAT-CALCULATORS: Stateful streaming window calculators and batch kernels.
FR-CALC-BUFFER, FR-CALC-AVERAGE, FR-CALC-HIGHEST, FR-CALC-LOWEST, FR-CALC-RSI,
FR-CALC-STDDEV, FR-CALC-SUM.
"""

from __future__ import annotations

import math
from typing import override

import numpy as np
import pytest
from app.core.data.contracts import DataframeSeries
from app.extend.calculators import (
    AbstractCalculator,
    AverageCalculator,
    AverageType,
    CalculatorError,
    HighestCalculator,
    LowestCalculator,
    RSICalculator,
    StdDevCalculator,
    SumCalculator,
    centered_deviation,
    ema_kernel,
    lwma_kernel,
    rolling_highest,
    rolling_lowest,
    rsi_kernel,
    sma_kernel,
    smma_kernel,
    std_dev_kernel,
    tema_kernel,
    time_window_highest,
    time_window_lowest,
)
from app.extend.calculators.base import to_numpy
from app.extend.calculators.highest import (
    rolling_extreme as rolling_extreme_h,
)
from app.extend.calculators.highest import (
    time_window_extreme as time_window_extreme_h,
)
from app.extend.calculators.highest import (
    validate_hhmm,
)
from app.extend.calculators.lowest import (
    rolling_extreme as rolling_extreme_l,
)
from app.extend.calculators.lowest import (
    time_window_extreme as time_window_extreme_l,
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
    sma = AverageCalculator(AverageType.SMA, period=3, average_precision=50)
    values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
    for bar_idx, val in enumerate(values):
        sma.on_bar_update(val, bar_idx)

    assert sma.get_value() == pytest.approx(50.0)


def test_average_calculator_ema() -> None:
    """Test EMA calculation matching standard exponential decay."""
    period = 3
    ema = AverageCalculator(AverageType.EMA, period=period)

    ema.on_bar_update(10.0, 0)
    assert ema.get_value() == 10.0

    ema.on_bar_update(20.0, 1)
    assert ema.get_value() == pytest.approx(15.0)

    ema.on_bar_update(40.0, 2)
    assert ema.get_value() == pytest.approx(27.5)


def test_average_calculator_smma() -> None:
    """Test SMMA (Wilder's smoothing) lifecycle."""
    smma = AverageCalculator(AverageType.SMMA, period=3)

    smma.on_bar_update(10.0, 0)
    smma.on_bar_update(20.0, 1)
    assert smma.get_value() == 20.0

    smma.on_bar_update(50.0, 2)
    assert smma.get_value() == pytest.approx(30.0)


def test_average_calculator_lwma() -> None:
    """Test LWMA linear weighted calculation matching donor window bounds."""
    lwma = AverageCalculator(AverageType.LWMA, period=3)

    lwma.on_bar_update(10.0, 0)
    assert lwma.get_value() == 10.0

    lwma.on_bar_update(20.0, 1)
    assert lwma.get_value() == pytest.approx(20.0)

    lwma.on_bar_update(30.0, 2)
    assert lwma.get_value() == pytest.approx((30.0 * 3 + 20.0 * 2) / 5)

    lwma.on_bar_update(40.0, 3)
    assert lwma.get_value() == pytest.approx((40.0 * 3 + 30.0 * 2 + 20.0 * 1) / 6)


def test_average_calculator_validation() -> None:
    """Test invalid MA types and negative precision handling."""
    with pytest.raises(CalculatorError):
        AverageCalculator(99, 14)

    calc = AverageCalculator(AverageType.SMA, 14, average_precision=-10)
    assert calc.average_precision == 0


def test_highest_calculator() -> None:
    """Test rolling highest value and index tracking."""
    highest = HighestCalculator(period=3)

    highest.on_bar_update(10.0, 0)
    assert highest.get_highest_value() == 10.0
    assert highest.get_highest_index() == 0
    assert highest.get_value() == 10.0

    highest.on_bar_update(25.0, 1)
    assert highest.get_highest_value() == 25.0
    assert highest.get_highest_index() == 0

    highest.on_bar_update(15.0, 2)
    assert highest.get_highest_value() == 25.0
    assert highest.get_highest_index() == 1

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

    # Intra-bar rewrite: price drops to 7.0 on same bar -> scans buffer
    highest.on_bar_update(7.0, 4)
    assert highest.get_highest_value() == 15.0
    assert highest.get_highest_index() == 2


def test_lowest_calculator() -> None:
    """Test rolling lowest value and index tracking."""
    lowest = LowestCalculator(period=3)

    lowest.on_bar_update(50.0, 0)
    assert lowest.get_lowest_value() == 50.0
    assert lowest.get_lowest_index() == 0
    assert lowest.get_value() == 50.0

    lowest.on_bar_update(20.0, 1)
    assert lowest.get_lowest_value() == 20.0
    assert lowest.get_lowest_index() == 0

    lowest.on_bar_update(35.0, 2)
    assert lowest.get_lowest_value() == 20.0
    assert lowest.get_lowest_index() == 1

    lowest.on_bar_update(40.0, 3)
    assert lowest.get_lowest_value() == 20.0
    assert lowest.get_lowest_index() == 2

    # Bar 4: 20.0 expires! Window is [35.0, 40.0, 60.0]. Min is 35.0 at lag 2
    lowest.on_bar_update(60.0, 4)
    assert lowest.get_lowest_value() == 35.0
    assert lowest.get_lowest_index() == 2

    # Intra-bar rewrite: price drops to 10.0 on same bar
    lowest.on_bar_update(10.0, 4)
    assert lowest.get_lowest_value() == 10.0
    assert lowest.get_lowest_index() == 0

    # Intra-bar rewrite: price rises to 70.0 on same bar -> scans buffer
    lowest.on_bar_update(70.0, 4)
    assert lowest.get_lowest_value() == 35.0
    assert lowest.get_lowest_index() == 2


def test_rsi_calculator() -> None:
    """Test RSI streaming calculations including boundary values."""
    rsi = RSICalculator(period=3)

    rsi.on_bar_update(100.0, 0)
    assert rsi.get_value() == 0.0

    rsi.on_bar_update(105.0, 1)
    rsi.on_bar_update(110.0, 2)
    rsi.on_bar_update(115.0, 3)
    assert rsi.get_value() == pytest.approx(100.0)

    rsi.on_bar_update(110.0, 4)
    val = rsi.get_value()
    assert 0.0 < val < 100.0

    # Test flat price movement -> rsi 50
    flat_rsi = RSICalculator(period=2)
    flat_rsi.on_bar_update(50.0, 0)
    flat_rsi.on_bar_update(50.0, 1)
    flat_rsi.on_bar_update(50.0, 2)
    assert flat_rsi.get_value() == pytest.approx(50.0)


def test_std_dev_calculator() -> None:
    """Test rolling population standard deviation calculation."""
    std = StdDevCalculator(period=3)

    std.on_bar_update(10.0, 0)
    assert std.get_value() == 0.0

    std.on_bar_update(20.0, 1)
    assert std.get_value() == pytest.approx(5.0)

    std.on_bar_update(30.0, 2)
    assert std.get_value() == pytest.approx(math.sqrt(200.0 / 3.0))

    std.on_bar_update(40.0, 3)
    assert std.get_value() == pytest.approx(math.sqrt(200.0 / 3.0))


def test_sum_calculator() -> None:
    """Test rolling sum with O(1) sliding window."""
    rolling_sum = SumCalculator(period=3)

    rolling_sum.on_bar_update(10.0, 0)
    assert rolling_sum.get_value() == 10.0

    rolling_sum.on_bar_update(20.0, 1)
    assert rolling_sum.get_value() == 30.0

    rolling_sum.on_bar_update(25.0, 1)
    assert rolling_sum.get_value() == 35.0

    rolling_sum.on_bar_update(15.0, 2)
    assert rolling_sum.get_value() == 50.0

    rolling_sum.on_bar_update(30.0, 3)
    assert rolling_sum.get_value() == 70.0


def test_moving_average_batch_kernels() -> None:
    """Test vectorized batch kernels: SMA, EMA, SMMA, LWMA, TEMA."""
    data = [10.0, 20.0, 30.0, 40.0, 50.0]

    # SMA
    sma = sma_kernel(data, 3)
    assert np.isnan(sma[0]) and np.isnan(sma[1])
    assert sma[2] == pytest.approx(20.0)
    assert sma[3] == pytest.approx(30.0)
    assert sma[4] == pytest.approx(40.0)

    # Empty / invalid
    assert np.all(np.isnan(sma_kernel([], 3)))
    assert np.all(np.isnan(sma_kernel(data, 0)))
    assert np.all(np.isnan(sma_kernel(data, 10)))

    # EMA
    ema = ema_kernel(data, 3)
    assert np.isnan(ema[0]) and np.isnan(ema[1])
    assert ema[2] == pytest.approx(20.0)
    assert not np.isnan(ema[3])

    assert np.all(np.isnan(ema_kernel([], 3)))
    assert np.all(np.isnan(ema_kernel(data, 0)))

    # SMMA
    smma = smma_kernel(data, 3)
    assert np.isnan(smma[0]) and np.isnan(smma[1])
    assert smma[2] == pytest.approx(20.0)

    assert np.all(np.isnan(smma_kernel([], 3)))
    assert np.all(np.isnan(smma_kernel(data, 0)))

    # LWMA
    lwma = lwma_kernel(data, 3)
    assert np.isnan(lwma[0]) and np.isnan(lwma[1])
    # [10, 20, 30] * [1, 2, 3] = (10 + 40 + 90) / 6 = 140 / 6 = 23.3333
    assert lwma[2] == pytest.approx(140.0 / 6.0)

    assert np.all(np.isnan(lwma_kernel([], 3)))
    assert np.all(np.isnan(lwma_kernel(data, 0)))

    # TEMA
    tema = tema_kernel(data, 2)
    assert not np.isnan(tema[-1])
    assert np.all(np.isnan(tema_kernel([], 2)))
    assert np.all(np.isnan(tema_kernel(data, 0)))
    assert np.all(np.isnan(tema_kernel(data, 10)))


def test_extrema_batch_and_time_window() -> None:
    """Test batch rolling extrema and time window filters."""
    vals = np.array([10.0, 50.0, 30.0, 20.0, 60.0])
    highs = rolling_highest(vals, 3)
    assert highs[0] == 10.0
    assert highs[1] == 50.0
    assert highs[2] == 50.0
    assert highs[3] == 50.0
    assert highs[4] == 60.0

    lows = rolling_lowest(vals, 3)
    assert lows[0] == 10.0
    assert lows[1] == 10.0
    assert lows[2] == 10.0
    assert lows[3] == 20.0
    assert lows[4] == 20.0

    # Extreme wrapper functions
    assert np.array_equal(rolling_extreme_h(vals, 3), highs)
    assert np.array_equal(rolling_extreme_l(vals, 3), lows)

    # HHMM validation
    assert validate_hhmm(0) == 0
    assert validate_hhmm(2359) == 2359
    assert validate_hhmm(1230) == 1230
    with pytest.raises(ValueError, match="valid HHMM"):
        validate_hhmm(-1)
    with pytest.raises(ValueError, match="valid HHMM"):
        validate_hhmm(2400)
    with pytest.raises(ValueError, match="valid HHMM"):
        validate_hhmm(1260)

    # Time window extreme
    timestamps = np.array([1700000000, 1700003600, 1700007200], dtype=np.int64)
    prices = np.array([100.0, 105.0, 95.0])
    win_h = time_window_highest(timestamps, prices, time_from=0, time_to=2359)
    assert len(win_h) == 3
    win_l = time_window_lowest(timestamps, prices, time_from=0, time_to=2359)
    assert len(win_l) == 3

    assert np.array_equal(
        time_window_extreme_h(timestamps, prices, time_from=0, time_to=2359),
        win_h,
    )
    assert np.array_equal(
        time_window_extreme_l(timestamps, prices, time_from=0, time_to=2359),
        win_l,
    )

    with pytest.raises(ValueError, match="aligned"):
        time_window_highest(timestamps[:2], prices, time_from=0, time_to=2359)
    with pytest.raises(ValueError, match="strictly increasing"):
        time_window_highest(
            np.array([100, 100, 100]), prices, time_from=0, time_to=2359
        )
    with pytest.raises(ValueError, match="finite"):
        time_window_highest(
            timestamps, np.array([1.0, np.nan, 3.0]), time_from=0, time_to=2359
        )


def test_rsi_kernel() -> None:
    """Test rsi_kernel with standard, empty, and invalid inputs."""
    data = [100.0, 102.0, 101.0, 104.0, 103.0, 106.0]
    out = rsi_kernel(data, 3)
    assert np.isnan(out[0]) and np.isnan(out[1]) and np.isnan(out[2])
    assert not np.isnan(out[3])

    assert np.all(np.isnan(rsi_kernel([], 3)))
    assert np.all(np.isnan(rsi_kernel(data, 0)))
    assert np.all(np.isnan(rsi_kernel(data, 10)))


def test_std_dev_kernel_and_centered_deviation() -> None:
    """Test centered deviation and std dev kernel batch formulas."""
    vals = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    centers = np.array([10.0, 15.0, 20.0, 25.0, 30.0])

    dev = centered_deviation(vals, centers, 3)
    assert len(dev) == 5
    assert not np.isnan(dev).any()

    dev_fixed = centered_deviation(vals, centers, 3, fixed_divisor=True)
    assert len(dev_fixed) == 5

    res = std_dev_kernel(vals, 3)
    assert len(res) == 5


def test_to_numpy_conversion() -> None:
    """Test to_numpy with numpy array, list, and DataframeSeries."""
    arr = np.array([1.0, 2.0, 3.0])
    assert np.array_equal(to_numpy(arr), arr)

    lst = [1.0, 2.0]
    assert isinstance(to_numpy(lst), np.ndarray)

    dfs = DataframeSeries(np.array([5.0, 6.0]), name="close")
    assert np.array_equal(to_numpy(dfs), np.array([5.0, 6.0]))
