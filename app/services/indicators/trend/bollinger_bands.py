"""Bollinger Bands calculator."""

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
    period: int, std_dev: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable Bollinger Bands configuration.

    Args:
        period: Required rolling period.
        std_dev: Positive standard-deviation multiplier.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    logger.debug("Building bollinger_bands config")
    expected = IndicatorConfig(
        indicator_id="bollinger_bands",
        parameters=(("period", period), ("std_dev", std_dev)),
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
            "supplied config disagrees with bollinger_bands wrapper arguments",
            {"indicator_id": "bollinger_bands"},
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
    logger.debug("Computing rolling availability for bollinger_bands")
    nanos = pd.DatetimeIndex([record.available_at for record in records]).asi8
    result = nanos.copy()
    if len(records) >= period:
        result[period - 1 :] = sliding_window_view(nanos, period).max(axis=1)
    return pd.Series(pd.to_datetime(result, unit="us", utc=True), index=index)


def bollinger_bands(
    data: MarketDataset,
    *,
    period: int,
    std_dev: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate close-price Bollinger Bands with sample deviation.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling period of at least two.
        std_dev: Positive standard-deviation multiplier.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic three-column Bollinger Bands ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating bollinger_bands for %s (period=%d, std_dev=%s)",
        data.symbol,
        period,
        std_dev,
    )
    resolved_config = _build_config(period, std_dev, config)
    validate_indicator("bollinger_bands", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = pd.Series(
        [float(record.close) for record in records], index=index, dtype="float64"
    )
    middle = close.rolling(window=period, min_periods=period).mean()
    deviation = close.rolling(window=period, min_periods=period).std(ddof=1)
    upper = middle + std_dev * deviation
    lower = middle - std_dev * deviation
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
    output_columns = (
        f"bollinger_bands_upper_{period}",
        f"bollinger_bands_middle_{period}",
        f"bollinger_bands_lower_{period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: upper,
            output_columns[1]: middle,
            output_columns[2]: lower,
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


__all__ = ["bollinger_bands"]
