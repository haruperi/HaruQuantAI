"""Traditional pivot-point calculator.

Implements spec ``IND-ST-03``'s Traditional pivot family. The current
Indicators domain contract exposes only a single bar series with no
calendar/session boundary metadata (Data does not yet publish session
markers to Indicators), so this implementation's declared "session" is the
immediately preceding bar of the same series rather than a calendar
session; each row's pivots are computed from the prior row's closed
``high``/``low``/``close``. This is a documented project-specific
simplification of the spec's session concept, not a formula deviation.
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


def _build_config(config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable pivot-points configuration.

    Args:
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="pivot_points",
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
    if (
        config.indicator_id != expected.indicator_id
        or config.parameters != expected.parameters
        or config.source is not None
        or config.formula_version != expected.formula_version
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "supplied config disagrees with pivot_points wrapper arguments",
            {"indicator_id": "pivot_points"},
        )
    return config


@guard_public_boundary
def pivot_points(
    data: MarketDataset,
    *,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Traditional pivot point, resistance, and support levels.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic pivot-points ``IndicatorResult`` carrying ``P``,
        ``R1``-``R3``, and ``S1``-``S3``, derived from the immediately
        preceding closed bar.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating pivot_points for %s", data.symbol)
    resolved_config = _build_config(config)
    _unwrap_indicator_response(
        validate_indicator("pivot_points", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    row_count = len(records)

    is_valid = np.zeros(row_count, dtype=bool)
    is_valid[1:] = True
    prior_high = np.full(row_count, np.nan, dtype="float64")
    prior_low = np.full(row_count, np.nan, dtype="float64")
    prior_close = np.full(row_count, np.nan, dtype="float64")
    prior_high[1:] = high[:-1]
    prior_low[1:] = low[:-1]
    prior_close[1:] = close[:-1]

    pivot = (prior_high + prior_low + prior_close) / 3.0
    r1 = 2.0 * pivot - prior_low
    s1 = 2.0 * pivot - prior_high
    r2 = pivot + (prior_high - prior_low)
    s2 = pivot - (prior_high - prior_low)
    r3 = 2.0 * pivot + (prior_high - 2.0 * prior_low)
    s3 = 2.0 * pivot - (2.0 * prior_high - prior_low)

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
        "pivot_points_p",
        "pivot_points_r1",
        "pivot_points_r2",
        "pivot_points_r3",
        "pivot_points_s1",
        "pivot_points_s2",
        "pivot_points_s3",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, pivot, np.nan),
            output_columns[1]: np.where(is_valid, r1, np.nan),
            output_columns[2]: np.where(is_valid, r2, np.nan),
            output_columns[3]: np.where(is_valid, r3, np.nan),
            output_columns[4]: np.where(is_valid, s1, np.nan),
            output_columns[5]: np.where(is_valid, s2, np.nan),
            output_columns[6]: np.where(is_valid, s3, np.nan),
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


__all__ = ["pivot_points"]
