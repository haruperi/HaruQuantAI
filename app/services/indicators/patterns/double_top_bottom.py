# ruff: noqa: C901, PLR0912, PLR0915
"""Double Top / Double Bottom pattern detector.

Implements spec ``IND-PT-01`` over confirmed pivots from
``structure.pivots`` and the canonical ``volatility.atr`` (the approved
cross-module dependencies), never recomputing either primitive. See
``patterns/_shared.py`` for the domain's documented four-state
simplification of the spec's five-state pattern model.
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


@guard_public_boundary
def double_top_bottom(
    data: MarketDataset,
    *,
    left: int,
    right: int,
    atr_period: int,
    tau_price: float,
    d_min_atr: float,
    beta_atr: float,
    m_confirm: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Detect spec ``IND-PT-01`` Double Top and Double Bottom patterns.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        left: Left-bar count fed to ``structure.pivots``.
        right: Right-bar count fed to ``structure.pivots``.
        atr_period: Smoothing period fed to ``volatility.atr``.
        tau_price: Required non-negative pivot-similarity tolerance
            (fraction of the average of the two pivot prices).
        d_min_atr: Required non-negative minimum prominence, in ATR
            multiples.
        beta_atr: Required non-negative neckline breakout buffer, in ATR
            multiples.
        m_confirm: Required maximum confirmation bars after the second
            pivot, at least one.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ``IndicatorResult`` carrying ``double_top_state``
        and ``double_bottom_state`` (``0``=NONE, ``1``=DETECTED,
        ``2``=CONFIRMED, ``3``=INVALIDATED) plus each pattern's neckline.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating double_top_bottom for %s", data.symbol)
    parameters = (
        ("atr_period", atr_period),
        ("beta_atr", beta_atr),
        ("d_min_atr", d_min_atr),
        ("left", left),
        ("m_confirm", m_confirm),
        ("right", right),
        ("tau_price", tau_price),
    )
    resolved_config = build_pattern_config("double_top_bottom", parameters, config)
    _unwrap_indicator_response(
        validate_indicator("double_top_bottom", data, resolved_config)
    )

    high_flag, high_price, low_flag, low_price = fetch_pivots(
        data, left=left, right=right
    )
    atr_values = fetch_atr(data, atr_period=atr_period)
    close = np.asarray(
        [float(record.close) for record in data.records], dtype="float64"
    )
    row_count = len(high_flag)
    is_valid = np.isfinite(atr_values) & np.isfinite(high_flag)
    first_valid = int(np.argmax(is_valid)) if is_valid.any() else row_count

    # The intervening-extreme candidate for a top scan is the lowest confirmed
    # low seen strictly between the previous and current confirmed high; for a
    # bottom scan it is the highest confirmed high seen strictly between the
    # previous and current confirmed low. Both are tracked by feeding the
    # opposite side's flag/price arrays as auxiliary context via closures below.
    def _scan_with_intervening(is_top: bool) -> tuple[np.ndarray, np.ndarray]:
        """Scan one pivot side with its intervening opposite extreme.

        Args:
            is_top: Whether to scan double-top rather than double-bottom geometry.

        Returns:
            Pattern-state and neckline arrays.

        Raises:
            None.
        """
        flag = high_flag if is_top else low_flag
        price = high_price if is_top else low_price
        opposite_flag = low_flag if is_top else high_flag
        opposite_price = low_price if is_top else high_price
        state = np.full(row_count, np.nan, dtype="float64")
        neckline = np.full(row_count, np.nan, dtype="float64")
        last_pivot_index: int | None = None
        last_pivot_price: float | None = None
        intervening_extreme: float | None = None
        active = False
        line = 0.0
        deadline = -1
        second_index = -1

        for t in range(row_count):
            if t < first_valid:
                continue
            current = NONE_STATE

            if active:
                breakout = (
                    close[t] < line - beta_atr * atr_values[t]
                    if is_top
                    else close[t] > line + beta_atr * atr_values[t]
                )
                if breakout:
                    current = CONFIRMED
                    active = False
                elif (flag[t] == 1.0 and t > second_index) or t >= deadline:
                    current = INVALIDATED
                    active = False
                else:
                    current = DETECTED
                neckline[t] = line

            if opposite_flag[t] == 1.0 and last_pivot_index is not None:
                candidate = opposite_price[t]
                if intervening_extreme is None:
                    intervening_extreme = candidate
                elif is_top:
                    intervening_extreme = min(intervening_extreme, candidate)
                else:
                    intervening_extreme = max(intervening_extreme, candidate)

            if flag[t] == 1.0:
                if (
                    last_pivot_index is not None
                    and last_pivot_price is not None
                    and intervening_extreme is not None
                    and not active
                ):
                    p1, p2 = last_pivot_price, price[t]
                    average = (p1 + p2) / 2.0
                    if average > 0.0 and abs(p1 - p2) / average <= tau_price:
                        prominence = (
                            min(p1, p2) - intervening_extreme
                            if is_top
                            else intervening_extreme - max(p1, p2)
                        )
                        if prominence >= d_min_atr * atr_values[t]:
                            active = True
                            line = intervening_extreme
                            deadline = t + m_confirm
                            second_index = t
                            if current == NONE_STATE:
                                current = DETECTED
                                neckline[t] = line
                last_pivot_index = t
                last_pivot_price = price[t]
                intervening_extreme = None

            state[t] = current

        return state, neckline

    top_state, top_neckline = _scan_with_intervening(is_top=True)
    bottom_state, bottom_neckline = _scan_with_intervening(is_top=False)

    is_valid[:first_valid] = False

    index, computed_from_start, computed_from_end, available_at, unavailable_reason = (
        causal_series(data, is_valid)
    )
    output_columns = (
        f"double_top_state_{left}_{right}_{atr_period}",
        f"double_top_neckline_{left}_{right}_{atr_period}",
        f"double_bottom_state_{left}_{right}_{atr_period}",
        f"double_bottom_neckline_{left}_{right}_{atr_period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, top_state, np.nan),
            output_columns[1]: np.where(
                is_valid & np.isfinite(top_neckline),
                top_neckline,
                np.where(is_valid, 0.0, np.nan),
            ),
            output_columns[2]: np.where(is_valid, bottom_state, np.nan),
            output_columns[3]: np.where(
                is_valid & np.isfinite(bottom_neckline),
                bottom_neckline,
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


__all__ = ["double_top_bottom"]
