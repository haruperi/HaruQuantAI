"""Unit tests for modular comparison condition strategy blocks under app.extend.blocks.comparisons.

FEAT-INC-BLOCKS-CONDITIONS: Modular comparison condition strategy blocks.
FR-COND-ARITHMETIC, FR-COND-CROSSOVER, FR-COND-TREND, FR-COND-COUNT, FR-COND-PERCENTILE, FR-COND-LOGIC, FR-COND-MA, FR-COND-FACADE.
"""

from __future__ import annotations

import numpy as np
from app.extend.blocks.comparisons import (
    Comparisons,
    MAType,
    calculate_ma,
    calculate_wma,
    changes_down,
    changes_down_spec,
    changes_up,
    changes_up_spec,
    condition_and,
    condition_and_spec,
    condition_not,
    condition_not_spec,
    condition_or,
    condition_or_spec,
    crosses_above,
    crosses_above_spec,
    crosses_below,
    crosses_below_spec,
    equals,
    equals_spec,
    indicator_above_ma,
    indicator_above_ma_spec,
    indicator_below_ma,
    indicator_below_ma_spec,
    indicator_crosses_above_ma,
    indicator_crosses_above_ma_spec,
    indicator_crosses_below_ma_spec,
    is_falling,
    is_falling_spec,
    is_greater,
    is_greater_count,
    is_greater_count_spec,
    is_greater_or_equal,
    is_greater_or_equal_spec,
    is_greater_percentile,
    is_greater_percentile_spec,
    is_greater_spec,
    is_lower,
    is_lower_count,
    is_lower_count_spec,
    is_lower_or_equal,
    is_lower_or_equal_spec,
    is_lower_percentile,
    is_lower_percentile_spec,
    is_lower_spec,
    is_rising,
    is_rising_spec,
    not_equals,
    not_equals_spec,
)


def test_block_specs_metadata() -> None:
    """Ensure all comparison blocks declare valid BlockSpec metadata."""
    specs = [
        is_greater_spec,
        is_lower_spec,
        is_greater_or_equal_spec,
        is_lower_or_equal_spec,
        equals_spec,
        not_equals_spec,
        crosses_above_spec,
        crosses_below_spec,
        is_rising_spec,
        is_falling_spec,
        changes_up_spec,
        changes_down_spec,
        is_greater_count_spec,
        is_lower_count_spec,
        is_greater_percentile_spec,
        is_lower_percentile_spec,
        condition_and_spec,
        condition_or_spec,
        condition_not_spec,
        indicator_above_ma_spec,
        indicator_below_ma_spec,
        indicator_crosses_above_ma_spec,
        indicator_crosses_below_ma_spec,
    ]
    for spec in specs:
        assert spec.category == "comparisons"
        assert spec.id.startswith("condition.")
        assert spec.version == "1.0.0"


def test_arithmetic_comparisons() -> None:
    """Test is_greater, is_lower, is_greater_or_equal, is_lower_or_equal, equals, not_equals."""
    assert is_greater(10.0, 5.0)
    assert not is_greater(5.0, 10.0)
    assert not is_greater(5.0, 5.0)

    assert is_lower(5.0, 10.0)
    assert not is_lower(10.0, 5.0)
    assert not is_lower(5.0, 5.0)

    assert is_greater_or_equal(10.0, 5.0)
    assert is_greater_or_equal(5.0, 5.0)
    assert not is_greater_or_equal(4.0, 5.0)

    assert is_lower_or_equal(5.0, 10.0)
    assert is_lower_or_equal(5.0, 5.0)
    assert not is_lower_or_equal(6.0, 5.0)

    assert equals(5.0000001, 5.0, precision=6)
    assert not equals(5.01, 5.0, precision=2)

    assert not_equals(5.1, 5.0)
    assert not not_equals(5.0, 5.0)


def test_crossovers() -> None:
    """Test crosses_above and crosses_below conditions."""
    left = np.array([10.0, 20.0])
    right = np.array([15.0, 15.0])

    # At lag 1: left=10 < right=15; at lag 0: left=20 > right=15 -> crosses above
    assert crosses_above(left, right, shift=0)
    assert not crosses_below(left, right, shift=0)

    # Reverse
    left_rev = np.array([20.0, 10.0])
    assert crosses_below(left_rev, right, shift=0)
    assert not crosses_above(left_rev, right, shift=0)


def test_trend_and_turning_points() -> None:
    """Test is_rising, is_falling, changes_up, changes_down."""
    rising_series = np.array([10.0, 20.0, 30.0, 40.0])
    # Chronological: 10, 20, 30, 40 -> newest is 40 at shift 0
    assert is_rising(rising_series, bars=3, shift=0)
    assert not is_falling(rising_series, bars=3, shift=0)

    falling_series = np.array([40.0, 30.0, 20.0, 10.0])
    assert is_falling(falling_series, bars=3, shift=0)
    assert not is_rising(falling_series, bars=3, shift=0)

    # Turning points: [v2, v1, v0] where v2 is oldest (shift 2), v0 is newest (shift 0)
    trough_series = np.array([100.0, 20.0, 10.0, 30.0])
    # shift 2 = 20.0, shift 1 = 10.0, shift 0 = 30.0 -> 20 > 10 < 30 -> changes_up
    assert changes_up(trough_series, shift=0)
    assert not changes_down(trough_series, shift=0)

    peak_series = np.array([100.0, 10.0, 30.0, 20.0])
    # shift 2 = 10.0, shift 1 = 30.0, shift 0 = 20.0 -> 10 < 30 > 20 -> changes_down
    assert changes_down(peak_series, shift=0)
    assert not changes_up(peak_series, shift=0)


def test_count_and_percentile() -> None:
    """Test is_greater_count, is_lower_count, is_greater_percentile, is_lower_percentile."""
    left = np.array([20.0, 25.0, 30.0])
    right = np.array([10.0, 15.0, 20.0])

    assert is_greater_count(left, right, bars=3, shift=0)
    assert not is_lower_count(left, right, bars=3, shift=0)

    # Percentile rank
    series = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    # Newest is 50.0 (shift 0), higher than all previous -> rank > 80%
    assert is_greater_percentile(series, percentile=80.0, bars=5, shift=0)
    assert not is_lower_percentile(series, percentile=20.0, bars=5, shift=0)


def test_logical_operators() -> None:
    """Test condition_and, condition_or, condition_not."""
    assert condition_and(True, True, lambda: True)
    assert not condition_and(True, False, lambda: True)

    assert condition_or(False, True, lambda: False)
    assert not condition_or(False, False, lambda: False)

    assert condition_not(False)
    assert not condition_not(True)


def test_indicator_moving_averages() -> None:
    """Test moving average calculation and comparative conditions."""
    series = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    # SMA of last 3 bars (shift 0: 50, 40, 30) -> mean 40.0
    ma_val = calculate_ma(series, period=3, ma_type=MAType.SMA, shift=0)
    assert ma_val == 40.0

    wma_val = calculate_wma(series, period=3, shift=0)
    # Weights 3, 2, 1 for 50, 40, 30 -> (150 + 80 + 30) / 6 = 260 / 6 = 43.333333
    assert abs(wma_val - (260.0 / 6.0)) < 1e-5

    # 50.0 is above SMA 40.0
    assert indicator_above_ma(series, period=3, ma_type=MAType.SMA, shift=0)
    assert not indicator_below_ma(series, period=3, ma_type=MAType.SMA, shift=0)

    # Crossover of indicator vs MA
    cross_series = np.array([10.0, 20.0, 15.0, 35.0])
    assert indicator_crosses_above_ma(
        cross_series, period=2, ma_type=MAType.SMA, shift=0
    )


def test_comparisons_facade() -> None:
    """Test Comparisons facade class methods."""
    comp = Comparisons(left=10.0, right=5.0)
    assert comp.is_greater()
    assert not comp.is_lower()
    assert comp.is_greater_or_equal()
    assert not comp.is_lower_or_equal()
    assert not comp.equals()
    assert comp.not_equals()

    # Static helpers
    assert Comparisons.condition_and(True, True)
    assert Comparisons.condition_or(False, True)
    assert Comparisons.condition_not(False)
