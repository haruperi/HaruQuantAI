"""Comparison, crossover, trend persistence, percentile, and MA blocks.

Description:
    Provides consolidated comparison and rule condition building blocks
    for quantitative trading rules: arithmetic comparisons, crossovers,
    multi-bar trend/count persistence, 3-bar turn detection, historical
    percentile ranking, indicator moving average relations, compound
    logical combinators, and the unified Comparisons facade class.

Purpose:
    FEAT-SERVICES-COMPARISONS: Quantitative comparison and rule condition
    building blocks.

Key Capabilities:
    - FR-SERVICES-COMPARISON-BASIC: Fundamental arithmetic comparison predicates
      [`is_greater()`, `is_lower()`, `equals()`, `not_equals()`] (`DEBUG`).
    - FR-SERVICES-COMPARISON-CROSSOVER: Bar-to-bar crossover predicates across
      consecutive shifts [`crosses_above()`, `crosses_below()`] (`DEBUG`).
    - FR-SERVICES-COMPARISON-TREND: Multi-bar directional trend persistence
      and 3-bar turn predicates [`is_rising()`, `is_falling()`, `changes_up()`,
      `changes_down()`] (`DEBUG`).
    - FR-SERVICES-COMPARISON-COUNT: Multi-bar persistent comparative predicates
      over rolling windows [`is_greater_count()`, `is_lower_count()`] (`DEBUG`).
    - FR-SERVICES-COMPARISON-PERCENTILE: Historical percentile rank predicates
      [`is_greater_percentile()`, `is_lower_percentile()`] (`DEBUG`).
    - FR-SERVICES-COMPARISON-MA: Moving average smoothing and indicator-to-MA
      predicates [`calculate_ma()`, `calculate_wma()`, `indicator_above_ma()`]
      (`DEBUG`).
    - FR-SERVICES-COMPARISON-LOGIC: Compound boolean logical combinators
      [`condition_and()`, `condition_or()`, `condition_not()`] (`DEBUG`).
    - FR-SERVICES-COMPARISONS-FACADE: Consolidated Comparisons facade class
      [`Comparisons`] (`DEBUG`).

Python API Usage:
    ```python
    import numpy as np
    from app.services.include.comparisons import crosses_above, is_greater, is_rising

    arr1 = np.array([10.0, 12.0, 15.0])
    arr2 = np.array([11.0, 13.0, 14.0])
    assert is_greater(arr1, arr2, shift=0) is True
    assert crosses_above(arr1, arr2, shift=0) is True
    assert is_rising(arr1, bars=3, shift=0) is True
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/include/test_comparisons.py --no-cov
    ```
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from enum import IntEnum
from typing import Any

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import IndicatorSeries

logger = get_logger(__name__)

__all__ = [
    "Comparisons",
    "MAType",
    "calculate_ma",
    "calculate_wma",
    "changes_down",
    "changes_up",
    "condition_and",
    "condition_not",
    "condition_or",
    "crosses_above",
    "crosses_below",
    "equals",
    "indicator_above_ma",
    "indicator_below_ma",
    "indicator_crosses_above_ma",
    "indicator_crosses_below_ma",
    "is_falling",
    "is_greater",
    "is_greater_count",
    "is_greater_or_equal",
    "is_greater_percentile",
    "is_lower",
    "is_lower_count",
    "is_lower_or_equal",
    "is_lower_percentile",
    "is_rising",
    "not_equals",
    "resolve_shift_value",
    "round_value",
]

DEFAULT_COMPARISON_PRECISION: int = 6
DEFAULT_COUNT_PRECISION: int = 5
MIN_TREND_BARS: int = 2


class MAType(IntEnum):
    """Moving average type selector for quantitative indicators."""

    SMA = 1
    EMA = 2
    WMA = 3
    HULL = 4


def round_value(val: float, precision: int = DEFAULT_COMPARISON_PRECISION) -> float:
    """Round a floating-point value to a specified decimal precision."""
    return float("nan") if math.isnan(val) else round(float(val), precision)


def resolve_shift_value(target: Any, shift: int = 0) -> float:
    """Resolve numerical value from scalar, array, series, or callable at shift."""
    if isinstance(target, IndicatorSeries):
        return target.get(shift)
    if callable(target):
        try:
            val = target(shift)
        except TypeError:
            val = target()
        return float(val) if val is not None else float("nan")
    if isinstance(target, (np.ndarray, Sequence)) and not isinstance(
        target, (str, bytes)
    ):
        n = len(target)
        return float(target[-(1 + shift)]) if 0 <= shift < n else float("nan")
    try:
        return float(target)
    except TypeError, ValueError:
        return float("nan")


def _pair(
    left: Any,
    right: Any,
    shift: int,
    precision: int,
    *,
    s1: int | None = None,
    s2: int | None = None,
    rd: int | None = None,
) -> tuple[float, float]:
    """Resolve and round left/right values at their effective shifts and precision."""
    p = precision if rd is None else rd
    return (
        round_value(resolve_shift_value(left, shift if s1 is None else s1), p),
        round_value(resolve_shift_value(right, shift if s2 is None else s2), p),
    )


def is_greater(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left value is strictly greater than right value."""
    val1, val2 = _pair(
        left, right, shift, precision, s1=shift1, s2=shift2, rd=round_digits
    )
    return not (math.isnan(val1) or math.isnan(val2)) and val1 > val2


def is_lower(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left value is strictly lower than right value."""
    val1, val2 = _pair(
        left, right, shift, precision, s1=shift1, s2=shift2, rd=round_digits
    )
    return not (math.isnan(val1) or math.isnan(val2)) and val1 < val2


def is_greater_or_equal(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left value is greater than or equal to right value."""
    val1, val2 = _pair(
        left, right, shift, precision, s1=shift1, s2=shift2, rd=round_digits
    )
    return not (math.isnan(val1) or math.isnan(val2)) and val1 >= val2


def is_lower_or_equal(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left value is lower than or equal to right value."""
    val1, val2 = _pair(
        left, right, shift, precision, s1=shift1, s2=shift2, rd=round_digits
    )
    return not (math.isnan(val1) or math.isnan(val2)) and val1 <= val2


def equals(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left value equals right value within rounding precision."""
    val1, val2 = _pair(
        left, right, shift, precision, s1=shift1, s2=shift2, rd=round_digits
    )
    return not (math.isnan(val1) or math.isnan(val2)) and val1 == val2


def not_equals(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    shift1: int | None = None,
    shift2: int | None = None,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left value does not equal right value within precision."""
    val1, val2 = _pair(
        left, right, shift, precision, s1=shift1, s2=shift2, rd=round_digits
    )
    return not (math.isnan(val1) or math.isnan(val2)) and val1 != val2


def crosses_above(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left crossed above right between shift + 1 and shift."""
    val11, val21 = _pair(left, right, shift + 1, precision, rd=round_digits)
    val10, val20 = _pair(left, right, shift, precision, rd=round_digits)
    if any(math.isnan(v) for v in (val11, val21, val10, val20)):
        return False
    return val11 < val21 and val10 > val20


def crosses_below(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether left crossed below right between shift + 1 and shift."""
    val11, val21 = _pair(left, right, shift + 1, precision, rd=round_digits)
    val10, val20 = _pair(left, right, shift, precision, rd=round_digits)
    if any(math.isnan(v) for v in (val11, val21, val10, val20)):
        return False
    return val11 > val21 and val10 < val20


def is_rising(
    indicator: Any,
    bars: int = 2,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether indicator is rising monotonically over a bar window."""
    if bars < MIN_TREND_BARS:
        return False
    p = precision if round_digits is None else round_digits
    prev_val = round_value(resolve_shift_value(indicator, bars + shift - 1), p)
    if math.isnan(prev_val):
        return False
    at_least_once = False
    for i in range(1, bars):
        curr_val = round_value(resolve_shift_value(indicator, bars + shift - 1 - i), p)
        if math.isnan(curr_val) or curr_val < prev_val:
            return False
        if curr_val == prev_val and not not_strict:
            return False
        if curr_val > prev_val:
            at_least_once = True
        prev_val = curr_val
    return at_least_once


def is_falling(
    indicator: Any,
    bars: int = 2,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate whether indicator is falling monotonically over a bar window."""
    if bars < MIN_TREND_BARS:
        return False
    p = precision if round_digits is None else round_digits
    prev_val = round_value(resolve_shift_value(indicator, bars + shift - 1), p)
    if math.isnan(prev_val):
        return False
    at_least_once = False
    for i in range(1, bars):
        curr_val = round_value(resolve_shift_value(indicator, bars + shift - 1 - i), p)
        if math.isnan(curr_val) or curr_val > prev_val:
            return False
        if curr_val == prev_val and not not_strict:
            return False
        if curr_val < prev_val:
            at_least_once = True
        prev_val = curr_val
    return at_least_once


def changes_up(
    indicator: Any,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate 3-bar upward turn (`v[s+2] > v[s+1] < v[s]`)."""
    p = precision if round_digits is None else round_digits
    v2 = round_value(resolve_shift_value(indicator, shift + 2), p)
    v1 = round_value(resolve_shift_value(indicator, shift + 1), p)
    v0 = round_value(resolve_shift_value(indicator, shift), p)
    if any(math.isnan(v) for v in (v2, v1, v0)):
        return False
    return (v2 >= v1 if not_strict else v2 > v1) and v1 < v0


def changes_down(
    indicator: Any,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
    *,
    round_digits: int | None = None,
) -> bool:
    """Evaluate 3-bar downward turn (`v[s+2] < v[s+1] > v[s]`)."""
    p = precision if round_digits is None else round_digits
    v2 = round_value(resolve_shift_value(indicator, shift + 2), p)
    v1 = round_value(resolve_shift_value(indicator, shift + 1), p)
    v0 = round_value(resolve_shift_value(indicator, shift), p)
    if any(math.isnan(v) for v in (v2, v1, v0)):
        return False
    return (v2 <= v1 if not_strict else v2 < v1) and v1 > v0


def is_greater_count(
    left: Any,
    right: Any,
    bars: int = 2,
    *,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether left > right remains true across a window of bars."""
    if bars < 1:
        return False
    at_least_once = False
    for i in range(bars):
        l_val, r_val = _pair(left, right, shift + i, precision)
        if math.isnan(l_val) or math.isnan(r_val) or l_val < r_val:
            return False
        if l_val == r_val and not not_strict:
            return False
        if l_val > r_val:
            at_least_once = True
    return at_least_once


def is_lower_count(
    left: Any,
    right: Any,
    bars: int = 2,
    *,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether left < right remains true across a window of bars."""
    if bars < 1:
        return False
    at_least_once = False
    for i in range(bars):
        l_val, r_val = _pair(left, right, shift + i, precision)
        if math.isnan(l_val) or math.isnan(r_val) or l_val > r_val:
            return False
        if l_val == r_val and not not_strict:
            return False
        if l_val < r_val:
            at_least_once = True
    return at_least_once


def is_greater_percentile(
    indicator: Any,
    percentile: float = 50.0,
    bars: int = 10,
    shift: int = 0,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether indicator value exceeds percentile rank over past bars."""
    if bars <= 0:
        return False
    curr_val = round_value(resolve_shift_value(indicator, shift), precision)
    if math.isnan(curr_val):
        return False
    count = 1
    for i in range(bars):
        prev_val = round_value(resolve_shift_value(indicator, shift + i), precision)
        if math.isnan(prev_val):
            return False
        if curr_val > prev_val:
            count += 1
    return (count / float(bars)) * 100.0 > round_value(percentile, precision)


def is_lower_percentile(
    indicator: Any,
    percentile: float = 50.0,
    bars: int = 10,
    shift: int = 0,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether indicator value falls below percentile rank over past bars."""
    if bars <= 0:
        return False
    curr_val = round_value(resolve_shift_value(indicator, shift), precision)
    if math.isnan(curr_val):
        return False
    count = 1
    for i in range(bars):
        prev_val = round_value(resolve_shift_value(indicator, shift + i), precision)
        if math.isnan(prev_val):
            return False
        if curr_val < prev_val:
            count += 1
    return (count / float(bars)) * 100.0 > round_value(percentile, precision)


def calculate_wma(
    indicator: Any,
    period: int,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> float:
    """Calculate Weighted Moving Average (WMA) for indicator series."""
    if period <= 0:
        return float("nan")
    weighted_sum = 0.0
    weight_sum = 0.0
    for i in range(period):
        weight = float(period - i)
        val = round_value(resolve_shift_value(indicator, shift + i), precision)
        if math.isnan(val):
            return float("nan")
        weighted_sum += val * weight
        weight_sum += weight
    return float("nan") if weight_sum == 0.0 else weighted_sum / weight_sum


def _calculate_sma(indicator: Any, period: int, shift: int, precision: int) -> float:
    """Compute Simple Moving Average sum-over-period."""
    total = 0.0
    for i in range(period):
        val = round_value(resolve_shift_value(indicator, shift + i), precision)
        if math.isnan(val):
            return float("nan")
        total += val
    return total / float(period)


def _calculate_ema(indicator: Any, period: int, shift: int, precision: int) -> float:
    """Compute Exponential Moving Average forward from window seed."""
    alpha = 2.0 / (float(period) + 1.0)
    prev_ema = round_value(
        resolve_shift_value(indicator, shift + period - 1), precision
    )
    if math.isnan(prev_ema):
        return float("nan")
    for i in range(period - 2, -1, -1):
        curr_val = round_value(resolve_shift_value(indicator, shift + i), precision)
        if math.isnan(curr_val):
            return float("nan")
        prev_ema = curr_val * alpha + prev_ema * (1.0 - alpha)
    return prev_ema


def _calculate_hull(indicator: Any, period: int, shift: int, precision: int) -> float:
    """Compute Hull Moving Average via 2*WMA(n/2) - WMA(n)."""
    half_wma = calculate_wma(indicator, max(1, period // 2), shift, precision)
    full_wma = calculate_wma(indicator, period, shift, precision)
    if math.isnan(half_wma) or math.isnan(full_wma):
        return float("nan")
    return 2.0 * half_wma - full_wma


def calculate_ma(
    indicator: Any,
    period: int,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> float:
    """Calculate Moving Average (SMA=1, EMA=2, WMA=3, HULL=4) for indicator blocks."""
    if period <= 0:
        return float("nan")
    type_code = int(ma_type)
    if type_code == MAType.SMA:
        return _calculate_sma(indicator, period, shift, precision)
    if type_code == MAType.EMA:
        return _calculate_ema(indicator, period, shift, precision)
    if type_code == MAType.WMA:
        return calculate_wma(indicator, period, shift, precision)
    if type_code == MAType.HULL:
        return _calculate_hull(indicator, period, shift, precision)
    raise ValueError(f"Unsupported MAType: {ma_type}")


def indicator_above_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator is above its Moving Average at shift."""
    ind_val = round_value(resolve_shift_value(indicator, shift), precision)
    ma_val = calculate_ma(indicator, period, ma_type, shift, precision)
    return not (math.isnan(ind_val) or math.isnan(ma_val)) and ind_val > ma_val


def indicator_below_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator is below its Moving Average at shift."""
    ind_val = round_value(resolve_shift_value(indicator, shift), precision)
    ma_val = calculate_ma(indicator, period, ma_type, shift, precision)
    return not (math.isnan(ind_val) or math.isnan(ma_val)) and ind_val < ma_val


def indicator_crosses_above_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator crosses above its MA from shift + 1 to shift."""
    ind_curr = round_value(resolve_shift_value(indicator, shift), precision)
    ind_prev = round_value(resolve_shift_value(indicator, shift + 1), precision)
    ma_curr = calculate_ma(indicator, period, ma_type, shift, precision)
    ma_prev = calculate_ma(indicator, period, ma_type, shift + 1, precision)
    if any(math.isnan(v) for v in (ind_curr, ind_prev, ma_curr, ma_prev)):
        return False
    return ind_prev < ma_prev and ind_curr > ma_curr


def indicator_crosses_below_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator crosses below its MA from shift + 1 to shift."""
    ind_curr = round_value(resolve_shift_value(indicator, shift), precision)
    ind_prev = round_value(resolve_shift_value(indicator, shift + 1), precision)
    ma_curr = calculate_ma(indicator, period, ma_type, shift, precision)
    ma_prev = calculate_ma(indicator, period, ma_type, shift + 1, precision)
    if any(math.isnan(v) for v in (ind_curr, ind_prev, ma_curr, ma_prev)):
        return False
    return ind_prev > ma_prev and ind_curr < ma_curr


def condition_and(*conditions: bool | Callable[[], Any] | Any) -> bool:
    """Evaluate short-circuit logical AND across multiple condition expressions."""
    for cond in conditions:
        val = cond() if callable(cond) else cond
        if not bool(val):
            return False
    return True


def condition_or(*conditions: bool | Callable[[], Any] | Any) -> bool:
    """Evaluate short-circuit logical OR across multiple condition expressions."""
    for cond in conditions:
        val = cond() if callable(cond) else cond
        if bool(val):
            return True
    return False


def condition_not(condition: bool | float | Callable[[], Any] | Any) -> bool:
    """Evaluate logical NOT on a condition expression."""
    val = condition() if callable(condition) else condition
    return not bool(val)


class Comparisons:
    """Consolidated facade for evaluating quantitative comparison blocks."""

    def __init__(
        self,
        left: Any = None,
        right: Any = None,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> None:
        """Initialize Comparisons facade with optional default operands."""
        self._left = left
        self._right = right
        self._precision = precision
        logger.debug(
            "FR-SERVICES-COMPARISONS-FACADE: Initialized facade (p=%d)",
            precision,
            extra={"fr_id": "FR-SERVICES-COMPARISONS-FACADE", "precision": precision},
        )

    def _ops(
        self, left: Any, right: Any, precision: int | None
    ) -> tuple[Any, Any, int]:
        """Resolve default left, right, and precision operands."""
        return (
            self._left if left is None else left,
            self._right if right is None else right,
            self._precision if precision is None else precision,
        )

    def is_greater(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_greater using instance operands if omitted."""
        l_op, r_op, p = self._ops(left, right, precision)
        return is_greater(l_op, r_op, shift=shift, precision=p)

    def is_lower(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_lower using instance operands if omitted."""
        l_op, r_op, p = self._ops(left, right, precision)
        return is_lower(l_op, r_op, shift=shift, precision=p)

    def is_greater_or_equal(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_greater_or_equal using instance operands if omitted."""
        l_op, r_op, p = self._ops(left, right, precision)
        return is_greater_or_equal(l_op, r_op, shift=shift, precision=p)

    def is_lower_or_equal(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_lower_or_equal using instance operands if omitted."""
        l_op, r_op, p = self._ops(left, right, precision)
        return is_lower_or_equal(l_op, r_op, shift=shift, precision=p)

    def equals(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate equals using instance operands if omitted."""
        l_op, r_op, p = self._ops(left, right, precision)
        return equals(l_op, r_op, shift=shift, precision=p)

    def not_equals(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate not_equals using instance operands if omitted."""
        l_op, r_op, p = self._ops(left, right, precision)
        return not_equals(l_op, r_op, shift=shift, precision=p)

    def crosses_above(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate crosses_above using instance operands if omitted."""
        l_op, r_op, p = self._ops(left, right, precision)
        return crosses_above(l_op, r_op, shift=shift, precision=p)

    def crosses_below(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate crosses_below using instance operands if omitted."""
        l_op, r_op, p = self._ops(left, right, precision)
        return crosses_below(l_op, r_op, shift=shift, precision=p)

    def is_rising(
        self,
        indicator: Any = None,
        bars: int = 2,
        *,
        shift: int = 0,
        not_strict: bool = False,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_rising using instance left operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return is_rising(
            l_op, bars=bars, shift=shift, not_strict=not_strict, precision=p
        )

    def is_falling(
        self,
        indicator: Any = None,
        bars: int = 2,
        *,
        shift: int = 0,
        not_strict: bool = False,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_falling using instance left operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return is_falling(
            l_op, bars=bars, shift=shift, not_strict=not_strict, precision=p
        )

    def changes_up(
        self,
        indicator: Any = None,
        *,
        shift: int = 0,
        not_strict: bool = False,
        precision: int | None = None,
    ) -> bool:
        """Evaluate changes_up using instance left operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return changes_up(l_op, shift=shift, not_strict=not_strict, precision=p)

    def changes_down(
        self,
        indicator: Any = None,
        *,
        shift: int = 0,
        not_strict: bool = False,
        precision: int | None = None,
    ) -> bool:
        """Evaluate changes_down using instance left operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return changes_down(l_op, shift=shift, not_strict=not_strict, precision=p)

    def is_greater_count(
        self,
        left: Any = None,
        right: Any = None,
        bars: int = 2,
        *,
        shift: int = 0,
        not_strict: bool = False,
        precision: int = DEFAULT_COUNT_PRECISION,
    ) -> bool:
        """Evaluate is_greater_count using instance operands if omitted."""
        l_op, r_op, _ = self._ops(left, right, precision)
        return is_greater_count(
            l_op,
            r_op,
            bars=bars,
            shift=shift,
            not_strict=not_strict,
            precision=precision,
        )

    def is_lower_count(
        self,
        left: Any = None,
        right: Any = None,
        bars: int = 2,
        *,
        shift: int = 0,
        not_strict: bool = False,
        precision: int = DEFAULT_COUNT_PRECISION,
    ) -> bool:
        """Evaluate is_lower_count using instance operands if omitted."""
        l_op, r_op, _ = self._ops(left, right, precision)
        return is_lower_count(
            l_op,
            r_op,
            bars=bars,
            shift=shift,
            not_strict=not_strict,
            precision=precision,
        )

    def is_greater_percentile(
        self,
        indicator: Any = None,
        percentile: float = 50.0,
        *,
        bars: int = 10,
        shift: int = 0,
        precision: int = DEFAULT_COUNT_PRECISION,
    ) -> bool:
        """Evaluate is_greater_percentile using instance operand if omitted."""
        l_op, _, _ = self._ops(indicator, None, precision)
        return is_greater_percentile(
            l_op, percentile=percentile, bars=bars, shift=shift, precision=precision
        )

    def is_lower_percentile(
        self,
        indicator: Any = None,
        percentile: float = 50.0,
        *,
        bars: int = 10,
        shift: int = 0,
        precision: int = DEFAULT_COUNT_PRECISION,
    ) -> bool:
        """Evaluate is_lower_percentile using instance operand if omitted."""
        l_op, _, _ = self._ops(indicator, None, precision)
        return is_lower_percentile(
            l_op, percentile=percentile, bars=bars, shift=shift, precision=precision
        )

    def indicator_above_ma(
        self,
        indicator: Any = None,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        *,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate indicator_above_ma using instance operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return indicator_above_ma(
            l_op, period=period, ma_type=ma_type, shift=shift, precision=p
        )

    def indicator_below_ma(
        self,
        indicator: Any = None,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        *,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate indicator_below_ma using instance operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return indicator_below_ma(
            l_op, period=period, ma_type=ma_type, shift=shift, precision=p
        )

    def indicator_crosses_above_ma(
        self,
        indicator: Any = None,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        *,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate indicator_crosses_above_ma using instance operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return indicator_crosses_above_ma(
            l_op, period=period, ma_type=ma_type, shift=shift, precision=p
        )

    def indicator_crosses_below_ma(
        self,
        indicator: Any = None,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        *,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate indicator_crosses_below_ma using instance operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return indicator_crosses_below_ma(
            l_op, period=period, ma_type=ma_type, shift=shift, precision=p
        )

    def calculate_wma(
        self,
        indicator: Any = None,
        period: int = 14,
        *,
        shift: int = 0,
        precision: int | None = None,
    ) -> float:
        """Calculate Weighted Moving Average using instance operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return calculate_wma(l_op, period=period, shift=shift, precision=p)

    def calculate_ma(
        self,
        indicator: Any = None,
        period: int = 14,
        ma_type: int | MAType = MAType.SMA,
        *,
        shift: int = 0,
        precision: int | None = None,
    ) -> float:
        """Calculate Moving Average using instance operand if omitted."""
        l_op, _, p = self._ops(indicator, None, precision)
        return calculate_ma(
            l_op, period=period, ma_type=ma_type, shift=shift, precision=p
        )

    @staticmethod
    def condition_and(*conditions: bool | Callable[[], Any] | Any) -> bool:
        """Evaluate short-circuit logical AND across multiple condition expressions."""
        return condition_and(*conditions)

    @staticmethod
    def condition_or(*conditions: bool | Callable[[], Any] | Any) -> bool:
        """Evaluate short-circuit logical OR across multiple condition expressions."""
        return condition_or(*conditions)

    @staticmethod
    def condition_not(condition: bool | float | Callable[[], Any] | Any) -> bool:
        """Evaluate logical NOT on a condition expression."""
        return condition_not(condition)
