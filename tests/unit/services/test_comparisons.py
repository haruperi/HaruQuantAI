"""Unit test suite for StrategyQuant X comparison building blocks.

Description:
    Tests verification of arithmetic comparisons, crossovers, multi-bar
    directional trends, multi-bar count persistence, historical percentile
    rankings, indicator-to-MA smoothing, compound boolean logic, and the
    Comparisons facade matching StrategyQuant X Comparison snippets.

Purpose:
    FEAT-SERVICES-COMPARISON-TESTS: Comprehensive test coverage for comparison
    building blocks.

Key Capabilities:
    - FR-SERVICES-TEST-COMPARISONS: Assert exact calculations, rounding,
      short-circuiting, and edge-case error bounds.
      Associated: `test_resolve_and_round()`, `test_basic_comparisons()`,
        `test_crossovers()`, `test_trend_persistence()`,
        `test_count_persistence()`, `test_percentile_rankings()`,
        `test_indicator_moving_averages()`, `test_logical_combinators()`,
        `test_comparisons_facade()`.
      Logging: DEBUG on test execution.

Python API Usage:
    ```python
    uv run pytest tests/unit/services/test_comparisons.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_comparisons.py --no-cov
    ```
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from app.services.indicators.base import IndicatorSeries
from app.services.utils.comparisons import (
    Comparisons,
    MAType,
    calculate_ma,
    calculate_wma,
    condition_and,
    condition_not,
    condition_or,
    crosses_above,
    crosses_below,
    equals,
    indicator_above_ma,
    indicator_below_ma,
    indicator_crosses_above_ma,
    indicator_crosses_below_ma,
    is_falling,
    is_greater,
    is_greater_count,
    is_greater_or_equal,
    is_greater_percentile,
    is_lower,
    is_lower_count,
    is_lower_or_equal,
    is_lower_percentile,
    is_rising,
    not_equals,
    resolve_shift_value,
    round_value,
)


def test_resolve_and_round() -> None:
    """Verify resolve_shift_value and round_value with various operand types."""
    # Rounding
    assert round_value(1.1234567, 6) == 1.123457
    assert round_value(1.1234543, 6) == 1.123454
    assert math.isnan(round_value(float("nan"), 6))

    # Scalars
    assert resolve_shift_value(42.5) == 42.5
    assert resolve_shift_value(10) == 10.0
    assert resolve_shift_value(np.float64(3.14)) == pytest.approx(3.14)

    # Lists / Sequences (shift 0 is newest / last element)
    seq = [10.0, 20.0, 30.0]
    assert resolve_shift_value(seq, shift=0) == 30.0
    assert resolve_shift_value(seq, shift=1) == 20.0
    assert resolve_shift_value(seq, shift=2) == 10.0
    assert math.isnan(resolve_shift_value(seq, shift=3))
    assert math.isnan(resolve_shift_value(seq, shift=-1))
    assert math.isnan(resolve_shift_value([], shift=0))

    # NumPy arrays
    arr = np.array([100.0, 200.0, 300.0])
    assert resolve_shift_value(arr, shift=0) == 300.0
    assert resolve_shift_value(arr, shift=1) == 200.0

    # IndicatorSeries
    series = IndicatorSeries(np.array([1.0, 2.0, 3.0]))
    assert resolve_shift_value(series, shift=0) == 3.0
    assert resolve_shift_value(series, shift=1) == 2.0
    assert math.isnan(resolve_shift_value(series, shift=5))

    # Callables
    assert resolve_shift_value(lambda s: s * 10.0, shift=2) == 20.0
    assert resolve_shift_value(lambda: 99.0, shift=0) == 99.0

    # Invalid string / object
    assert math.isnan(resolve_shift_value("invalid"))


def test_basic_comparisons() -> None:
    """Verify basic arithmetic comparisons with precision rounding and bounds."""
    # Strict greater / lower
    assert is_greater(10.000001, 10.0, precision=6)
    assert not is_greater(10.0000004, 10.0, precision=6)
    assert is_lower(9.999999, 10.0, precision=6)
    assert not is_lower(10.0, 9.999999, precision=6)

    # Greater or equal / lower or equal
    assert is_greater_or_equal(10.0, 10.0, precision=6)
    assert is_greater_or_equal(10.0000004, 10.0, precision=6)
    assert is_lower_or_equal(10.0, 10.0, precision=6)
    assert is_lower_or_equal(9.9999996, 10.0, precision=6)

    # Equals / Not equals
    assert equals(1.234567, 1.2345674, precision=6)
    assert not equals(1.234567, 1.234568, precision=6)
    assert not_equals(1.234567, 1.234568, precision=6)
    assert not not_equals(1.234567, 1.2345674, precision=6)

    # NaN / boundary conditions return False
    assert not is_greater(float("nan"), 10.0)
    assert not is_lower(10.0, float("nan"))
    assert not is_greater_or_equal(float("nan"), float("nan"))
    assert not is_lower_or_equal(float("nan"), 10.0)
    assert not equals(float("nan"), float("nan"))
    assert not not_equals(float("nan"), 10.0)


def test_crossovers() -> None:
    """Verify crosses_above and crosses_below conditions."""
    left = np.array([10.0, 12.0, 15.0])
    right = np.array([10.0, 13.0, 14.0])

    # At shift=0: prev (shift 1) left=12 < right=13; curr (shift 0) left=15 > right=14
    assert crosses_above(left, right, shift=0)
    assert not crosses_below(left, right, shift=0)

    # Inverted
    left_inv = np.array([10.0, 13.0, 14.0])
    right_inv = np.array([10.0, 12.0, 15.0])
    assert crosses_below(left_inv, right_inv, shift=0)
    assert not crosses_above(left_inv, right_inv, shift=0)

    # Non-crossing (both above or equal)
    left_same = np.array([10.0, 14.0, 15.0])
    right_same = np.array([10.0, 12.0, 13.0])
    assert not crosses_above(left_same, right_same, shift=0)
    assert not crosses_below(left_same, right_same, shift=0)

    # Out of bounds / NaN
    assert not crosses_above(left, right, shift=2)  # shift+1=3 is out of bounds
    assert not crosses_below(left, right, shift=2)


def test_trend_persistence() -> None:
    """Verify is_rising and is_falling trend progression."""
    # Chronological: oldest to newest
    # [10, 12, 15] is rising
    rising_arr = np.array([10.0, 12.0, 15.0])
    assert is_rising(rising_arr, bars=3, shift=0)
    assert not is_falling(rising_arr, bars=3, shift=0)

    # [15, 12, 10] is falling
    falling_arr = np.array([15.0, 12.0, 10.0])
    assert is_falling(falling_arr, bars=3, shift=0)
    assert not is_rising(falling_arr, bars=3, shift=0)

    # Flat sequence [10, 10, 10]: strict=False, not_strict=True must both be False
    # because it must rise/fall at least once!
    flat_arr = np.array([10.0, 10.0, 10.0])
    assert not is_rising(flat_arr, bars=3, shift=0, not_strict=False)
    assert not is_rising(flat_arr, bars=3, shift=0, not_strict=True)
    assert not is_falling(flat_arr, bars=3, shift=0, not_strict=False)
    assert not is_falling(flat_arr, bars=3, shift=0, not_strict=True)

    # Flat step with rise: [10, 10, 12]
    plateau_rise = np.array([10.0, 10.0, 12.0])
    assert not is_rising(plateau_rise, bars=3, shift=0, not_strict=False)
    assert is_rising(plateau_rise, bars=3, shift=0, not_strict=True)

    # Flat step with fall: [12, 10, 10]
    plateau_fall = np.array([12.0, 10.0, 10.0])
    assert not is_falling(plateau_fall, bars=3, shift=0, not_strict=False)
    assert is_falling(plateau_fall, bars=3, shift=0, not_strict=True)

    # Reversal: [10, 15, 12]
    rev_arr = np.array([10.0, 15.0, 12.0])
    assert not is_rising(rev_arr, bars=3, shift=0)
    assert not is_falling(rev_arr, bars=3, shift=0)

    # Invalid bars < 2 or out of bounds
    assert not is_rising(rising_arr, bars=1, shift=0)
    assert not is_falling(falling_arr, bars=1, shift=0)
    assert not is_rising(rising_arr, bars=10, shift=0)
    assert not is_falling(falling_arr, bars=10, shift=0)


def test_count_persistence() -> None:
    """Verify is_greater_count and is_lower_count over rolling bar windows."""
    # Data: 3 bars where left > right
    # At shift=0,1,2: left=[12, 14, 16], right=[10, 11, 13]
    left = np.array([12.0, 14.0, 16.0])
    right = np.array([10.0, 11.0, 13.0])

    assert is_greater_count(left, right, bars=3, shift=0)
    assert not is_lower_count(left, right, bars=3, shift=0)

    # Inverted
    assert is_lower_count(right, left, bars=3, shift=0)
    assert not is_greater_count(right, left, bars=3, shift=0)

    # One bar fails condition
    left_break = np.array([12.0, 9.0, 16.0])  # bar 1 (shift 1) left < right
    assert not is_greater_count(left_break, right, bars=3, shift=0)

    # Strict equality vs not_strict
    left_eq = np.array([10.0, 11.0, 16.0])  # shifts 2 and 1 are equal to right
    assert not is_greater_count(left_eq, right, bars=3, shift=0, not_strict=False)
    assert is_greater_count(left_eq, right, bars=3, shift=0, not_strict=True)

    # All equal: cannot be True even with not_strict (at_least_once requirement)
    left_all_eq = np.array([10.0, 11.0, 13.0])
    assert not is_greater_count(left_all_eq, right, bars=3, shift=0, not_strict=True)
    assert not is_lower_count(left_all_eq, right, bars=3, shift=0, not_strict=True)

    # Bounds & parameter validation
    assert not is_greater_count(left, right, bars=0, shift=0)
    assert not is_lower_count(left, right, bars=0, shift=0)
    assert not is_greater_count(left, right, bars=10, shift=0)


def test_percentile_rankings() -> None:
    """Verify is_greater_percentile and is_lower_percentile calculations."""
    # 10 bars ascending: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    # At shift=0, current value is 10.
    # It is strictly greater than past values 1..9 (9 values).
    # count = 1 + 9 = 10. percrank = 10 / 10 * 100 = 100.0%
    data = np.arange(1.0, 11.0)
    assert is_greater_percentile(data, percentile=50.0, bars=10, shift=0)
    assert is_greater_percentile(data, percentile=90.0, bars=10, shift=0)
    assert not is_greater_percentile(data, percentile=100.0, bars=10, shift=0)

    # At shift=0, current value 10 is NOT lower than any past values.
    # count remains 1. percrank = 1 / 10 * 100 = 10.0%
    assert not is_lower_percentile(data, percentile=50.0, bars=10, shift=0)
    assert is_lower_percentile(data, percentile=5.0, bars=10, shift=0)

    # Descending: [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    # At shift=0, current value is 1. Lower than past 9 values.
    # count = 10. percrank = 100.0%
    data_desc = np.arange(10.0, 0.0, -1.0)
    assert is_lower_percentile(data_desc, percentile=50.0, bars=10, shift=0)
    assert not is_greater_percentile(data_desc, percentile=50.0, bars=10, shift=0)

    # Bounds
    assert not is_greater_percentile(data, bars=0)
    assert not is_lower_percentile(data, bars=0)
    assert not is_greater_percentile(data, bars=20)


def test_indicator_moving_averages() -> None:
    """Verify calculate_ma, calculate_wma, and indicator-to-MA condition blocks."""
    # Data: [10, 12, 14, 16, 18]
    data = np.array([10.0, 12.0, 14.0, 16.0, 18.0])

    # SMA: at shift=0, period=3: mean(14, 16, 18) = 16.0
    sma = calculate_ma(data, period=3, ma_type=MAType.SMA, shift=0)
    assert sma == 16.0

    # WMA: weights (3, 2, 1) for (18, 16, 14) -> (18*3 + 16*2 + 14*1) / (3+2+1)
    # = (54 + 32 + 14) / 6 = 100 / 6 = 16.666667
    wma = calculate_wma(data, period=3, shift=0)
    assert wma == round(100.0 / 6.0, 6)

    # EMA: period=3, alpha = 2 / 4 = 0.5
    # Window from shift 0 is [14, 16, 18]
    # Seed at shift+period-1 (shift 2, value 14): prev_ema = 14
    # i=1 (value 16): 16 * 0.5 + 14 * 0.5 = 15.0
    # i=0 (value 18): 18 * 0.5 + 15 * 0.5 = 16.5
    ema = calculate_ma(data, period=3, ma_type=MAType.EMA, shift=0)
    assert ema == 16.5

    # Hull MA: 2 * WMA(period // 2) - WMA(period)
    # period=4, half_period=2
    hma = calculate_ma(data, period=4, ma_type=MAType.HULL, shift=0)
    assert not math.isnan(hma)

    # Indicator above/below MA
    # At shift=0, data[0] is 18.0 > SMA (16.0)
    assert indicator_above_ma(data, period=3, ma_type=MAType.SMA, shift=0)
    assert not indicator_below_ma(data, period=3, ma_type=MAType.SMA, shift=0)

    # Crossing MA: create series crossing above its SMA
    # prev bar (shift 1): indicator was 10.0, SMA was 12.0 -> below
    # curr bar (shift 0): indicator is 18.0, SMA is 14.0 -> above
    cross_data = np.array([12.0, 14.0, 10.0, 18.0])
    # shift 1: window [12, 14, 10], SMA = 12.0; ind = 10.0 (< 12.0)
    # shift 0: window [14, 10, 18], SMA = 14.0; ind = 18.0 (> 14.0)
    assert indicator_crosses_above_ma(cross_data, period=3, ma_type=MAType.SMA, shift=0)
    assert not indicator_crosses_below_ma(
        cross_data, period=3, ma_type=MAType.SMA, shift=0
    )

    # Invalid MA type or period
    with pytest.raises(ValueError):
        calculate_ma(data, period=3, ma_type=99)
    assert math.isnan(calculate_ma(data, period=0))
    assert math.isnan(calculate_wma(data, period=0))


def test_logical_combinators() -> None:
    """Verify condition_and, condition_or, and condition_not evaluation."""
    assert condition_and(True, True, True)
    assert not condition_and(True, False, True)
    assert not condition_and(False, True)

    assert condition_or(False, False, True)
    assert not condition_or(False, False, False)
    assert condition_or(True, False)

    assert condition_not(False)
    assert not condition_not(True)
    assert condition_not(0)
    assert not condition_not(1)

    # Callables and short-circuit verification
    called: list[str] = []

    def true_fn() -> bool:
        called.append("true")
        return True

    def false_fn() -> bool:
        called.append("false")
        return False

    # AND short-circuits after false_fn
    called.clear()
    res_and = condition_and(true_fn, false_fn, true_fn)
    assert not res_and
    assert called == ["true", "false"]

    # OR short-circuits after true_fn
    called.clear()
    res_or = condition_or(false_fn, true_fn, false_fn)
    assert res_or
    assert called == ["false", "true"]

    # NOT callable
    assert condition_not(false_fn)


def test_comparisons_facade() -> None:
    """Verify Comparisons facade instance methods and default binding."""
    arr1 = np.array([10.0, 12.0, 15.0])
    arr2 = np.array([11.0, 13.0, 14.0])

    comp = Comparisons(arr1, arr2)

    # Arithmetic
    assert comp.is_greater(shift=0)
    assert not comp.is_lower(shift=0)
    assert comp.is_greater_or_equal(shift=0)
    assert not comp.is_lower_or_equal(shift=0)
    assert not comp.equals(shift=0)
    assert comp.not_equals(shift=0)

    # Crossovers
    assert comp.crosses_above(shift=0)
    assert not comp.crosses_below(shift=0)

    # Trend
    assert comp.is_rising(bars=3, shift=0)
    assert not comp.is_falling(bars=3, shift=0)

    # Count
    # Override operands
    assert comp.is_greater_count(
        left=np.array([12.0, 14.0]), right=np.array([10.0, 11.0]), bars=2
    )
    assert comp.is_lower_count(
        left=np.array([10.0, 11.0]), right=np.array([12.0, 14.0]), bars=2
    )

    # Percentile
    data_10 = np.arange(1.0, 11.0)
    assert comp.is_greater_percentile(indicator=data_10, percentile=50.0, bars=10)
    assert not comp.is_lower_percentile(indicator=data_10, percentile=50.0, bars=10)

    # Indicator MA
    ma_data = np.array([10.0, 12.0, 14.0, 16.0, 18.0])
    assert comp.indicator_above_ma(indicator=ma_data, period=3, shift=0)
    assert not comp.indicator_below_ma(indicator=ma_data, period=3, shift=0)

    # Cross MA
    cross_data = np.array([12.0, 14.0, 10.0, 18.0])
    assert comp.indicator_crosses_above_ma(indicator=cross_data, period=3, shift=0)
    assert not comp.indicator_crosses_below_ma(indicator=cross_data, period=3, shift=0)
