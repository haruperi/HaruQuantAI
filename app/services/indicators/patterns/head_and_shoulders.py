# ruff: noqa: C901, PLR0912, PLR2004
"""Head and Shoulders / Inverse Head and Shoulders pattern detector.

Implements spec ``IND-PT-02`` over confirmed pivots from
``structure.pivots`` and the canonical ``volatility.atr`` (the approved
cross-module dependencies).
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
    fit_line,
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


def _scan(
    *,
    shoulder_flag: np.ndarray,
    shoulder_price: np.ndarray,
    trough_flag: np.ndarray,
    trough_price: np.ndarray,
    close: np.ndarray,
    atr_values: np.ndarray,
    tau_shoulder: float,
    d_head_atr: float,
    beta_atr: float,
    m_confirm: int,
    first_valid: int,
    bearish: bool,
) -> np.ndarray:
    """Scan for the bearish (highs) or inverse/bullish (lows) formation.

    Args:
        shoulder_flag: The shoulder flag value.
        shoulder_price: The shoulder price value.
        trough_flag: The trough flag value.
        trough_price: The trough price value.
        close: The close value.
        atr_values: The atr values value.
        tau_shoulder: The tau shoulder value.
        d_head_atr: The d head atr value.
        beta_atr: The beta atr value.
        m_confirm: The m confirm value.
        first_valid: The first valid value.
        bearish: The bearish value.

    Returns:
        The np.ndarray result.

    Raises:
        None.
    """
    row_count = len(shoulder_flag)
    state = np.full(row_count, np.nan, dtype="float64")
    shoulders: list[tuple[int, float]] = []
    troughs: list[tuple[int, float]] = []
    active = False
    neckline_slope = 0.0
    neckline_intercept = 0.0
    deadline = -1
    second_shoulder_index = -1

    for t in range(row_count):
        if t < first_valid:
            continue
        current = NONE_STATE

        if active:
            projected = neckline_intercept + neckline_slope * t
            breakout = (
                close[t] < projected - beta_atr * atr_values[t]
                if bearish
                else (close[t] > projected + beta_atr * atr_values[t])
            )
            if breakout:
                current = CONFIRMED
                active = False
            elif (
                shoulder_flag[t] == 1.0 and t > second_shoulder_index
            ) or t >= deadline:
                current = INVALIDATED
                active = False
            else:
                current = DETECTED

        if trough_flag[t] == 1.0:
            troughs.append((t, trough_price[t]))
            troughs = troughs[-2:]

        if shoulder_flag[t] == 1.0:
            shoulders.append((t, shoulder_price[t]))
            shoulders = shoulders[-3:]
            if len(shoulders) == 3 and len(troughs) == 2 and not active:
                (_, s_l), (_, head), (_, s_r) = shoulders
                t1_idx, t1_price = troughs[0]
                t2_idx, t2_price = troughs[1]
                if t1_idx > shoulders[0][0] and t2_idx > shoulders[1][0]:
                    is_head_extreme = (
                        head > s_l and head > s_r
                        if bearish
                        else (head < s_l and head < s_r)
                    )
                    average = (s_l + s_r) / 2.0
                    similar = average > 0.0 and abs(s_l - s_r) / average <= tau_shoulder
                    prominence = (
                        head - max(s_l, s_r) if bearish else min(s_l, s_r) - head
                    )
                    if (
                        is_head_extreme
                        and similar
                        and prominence >= d_head_atr * atr_values[t]
                    ):
                        fit = fit_line(
                            np.array([t1_idx, t2_idx], dtype="float64"),
                            np.array([t1_price, t2_price], dtype="float64"),
                        )
                        if fit is not None:
                            neckline_slope, neckline_intercept = fit
                            active = True
                            deadline = t + m_confirm
                            second_shoulder_index = t
                            if current == NONE_STATE:
                                current = DETECTED

        state[t] = current

    return state


@guard_public_boundary
def head_and_shoulders(
    data: MarketDataset,
    *,
    left: int,
    right: int,
    atr_period: int,
    tau_shoulder: float,
    d_head_atr: float,
    beta_atr: float,
    m_confirm: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Detect spec ``IND-PT-02`` Head and Shoulders and its inverse.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        left: Left-bar count fed to ``structure.pivots``.
        right: Right-bar count fed to ``structure.pivots``.
        atr_period: Smoothing period fed to ``volatility.atr``.
        tau_shoulder: Required non-negative shoulder-similarity tolerance.
        d_head_atr: Required non-negative minimum head prominence, in ATR
            multiples.
        beta_atr: Required non-negative neckline breakout buffer, in ATR
            multiples.
        m_confirm: Required maximum confirmation bars, at least one.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ``IndicatorResult`` carrying
        ``head_shoulders_state`` (bearish, from highs/lows troughs) and
        ``inverse_head_shoulders_state`` (``0``=NONE, ``1``=DETECTED,
        ``2``=CONFIRMED, ``3``=INVALIDATED).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating head_and_shoulders for %s", data.symbol)
    parameters = (
        ("atr_period", atr_period),
        ("beta_atr", beta_atr),
        ("d_head_atr", d_head_atr),
        ("left", left),
        ("m_confirm", m_confirm),
        ("right", right),
        ("tau_shoulder", tau_shoulder),
    )
    resolved_config = build_pattern_config("head_and_shoulders", parameters, config)
    _unwrap_indicator_response(
        validate_indicator("head_and_shoulders", data, resolved_config)
    )
    high_flag, high_price, low_flag, low_price = fetch_pivots(
        data, left=left, right=right
    )
    atr_values = fetch_atr(data, atr_period=atr_period)
    close = np.asarray(
        [float(record.close) for record in data.records], dtype="float64"
    )
    is_valid = np.isfinite(atr_values) & np.isfinite(high_flag)
    first_valid = int(np.argmax(is_valid)) if is_valid.any() else len(close)

    bearish_state = _scan(
        shoulder_flag=high_flag,
        shoulder_price=high_price,
        trough_flag=low_flag,
        trough_price=low_price,
        close=close,
        atr_values=atr_values,
        tau_shoulder=tau_shoulder,
        d_head_atr=d_head_atr,
        beta_atr=beta_atr,
        m_confirm=m_confirm,
        first_valid=first_valid,
        bearish=True,
    )
    inverse_state = _scan(
        shoulder_flag=low_flag,
        shoulder_price=low_price,
        trough_flag=high_flag,
        trough_price=high_price,
        close=close,
        atr_values=atr_values,
        tau_shoulder=tau_shoulder,
        d_head_atr=d_head_atr,
        beta_atr=beta_atr,
        m_confirm=m_confirm,
        first_valid=first_valid,
        bearish=False,
    )
    is_valid[:first_valid] = False

    index, computed_from_start, computed_from_end, available_at, unavailable_reason = (
        causal_series(data, is_valid)
    )
    output_columns = (
        f"head_shoulders_state_{left}_{right}_{atr_period}",
        f"inverse_head_shoulders_state_{left}_{right}_{atr_period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, bearish_state, np.nan),
            output_columns[1]: np.where(is_valid, inverse_state, np.nan),
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


__all__ = ["head_and_shoulders"]
