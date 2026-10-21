"""Unit tests for app.services.include.comparisons blocks and Comparisons facade.

Description:
    Validates all 23 concrete comparison blocks (21 StrategyQuant X comparison
    blocks plus changes_up and changes_down turning-point predicates), moving
    average smoothing helpers (SMA, EMA, WMA, Hull) with exact unrounded output
    parity, shift resolution, and the unified Comparisons facade class.

Purpose:
    FEAT-SERVICES-COMPARISONS: Quantitative comparison and rule condition
    building blocks verification.

Key Capabilities:
    - FR-SERVICES-COMPARISON-BASIC: Verify arithmetic equality and inequality predicates.
    - FR-SERVICES-COMPARISON-CROSSOVER: Verify bar-to-bar crossover predicates.
    - FR-SERVICES-COMPARISON-TREND: Verify rising, falling, and turning-point predicates.
    - FR-SERVICES-COMPARISON-COUNT: Verify rolling window count comparisons.
    - FR-SERVICES-COMPARISON-PERCENTILE: Verify percentile rank comparisons.
    - FR-SERVICES-COMPARISON-MA: Verify exact donor MA rounding and indicator-to-MA relations.
    - FR-SERVICES-COMPARISON-LOGIC: Verify short-circuit logical combinators.
    - FR-SERVICES-COMPARISONS-FACADE: Verify Comparisons facade method parity.

Python API Usage:
    ```python
    from app.services.include.comparisons import Comparisons, MAType

    comp = Comparisons([10.0, 12.0, 15.0], [11.0, 13.0, 14.0])
    assert comp.is_greater() is True
    assert comp.crosses_above() is True
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/include/test_comparisons.py --no-cov
    ```
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from app.services.include.comparisons import (
    Comparisons,
    MAType,
    calculate_ma,
    calculate_wma,
    changes_down,
    changes_up,
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
from app.services.indicators.base import IndicatorSeries


def test_round_and_resolve_shift_value() -> None:
    """Verify round_value and resolve_shift_value across supported input types."""
    assert math.isnan(round_value(float("nan")))
    assert round_value(1.1234567, 6) == 1.123457

    series = IndicatorSeries(np.array([1.0, 2.0, 3.0]))
    assert resolve_shift_value(series, 0) == 3.0
    assert resolve_shift_value(series, 1) == 2.0

    assert resolve_shift_value(lambda s: 10.0 + s, 2) == 12.0
    assert resolve_shift_value(lambda: 42.0, 1) == 42.0
    assert math.isnan(resolve_shift_value(lambda: None, 0))

    arr = [5.0, 6.0, 7.0]
    assert resolve_shift_value(arr, 0) == 7.0
    assert math.isnan(resolve_shift_value(arr, 5))

    assert resolve_shift_value(9.5, 0) == 9.5
    assert math.isnan(resolve_shift_value("not-a-number", 0))


def test_basic_left_right_comparisons() -> None:
    """Verify is_greater, is_lower, is_greater_or_equal, is_lower_or_equal, equals, not_equals."""
    assert is_greater(10.000001, 10.0) is True
    assert is_greater(10.0000001, 10.0) is False
    assert is_lower(9.999999, 10.0) is True
    assert is_greater_or_equal(10.0000001, 10.0) is True
    assert is_lower_or_equal(10.0000001, 10.0) is True
    assert equals(10.0000001, 10.0) is True
    assert not_equals(10.000001, 10.0) is True
    assert is_greater(float("nan"), 1.0) is False


def test_crossovers() -> None:
    """Verify crosses_above and crosses_below."""
    left = [10.0, 15.0]
    right = [12.0, 13.0]
    assert crosses_above(left, right, shift=0) is True
    assert crosses_below(right, left, shift=0) is True
    assert crosses_above([10.0], right, shift=0) is False
    assert crosses_below([10.0], right, shift=0) is False


def test_is_rising_is_falling_and_turns() -> None:
    """Verify is_rising, is_falling, changes_up, and changes_down."""
    assert is_rising([1.0, 2.0, 3.0], bars=1) is False
    assert is_rising([float("nan"), 2.0, 3.0], bars=3) is False
    assert is_rising([1.0, float("nan"), 3.0], bars=3) is False
    assert is_rising([1.0, 2.0, 3.0], bars=3) is True
    assert is_rising([1.0, 2.0, 2.0], bars=3, not_strict=False) is False
    assert is_rising([1.0, 2.0, 2.0], bars=3, not_strict=True) is True
    assert is_rising([2.0, 2.0, 2.0], bars=3, not_strict=True) is False

    assert is_falling([3.0, 2.0, 1.0], bars=1) is False
    assert is_falling([float("nan"), 2.0, 1.0], bars=3) is False
    assert is_falling([3.0, float("nan"), 1.0], bars=3) is False
    assert is_falling([3.0, 2.0, 1.0], bars=3) is True
    assert is_falling([3.0, 2.0, 2.0], bars=3, not_strict=False) is False
    assert is_falling([3.0, 2.0, 2.0], bars=3, not_strict=True) is True
    assert is_falling([2.0, 2.0, 2.0], bars=3, not_strict=True) is False

    assert changes_up([3.0, 1.0, 2.0], shift=0) is True
    assert changes_up([1.0, 2.0, 3.0], shift=0) is False
    assert changes_up([1.0, 2.0], shift=0) is False

    assert changes_down([1.0, 3.0, 2.0], shift=0) is True
    assert changes_down([3.0, 2.0, 1.0], shift=0) is False
    assert changes_down([2.0, 1.0], shift=0) is False


def test_count_and_percentile_comparisons() -> None:
    """Verify is_greater_count, is_lower_count, is_greater_percentile, is_lower_percentile."""
    assert is_greater_count([3.0, 4.0], [1.0, 2.0], bars=0) is False
    assert is_greater_count([3.0, 4.0], [1.0, 2.0], bars=2) is True
    assert is_greater_count([3.0, 2.0], [3.0, 1.0], bars=2, not_strict=False) is False
    assert is_greater_count([3.0, 2.0], [3.0, 1.0], bars=2, not_strict=True) is True
    assert is_greater_count([1.0, 2.0], [3.0, 1.0], bars=2) is False

    assert is_lower_count([1.0, 2.0], [3.0, 4.0], bars=0) is False
    assert is_lower_count([1.0, 2.0], [3.0, 4.0], bars=2) is True
    assert is_lower_count([3.0, 1.0], [3.0, 2.0], bars=2, not_strict=False) is False
    assert is_lower_count([3.0, 1.0], [3.0, 2.0], bars=2, not_strict=True) is True
    assert is_lower_count([3.0, 2.0], [1.0, 4.0], bars=2) is False

    series = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert is_greater_percentile(series, percentile=80.0, bars=5) is True
    assert is_greater_percentile(series, percentile=50.0, bars=0) is False
    assert is_greater_percentile([float("nan")], percentile=50.0, bars=1) is False
    assert is_greater_percentile([1.0], percentile=50.0, bars=2) is False

    rev = [5.0, 4.0, 3.0, 2.0, 1.0]
    assert is_lower_percentile(rev, percentile=80.0, bars=5) is True
    assert is_lower_percentile(rev, percentile=50.0, bars=0) is False
    assert is_lower_percentile([float("nan")], percentile=50.0, bars=1) is False
    assert is_lower_percentile([1.0], percentile=50.0, bars=2) is False


def test_ma_calculations_exact_unrounded_parity_and_conditions() -> None:
    """Verify exact SQX unrounded MA calculation output and MA comparison blocks."""
    # Inputs round to 6 decimals, but division 4.0 / 3.0 is NOT rounded to 6 decimals
    vals = [1.0, 1.0, 2.0]
    sma_val = calculate_ma(vals, period=3, ma_type=MAType.SMA, shift=0)
    assert sma_val == 4.0 / 3.0
    assert sma_val != round(4.0 / 3.0, 6)

    wma_val = calculate_wma([1.0, 1.0, 1.0], period=3, shift=0)
    assert wma_val == 1.0
    assert math.isnan(calculate_wma(vals, period=0))
    assert math.isnan(calculate_wma([1.0, float("nan"), 2.0], period=3))

    ema_val = calculate_ma([1.0, 2.0, 4.0], period=3, ma_type=MAType.EMA, shift=0)
    assert ema_val == 2.75
    assert math.isnan(
        calculate_ma([float("nan"), 2.0, 4.0], period=3, ma_type=MAType.EMA)
    )
    assert math.isnan(
        calculate_ma([1.0, float("nan"), 4.0], period=3, ma_type=MAType.EMA)
    )

    hull_val = calculate_ma(
        [1.0, 2.0, 3.0, 4.0], period=4, ma_type=MAType.HULL, shift=0
    )
    assert not math.isnan(hull_val)
    assert math.isnan(
        calculate_ma([1.0, float("nan"), 3.0, 4.0], period=4, ma_type=MAType.HULL)
    )
    assert math.isnan(calculate_ma(vals, period=0))
    assert math.isnan(
        calculate_ma([1.0, float("nan"), 2.0], period=3, ma_type=MAType.SMA)
    )

    with pytest.raises(ValueError, match="Unsupported MAType"):
        calculate_ma(vals, period=3, ma_type=99)

    rising_series = [10.0, 11.0, 12.0, 15.0]
    assert indicator_above_ma(rising_series, period=3, ma_type=MAType.SMA) is True
    assert (
        indicator_below_ma([15.0, 12.0, 11.0, 10.0], period=3, ma_type=MAType.SMA)
        is True
    )

    cross_up = [10.0, 10.0, 9.0, 14.0]
    assert indicator_crosses_above_ma(cross_up, period=3, ma_type=MAType.SMA) is True
    assert indicator_crosses_above_ma([10.0], period=3, ma_type=MAType.SMA) is False

    cross_dn = [10.0, 10.0, 11.0, 6.0]
    assert indicator_crosses_below_ma(cross_dn, period=3, ma_type=MAType.SMA) is True
    assert indicator_crosses_below_ma([10.0], period=3, ma_type=MAType.SMA) is False


def test_logical_combinators_and_comparisons_facade() -> None:
    """Verify condition_and, condition_or, condition_not and full Comparisons facade."""
    assert condition_and(True, lambda: True, 1) is True
    assert condition_and(True, lambda: False, 1) is False
    assert condition_or(False, lambda: True) is True
    assert condition_or(False, lambda: 0) is False
    assert condition_not(False) is True
    assert condition_not(lambda: True) is False

    comp = Comparisons([10.0, 11.0, 12.0, 15.0], [9.0, 10.0, 13.0, 14.0])
    assert comp.is_greater() is True
    assert comp.is_lower() is False
    assert comp.is_greater_or_equal() is True
    assert comp.is_lower_or_equal() is False
    assert comp.equals() is False
    assert comp.not_equals() is True
    assert comp.crosses_above() is True
    assert comp.crosses_below() is False
    assert comp.is_rising(bars=3) is True
    assert comp.is_falling(bars=3) is False
    assert comp.changes_up([12.0, 10.0, 14.0]) is True
    assert comp.changes_down([10.0, 14.0, 12.0]) is True
    assert comp.is_greater_count(bars=1) is True
    assert comp.is_lower_count(bars=1) is False
    assert comp.is_greater_percentile(percentile=50.0, bars=4) is True
    assert comp.is_lower_percentile(percentile=50.0, bars=4) is False
    assert comp.indicator_above_ma(period=3) is True
    assert comp.indicator_below_ma(period=3) is False
    assert comp.indicator_crosses_above_ma([10.0, 10.0, 9.0, 14.0], period=3) is True
    assert comp.indicator_crosses_below_ma([10.0, 10.0, 11.0, 6.0], period=3) is True
    assert not math.isnan(comp.calculate_wma(period=3))
    assert not math.isnan(comp.calculate_ma(period=3, ma_type=MAType.WMA))
    assert comp.condition_and(True, True) is True
    assert comp.condition_or(False, True) is True
    assert comp.condition_not(False) is True
