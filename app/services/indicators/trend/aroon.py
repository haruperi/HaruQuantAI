"""Aroon Up, Aroon Down, and Aroon Oscillator calculator.

Implements spec ``IND-TR-04`` over an ``N+1``-bar window. Ties resolve to
the most recent occurrence (the smallest bars-since-extreme age).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    _unwrap_indicator_response,
    guard_public_boundary,
)
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator
from app.utils import get_logger

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


def _build_config(lookback: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable Aroon configuration.

    Args:
        lookback: The lookback value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="aroon",
        parameters=(("lookback", lookback),),
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
            "supplied config disagrees with aroon wrapper arguments",
            {"indicator_id": "aroon"},
        )
    return config


@guard_public_boundary
def aroon(
    data: MarketDataset,
    *,
    lookback: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Aroon Up, Aroon Down, and the Aroon Oscillator.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        lookback: Required lookback ``N`` of at least one; the evaluation
            window contains ``N+1`` bars.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Aroon ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating aroon for %s (lookback=%d)", data.symbol, lookback)
    resolved_config = _build_config(lookback, config)
    _unwrap_indicator_response(validate_indicator("aroon", data, resolved_config))
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    row_count = len(records)
    window_size = lookback + 1

    is_valid = np.zeros(row_count, dtype=bool)
    aroon_up = np.full(row_count, np.nan, dtype="float64")
    aroon_down = np.full(row_count, np.nan, dtype="float64")
    aroon_osc = np.full(row_count, np.nan, dtype="float64")

    for position in range(window_size - 1, row_count):
        window_high = high[position - window_size + 1 : position + 1]
        window_low = low[position - window_size + 1 : position + 1]
        # Most-recent-tie policy: take the last occurrence of the extreme.
        age_high = (
            window_size - 1 - int(np.flatnonzero(window_high == window_high.max())[-1])
        )
        age_low = (
            window_size - 1 - int(np.flatnonzero(window_low == window_low.min())[-1])
        )
        up = 100.0 * (lookback - age_high) / lookback
        down = 100.0 * (lookback - age_low) / lookback
        aroon_up[position] = up
        aroon_down[position] = down
        aroon_osc[position] = up - down
        is_valid[position] = True

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

    output_columns = (
        f"aroon_up_{lookback}",
        f"aroon_down_{lookback}",
        f"aroon_oscillator_{lookback}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: aroon_up,
            output_columns[1]: aroon_down,
            output_columns[2]: aroon_osc,
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


__all__ = ["aroon"]
