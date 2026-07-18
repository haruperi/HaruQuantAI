"""Engulfing candlestick-pattern calculator."""

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


def _build_config(config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable Engulfing configuration.

    Args:
        config: Optional explicit parameterless configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            parameterless Engulfing contract.
    """
    logger.debug("Building engulfing config")
    expected = IndicatorConfig(
        indicator_id="engulfing",
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
            "supplied config disagrees with engulfing wrapper arguments",
            {"indicator_id": "engulfing"},
        )
    return config


def engulfing(
    data: MarketDataset,
    *,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Identify bullish and bearish two-candle Engulfing patterns.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        config: Optional explicit parameterless configuration.

    Returns:
        A deterministic Engulfing result: ``1``, ``-1``, or ``0`` after
        one warmup row.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating engulfing for %s", data.symbol)
    resolved_config = _build_config(config)
    validate_indicator("engulfing", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    open_price = np.asarray([float(record.open) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    values = np.full(len(records), np.nan, dtype="float64")
    if len(records) > 1:
        bullish = (
            (close[:-1] < open_price[:-1])
            & (close[1:] > open_price[1:])
            & (close[1:] >= open_price[:-1])
            & (open_price[1:] <= close[:-1])
        )
        bearish = (
            (close[:-1] > open_price[:-1])
            & (close[1:] < open_price[1:])
            & (close[1:] <= open_price[:-1])
            & (open_price[1:] >= close[:-1])
        )
        values[1:] = np.where(bullish, 1.0, np.where(bearish, -1.0, 0.0))
    is_valid = np.arange(len(records)) >= 1
    row_time = pd.Series(index, index=index)
    computed_from_start = row_time.shift(1)
    computed_from_start[~is_valid] = pd.NaT
    computed_from_end = row_time.copy()
    computed_from_end[~is_valid] = pd.NaT
    available_at = pd.Series([record.available_at for record in records], index=index)
    if len(records) > 1:
        nanos = pd.DatetimeIndex([record.available_at for record in records]).asi8
        available_at.iloc[1:] = pd.to_datetime(
            np.maximum(nanos[:-1], nanos[1:]), unit="us", utc=True
        )
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_valid] = "warmup"

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=("engulfing",),
        output_values=pd.DataFrame({"engulfing": values}, index=index),
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["engulfing"]
