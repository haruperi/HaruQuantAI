# ruff: noqa: C901, PLR0915
"""Triangle pattern detector.

Implements spec ``IND-PT-03`` by fitting OLS boundary lines over the most
recent confirmed pivots from ``structure.pivots`` (each bar's geometry is
evaluated independently from the confirmed pivots visible up to that bar,
so no persistent cross-bar state machine is required for this pattern),
plus the canonical ``volatility.atr``.
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
# triangle_type: 0=NONE, 1=SYMMETRICAL, 2=ASCENDING, 3=DESCENDING
_NONE_TYPE, _SYMMETRICAL, _ASCENDING, _DESCENDING = 0.0, 1.0, 2.0, 3.0
# breakout_state: 0=NONE, 1=INSIDE, 2=BREAKOUT_UP, 3=BREAKOUT_DOWN
_NO_TRIANGLE, _INSIDE, _BREAKOUT_UP, _BREAKOUT_DOWN = 0.0, 1.0, 2.0, 3.0


@guard_public_boundary
def triangle(
    data: MarketDataset,
    *,
    left: int,
    right: int,
    atr_period: int,
    lookback: int,
    min_touches: int,
    slope_flat: float,
    beta_atr: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Detect spec ``IND-PT-03`` Triangle (symmetrical/ascending/descending).

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
        beta_atr: Required non-negative breakout confirmation buffer, in
            ATR multiples.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ``IndicatorResult`` carrying ``triangle_type``
        (``0``=NONE, ``1``=SYMMETRICAL, ``2``=ASCENDING, ``3``=DESCENDING)
        and ``triangle_breakout_state`` (``0``=NONE (no triangle),
        ``1``=INSIDE, ``2``=BREAKOUT_UP, ``3``=BREAKOUT_DOWN).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating triangle for %s", data.symbol)
    parameters = (
        ("atr_period", atr_period),
        ("beta_atr", beta_atr),
        ("left", left),
        ("lookback", lookback),
        ("min_touches", min_touches),
        ("right", right),
        ("slope_flat", slope_flat),
    )
    resolved_config = build_pattern_config("triangle", parameters, config)
    _unwrap_indicator_response(validate_indicator("triangle", data, resolved_config))
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

    pattern_type = np.full(row_count, np.nan, dtype="float64")
    breakout_state = np.full(row_count, np.nan, dtype="float64")

    for t in range(first_valid, row_count):
        lower_bound = max(0, t - lookback)
        upper_flags = high_flag[lower_bound : t + 1]
        upper_prices = high_price[lower_bound : t + 1]
        lower_flags = low_flag[lower_bound : t + 1]
        lower_prices = low_price[lower_bound : t + 1]
        upper_idx, upper_pts = recent_pivot_points(
            upper_flags, upper_prices, len(upper_flags) - 1, min_touches
        )
        lower_idx, lower_pts = recent_pivot_points(
            lower_flags, lower_prices, len(lower_flags) - 1, min_touches
        )
        current_type = _NONE_TYPE
        current_breakout = _NO_TRIANGLE
        if len(upper_idx) >= min_touches and len(lower_idx) >= min_touches:
            upper_fit = fit_line(upper_idx.astype("float64"), upper_pts)
            lower_fit = fit_line(lower_idx.astype("float64"), lower_pts)
            if upper_fit is not None and lower_fit is not None:
                b_u, a_u = upper_fit
                b_l, a_l = lower_fit
                offset = float(lower_bound)
                projected_upper = a_u + b_u * (t - offset)
                projected_lower = a_l + b_l * (t - offset)
                gap = projected_upper - projected_lower
                converging = b_u < b_l
                if gap > 0.0 and converging:
                    if b_u < 0.0 and b_l > 0.0:
                        current_type = _SYMMETRICAL
                    elif abs(b_u) <= slope_flat and b_l > 0.0:
                        current_type = _ASCENDING
                    elif b_u < 0.0 and abs(b_l) <= slope_flat:
                        current_type = _DESCENDING
                    if current_type != _NONE_TYPE:
                        if close[t] > projected_upper + beta_atr * atr_values[t]:
                            current_breakout = _BREAKOUT_UP
                        elif close[t] < projected_lower - beta_atr * atr_values[t]:
                            current_breakout = _BREAKOUT_DOWN
                        else:
                            current_breakout = _INSIDE
        pattern_type[t] = current_type
        breakout_state[t] = current_breakout

    is_valid[:first_valid] = False

    index, computed_from_start, computed_from_end, available_at, unavailable_reason = (
        causal_series(data, is_valid)
    )
    output_columns = (
        f"triangle_type_{left}_{right}_{atr_period}",
        f"triangle_breakout_state_{left}_{right}_{atr_period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, pattern_type, np.nan),
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


__all__ = ["triangle"]
