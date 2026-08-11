"""Rising / Falling Wedge pattern detector.

Implements spec ``IND-PT-08`` by fitting OLS boundary lines over the most
recent confirmed pivots from ``structure.pivots`` (evaluated independently
per bar, matching ``patterns.triangle``'s approach), plus the canonical
``volatility.atr``.
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
# wedge_type: 0=NONE, 1=RISING, 2=FALLING
_NONE_TYPE, _RISING, _FALLING = 0.0, 1.0, 2.0
# breakout_state: 0=NONE, 1=INSIDE, 2=BREAKOUT_UP, 3=BREAKOUT_DOWN
_NO_WEDGE, _INSIDE, _BREAKOUT_UP, _BREAKOUT_DOWN = 0.0, 1.0, 2.0, 3.0


@guard_public_boundary
def wedge(
    data: MarketDataset,
    *,
    left: int,
    right: int,
    atr_period: int,
    lookback: int,
    min_touches: int,
    beta_atr: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Detect spec ``IND-PT-08`` Rising and Falling Wedge.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        left: Left-bar count fed to ``structure.pivots``.
        right: Right-bar count fed to ``structure.pivots``.
        atr_period: Smoothing period fed to ``volatility.atr``.
        lookback: Required trailing bar window searched for touches, at
            least ``2 * min_touches``.
        min_touches: Required minimum confirmed pivots per boundary, at
            least two.
        beta_atr: Required non-negative breakout confirmation buffer, in
            ATR multiples.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ``IndicatorResult`` carrying ``wedge_type``
        (``0``=NONE, ``1``=RISING, ``2``=FALLING) and
        ``wedge_breakout_state`` (``0``=NONE (no wedge), ``1``=INSIDE,
        ``2``=BREAKOUT_UP, ``3``=BREAKOUT_DOWN).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating wedge for %s", data.symbol)
    parameters = (
        ("atr_period", atr_period),
        ("beta_atr", beta_atr),
        ("left", left),
        ("lookback", lookback),
        ("min_touches", min_touches),
        ("right", right),
    )
    resolved_config = build_pattern_config("wedge", parameters, config)
    _unwrap_indicator_response(validate_indicator("wedge", data, resolved_config))
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
        current_type = _NONE_TYPE
        current_breakout = _NO_WEDGE
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
                if gap > 0.0:
                    if b_u > 0.0 and b_l > 0.0 and b_l > b_u:
                        current_type = _RISING
                    elif b_u < 0.0 and b_l < 0.0 and abs(b_u) > abs(b_l):
                        current_type = _FALLING
                    if current_type != _NONE_TYPE:
                        if current_type == _RISING and close[t] < (
                            projected_lower - beta_atr * atr_values[t]
                        ):
                            current_breakout = _BREAKOUT_DOWN
                        elif current_type == _FALLING and close[t] > (
                            projected_upper + beta_atr * atr_values[t]
                        ):
                            current_breakout = _BREAKOUT_UP
                        else:
                            current_breakout = _INSIDE
        pattern_type[t] = current_type
        breakout_state[t] = current_breakout

    is_valid[:first_valid] = False

    index, computed_from_start, computed_from_end, available_at, unavailable_reason = (
        causal_series(data, is_valid)
    )
    output_columns = (
        f"wedge_type_{left}_{right}_{atr_period}",
        f"wedge_breakout_state_{left}_{right}_{atr_period}",
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


__all__ = ["wedge"]
