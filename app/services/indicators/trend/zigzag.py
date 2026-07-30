"""Causal confirmed-pivot ZigZag indicator."""

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


def _build_config(depth: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build the exact approved ZigZag configuration.

    Args:
        depth: Bars required on each side of a confirmed pivot.
        config: Optional explicitly supplied configuration.

    Returns:
        Complete immutable indicator configuration.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments or formula version.
    """
    expected = IndicatorConfig(
        indicator_id="zigzag",
        parameters=(("depth", depth),),
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
        or config.formula_version != _FORMULA_VERSION
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "supplied config disagrees with ZigZag depth or formula version",
            {"indicator_id": "zigzag"},
        )
    return config


def _confirmed_pivots(
    high: np.ndarray,
    low: np.ndarray,
    depth: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return alternating pivots on their causal confirmation rows.

    A pivot centered at position ``p`` is emitted only at ``p + depth``.
    Tied extrema are not pivots. Consecutive candidates of the same type are
    ignored so an already confirmed pivot is never retrospectively replaced.

    Args:
        high: Ordered finite high prices.
        low: Ordered finite low prices.
        depth: Required bars on either side of a pivot.

    Returns:
        Parallel pivot values, pivot types (``1`` high, ``-1`` low), and a
        Boolean readiness mask indexed by confirmation row.
    """
    size = len(high)
    values = np.full(size, np.nan, dtype="float64")
    types = np.full(size, np.nan, dtype="float64")
    ready = np.zeros(size, dtype=bool)
    last_type = 0
    for center in range(depth, size - depth):
        start = center - depth
        stop = center + depth + 1
        high_window = high[start:stop]
        low_window = low[start:stop]
        is_high = bool(
            high[center] == high_window.max()
            and np.count_nonzero(high_window == high[center]) == 1
        )
        is_low = bool(
            low[center] == low_window.min()
            and np.count_nonzero(low_window == low[center]) == 1
        )
        if is_high and not is_low:
            pivot_type = 1
        elif is_low and not is_high:
            pivot_type = -1
        else:
            pivot_type = 0
        if pivot_type in (0, last_type):
            continue
        confirmation = center + depth
        values[confirmation] = high[center] if pivot_type == 1 else low[center]
        types[confirmation] = float(pivot_type)
        ready[confirmation] = True
        last_type = pivot_type
    return values, types, ready


@guard_public_boundary
def zigzag(
    data: MarketDataset,
    *,
    depth: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate causal confirmed ZigZag pivots for one bar dataset.

    The result emits a pivot on its confirmation row, never on the historical
    center row. This makes every populated value safe at its declared
    ``available_at`` and prevents a later bar from rewriting a prior result.

    Args:
        data: Normalized immutable bar dataset.
        depth: Bars required on each side of a confirmed pivot; at least two.
        config: Optional exact configuration matching ``depth``.

    Returns:
        Atomic result with ``zigzag_value_{depth}`` and
        ``zigzag_type_{depth}`` columns.

    Raises:
        IndicatorError: On invalid configuration, input, or atomic result
            construction failure.
    """
    logger.info("Calculating causal ZigZag for %s (depth=%d)", data.symbol, depth)
    resolved_config = _build_config(depth, config)
    _unwrap_indicator_response(validate_indicator("zigzag", data, resolved_config))
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records],
        name="timestamp",
        tz="UTC",
    )
    high = np.array([float(record.high) for record in records], dtype="float64")
    low = np.array([float(record.low) for record in records], dtype="float64")
    values, types, ready = _confirmed_pivots(high, low, depth)

    computed_from_start = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    computed_from_end = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    available_at = pd.Series(
        [record.available_at for record in records],
        index=index,
    )
    for confirmation in np.flatnonzero(ready):
        center = int(confirmation) - depth
        computed_from_start.iloc[confirmation] = records[center - depth].timestamp
        computed_from_end.iloc[confirmation] = records[confirmation].timestamp
        available_at.iloc[confirmation] = max(
            record.available_at for record in records[: confirmation + 1]
        )

    unavailable_reason = pd.Series("not_pivot", index=index, dtype=object)
    unavailable_reason.iloc[: 2 * depth] = "warmup"
    unavailable_reason[ready] = pd.NA
    output_columns = (f"zigzag_value_{depth}", f"zigzag_type_{depth}")
    output_values = pd.DataFrame(
        {output_columns[0]: values, output_columns[1]: types},
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


__all__ = ["zigzag"]
