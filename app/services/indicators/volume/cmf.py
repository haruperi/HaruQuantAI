"""Chaikin Money Flow calculator."""

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


def _build_config(period: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable CMF configuration.

    Args:
        period: Required rolling period.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    logger.debug("Building cmf config")
    expected = IndicatorConfig(
        indicator_id="cmf",
        parameters=(("period", period),),
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
            "supplied config disagrees with cmf wrapper arguments",
            {"indicator_id": "cmf"},
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
    logger.debug("Computing rolling availability for cmf")
    nanos = pd.DatetimeIndex([record.available_at for record in records]).asi8
    result = nanos.copy()
    if len(records) >= period:
        result[period - 1 :] = sliding_window_view(nanos, period).max(axis=1)
    return pd.Series(pd.to_datetime(result, unit="us", utc=True), index=index)


def cmf(
    data: MarketDataset,
    *,
    period: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Chaikin Money Flow over an inclusive rolling window.

    Zero-range bars contribute a zero money-flow multiplier. A complete
    zero-volume window returns zero rather than an epsilon approximation.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling period of at least two.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic CMF ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating cmf for %s (period=%d)", data.symbol, period)
    resolved_config = _build_config(period, config)
    validate_indicator("cmf", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    volume = pd.Series(
        [float(record.volume) for record in records], index=index, dtype="float64"
    )
    price_range = high - low
    multiplier = np.zeros(len(records), dtype="float64")
    non_zero_range = price_range != 0.0
    multiplier[non_zero_range] = (
        (close[non_zero_range] - low[non_zero_range])
        - (high[non_zero_range] - close[non_zero_range])
    ) / price_range[non_zero_range]
    money_flow_volume = pd.Series(multiplier, index=index) * volume
    numerator = money_flow_volume.rolling(period, min_periods=period).sum()
    denominator = volume.rolling(period, min_periods=period).sum()
    values = numerator.div(denominator.where(denominator != 0.0)).fillna(0.0)
    is_valid = np.arange(len(records)) >= period - 1
    values[~is_valid] = np.nan
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
    output_column = f"cmf_{period}"

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


__all__ = ["cmf"]
