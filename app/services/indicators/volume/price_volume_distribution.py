"""Rolling price-volume point-of-control calculator."""

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
    period: int, bins: int, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable price-volume configuration.

    Args:
        period: Required rolling period.
        bins: Required number of price bins.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    logger.debug("Building price_volume_distribution config")
    expected = IndicatorConfig(
        indicator_id="price_volume_distribution",
        parameters=(("bins", bins), ("period", period)),
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
            "supplied config disagrees with price_volume_distribution arguments",
            {"indicator_id": "price_volume_distribution"},
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
    logger.debug("Computing rolling availability for price_volume_distribution")
    nanos = pd.DatetimeIndex([record.available_at for record in records]).asi8
    result = nanos.copy()
    if len(records) >= period:
        result[period - 1 :] = sliding_window_view(nanos, period).max(axis=1)
    return pd.Series(pd.to_datetime(result, unit="us", utc=True), index=index)


def _point_of_control(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
    period: int,
    bins: int,
) -> np.ndarray:
    """Calculate rolling volume-by-close point-of-control prices.

    Args:
        high: Row-ordered high prices.
        low: Row-ordered low prices.
        close: Row-ordered close prices.
        volume: Row-ordered volumes.
        period: Inclusive rolling window size.
        bins: Number of equal-width price bins.

    Returns:
        A float64 array with ``NaN`` warmup values.
    """
    logger.debug("Computing point of control for price_volume_distribution")
    values = np.full(len(close), np.nan, dtype="float64")
    for end in range(period - 1, len(close)):
        start = end - period + 1
        minimum = float(low[start : end + 1].min())
        maximum = float(high[start : end + 1].max())
        if maximum == minimum:
            values[end] = maximum
            continue
        edges = np.linspace(minimum, maximum, bins + 1)
        indices = np.searchsorted(edges, close[start : end + 1], side="right") - 1
        indices = np.clip(indices, 0, bins - 1)
        bin_volume = np.bincount(
            indices, weights=volume[start : end + 1], minlength=bins
        )
        point_index = int(np.argmax(bin_volume))
        values[end] = (edges[point_index] + edges[point_index + 1]) / 2.0
    return values


def price_volume_distribution(
    data: MarketDataset,
    *,
    period: int,
    bins: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate rolling volume-by-price point of control.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling period of at least two.
        bins: Required positive number of equal-width price bins.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic price-volume distribution ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating price_volume_distribution for %s (period=%d, bins=%d)",
        data.symbol,
        period,
        bins,
    )
    resolved_config = _build_config(period, bins, config)
    validate_indicator("price_volume_distribution", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    volume = np.asarray([float(record.volume) for record in records], dtype="float64")
    values = _point_of_control(high, low, close, volume, period, bins)
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
    output_column = f"price_volume_distribution_{period}_{bins}"

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


__all__ = ["price_volume_distribution"]
