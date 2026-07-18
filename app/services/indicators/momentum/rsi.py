"""Relative Strength Index calculator."""

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
_FLAT_RSI = 50.0


def _build_config(
    period: int, source: str, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable RSI configuration.

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
    logger.debug("Building rsi config")
    expected = IndicatorConfig(
        indicator_id="rsi",
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
            "supplied config disagrees with rsi wrapper arguments",
            {"indicator_id": "rsi"},
        )
    return config


def _wilder_rsi(prices: np.ndarray, period: int) -> tuple[np.ndarray, np.ndarray]:
    """Calculate Wilder-smoothed RSI values and their valid mask.

    Args:
        prices: Row-ordered selected prices.
        period: Validated smoothing period.

    Returns:
        A values array and Boolean valid-row mask.
    """
    logger.debug("Computing Wilder RSI")
    values = np.full(len(prices), np.nan, dtype="float64")
    is_valid = np.zeros(len(prices), dtype=bool)
    if len(prices) < period + 1:
        return values, is_valid
    deltas = np.diff(prices)
    gains = np.where(deltas > 0.0, deltas, 0.0)
    losses = np.where(deltas < 0.0, -deltas, 0.0)
    average_gain = float(gains[:period].mean())
    average_loss = float(losses[:period].mean())
    for position in range(period, len(prices)):
        if position > period:
            average_gain = (average_gain * (period - 1) + gains[position - 1]) / period
            average_loss = (average_loss * (period - 1) + losses[position - 1]) / period
        if average_gain == 0.0 and average_loss == 0.0:
            values[position] = _FLAT_RSI
        elif average_loss == 0.0:
            values[position] = 100.0
        elif average_gain == 0.0:
            values[position] = 0.0
        else:
            relative_strength = average_gain / average_loss
            values[position] = 100.0 - 100.0 / (1.0 + relative_strength)
    is_valid[period:] = True
    return values, is_valid


def rsi(
    data: MarketDataset,
    *,
    period: int,
    source: str = "close",
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Wilder Relative Strength Index.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required smoothing period of at least two.
        source: Selected OHLC source.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic RSI ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating rsi for %s (period=%d, source=%s)", data.symbol, period, source
    )
    resolved_config = _build_config(period, source, config)
    validate_indicator("rsi", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    prices = np.asarray(
        [float(getattr(record, source)) for record in records], dtype="float64"
    )
    values, is_valid = _wilder_rsi(prices, period)
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
    output_column = f"rsi_{period}" if source == "close" else f"rsi_{source}_{period}"

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


__all__ = ["rsi"]
