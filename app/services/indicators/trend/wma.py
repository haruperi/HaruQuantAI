"""Weighted Moving Average calculator."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

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


def _build_config(
    period: int, source: str, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable WMA configuration.

    Args:
        period: Required rolling period.
        source: Selected OHLC source.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    logger.debug("Building wma config")
    expected = IndicatorConfig(
        indicator_id="wma",
        parameters=(("period", period),),
        source=source,
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
        or config.source != expected.source
        or config.formula_version != expected.formula_version
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "supplied config disagrees with wma wrapper arguments",
            {"indicator_id": "wma"},
        )
    return config


def _rolling_available_at(
    records: tuple[OHLCVRecord, ...], index: pd.DatetimeIndex, period: int
) -> pd.Series:
    """Return the inclusive rolling maximum availability timestamp.

    Args:
        records: Validated OHLCV records.
        index: Canonical result index.
        period: Inclusive rolling window size.

    Returns:
        Row-aligned UTC availability timestamps.
    """
    logger.debug("Computing rolling availability for wma")
    nanos = pd.DatetimeIndex([record.available_at for record in records]).asi8
    result = nanos.copy()
    if len(records) >= period:
        result[period - 1 :] = sliding_window_view(nanos, period).max(axis=1)
    return pd.Series(pd.to_datetime(result, unit="us", utc=True), index=index)


def _weighted_average(prices: np.ndarray, period: int) -> np.ndarray:
    """Calculate vectorized linearly weighted rolling averages.

    Args:
        prices: Row-ordered prices.
        period: Inclusive rolling window size.

    Returns:
        A float64 array with ``NaN`` warmup values.
    """
    logger.debug("Computing weighted average for wma")
    values = np.full(len(prices), np.nan, dtype="float64")
    if len(prices) >= period:
        weights = np.arange(1, period + 1, dtype="float64")
        windows = sliding_window_view(prices, period)
        values[period - 1 :] = windows @ weights / weights.sum()
    return values


def wma(
    data: MarketDataset,
    *,
    period: int,
    source: str = "close",
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate linear Weighted Moving Average.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling period of at least two.
        source: Selected OHLC source.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic WMA ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating wma for %s (period=%d, source=%s)", data.symbol, period, source
    )
    resolved_config = _build_config(period, source, config)
    validate_indicator("wma", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    prices = np.asarray(
        [float(getattr(record, source)) for record in records], dtype="float64"
    )
    values = _weighted_average(prices, period)
    is_valid = np.arange(len(records)) >= period - 1
    row_time = pd.Series(index, index=index)
    computed_from_start = row_time.shift(period - 1)
    computed_from_start[~is_valid] = pd.NaT
    computed_from_end = row_time.copy()
    computed_from_end[~is_valid] = pd.NaT
    available_at = pd.Series([record.available_at for record in records], index=index)
    rolling_available = _rolling_available_at(records, index, period)
    available_at[is_valid] = rolling_available[is_valid]
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_valid] = "warmup"
    output_column = f"wma_{period}" if source == "close" else f"wma_{source}_{period}"

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=(output_column,),
        output_values=pd.DataFrame({output_column: values}, index=index),
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["wma"]
