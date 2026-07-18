"""On-Balance Volume calculator."""

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
    """Build or validate the immutable OBV configuration.

    Args:
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            parameterless OBV contract.
    """
    logger.debug("Building obv config")
    expected = IndicatorConfig(
        indicator_id="obv",
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
            "supplied config disagrees with obv wrapper arguments",
            {"indicator_id": "obv"},
        )
    return config


def obv(
    data: MarketDataset,
    *,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate cumulative On-Balance Volume from close direction.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        config: Optional explicit parameterless configuration.

    Returns:
        A deterministic OBV ``IndicatorResult`` valid from the first row.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating obv for %s", data.symbol)
    resolved_config = _build_config(config)
    validate_indicator("obv", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    volume = np.asarray([float(record.volume) for record in records], dtype="float64")
    direction = np.zeros(len(records), dtype="float64")
    close_change = np.diff(close)
    direction[1:] = np.where(
        close_change > 0.0, volume[1:], np.where(close_change < 0.0, -volume[1:], 0.0)
    )
    values = np.cumsum(direction)
    computed_from_start = pd.Series(records[0].timestamp, index=index)
    computed_from_end = pd.Series(index, index=index)
    available_at = pd.Series(
        [record.available_at for record in records], index=index
    ).cummax()
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=("obv",),
        output_values=pd.DataFrame({"obv": values}, index=index),
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["obv"]
