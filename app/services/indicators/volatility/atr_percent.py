"""ATR Percent (normalized ATR) calculator.

Implements spec ``IND-VOL-02``: ``ATRP_t = 100 * ATR_t / C_t``. This file
computes its own internal Wilder true-range/ATR primitive rather than
calling the sibling ``volatility.atr`` public function, matching the
package convention that no indicator leaf file invokes another sibling
leaf file's public wrapper.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from app.composition.logging import get_logger
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    _unwrap_indicator_response,
    guard_public_boundary,
)
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.indicators.core.contracts import (
        _MarketDataset as MarketDataset,
    )
    from app.services.indicators.core.contracts import (
        _OHLCVRecord as OHLCVRecord,
    )
    from app.services.indicators.core.results import IndicatorResult

_FORMULA_VERSION = "1.0.0"
_INDICATOR_VERSION = "1.0.0"


def _build_config(period: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable ATR Percent configuration.

    Args:
        period: Required smoothing period, inherited by the internal ATR.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    expected = IndicatorConfig(
        indicator_id="atr_percent",
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
            "supplied config disagrees with atr_percent wrapper arguments",
            {"indicator_id": "atr_percent"},
        )
    return config


def _wilder_atr(records: tuple[OHLCVRecord, ...], period: int) -> np.ndarray:
    """Calculate the internal Wilder-smoothed ATR primitive.

        Duplicates ``volatility.atr``'s private true-range/RMA formula rather
        than importing it, per the package's no-sibling-call convention.

    Args:
            records: Validated OHLCV records.
            period: Required smoothing period of at least two.

    Returns:
            A float64 ATR array with ``nan`` warmup rows.

    Raises:
        None.
    """
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    previous_close = np.empty(len(records), dtype="float64")
    previous_close[0] = close[0]
    previous_close[1:] = close[:-1]
    true_range = np.asarray(
        np.maximum.reduce(
            (high - low, np.abs(high - previous_close), np.abs(low - previous_close))
        ),
        dtype="float64",
    )
    values = np.full(len(records), np.nan, dtype="float64")
    if len(records) >= period:
        previous = float(true_range[:period].mean())
        values[period - 1] = previous
        for position in range(period, len(records)):
            previous = (previous * (period - 1) + true_range[position]) / period
            values[position] = previous
    return values


@guard_public_boundary
def atr_percent(
    data: MarketDataset,
    *,
    period: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate normalized ATR as a percent of close price.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required ATR smoothing period of at least two.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ATR Percent ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating atr_percent for %s (period=%d)", data.symbol, period)
    resolved_config = _build_config(period, config)
    _unwrap_indicator_response(validate_indicator("atr_percent", data, resolved_config))
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    atr_values = _wilder_atr(records, period)
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    is_valid = np.zeros(len(records), dtype=bool)
    is_valid[period - 1 :] = len(records) >= period
    values = np.full(len(records), np.nan, dtype="float64")
    values[is_valid] = 100.0 * atr_values[is_valid] / close[is_valid]

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
    output_column = f"atr_percent_{period}"

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


__all__ = ["atr_percent"]
