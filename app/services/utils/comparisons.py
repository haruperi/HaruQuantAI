"""Comparison, crossover, trend persistence, percentile, and MA blocks.

Description:
    Provides consolidated comparison and rule condition building blocks
    matching StrategyQuant X:
    - Arithmetic comparisons: IsGreater, IsLower, IsGreaterOrEqual,
      IsLowerOrEqual, Equals, NotEquals with 6-decimal precision rounding.
    - Crossover comparisons: CrossesAbove, CrossesBelow evaluating historical
      shift 1 versus shift 0.
    - Trend persistence: IsRising, IsFalling evaluating monotonic directional
      progression over multi-bar windows with optional NotStrict equality.
    - Count persistence: IsGreaterCount, IsLowerCount evaluating rolling multi-bar
      condition retention with 5-decimal precision.
    - Percentile ranking: IsGreaterPercentil, IsLowerPercentil calculating past
      window percentile ranks with 5-decimal precision.
    - Indicator Moving Average relations: Simple, Exponential, Weighted, and
      Hull Moving Average calculations and crossover / positional conditions.
    - Compound logic: AND, OR, and Not short-circuit combinators.
    - Comparisons: Unified facade class providing both instance-bound and
      functional evaluation.

Purpose:
    FEAT-SERVICES-COMPARISONS: Quantitative comparison and rule condition
    building blocks.

Key Capabilities:
    - FR-SERVICES-COMPARISON-BASIC: Fundamental arithmetic comparison predicates
      with precision rounding.
      Associated: `is_greater()`, `is_lower()`, `is_greater_or_equal()`,
      `is_lower_or_equal()`, `equals()`, `not_equals()`.
      Logging: DEBUG on evaluation with values, precision, and result.
    - FR-SERVICES-COMPARISON-CROSSOVER: Bar-to-bar crossover predicates across
      consecutive shifts.
      Associated: `crosses_above()`, `crosses_below()`.
      Logging: DEBUG on crossover evaluation with current/previous values and result.
    - FR-SERVICES-COMPARISON-TREND: Multi-bar directional trend persistence
      predicates with strictness controls.
      Associated: `is_rising()`, `is_falling()`.
      Logging: DEBUG on trend evaluation with bar window, strictness, and result.
    - FR-SERVICES-COMPARISON-COUNT: Multi-bar persistent comparative predicates
      over rolling windows.
      Associated: `is_greater_count()`, `is_lower_count()`.
      Logging: DEBUG on count evaluation with bar count, strictness, and result.
    - FR-SERVICES-COMPARISON-PERCENTILE: Historical percentile rank predicates
      comparing current bar against past window.
      Associated: `is_greater_percentile()`, `is_lower_percentile()`.
      Logging: DEBUG on percentile evaluation with rank, threshold, and result.
    - FR-SERVICES-COMPARISON-MA: Moving average smoothing and indicator-to-MA
      comparison and crossover predicates.
      Associated: `calculate_ma()`, `calculate_wma()`, `indicator_above_ma()`,
      `indicator_below_ma()`, `indicator_crosses_above_ma()`,
      `indicator_crosses_below_ma()`.
      Logging: DEBUG on MA calculation and condition evaluation.
    - FR-SERVICES-COMPARISON-LOGIC: Compound boolean logical combinators.
      Associated: `condition_and()`, `condition_or()`, `condition_not()`.
      Logging: DEBUG on short-circuit condition evaluation.
    - FR-SERVICES-COMPARISONS-FACADE: Consolidated Comparisons facade class
      binding series and providing unified condition evaluation.
      Associated: `Comparisons`.
      Logging: DEBUG on facade evaluation.

Python API Usage:
    ```python
    import numpy as np
    from app.services.utils.comparisons import (
        MAType,
        crosses_above,
        is_greater,
        is_rising,
    )

    arr1 = np.array([10.0, 12.0, 15.0])
    arr2 = np.array([11.0, 13.0, 14.0])

    greater = is_greater(arr1, arr2, shift=0)  # 15.0 > 14.0 -> True
    crossed = crosses_above(arr1, arr2, shift=0)  # 12<13 and 15>14 -> True
    rising = is_rising(arr1, bars=3, shift=0)  # 10 -> 12 -> 15 -> True
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_comparisons.py --no-cov
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

DEFAULT_COMPARISON_PRECISION: int = 6
DEFAULT_COUNT_PRECISION: int = 5
MIN_TREND_BARS: int = 2


class MAType(IntEnum):
    """Moving average type selector matching StrategyQuant X."""

    SMA = 1
    EMA = 2
    WMA = 3
    HULL = 4


def round_value(val: float, precision: int = DEFAULT_COMPARISON_PRECISION) -> float:
    """Round a floating-point value to a specified decimal precision.

    Args:
        val: Numeric float value.
        precision: Number of decimal digits to round to.

    Returns:
        Rounded float value, or NaN if input is NaN.
    """
    if math.isnan(val):
        return float("nan")
    return round(float(val), precision)


def resolve_shift_value(target: Any, shift: int = 0) -> float:
    """Resolve numerical value from scalar, array, series, or callable at shift.

    Args:
        target: Float scalar, Sequence, np.ndarray, IndicatorSeries, or Callable.
        shift: Historical bar offset where 0 is newest bar, 1 is 1 bar ago.

    Returns:
        Float value at the given shift, or NaN if out of bounds or invalid.
    """
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
        if 0 <= shift < n:
            return float(target[-(1 + shift)])
        return float("nan")

    try:
        return float(target)
    except TypeError, ValueError:
        return float("nan")


def is_greater(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether left value is strictly greater than right value.

    Args:
        left: Left operand (scalar, series, array, or callable).
        right: Right operand (scalar, series, array, or callable).
        shift: Historical bar offset.
        precision: Rounding decimal precision (default 6).

    Returns:
        True if left > right after rounding, False otherwise.
    """
    val1 = round_value(resolve_shift_value(left, shift), precision)
    val2 = round_value(resolve_shift_value(right, shift), precision)
    res = not (math.isnan(val1) or math.isnan(val2)) and val1 > val2
    logger.debug(
        "FR-SERVICES-COMPARISON-BASIC: is_greater(shift=%d, p=%d) "
        "val1=%s, val2=%s -> %s",
        shift,
        precision,
        val1,
        val2,
        res,
    )
    return res


def is_lower(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether left value is strictly lower than right value.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.
        precision: Rounding decimal precision (default 6).

    Returns:
        True if left < right after rounding, False otherwise.
    """
    val1 = round_value(resolve_shift_value(left, shift), precision)
    val2 = round_value(resolve_shift_value(right, shift), precision)
    res = not (math.isnan(val1) or math.isnan(val2)) and val1 < val2
    logger.debug(
        "FR-SERVICES-COMPARISON-BASIC: is_lower(shift=%d, p=%d) val1=%s, val2=%s -> %s",
        shift,
        precision,
        val1,
        val2,
        res,
    )
    return res


def is_greater_or_equal(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether left value is greater than or equal to right value.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.
        precision: Rounding decimal precision (default 6).

    Returns:
        True if left >= right after rounding, False otherwise.
    """
    val1 = round_value(resolve_shift_value(left, shift), precision)
    val2 = round_value(resolve_shift_value(right, shift), precision)
    res = not (math.isnan(val1) or math.isnan(val2)) and val1 >= val2
    logger.debug(
        "FR-SERVICES-COMPARISON-BASIC: is_greater_or_equal(shift=%d, p=%d) "
        "val1=%s, val2=%s -> %s",
        shift,
        precision,
        val1,
        val2,
        res,
    )
    return res


def is_lower_or_equal(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether left value is lower than or equal to right value.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.
        precision: Rounding decimal precision (default 6).

    Returns:
        True if left <= right after rounding, False otherwise.
    """
    val1 = round_value(resolve_shift_value(left, shift), precision)
    val2 = round_value(resolve_shift_value(right, shift), precision)
    res = not (math.isnan(val1) or math.isnan(val2)) and val1 <= val2
    logger.debug(
        "FR-SERVICES-COMPARISON-BASIC: is_lower_or_equal(shift=%d, p=%d) "
        "val1=%s, val2=%s -> %s",
        shift,
        precision,
        val1,
        val2,
        res,
    )
    return res


def equals(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether left value equals right value within rounding precision.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.
        precision: Rounding decimal precision (default 6).

    Returns:
        True if left == right after rounding, False otherwise.
    """
    val1 = round_value(resolve_shift_value(left, shift), precision)
    val2 = round_value(resolve_shift_value(right, shift), precision)
    res = not (math.isnan(val1) or math.isnan(val2)) and val1 == val2
    logger.debug(
        "FR-SERVICES-COMPARISON-BASIC: equals(shift=%d, p=%d) val1=%s, val2=%s -> %s",
        shift,
        precision,
        val1,
        val2,
        res,
    )
    return res


def not_equals(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether left value does not equal right value within precision.

    Args:
        left: Left operand.
        right: Right operand.
        shift: Historical bar offset.
        precision: Rounding decimal precision (default 6).

    Returns:
        True if left != right after rounding, False otherwise.
    """
    val1 = round_value(resolve_shift_value(left, shift), precision)
    val2 = round_value(resolve_shift_value(right, shift), precision)
    res = not (math.isnan(val1) or math.isnan(val2)) and val1 != val2
    logger.debug(
        "FR-SERVICES-COMPARISON-BASIC: not_equals(shift=%d, p=%d) "
        "val1=%s, val2=%s -> %s",
        shift,
        precision,
        val1,
        val2,
        res,
    )
    return res


def crosses_above(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether left crossed above right between shift + 1 and shift.

    Matches SQX CrossesAbove: Left(1) < Right(1) and Left(0) > Right(0).

    Args:
        left: Left series or callable.
        right: Right series or callable.
        shift: Current bar offset (0 for newest bar).
        precision: Rounding decimal precision (default 6).

    Returns:
        True if crossover occurred, False otherwise.
    """
    val11 = round_value(resolve_shift_value(left, shift + 1), precision)
    val21 = round_value(resolve_shift_value(right, shift + 1), precision)
    val10 = round_value(resolve_shift_value(left, shift), precision)
    val20 = round_value(resolve_shift_value(right, shift), precision)

    if math.isnan(val11) or math.isnan(val21) or math.isnan(val10) or math.isnan(val20):
        res = False
    else:
        res = val11 < val21 and val10 > val20

    logger.debug(
        "FR-SERVICES-COMPARISON-CROSSOVER: crosses_above(shift=%d) "
        "prev=(%s, %s), curr=(%s, %s) -> %s",
        shift,
        val11,
        val21,
        val10,
        val20,
        res,
    )
    return res


def crosses_below(
    left: Any,
    right: Any,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether left crossed below right between shift + 1 and shift.

    Matches SQX CrossesBelow: Left(1) > Right(1) and Left(0) < Right(0).

    Args:
        left: Left series or callable.
        right: Right series or callable.
        shift: Current bar offset (0 for newest bar).
        precision: Rounding decimal precision (default 6).

    Returns:
        True if cross-under occurred, False otherwise.
    """
    val11 = round_value(resolve_shift_value(left, shift + 1), precision)
    val21 = round_value(resolve_shift_value(right, shift + 1), precision)
    val10 = round_value(resolve_shift_value(left, shift), precision)
    val20 = round_value(resolve_shift_value(right, shift), precision)

    if math.isnan(val11) or math.isnan(val21) or math.isnan(val10) or math.isnan(val20):
        res = False
    else:
        res = val11 > val21 and val10 < val20

    logger.debug(
        "FR-SERVICES-COMPARISON-CROSSOVER: crosses_below(shift=%d) "
        "prev=(%s, %s), curr=(%s, %s) -> %s",
        shift,
        val11,
        val21,
        val10,
        val20,
        res,
    )
    return res


def is_rising(
    indicator: Any,
    bars: int = 2,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator is rising monotonically over a bar window.

    Matches SQX IsRising: walks forward from oldest bar (bars + shift - 1)
    to shift. Returns False if falling or if equal while not_strict is False.
    Requires at least one strictly rising step.

    Args:
        indicator: Series or callable providing historical values.
        bars: Number of bars the value must be rising (minimum 2).
        shift: Shift offset of the latest bar evaluated.
        not_strict: If True, equal adjacent values are permitted.
        precision: Rounding decimal precision (default 6).

    Returns:
        True if rising over the specified window, False otherwise.
    """
    if bars < MIN_TREND_BARS:
        logger.debug(
            "FR-SERVICES-COMPARISON-TREND: is_rising bars=%d < %d -> False",
            bars,
            MIN_TREND_BARS,
        )
        return False

    prev_val = round_value(resolve_shift_value(indicator, bars + shift - 1), precision)
    if math.isnan(prev_val):
        return False

    at_least_once = False
    for i in range(1, bars):
        curr_val = round_value(
            resolve_shift_value(indicator, bars + shift - 1 - i), precision
        )
        if math.isnan(curr_val):
            return False

        if curr_val < prev_val:
            logger.debug(
                "FR-SERVICES-COMPARISON-TREND: is_rising broke at bar %d "
                "(curr=%s < prev=%s)",
                i,
                curr_val,
                prev_val,
            )
            return False

        if curr_val == prev_val and not not_strict:
            logger.debug(
                "FR-SERVICES-COMPARISON-TREND: is_rising strict equal at bar %d "
                "(val=%s)",
                i,
                curr_val,
            )
            return False

        if curr_val > prev_val:
            at_least_once = True

        prev_val = curr_val

    logger.debug(
        "FR-SERVICES-COMPARISON-TREND: is_rising(bars=%d, shift=%d, "
        "not_strict=%s) -> %s",
        bars,
        shift,
        not_strict,
        at_least_once,
    )
    return at_least_once


def is_falling(
    indicator: Any,
    bars: int = 2,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator is falling monotonically over a bar window.

    Matches SQX IsFalling: walks forward from oldest bar (bars + shift - 1)
    to shift. Returns False if rising or if equal while not_strict is False.
    Requires at least one strictly falling step.

    Args:
        indicator: Series or callable providing historical values.
        bars: Number of bars the value must be falling (minimum 2).
        shift: Shift offset of the latest bar evaluated.
        not_strict: If True, equal adjacent values are permitted.
        precision: Rounding decimal precision (default 6).

    Returns:
        True if falling over the specified window, False otherwise.
    """
    if bars < MIN_TREND_BARS:
        logger.debug(
            "FR-SERVICES-COMPARISON-TREND: is_falling bars=%d < %d -> False",
            bars,
            MIN_TREND_BARS,
        )
        return False

    prev_val = round_value(resolve_shift_value(indicator, bars + shift - 1), precision)
    if math.isnan(prev_val):
        return False

    at_least_once = False
    for i in range(1, bars):
        curr_val = round_value(
            resolve_shift_value(indicator, bars + shift - 1 - i), precision
        )
        if math.isnan(curr_val):
            return False

        if curr_val > prev_val:
            logger.debug(
                "FR-SERVICES-COMPARISON-TREND: is_falling broke at bar %d "
                "(curr=%s > prev=%s)",
                i,
                curr_val,
                prev_val,
            )
            return False

        if curr_val == prev_val and not not_strict:
            logger.debug(
                "FR-SERVICES-COMPARISON-TREND: is_falling strict equal at bar %d "
                "(val=%s)",
                i,
                curr_val,
            )
            return False

        if curr_val < prev_val:
            at_least_once = True

        prev_val = curr_val

    logger.debug(
        "FR-SERVICES-COMPARISON-TREND: is_falling(bars=%d, shift=%d, "
        "not_strict=%s) -> %s",
        bars,
        shift,
        not_strict,
        at_least_once,
    )
    return at_least_once


def is_greater_count(
    left: Any,
    right: Any,
    bars: int = 2,
    *,
    shift: int = 0,
    not_strict: bool = False,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether left > right remains true across a window of bars.

    Matches SQX IsGreaterCount with 5-decimal rounding precision.

    Args:
        left: Left series or callable.
        right: Right series or callable.
        bars: Number of consecutive bars condition must hold (minimum 1).
        shift: Shift offset of evaluation.
        not_strict: If True, equality is tolerated.
        precision: Rounding decimal precision (default 5).

    Returns:
        True if condition held and left > right at least once, False otherwise.
    """
    if bars < 1:
        return False

    at_least_once = False
    for i in range(bars):
        idx = shift + i
        l_val = round_value(resolve_shift_value(left, idx), precision)
        r_val = round_value(resolve_shift_value(right, idx), precision)

        if math.isnan(l_val) or math.isnan(r_val):
            return False

        if l_val < r_val:
            logger.debug(
                "FR-SERVICES-COMPARISON-COUNT: is_greater_count failed at shift %d "
                "(left=%s < right=%s)",
                idx,
                l_val,
                r_val,
            )
            return False

        if l_val == r_val and not not_strict:
            logger.debug(
                "FR-SERVICES-COMPARISON-COUNT: is_greater_count equal at shift %d "
                "(val=%s)",
                idx,
                l_val,
            )
            return False

        if l_val > r_val:
            at_least_once = True

    logger.debug(
        "FR-SERVICES-COMPARISON-COUNT: is_greater_count(bars=%d, shift=%d, "
        "not_strict=%s) -> %s",
        bars,
        shift,
        not_strict,
        at_least_once,
    )
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
    """Evaluate whether left < right remains true across a window of bars.

    Matches SQX IsLowerCount with 5-decimal rounding precision.

    Args:
        left: Left series or callable.
        right: Right series or callable.
        bars: Number of consecutive bars condition must hold (minimum 1).
        shift: Shift offset of evaluation.
        not_strict: If True, equality is tolerated.
        precision: Rounding decimal precision (default 5).

    Returns:
        True if condition held and left < right at least once, False otherwise.
    """
    if bars < 1:
        return False

    at_least_once = False
    for i in range(bars):
        idx = shift + i
        l_val = round_value(resolve_shift_value(left, idx), precision)
        r_val = round_value(resolve_shift_value(right, idx), precision)

        if math.isnan(l_val) or math.isnan(r_val):
            return False

        if l_val > r_val:
            logger.debug(
                "FR-SERVICES-COMPARISON-COUNT: is_lower_count failed at shift %d "
                "(left=%s > right=%s)",
                idx,
                l_val,
                r_val,
            )
            return False

        if l_val == r_val and not not_strict:
            logger.debug(
                "FR-SERVICES-COMPARISON-COUNT: is_lower_count equal at shift %d "
                "(val=%s)",
                idx,
                l_val,
            )
            return False

        if l_val < r_val:
            at_least_once = True

    logger.debug(
        "FR-SERVICES-COMPARISON-COUNT: is_lower_count(bars=%d, shift=%d, "
        "not_strict=%s) -> %s",
        bars,
        shift,
        not_strict,
        at_least_once,
    )
    return at_least_once


def is_greater_percentile(
    indicator: Any,
    percentile: float = 50.0,
    bars: int = 10,
    shift: int = 0,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether indicator value exceeds percentile rank over past bars.

    Matches SQX IsGreaterPercentil:
    count starts at 1, count incremented whenever currVal > prevVal(shift+i).
    percrank = (count / bars) * 100. Returns percrank > round(percentile, 5).

    Args:
        indicator: Indicator series or callable.
        percentile: Percentile threshold in range [0, 100].
        bars: Number of historical bars to evaluate.
        shift: Shift offset of evaluated bar.
        precision: Rounding decimal precision (default 5).

    Returns:
        True if percentile rank exceeds threshold, False otherwise.
    """
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

    percrank = (count / float(bars)) * 100.0
    rb = round_value(percentile, precision)
    res = percrank > rb

    logger.debug(
        "FR-SERVICES-COMPARISON-PERCENTILE: is_greater_percentile "
        "rank=%.2f%% > thresh=%.2f%% (count=%d, bars=%d) -> %s",
        percrank,
        rb,
        count,
        bars,
        res,
    )
    return res


def is_lower_percentile(
    indicator: Any,
    percentile: float = 50.0,
    bars: int = 10,
    shift: int = 0,
    precision: int = DEFAULT_COUNT_PRECISION,
) -> bool:
    """Evaluate whether indicator value falls below percentile rank over past bars.

    Matches SQX IsLowerPercentil:
    count starts at 1, count incremented whenever currVal < prevVal(shift+i).
    percrank = (count / bars) * 100. Returns percrank > round(percentile, 5).

    Args:
        indicator: Indicator series or callable.
        percentile: Percentile threshold in range [0, 100].
        bars: Number of historical bars to evaluate.
        shift: Shift offset of evaluated bar.
        precision: Rounding decimal precision (default 5).

    Returns:
        True if lower percentile rank exceeds threshold, False otherwise.
    """
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

    percrank = (count / float(bars)) * 100.0
    rb = round_value(percentile, precision)
    res = percrank > rb

    logger.debug(
        "FR-SERVICES-COMPARISON-PERCENTILE: is_lower_percentile "
        "rank=%.2f%% > thresh=%.2f%% (count=%d, bars=%d) -> %s",
        percrank,
        rb,
        count,
        bars,
        res,
    )
    return res


def calculate_wma(
    indicator: Any,
    period: int,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> float:
    """Calculate Weighted Moving Average (WMA) matching SQX IndicatorMA.

    Formula: sum(round(Ind[shift+i], 6) * (period - i)) / sum(period - i).

    Args:
        indicator: Series or callable.
        period: Number of periods.
        shift: Historical bar offset.
        precision: Decimal rounding precision.

    Returns:
        WMA value as float, or NaN if insufficient data.
    """
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

    if weight_sum == 0.0:
        return float("nan")

    res = round_value(weighted_sum / weight_sum, precision)
    logger.debug(
        "FR-SERVICES-COMPARISON-MA: calculate_wma(period=%d, shift=%d) = %s",
        period,
        shift,
        res,
    )
    return res


def _calculate_sma(
    indicator: Any,
    period: int,
    shift: int,
    precision: int,
) -> float:
    """Compute Simple Moving Average sum-over-period."""
    total = 0.0
    for i in range(period):
        val = round_value(resolve_shift_value(indicator, shift + i), precision)
        if math.isnan(val):
            return float("nan")
        total += val
    return round_value(total / float(period), precision)


def _calculate_ema(
    indicator: Any,
    period: int,
    shift: int,
    precision: int,
) -> float:
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

    return round_value(prev_ema, precision)


def _calculate_hull(
    indicator: Any,
    period: int,
    shift: int,
    precision: int,
) -> float:
    """Compute Hull Moving Average matching SQX 2*WMA(n/2) - WMA(n)."""
    half_period = max(1, period // 2)
    half_wma = calculate_wma(indicator, half_period, shift, precision)
    full_wma = calculate_wma(indicator, period, shift, precision)
    if math.isnan(half_wma) or math.isnan(full_wma):
        return float("nan")
    return round_value(2.0 * half_wma - full_wma, precision)


def calculate_ma(
    indicator: Any,
    period: int,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> float:
    """Calculate Moving Average matching SQX IndicatorMAComparisonBlockAbstract.

    Supports:
    - 1: Simple MA (SMA)
    - 2: Exponential MA (EMA)
    - 3: Weighted MA (WMA)
    - 4: Hull MA (2 * WMA(period // 2) - WMA(period))

    Args:
        indicator: Series or callable.
        period: Number of periods.
        ma_type: MA type (1=SMA, 2=EMA, 3=WMA, 4=Hull).
        shift: Historical bar offset.
        precision: Decimal rounding precision.

    Returns:
        Computed MA value as float, or NaN if insufficient data.

    Raises:
        ValueError: If ma_type is unrecognized.
    """
    if period <= 0:
        return float("nan")

    type_code = int(ma_type)

    if type_code == MAType.SMA:
        res = _calculate_sma(indicator, period, shift, precision)
    elif type_code == MAType.EMA:
        res = _calculate_ema(indicator, period, shift, precision)
    elif type_code == MAType.WMA:
        res = calculate_wma(indicator, period, shift, precision)
    elif type_code == MAType.HULL:
        res = _calculate_hull(indicator, period, shift, precision)
    else:
        raise ValueError(f"Unsupported MAType: {ma_type}")

    logger.debug(
        "FR-SERVICES-COMPARISON-MA: calculate_ma(period=%d, type=%d, shift=%d) = %s",
        period,
        type_code,
        shift,
        res,
    )
    return res


def indicator_above_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator is above its Moving Average at shift.

    Args:
        indicator: Indicator series or callable.
        period: Moving Average period.
        ma_type: MA type (SMA=1, EMA=2, WMA=3, HULL=4).
        shift: Historical bar offset.
        precision: Rounding decimal precision.

    Returns:
        True if Indicator[shift] > MA[shift], False otherwise.
    """
    ind_val = round_value(resolve_shift_value(indicator, shift), precision)
    ma_val = calculate_ma(indicator, period, ma_type, shift, precision)
    res = not (math.isnan(ind_val) or math.isnan(ma_val)) and ind_val > ma_val
    logger.debug(
        "FR-SERVICES-COMPARISON-MA: indicator_above_ma ind=%s, ma=%s -> %s",
        ind_val,
        ma_val,
        res,
    )
    return res


def indicator_below_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator is below its Moving Average at shift.

    Args:
        indicator: Indicator series or callable.
        period: Moving Average period.
        ma_type: MA type (SMA=1, EMA=2, WMA=3, HULL=4).
        shift: Historical bar offset.
        precision: Rounding decimal precision.

    Returns:
        True if Indicator[shift] < MA[shift], False otherwise.
    """
    ind_val = round_value(resolve_shift_value(indicator, shift), precision)
    ma_val = calculate_ma(indicator, period, ma_type, shift, precision)
    res = not (math.isnan(ind_val) or math.isnan(ma_val)) and ind_val < ma_val
    logger.debug(
        "FR-SERVICES-COMPARISON-MA: indicator_below_ma ind=%s, ma=%s -> %s",
        ind_val,
        ma_val,
        res,
    )
    return res


def indicator_crosses_above_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator crosses above its MA from shift + 1 to shift.

    Args:
        indicator: Indicator series or callable.
        period: Moving Average period.
        ma_type: MA type (SMA=1, EMA=2, WMA=3, HULL=4).
        shift: Historical bar offset.
        precision: Rounding decimal precision.

    Returns:
        True if Ind[shift+1] < MA[shift+1] and Ind[shift] > MA[shift].
    """
    ind_curr = round_value(resolve_shift_value(indicator, shift), precision)
    ind_prev = round_value(resolve_shift_value(indicator, shift + 1), precision)
    ma_curr = calculate_ma(indicator, period, ma_type, shift, precision)
    ma_prev = calculate_ma(indicator, period, ma_type, shift + 1, precision)

    if (
        math.isnan(ind_curr)
        or math.isnan(ind_prev)
        or math.isnan(ma_curr)
        or math.isnan(ma_prev)
    ):
        res = False
    else:
        res = ind_prev < ma_prev and ind_curr > ma_curr

    logger.debug(
        "FR-SERVICES-COMPARISON-MA: indicator_crosses_above_ma "
        "prev=(%s, %s), curr=(%s, %s) -> %s",
        ind_prev,
        ma_prev,
        ind_curr,
        ma_curr,
        res,
    )
    return res


def indicator_crosses_below_ma(
    indicator: Any,
    period: int = 14,
    ma_type: int | MAType = MAType.SMA,
    shift: int = 0,
    precision: int = DEFAULT_COMPARISON_PRECISION,
) -> bool:
    """Evaluate whether indicator crosses below its MA from shift + 1 to shift.

    Args:
        indicator: Indicator series or callable.
        period: Moving Average period.
        ma_type: MA type (SMA=1, EMA=2, WMA=3, HULL=4).
        shift: Historical bar offset.
        precision: Rounding decimal precision.

    Returns:
        True if Ind[shift+1] > MA[shift+1] and Ind[shift] < MA[shift].
    """
    ind_curr = round_value(resolve_shift_value(indicator, shift), precision)
    ind_prev = round_value(resolve_shift_value(indicator, shift + 1), precision)
    ma_curr = calculate_ma(indicator, period, ma_type, shift, precision)
    ma_prev = calculate_ma(indicator, period, ma_type, shift + 1, precision)

    if (
        math.isnan(ind_curr)
        or math.isnan(ind_prev)
        or math.isnan(ma_curr)
        or math.isnan(ma_prev)
    ):
        res = False
    else:
        res = ind_prev > ma_prev and ind_curr < ma_curr

    logger.debug(
        "FR-SERVICES-COMPARISON-MA: indicator_crosses_below_ma "
        "prev=(%s, %s), curr=(%s, %s) -> %s",
        ind_prev,
        ma_prev,
        ind_curr,
        ma_curr,
        res,
    )
    return res


def condition_and(*conditions: bool | Callable[[], Any] | Any) -> bool:
    """Evaluate short-circuit logical AND across multiple condition expressions.

    Args:
        *conditions: Booleans, numbers, or callable functions returning booleans.

    Returns:
        True if all conditions evaluate True, False on first False evaluation.
    """
    for cond in conditions:
        val = cond() if callable(cond) else cond
        if not bool(val):
            logger.debug(
                "FR-SERVICES-COMPARISON-LOGIC: condition_and short-circuited False"
            )
            return False

    logger.debug("FR-SERVICES-COMPARISON-LOGIC: condition_and evaluated True")
    return True


def condition_or(*conditions: bool | Callable[[], Any] | Any) -> bool:
    """Evaluate short-circuit logical OR across multiple condition expressions.

    Args:
        *conditions: Booleans, numbers, or callable functions returning booleans.

    Returns:
        True on first True evaluation, False if all evaluate False.
    """
    for cond in conditions:
        val = cond() if callable(cond) else cond
        if bool(val):
            logger.debug(
                "FR-SERVICES-COMPARISON-LOGIC: condition_or short-circuited True"
            )
            return True

    logger.debug("FR-SERVICES-COMPARISON-LOGIC: condition_or evaluated False")
    return False


def condition_not(condition: bool | float | Callable[[], Any] | Any) -> bool:
    """Evaluate logical NOT on a condition expression.

    Args:
        condition: Boolean, number, or callable returning a boolean or number.

    Returns:
        True if condition evaluates False or 0, False otherwise.
    """
    val = condition() if callable(condition) else condition
    res = not bool(val)
    logger.debug("FR-SERVICES-COMPARISON-LOGIC: condition_not(%s) -> %s", val, res)
    return res


class Comparisons:
    """Consolidated facade for evaluating StrategyQuant X comparison blocks."""

    def __init__(
        self,
        left: Any = None,
        right: Any = None,
        precision: int = DEFAULT_COMPARISON_PRECISION,
    ) -> None:
        """Initialize Comparisons facade with optional default operands.

        Args:
            left: Default left operand.
            right: Default right operand.
            precision: Default rounding precision.
        """
        self._left = left
        self._right = right
        self._precision = precision
        logger.debug(
            "FR-SERVICES-COMPARISONS-FACADE: Initialized facade (p=%d)",
            precision,
        )

    def is_greater(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_greater using instance operands if omitted."""
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
        p = self._precision if precision is None else precision
        return is_greater(l_op, r_op, shift=shift, precision=p)

    def is_lower(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_lower using instance operands if omitted."""
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
        p = self._precision if precision is None else precision
        return is_lower(l_op, r_op, shift=shift, precision=p)

    def is_greater_or_equal(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_greater_or_equal using instance operands if omitted."""
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
        p = self._precision if precision is None else precision
        return is_greater_or_equal(l_op, r_op, shift=shift, precision=p)

    def is_lower_or_equal(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate is_lower_or_equal using instance operands if omitted."""
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
        p = self._precision if precision is None else precision
        return is_lower_or_equal(l_op, r_op, shift=shift, precision=p)

    def equals(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate equals using instance operands if omitted."""
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
        p = self._precision if precision is None else precision
        return equals(l_op, r_op, shift=shift, precision=p)

    def not_equals(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate not_equals using instance operands if omitted."""
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
        p = self._precision if precision is None else precision
        return not_equals(l_op, r_op, shift=shift, precision=p)

    def crosses_above(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate crosses_above using instance operands if omitted."""
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
        p = self._precision if precision is None else precision
        return crosses_above(l_op, r_op, shift=shift, precision=p)

    def crosses_below(
        self,
        left: Any = None,
        right: Any = None,
        shift: int = 0,
        precision: int | None = None,
    ) -> bool:
        """Evaluate crosses_below using instance operands if omitted."""
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
        p = self._precision if precision is None else precision
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
        ind = self._left if indicator is None else indicator
        p = self._precision if precision is None else precision
        return is_rising(
            ind, bars=bars, shift=shift, not_strict=not_strict, precision=p
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
        ind = self._left if indicator is None else indicator
        p = self._precision if precision is None else precision
        return is_falling(
            ind, bars=bars, shift=shift, not_strict=not_strict, precision=p
        )

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
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
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
        l_op = self._left if left is None else left
        r_op = self._right if right is None else right
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
        ind = self._left if indicator is None else indicator
        return is_greater_percentile(
            ind,
            percentile=percentile,
            bars=bars,
            shift=shift,
            precision=precision,
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
        ind = self._left if indicator is None else indicator
        return is_lower_percentile(
            ind,
            percentile=percentile,
            bars=bars,
            shift=shift,
            precision=precision,
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
        ind = self._left if indicator is None else indicator
        p = self._precision if precision is None else precision
        return indicator_above_ma(
            ind, period=period, ma_type=ma_type, shift=shift, precision=p
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
        ind = self._left if indicator is None else indicator
        p = self._precision if precision is None else precision
        return indicator_below_ma(
            ind, period=period, ma_type=ma_type, shift=shift, precision=p
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
        ind = self._left if indicator is None else indicator
        p = self._precision if precision is None else precision
        return indicator_crosses_above_ma(
            ind, period=period, ma_type=ma_type, shift=shift, precision=p
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
        ind = self._left if indicator is None else indicator
        p = self._precision if precision is None else precision
        return indicator_crosses_below_ma(
            ind, period=period, ma_type=ma_type, shift=shift, precision=p
        )
