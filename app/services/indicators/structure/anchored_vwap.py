"""Anchored VWAP calculator.

Implements spec ``IND-ST-04`` over bar-mode typical price
``TP=(H+L+C)/3``: ``AVWAP_{a,t} = sum(TP_i*V_i)/sum(V_i)`` for ``i`` from
the explicit anchor row through ``t``. The anchor is supplied as an
explicit, already-visible row position within the dataset (a timestamp
anchor is out of scope without a Data-owned timestamp-to-position lookup).
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


def _build_config(anchor_index: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable anchored-VWAP configuration.

    Args:
        anchor_index: The anchor index value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="anchored_vwap",
        parameters=(("anchor_index", anchor_index),),
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
            "supplied config disagrees with anchored_vwap wrapper arguments",
            {"indicator_id": "anchored_vwap"},
        )
    return config


@guard_public_boundary
def anchored_vwap(
    data: MarketDataset,
    *,
    anchor_index: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate anchored VWAP, cumulative volume, and price deviation.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        anchor_index: Required non-negative zero-based row position marking
            the explicit, already-visible anchor bar; must be a valid row
            index within the dataset.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic anchored-VWAP ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating anchored_vwap for %s (anchor_index=%d)", data.symbol, anchor_index
    )
    if anchor_index < 0 or anchor_index >= data.record_count:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "anchor_index must be a valid row position within the dataset",
            {"anchor_index": anchor_index},
        )
    resolved_config = _build_config(anchor_index, config)
    _unwrap_indicator_response(
        validate_indicator("anchored_vwap", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    volume = np.asarray([float(record.volume) for record in records], dtype="float64")
    row_count = len(records)

    typical_price = (high + low + close) / 3.0
    tail_price_volume = np.zeros(row_count, dtype="float64")
    tail_volume = np.zeros(row_count, dtype="float64")
    tail_price_volume[anchor_index:] = (
        typical_price[anchor_index:] * volume[anchor_index:]
    )
    tail_volume[anchor_index:] = volume[anchor_index:]
    cumulative_price_volume = np.cumsum(tail_price_volume)
    cumulative_volume = np.cumsum(tail_volume)

    is_valid = np.zeros(row_count, dtype=bool)
    is_valid[anchor_index:] = cumulative_volume[anchor_index:] > 0.0
    avwap = np.full(row_count, np.nan, dtype="float64")
    avwap[is_valid] = cumulative_price_volume[is_valid] / cumulative_volume[is_valid]
    deviation = np.full(row_count, np.nan, dtype="float64")
    deviation[is_valid] = close[is_valid] - avwap[is_valid]

    computed_from_start = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    computed_from_end = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    if is_valid.any():
        computed_from_start[is_valid] = index[anchor_index]
        computed_from_end[is_valid] = index[is_valid]
    available_at = pd.Series([record.available_at for record in records], index=index)
    cumulative_available = available_at.cummax()
    available_at[is_valid] = cumulative_available[is_valid]
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_valid] = "warmup"

    output_columns = (
        f"anchored_vwap_{anchor_index}",
        f"anchored_vwap_cumulative_volume_{anchor_index}",
        f"anchored_vwap_deviation_{anchor_index}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: avwap,
            output_columns[1]: np.where(is_valid, cumulative_volume, np.nan),
            output_columns[2]: deviation,
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


__all__ = ["anchored_vwap"]
