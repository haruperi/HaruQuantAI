"""Shared internal utilities and numerical helpers for comparison condition blocks.

Description:
    Provides numerical helpers, moving average calculations (SMA, EMA,
    WMA, Hull), operand shift resolution, rounding utilities, and
    non-silent diagnostic logging for quantitative comparison blocks.
Purpose:
    FEAT-COMPARISONS-BLOCKS: Provide shared calculation and logging
    utilities for comparison blocks.
Key Capabilities:
    - FR-comparison-helpers: Operand resolution and moving average computations.
    - FR-comparison-logging: Non-silent debug requirement logging.
Python API Usage:
    from app.extend.blocks.comparisons._common import (
        _log_comparison,
        calculate_ma,
        resolve_shift_value,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_comparisons.py --no-cov
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from app.core.data.contracts import DataframeSeries
from app.core.enums import MAType
from app.core.host.logging import get_logger
from app.core.trading.blocks.series import round_value

__all__ = [
    "DEFAULT_COMPARISON_PRECISION",
    "DEFAULT_COUNT_PRECISION",
    "MIN_TREND_BARS",
    "_log_comparison",
    "calculate_ma",
    "calculate_wma",
    "resolve_shift_value",
    "round_value",
]

DEFAULT_COMPARISON_PRECISION: int = 6
DEFAULT_COUNT_PRECISION: int = 5
MIN_TREND_BARS: int = 2


logger = get_logger(__name__)


def _log_comparison(name: str, result: bool) -> bool:
    """Log comparison block evaluation and return boolean result."""
    logger.debug("FR-LIBS-COMPARISON-EVAL: %s result=%s", name, result)
    return result


def resolve_shift_value(target: Any, shift: int = 0) -> float:
    """Resolve numerical value from scalar, array, series, or callable at shift.

    Scalars evaluate to their constant float value across all historical shifts.
    """
    if isinstance(target, DataframeSeries):
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
