"""Breakout and Retest pattern detector.

Implements spec ``IND-PT-07`` using the most recently confirmed pivot
low/high from ``structure.pivots`` as the structural level, and the
canonical ``volatility.atr`` (the approved cross-module dependencies).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from app.services.indicators.core.errors import (
    _unwrap_indicator_response,
    guard_public_boundary,
)
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator
from app.services.indicators.patterns._shared import (
    CONFIRMED,
    DETECTED,
    INVALIDATED,
    NONE_STATE,
    build_pattern_config,
    causal_series,
    fetch_atr,
    fetch_pivots,
)
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.indicators.core.contracts import IndicatorConfig
    from app.services.indicators.core.contracts import (
        _MarketDataset as MarketDataset,
    )
    from app.services.indicators.core.results import IndicatorResult

_INDICATOR_VERSION = "1.0.0"


def _scan_side(
    *,
    flag: np.ndarray,
    price: np.ndarray,
    close: np.ndarray,
    low_or_high: np.ndarray,
    atr_values: np.ndarray,
    beta_atr: float,
    tau_price: float,
    m: int,
    first_valid: int,
    bullish: bool,
) -> np.ndarray:
    """Scan one side: bullish breakout above a pivot low, or bearish below a high.

    Args:
        flag: The flag value.
        price: The price value.
        close: The close value.
        low_or_high: The low or high value.
        atr_values: The atr values value.
        beta_atr: The beta atr value.
        tau_price: The tau price value.
        m: The m value.
        first_valid: The first valid value.
        bullish: The bullish value.

    Returns:
        The np.ndarray result.

    Raises:
        None.
    """
    row_count = len(flag)
    state = np.full(row_count, np.nan, dtype="float64")
    level: float | None = None
    active = False
    breakout_index = -1
    retested = False

    for t in range(row_count):
        if t < first_valid:
            continue
        current = NONE_STATE

        if flag[t] == 1.0:
            level = price[t]

        if not active and level is not None:
            broke = (
                close[t] > level + beta_atr * atr_values[t]
                if bullish
                else close[t] < level - beta_atr * atr_values[t]
            )
            if broke:
                active = True
                breakout_index = t
                retested = False
                current = DETECTED

        if active and not retested and level is not None:
            touched = abs(low_or_high[t] - level) <= tau_price
            holding = close[t] > level if bullish else close[t] < level
            if touched and holding:
                retested = True
                current = CONFIRMED
                active = False
            elif (
                close[t] < level - tau_price
                if bullish
                else close[t] > level + tau_price
            ) or t - breakout_index >= m:
                current = INVALIDATED
                active = False
                level = None
            else:
                current = DETECTED

        state[t] = current

    return state


@guard_public_boundary
def breakout_retest(
    data: MarketDataset,
    *,
    left: int,
    right: int,
    atr_period: int,
    beta_atr: float,
    tau_price: float,
    m: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Detect spec ``IND-PT-07`` Breakout and Retest.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        left: Left-bar count fed to ``structure.pivots``.
        right: Right-bar count fed to ``structure.pivots``.
        atr_period: Smoothing period fed to ``volatility.atr``.
        beta_atr: Required non-negative breakout confirmation buffer, in
            ATR multiples.
        tau_price: Required non-negative retest price tolerance.
        m: Required maximum retest bars, at least one.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ``IndicatorResult`` carrying
        ``breakout_retest_bullish_state`` and
        ``breakout_retest_bearish_state`` (``0``=NONE, ``1``=DETECTED,
        ``2``=CONFIRMED, ``3``=INVALIDATED).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating breakout_retest for %s", data.symbol)
    parameters = (
        ("atr_period", atr_period),
        ("beta_atr", beta_atr),
        ("left", left),
        ("m", m),
        ("right", right),
        ("tau_price", tau_price),
    )
    resolved_config = build_pattern_config("breakout_retest", parameters, config)
    _unwrap_indicator_response(
        validate_indicator("breakout_retest", data, resolved_config)
    )
    high_flag, high_price, low_flag, low_price = fetch_pivots(
        data, left=left, right=right
    )
    atr_values = fetch_atr(data, atr_period=atr_period)
    close = np.asarray(
        [float(record.close) for record in data.records], dtype="float64"
    )
    low = np.asarray([float(record.low) for record in data.records], dtype="float64")
    high = np.asarray([float(record.high) for record in data.records], dtype="float64")
    row_count = len(close)
    is_valid = np.isfinite(atr_values) & np.isfinite(high_flag)
    first_valid = int(np.argmax(is_valid)) if is_valid.any() else row_count

    bullish_state = _scan_side(
        flag=low_flag,
        price=low_price,
        close=close,
        low_or_high=low,
        atr_values=atr_values,
        beta_atr=beta_atr,
        tau_price=tau_price,
        m=m,
        first_valid=first_valid,
        bullish=True,
    )
    bearish_state = _scan_side(
        flag=high_flag,
        price=high_price,
        close=close,
        low_or_high=high,
        atr_values=atr_values,
        beta_atr=beta_atr,
        tau_price=tau_price,
        m=m,
        first_valid=first_valid,
        bullish=False,
    )
    is_valid[:first_valid] = False

    index, computed_from_start, computed_from_end, available_at, unavailable_reason = (
        causal_series(data, is_valid)
    )
    output_columns = (
        f"breakout_retest_bullish_state_{left}_{right}_{atr_period}",
        f"breakout_retest_bearish_state_{left}_{right}_{atr_period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, bullish_state, np.nan),
            output_columns[1]: np.where(is_valid, bearish_state, np.nan),
        },
        index=index,
    )

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=output_columns,
        output_values=output_values,
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["breakout_retest"]
