"""Inside Bar candlestick-pattern calculator."""

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
    """Build or validate the immutable Inside Bar configuration.

    Args:
        config: Optional explicit parameterless configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            parameterless Inside Bar contract.
    """
    logger.debug("Building inside_bar config")
    expected = IndicatorConfig(
        indicator_id="inside_bar",
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
            "supplied config disagrees with inside_bar wrapper arguments",
            {"indicator_id": "inside_bar"},
        )
    return config


def inside_bar(
    data: MarketDataset,
    *,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Identify candles fully contained in the previous candle range.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        config: Optional explicit parameterless configuration.

    Returns:
        A deterministic binary Inside Bar result after one warmup row.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating inside_bar for %s", data.symbol)
    resolved_config = _build_config(config)
    validate_indicator("inside_bar", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    values = np.full(len(records), np.nan, dtype="float64")
    if len(records) > 1:
        values[1:] = ((high[1:] <= high[:-1]) & (low[1:] >= low[:-1])).astype("float64")
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
        output_columns=("inside_bar",),
        output_values=pd.DataFrame({"inside_bar": values}, index=index),
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["inside_bar"]
