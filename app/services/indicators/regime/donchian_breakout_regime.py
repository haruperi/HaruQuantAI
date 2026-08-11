# ruff: noqa: PD011
"""Donchian breakout regime classifier.

Implements spec ``IND-RG-04`` by classifying the canonical
``structure.donchian_channels`` (prior-bars-only mode) and
``volatility.atr`` public wrappers (the approved cross-module dependencies
for this indicator). ``structure/`` owns the channel levels; this module
owns only the breakout-state classification.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    _unwrap_indicator_response,
    guard_public_boundary,
)
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator
from app.services.indicators.structure.donchian_channels import (
    donchian_channels as _donchian_channels,
)
from app.services.indicators.volatility.atr import atr as _atr
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.indicators.core.contracts import (
        _MarketDataset as MarketDataset,
    )
    from app.services.indicators.core.contracts import (
        _OHLCVRecord as OHLCVRecord,
    )
    from app.services.indicators.core.results import IndicatorResult

_FORMULA_VERSION = "1.0.0"
_INDICATOR_VERSION = "1.0.0"
# 0=INSIDE_CHANNEL, 1=BREAKOUT_UP, 2=BREAKOUT_DOWN
_INSIDE_CHANNEL, _BREAKOUT_UP, _BREAKOUT_DOWN = 0.0, 1.0, 2.0


def _build_config(
    period: int, atr_period: int, beta_atr: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable Donchian-breakout-regime configuration.

    Args:
        period: The period value.
        atr_period: The atr period value.
        beta_atr: The beta atr value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="donchian_breakout_regime",
        parameters=(
            ("atr_period", atr_period),
            ("beta_atr", beta_atr),
            ("period", period),
        ),
        source=None,
        formula_version=_FORMULA_VERSION,
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    if config is None:
        return expected
    if (
        config.indicator_id != expected.indicator_id
        or config.parameters != expected.parameters
        or config.source is not None
        or config.formula_version != expected.formula_version
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "supplied config disagrees with donchian_breakout_regime arguments",
            {"indicator_id": "donchian_breakout_regime"},
        )
    return config


@guard_public_boundary
def donchian_breakout_regime(
    data: MarketDataset,
    *,
    period: int,
    atr_period: int,
    beta_atr: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Classify spec ``IND-RG-04`` Donchian breakout regime.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required Donchian window fed with ``include_current=False``
            so the current bar never tests its own channel.
        atr_period: Required smoothing period fed to the canonical ATR.
        beta_atr: Required non-negative breakout confirmation buffer, in
            ATR multiples.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Donchian-breakout-regime ``IndicatorResult``
        carrying the breakout state (``0``=INSIDE_CHANNEL,
        ``1``=BREAKOUT_UP, ``2``=BREAKOUT_DOWN), the breached level, and
        the ATR-normalized breakout distance.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating donchian_breakout_regime for %s (period=%d, atr_period=%d)",
        data.symbol,
        period,
        atr_period,
    )
    resolved_config = _build_config(period, atr_period, beta_atr, config)
    _unwrap_indicator_response(
        validate_indicator("donchian_breakout_regime", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")

    donchian_result: IndicatorResult = _unwrap_indicator_response(
        _donchian_channels(data, period=period, include_current=False)
    )
    upper = donchian_result.values[f"donchian_upper_{period}"].to_numpy("float64")
    lower = donchian_result.values[f"donchian_lower_{period}"].to_numpy("float64")
    atr_result: IndicatorResult = _unwrap_indicator_response(
        _atr(data, period=atr_period)
    )
    atr_values = atr_result.values[f"atr_{atr_period}"].to_numpy("float64")

    is_valid = np.isfinite(upper) & np.isfinite(lower) & np.isfinite(atr_values)
    breakout_up = close > (upper + beta_atr * atr_values)
    breakout_down = close < (lower - beta_atr * atr_values)
    state = np.select(
        [breakout_up, breakout_down],
        [_BREAKOUT_UP, _BREAKOUT_DOWN],
        default=_INSIDE_CHANNEL,
    )
    breached_level = np.select(
        [breakout_up, breakout_down], [upper, lower], default=np.nan
    )
    safe_atr = np.where(atr_values > 0.0, atr_values, np.nan)
    distance_atr = np.where(
        breakout_up,
        (close - upper) / safe_atr,
        np.where(breakout_down, (lower - close) / safe_atr, 0.0),
    )
    distance_atr = np.where(np.isfinite(distance_atr), distance_atr, 0.0)

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
        f"breakout_state_{period}_{atr_period}",
        f"breached_level_{period}_{atr_period}",
        f"breakout_distance_atr_{period}_{atr_period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, state, np.nan),
            output_columns[1]: np.where(
                is_valid & np.isfinite(breached_level),
                breached_level,
                np.where(is_valid, 0.0, np.nan),
            ),
            output_columns[2]: np.where(is_valid, distance_atr, np.nan),
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


__all__ = ["donchian_breakout_regime"]
