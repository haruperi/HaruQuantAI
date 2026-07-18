"""Exponential Moving Average calculator."""

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


def _build_config(
    period: int, source: str, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable EMA configuration.

    Args:
        period: Required smoothing period.
        source: Selected OHLC source.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    logger.debug("Building ema config (period=%d, source=%s)", period, source)
    expected = IndicatorConfig(
        indicator_id="ema",
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
            "supplied config disagrees with ema wrapper arguments",
            {"indicator_id": "ema"},
        )
    return config


def _output_column(source: str, period: int) -> str:
    """Return the canonical EMA output column.

    Args:
        source: Selected OHLC source.
        period: Validated smoothing period.

    Returns:
        The deterministic output column name.
    """
    logger.debug("Resolving ema output column (source=%s, period=%d)", source, period)
    return f"ema_{period}" if source == "close" else f"ema_{source}_{period}"


def ema(
    data: MarketDataset,
    *,
    period: int,
    source: str = "close",
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate EMA with an SMA seed and recursive smoothing.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required smoothing period of at least two.
        source: Selected OHLC source.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic EMA ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating ema for %s (period=%d, source=%s)", data.symbol, period, source
    )
    resolved_config = _build_config(period, source, config)
    validate_indicator("ema", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    prices = np.asarray(
        [float(getattr(record, source)) for record in records], dtype="float64"
    )
    values = np.full(len(records), np.nan, dtype="float64")
    is_valid = np.zeros(len(records), dtype=bool)
    if len(records) >= period:
        alpha = 2.0 / (period + 1)
        previous = float(prices[:period].mean())
        values[period - 1] = previous
        for position in range(period, len(records)):
            previous = prices[position] * alpha + previous * (1.0 - alpha)
            values[position] = previous
        is_valid[period - 1 :] = True

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
    output_column = _output_column(source, period)

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


__all__ = ["ema"]
