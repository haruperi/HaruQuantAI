"""Confirmed swing high/low pivot calculator.

Implements spec ``IND-ST-01``: a pivot high/low at index ``t`` is the
max/min of the ``l``-left/``r``-right bar window, but is only *confirmed*
(published) at ``t+r`` once the right-side bars are closed and available,
so no pivot is ever represented before its confirmation bar.
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


def _build_config(
    left: int, right: int, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable pivots configuration.

    Args:
        left: The left value.
        right: The right value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="pivots",
        parameters=(("left", left), ("right", right)),
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
            "supplied config disagrees with pivots wrapper arguments",
            {"indicator_id": "pivots"},
        )
    return config


@guard_public_boundary
def pivots(
    data: MarketDataset,
    *,
    left: int,
    right: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate confirmed swing-high/swing-low pivot flags and prices.

    A pivot high at bar ``t`` requires ``high[t]`` to be the strict maximum
    of the ``[t-left, t+right]`` window (most-recent-tie policy for equal
    highs); the pivot is published at bar ``t+right``, never earlier. The
    symmetric rule applies to pivot lows on ``low``.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        left: Required left-bar count of at least one.
        right: Required right-bar count of at least one.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic pivots ``IndicatorResult`` carrying pivot flags
        (``1.0``/``0.0``) and pivot prices (``0.0`` where no pivot is
        confirmed at that row).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating pivots for %s (left=%d, right=%d)", data.symbol, left, right
    )
    resolved_config = _build_config(left, right, config)
    _unwrap_indicator_response(validate_indicator("pivots", data, resolved_config))
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    row_count = len(records)
    window = left + right + 1

    is_valid = np.zeros(row_count, dtype=bool)
    pivot_high_flag = np.zeros(row_count, dtype="float64")
    pivot_high_price = np.zeros(row_count, dtype="float64")
    pivot_low_flag = np.zeros(row_count, dtype="float64")
    pivot_low_price = np.zeros(row_count, dtype="float64")

    for pivot_index in range(left, row_count - right):
        confirm_at = pivot_index + right
        window_high = high[pivot_index - left : pivot_index + right + 1]
        window_low = low[pivot_index - left : pivot_index + right + 1]
        if window_high.size != window:
            continue
        if high[pivot_index] == window_high.max():
            pivot_high_flag[confirm_at] = 1.0
            pivot_high_price[confirm_at] = float(high[pivot_index])
        if low[pivot_index] == window_low.min():
            pivot_low_flag[confirm_at] = 1.0
            pivot_low_price[confirm_at] = float(low[pivot_index])
        is_valid[confirm_at] = True

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
        f"pivot_high_flag_{left}_{right}",
        f"pivot_high_price_{left}_{right}",
        f"pivot_low_flag_{left}_{right}",
        f"pivot_low_price_{left}_{right}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: pivot_high_flag,
            output_columns[1]: pivot_high_price,
            output_columns[2]: pivot_low_flag,
            output_columns[3]: pivot_low_price,
        },
        index=index,
    )
    output_values.loc[~is_valid, :] = np.nan

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


__all__ = ["pivots"]
