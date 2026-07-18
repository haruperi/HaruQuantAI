"""Doji candlestick-pattern calculator."""

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


def _build_config(threshold: float, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable Doji configuration.

    Args:
        threshold: Maximum candle-body share of the full range.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    logger.debug("Building doji config (threshold=%s)", threshold)
    expected = IndicatorConfig(
        indicator_id="doji",
        parameters=(("threshold", threshold),),
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
            "supplied config disagrees with doji wrapper arguments",
            {"indicator_id": "doji"},
        )
    return config


def doji(
    data: MarketDataset,
    *,
    threshold: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Identify Doji candles from body-to-range proportion.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        threshold: Positive maximum body share, no greater than one.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic binary Doji ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating doji for %s (threshold=%s)", data.symbol, threshold)
    resolved_config = _build_config(threshold, config)
    validate_indicator("doji", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    open_price = np.asarray([float(record.open) for record in records], dtype="float64")
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    candle_range = high - low
    body = np.abs(close - open_price)
    # A positive-range candle is a Doji when its body is within the threshold
    # share of the range. A zero-range candle (high == low, hence
    # open == close) is a Doji per FR-INDI-031's open-equals-close rule.
    is_doji = np.where(
        candle_range > 0.0,
        body <= threshold * candle_range,
        np.isclose(open_price, close),
    )
    values = is_doji.astype("float64")
    row_time = pd.Series(index, index=index)
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=("doji",),
        output_values=pd.DataFrame({"doji": values}, index=index),
        available_at=pd.Series(
            [record.available_at for record in records], index=index
        ),
        computed_from_start=row_time,
        computed_from_end=row_time.copy(),
        unavailable_reason=unavailable_reason,
    )


__all__ = ["doji"]
