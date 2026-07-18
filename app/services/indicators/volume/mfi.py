"""Money Flow Index calculator."""

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
_FLAT_MFI = 50.0


def _build_config(period: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable MFI configuration.

    Args:
        period: Required rolling period.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    logger.debug("Building mfi config")
    expected = IndicatorConfig(
        indicator_id="mfi",
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
            "supplied config disagrees with mfi wrapper arguments",
            {"indicator_id": "mfi"},
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
    logger.debug("Computing rolling availability for mfi")
    nanos = pd.DatetimeIndex([record.available_at for record in records]).asi8
    result = nanos.copy()
    if len(records) >= period:
        result[period - 1 :] = sliding_window_view(nanos, period).max(axis=1)
    return pd.Series(pd.to_datetime(result, unit="us", utc=True), index=index)


def mfi(
    data: MarketDataset,
    *,
    period: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Money Flow Index from typical-price direction and volume.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling period of at least two.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic MFI ``IndicatorResult`` bounded to ``[0, 100]``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating mfi for %s (period=%d)", data.symbol, period)
    resolved_config = _build_config(period, config)
    validate_indicator("mfi", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    typical_price = np.asarray(
        [float((record.high + record.low + record.close) / 3) for record in records],
        dtype="float64",
    )
    volume = np.asarray([float(record.volume) for record in records], dtype="float64")
    raw_money_flow = typical_price * volume
    change = np.zeros(len(records), dtype="float64")
    change[1:] = np.diff(typical_price)
    positive_flow = pd.Series(np.where(change > 0.0, raw_money_flow, 0.0), index=index)
    negative_flow = pd.Series(np.where(change < 0.0, raw_money_flow, 0.0), index=index)
    positive_sum = positive_flow.rolling(period, min_periods=period).sum()
    negative_sum = negative_flow.rolling(period, min_periods=period).sum()
    values = pd.Series(np.nan, index=index, dtype="float64")
    both_zero = (positive_sum == 0.0) & (negative_sum == 0.0)
    no_negative = (positive_sum > 0.0) & (negative_sum == 0.0)
    no_positive = (positive_sum == 0.0) & (negative_sum > 0.0)
    normal = (positive_sum > 0.0) & (negative_sum > 0.0)
    values[both_zero] = _FLAT_MFI
    values[no_negative] = 100.0
    values[no_positive] = 0.0
    ratio = positive_sum[normal] / negative_sum[normal]
    values[normal] = 100.0 - 100.0 / (1.0 + ratio)
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
    output_column = f"mfi_{period}"

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


__all__ = ["mfi"]
