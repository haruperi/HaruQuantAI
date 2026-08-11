# ruff: noqa: PLR0915
"""Flag / Pennant pattern detector.

Implements spec ``IND-PT-04`` over closed prices and the canonical
``volatility.atr`` (the approved cross-module dependency). Each bar's
impulse/consolidation geometry is evaluated independently from the fixed
trailing ``impulse_lookback``/``consolidation_bars`` windows ending at that
bar, so no persistent cross-bar state machine is required for this
pattern.
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
from app.services.indicators.patterns._shared import (
    build_pattern_config,
    fetch_atr,
)
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
# consolidation_type: 0=NONE, 1=FLAG, 2=PENNANT
_NONE_TYPE, _FLAG, _PENNANT = 0.0, 1.0, 2.0
# breakout_state: 0=NONE, 1=DETECTED, 2=BREAKOUT_UP, 3=BREAKOUT_DOWN
_NO_PATTERN, _DETECTED, _BREAKOUT_UP, _BREAKOUT_DOWN = 0.0, 1.0, 2.0, 3.0


@guard_public_boundary
def flag_pennant(
    data: MarketDataset,
    *,
    atr_period: int,
    impulse_lookback: int,
    consolidation_bars: int,
    impulse_min_atr: float,
    retrace_max: float,
    beta_atr: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Detect spec ``IND-PT-04`` Flag and Pennant consolidations.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        atr_period: Smoothing period fed to ``volatility.atr``.
        impulse_lookback: Required bar count spanning the impulse leg, at
            least one.
        consolidation_bars: Required bar count spanning the trailing
            consolidation window, at least two.
        impulse_min_atr: Required non-negative minimum impulse magnitude,
            in ATR multiples.
        retrace_max: Required consolidation retracement ceiling, as a
            fraction of the impulse magnitude.
        beta_atr: Required non-negative breakout confirmation buffer, in
            ATR multiples.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ``IndicatorResult`` carrying
        ``consolidation_type`` (``0``=NONE, ``1``=FLAG, ``2``=PENNANT) and
        ``breakout_state`` (``0``=NONE, ``1``=DETECTED, ``2``=BREAKOUT_UP,
        ``3``=BREAKOUT_DOWN).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating flag_pennant for %s", data.symbol)
    parameters = (
        ("atr_period", atr_period),
        ("beta_atr", beta_atr),
        ("consolidation_bars", consolidation_bars),
        ("impulse_lookback", impulse_lookback),
        ("impulse_min_atr", impulse_min_atr),
        ("retrace_max", retrace_max),
    )
    resolved_config = build_pattern_config("flag_pennant", parameters, config)
    _unwrap_indicator_response(
        validate_indicator("flag_pennant", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(r.high) for r in records], dtype="float64")
    low = np.asarray([float(r.low) for r in records], dtype="float64")
    close = np.asarray([float(r.close) for r in records], dtype="float64")
    atr_values = fetch_atr(data, atr_period=atr_period)
    row_count = len(records)
    warmup = impulse_lookback + consolidation_bars
    is_valid = np.zeros(row_count, dtype=bool)

    consolidation_type = np.full(row_count, np.nan, dtype="float64")
    breakout_state = np.full(row_count, np.nan, dtype="float64")

    for t in range(row_count):
        if t < warmup or not np.isfinite(atr_values[t - consolidation_bars]):
            continue
        impulse_end = t - consolidation_bars
        impulse_start = impulse_end - impulse_lookback
        if impulse_start < 0:
            continue
        is_valid[t] = True
        impulse_move = close[impulse_end] - close[impulse_start]
        base_atr = atr_values[impulse_end]
        current_type = _NONE_TYPE
        current_state = _NO_PATTERN
        if np.isfinite(base_atr) and base_atr > 0.0 and impulse_move != 0.0:
            impulse_atr = abs(impulse_move) / base_atr
            if impulse_atr >= impulse_min_atr:
                window_close = close[impulse_end : t + 1]
                direction = np.sign(impulse_move)
                opposite_excursion = (
                    float(np.min(window_close))
                    if direction > 0
                    else float(np.max(window_close))
                )
                retrace = abs(opposite_excursion - close[impulse_end]) / abs(
                    impulse_move
                )
                if retrace <= retrace_max:
                    ranges = high[impulse_end : t + 1] - low[impulse_end : t + 1]
                    half = max(1, len(ranges) // 2)
                    first_half_range = float(np.mean(ranges[:half]))
                    second_half_range = (
                        float(np.mean(ranges[half:]))
                        if len(ranges) > half
                        else (first_half_range)
                    )
                    current_type = (
                        _PENNANT
                        if second_half_range < 0.75 * first_half_range
                        else _FLAG
                    )
                    consolidation_extreme = (
                        float(np.max(window_close))
                        if direction > 0
                        else float(np.min(window_close))
                    )
                    if (
                        direction > 0
                        and close[t] > consolidation_extreme + beta_atr * atr_values[t]
                    ):
                        current_state = _BREAKOUT_UP
                    elif (
                        direction < 0
                        and close[t] < consolidation_extreme - beta_atr * atr_values[t]
                    ):
                        current_state = _BREAKOUT_DOWN
                    else:
                        current_state = _DETECTED
        consolidation_type[t] = current_type
        breakout_state[t] = current_state

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

    output_columns = (
        f"consolidation_type_{atr_period}_{impulse_lookback}_{consolidation_bars}",
        f"consolidation_breakout_state_{atr_period}_{impulse_lookback}_{consolidation_bars}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, consolidation_type, np.nan),
            output_columns[1]: np.where(is_valid, breakout_state, np.nan),
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


__all__ = ["flag_pennant"]
