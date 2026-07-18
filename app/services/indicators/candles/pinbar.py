"""Pinbar candlestick-pattern calculator."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset, OHLCVRecord
    from app.services.indicators.core.results import IndicatorResult

_FORMULA_VERSION = "1.0.0"
_INDICATOR_VERSION = "1.0.0"
_SHADOW_RATIO = 0.6
_BODY_RATIO = 0.3


def _build_config(config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable Pinbar configuration.

    Args:
        config: Optional explicit parameterless configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            fixed Pinbar formula.
    """
    logger.debug("Building pinbar config")
    expected = IndicatorConfig(
        indicator_id="pinbar",
        parameters=(),
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
    if config != expected:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "supplied config disagrees with pinbar wrapper arguments",
            {"indicator_id": "pinbar"},
        )
    return config


def pinbar(
    data: MarketDataset,
    *,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Identify bullish and bearish Pinbar candles.

    The fixed formula requires a shadow greater than 60% of the candle
    range and a body smaller than 30%. Bullish matches take deterministic
    precedence if both fixed conditions happen to hold.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        config: Optional explicit parameterless configuration.

    Returns:
        A deterministic Pinbar result: ``1``, ``-1``, or ``0``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating pinbar for %s", data.symbol)
    resolved_config = _build_config(config)
    validate_indicator("pinbar", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    open_price = np.asarray([float(record.open) for record in records], dtype="float64")
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    candle_range = high - low
    body = np.abs(close - open_price)
    lower_shadow = np.minimum(open_price, close) - low
    upper_shadow = high - np.maximum(open_price, close)
    bullish = (
        (candle_range > 0.0)
        & (lower_shadow > _SHADOW_RATIO * candle_range)
        & (body < _BODY_RATIO * candle_range)
    )
    bearish = (
        (candle_range > 0.0)
        & (upper_shadow > _SHADOW_RATIO * candle_range)
        & (body < _BODY_RATIO * candle_range)
    )
    values = np.where(bullish, 1.0, np.where(bearish, -1.0, 0.0))
    row_time = pd.Series(index, index=index)
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=("pinbar",),
        output_values=pd.DataFrame({"pinbar": values}, index=index),
        available_at=pd.Series(
            [record.available_at for record in records], index=index
        ),
        computed_from_start=row_time,
        computed_from_end=row_time.copy(),
        unavailable_reason=unavailable_reason,
    )


__all__ = ["pinbar"]
