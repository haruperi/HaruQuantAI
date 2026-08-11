# ruff: noqa: PLR2004
"""Three-Bar Reversal pattern detector.

Implements spec ``IND-PT-10`` directly over three consecutive closed OHLC
bars and the canonical ``volatility.atr`` (the approved cross-module
dependency). No pivot lookback is required for this pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from app.services.indicators.core.errors import (
    _unwrap_indicator_response,
    guard_public_boundary,
)
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator
from app.services.indicators.patterns._shared import build_pattern_config, fetch_atr
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.indicators.core.contracts import IndicatorConfig
    from app.services.indicators.core.contracts import (
        _MarketDataset as MarketDataset,
    )
    from app.services.indicators.core.contracts import (
        _OHLCVRecord as OHLCVRecord,
    )
    from app.services.indicators.core.results import IndicatorResult

_INDICATOR_VERSION = "1.0.0"
# 0=NONE, 1=BULLISH_3BAR_REVERSAL, 2=BEARISH_3BAR_REVERSAL
_NONE, _BULLISH, _BEARISH = 0.0, 1.0, 2.0


@guard_public_boundary
def three_bar_reversal(
    data: MarketDataset,
    *,
    atr_period: int,
    body_min_atr: float,
    confirm_fraction: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Detect spec ``IND-PT-10`` Bullish/Bearish Three-Bar Reversal.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        atr_period: Smoothing period fed to ``volatility.atr``.
        body_min_atr: Required non-negative minimum first-bar body, in ATR
            multiples.
        confirm_fraction: Required non-negative confirmation-bar excursion
            fraction of the first bar's body.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ``IndicatorResult`` carrying ``reversal_state``
        (``0``=NONE, ``1``=BULLISH_3BAR_REVERSAL, ``2``=BEARISH_3BAR_REVERSAL).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating three_bar_reversal for %s", data.symbol)
    parameters = (
        ("atr_period", atr_period),
        ("body_min_atr", body_min_atr),
        ("confirm_fraction", confirm_fraction),
    )
    resolved_config = build_pattern_config("three_bar_reversal", parameters, config)
    _unwrap_indicator_response(
        validate_indicator("three_bar_reversal", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    open_price = np.asarray([float(r.open) for r in records], dtype="float64")
    high = np.asarray([float(r.high) for r in records], dtype="float64")
    low = np.asarray([float(r.low) for r in records], dtype="float64")
    close = np.asarray([float(r.close) for r in records], dtype="float64")
    atr_values = fetch_atr(data, atr_period=atr_period)
    row_count = len(records)

    state = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    if row_count > 2:
        atr_prior = atr_values[:-2]
        candidate = np.isfinite(atr_prior)
        o0, h0, l0, c0 = open_price[:-2], high[:-2], low[:-2], close[:-2]
        h1, l1 = high[1:-1], low[1:-1]
        c2 = close[2:]
        body0 = np.abs(o0 - c0)
        strong_body = body0 >= body_min_atr * np.where(candidate, atr_prior, np.nan)

        bearish_first = c0 < o0
        lower_low_second = l1 < l0
        bull_confirm = (c2 > h1) & (c2 > o0 + confirm_fraction * (o0 - c0))
        bullish = bearish_first & strong_body & lower_low_second & bull_confirm

        bullish_first_bar = c0 > o0
        higher_high_second = h1 > h0
        bear_confirm = (c2 < l1) & (c2 < o0 - confirm_fraction * (c0 - o0))
        bearish = bullish_first_bar & strong_body & higher_high_second & bear_confirm

        result_state = np.where(bullish, _BULLISH, np.where(bearish, _BEARISH, _NONE))
        state[2:] = np.where(candidate, result_state, np.nan)
        is_valid[2:] = candidate

    computed_from_start = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    computed_from_end = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    if is_valid.any():
        computed_from_start[is_valid] = records[0].timestamp
        computed_from_end[is_valid] = index[is_valid]
    available_at = pd.Series([record.available_at for record in records], index=index)
    cumulative_available = available_at.cummax()
    available_at[is_valid] = cumulative_available[is_valid]
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_valid] = "warmup"

    output_column = f"reversal_state_{atr_period}"
    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=(output_column,),
        output_values=pd.DataFrame(
            {output_column: np.where(is_valid, state, np.nan)}, index=index
        ),
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["three_bar_reversal"]
