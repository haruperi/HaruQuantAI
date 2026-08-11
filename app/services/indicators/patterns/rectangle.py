"""Rectangle / Trading Range pattern detector.

Implements spec ``IND-PT-09`` over confirmed pivots from
``structure.pivots`` and the canonical ``volatility.atr`` (evaluated
independently per bar, matching ``patterns.triangle``'s approach).
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
    build_pattern_config,
    causal_series,
    fetch_atr,
    fetch_pivots,
    fit_line,
    recent_pivot_points,
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
# 0=NONE, 1=RANGE_ACTIVE, 2=BREAKOUT_UP, 3=BREAKOUT_DOWN
_NONE_STATE, _RANGE_ACTIVE, _BREAKOUT_UP, _BREAKOUT_DOWN = 0.0, 1.0, 2.0, 3.0


@guard_public_boundary
def rectangle(
    data: MarketDataset,
    *,
    left: int,
    right: int,
    atr_period: int,
    lookback: int,
    min_touches: int,
    slope_flat: float,
    tolerance: float,
    beta_atr: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Detect spec ``IND-PT-09`` Rectangle / Trading Range.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        left: Left-bar count fed to ``structure.pivots``.
        right: Right-bar count fed to ``structure.pivots``.
        atr_period: Smoothing period fed to ``volatility.atr``.
        lookback: Required trailing bar window searched for touches, at
            least ``2 * min_touches``.
        min_touches: Required minimum confirmed pivots per boundary, at
            least two.
        slope_flat: Required non-negative flat-slope threshold.
        tolerance: Required non-negative touch-price tolerance around each
            boundary's mean level.
        beta_atr: Required non-negative breakout confirmation buffer, in
            ATR multiples.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ``IndicatorResult`` carrying ``rectangle_state``
        (``0``=NONE, ``1``=RANGE_ACTIVE, ``2``=BREAKOUT_UP,
        ``3``=BREAKOUT_DOWN) plus the ``rectangle_upper``/
        ``rectangle_lower`` mean boundary levels.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating rectangle for %s", data.symbol)
    parameters = (
        ("atr_period", atr_period),
        ("beta_atr", beta_atr),
        ("left", left),
        ("lookback", lookback),
        ("min_touches", min_touches),
        ("right", right),
        ("slope_flat", slope_flat),
        ("tolerance", tolerance),
    )
    resolved_config = build_pattern_config("rectangle", parameters, config)
    _unwrap_indicator_response(validate_indicator("rectangle", data, resolved_config))
    high_flag, high_price, low_flag, low_price = fetch_pivots(
        data, left=left, right=right
    )
    atr_values = fetch_atr(data, atr_period=atr_period)
    close = np.asarray(
        [float(record.close) for record in data.records], dtype="float64"
    )
    row_count = len(close)
    is_valid = np.isfinite(atr_values) & np.isfinite(high_flag)
    first_valid = int(np.argmax(is_valid)) if is_valid.any() else row_count

    state = np.full(row_count, np.nan, dtype="float64")
    upper_level = np.full(row_count, np.nan, dtype="float64")
    lower_level = np.full(row_count, np.nan, dtype="float64")

    for t in range(first_valid, row_count):
        lower_bound = max(0, t - lookback)
        upper_idx, upper_pts = recent_pivot_points(
            high_flag[lower_bound : t + 1],
            high_price[lower_bound : t + 1],
            t - lower_bound,
            min_touches,
        )
        lower_idx, lower_pts = recent_pivot_points(
            low_flag[lower_bound : t + 1],
            low_price[lower_bound : t + 1],
            t - lower_bound,
            min_touches,
        )
        current_state = _NONE_STATE
        current_upper = np.nan
        current_lower = np.nan
        if len(upper_idx) >= min_touches and len(lower_idx) >= min_touches:
            upper_fit = fit_line(upper_idx.astype("float64"), upper_pts)
            lower_fit = fit_line(lower_idx.astype("float64"), lower_pts)
            mean_upper = float(np.mean(upper_pts))
            mean_lower = float(np.mean(lower_pts))
            flat_upper = upper_fit is not None and abs(upper_fit[0]) <= slope_flat
            flat_lower = lower_fit is not None and abs(lower_fit[0]) <= slope_flat
            touches_hold = bool(
                np.all(np.abs(upper_pts - mean_upper) <= tolerance)
            ) and bool(np.all(np.abs(lower_pts - mean_lower) <= tolerance))
            if flat_upper and flat_lower and touches_hold and mean_upper > mean_lower:
                current_upper = mean_upper
                current_lower = mean_lower
                if close[t] > mean_upper + beta_atr * atr_values[t]:
                    current_state = _BREAKOUT_UP
                elif close[t] < mean_lower - beta_atr * atr_values[t]:
                    current_state = _BREAKOUT_DOWN
                else:
                    current_state = _RANGE_ACTIVE
        state[t] = current_state
        upper_level[t] = current_upper
        lower_level[t] = current_lower

    is_valid[:first_valid] = False

    index, computed_from_start, computed_from_end, available_at, unavailable_reason = (
        causal_series(data, is_valid)
    )
    output_columns = (
        f"rectangle_state_{left}_{right}_{atr_period}",
        f"rectangle_upper_{left}_{right}_{atr_period}",
        f"rectangle_lower_{left}_{right}_{atr_period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, state, np.nan),
            output_columns[1]: np.where(
                is_valid & np.isfinite(upper_level),
                upper_level,
                np.where(is_valid, 0.0, np.nan),
            ),
            output_columns[2]: np.where(
                is_valid & np.isfinite(lower_level),
                lower_level,
                np.where(is_valid, 0.0, np.nan),
            ),
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


__all__ = ["rectangle"]
