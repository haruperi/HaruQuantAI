"""Price gap and three-bar fair-value-gap calculator.

Implements spec ``IND-ST-06``: one-bar ``GapUp``/``GapDown`` and three-bar
``FVGUp``/``FVGDown`` imbalances against a declared minimum-gap threshold
``g_min``. The spec's ``g_min = max(k_tick*delta, k_atr*ATR)`` composite is
simplified to a single declared ``min_gap`` price threshold supplied
directly by the caller (documented simplification: this leaf file does not
cross-depend on ``volatility.atr`` or a tick-size contract this session).
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


def _build_config(min_gap: float, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable gaps configuration.

    Args:
        min_gap: The min gap value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="gaps",
        parameters=(("min_gap", min_gap),),
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
            "supplied config disagrees with gaps wrapper arguments",
            {"indicator_id": "gaps"},
        )
    return config


@guard_public_boundary
def gaps(
    data: MarketDataset,
    *,
    min_gap: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate one-bar gap and three-bar fair-value-gap sizes.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        min_gap: Required non-negative minimum gap threshold ``g_min`` in
            price units; a gap/FVG below this threshold reports as ``0.0``.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic gaps ``IndicatorResult`` carrying ``gap_up``,
        ``gap_down``, ``fvg_up``, and ``fvg_down`` sizes (``0.0`` when no
        qualifying gap exists at that row).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info("Calculating gaps for %s (min_gap=%s)", data.symbol, min_gap)
    if min_gap < 0:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "min_gap must be non-negative",
            {"min_gap": min_gap},
        )
    resolved_config = _build_config(min_gap, config)
    _unwrap_indicator_response(validate_indicator("gaps", data, resolved_config))
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    row_count = len(records)

    is_valid = np.zeros(row_count, dtype=bool)
    is_valid[2:] = True
    gap_up = np.zeros(row_count, dtype="float64")
    gap_down = np.zeros(row_count, dtype="float64")
    fvg_up = np.zeros(row_count, dtype="float64")
    fvg_down = np.zeros(row_count, dtype="float64")

    raw_gap_up = np.zeros(row_count, dtype="float64")
    raw_gap_down = np.zeros(row_count, dtype="float64")
    raw_gap_up[1:] = low[1:] - high[:-1]
    raw_gap_down[1:] = low[:-1] - high[1:]
    raw_fvg_up = np.zeros(row_count, dtype="float64")
    raw_fvg_down = np.zeros(row_count, dtype="float64")
    raw_fvg_up[2:] = low[2:] - high[:-2]
    raw_fvg_down[2:] = low[:-2] - high[2:]

    gap_up[is_valid] = np.where(
        raw_gap_up[is_valid] >= min_gap, raw_gap_up[is_valid], 0.0
    )
    gap_down[is_valid] = np.where(
        raw_gap_down[is_valid] >= min_gap, raw_gap_down[is_valid], 0.0
    )
    fvg_up[is_valid] = np.where(
        raw_fvg_up[is_valid] >= min_gap, raw_fvg_up[is_valid], 0.0
    )
    fvg_down[is_valid] = np.where(
        raw_fvg_down[is_valid] >= min_gap, raw_fvg_down[is_valid], 0.0
    )

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

    output_columns = ("gap_up", "gap_down", "fvg_up", "fvg_down")
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, gap_up, np.nan),
            output_columns[1]: np.where(is_valid, gap_down, np.nan),
            output_columns[2]: np.where(is_valid, fvg_up, np.nan),
            output_columns[3]: np.where(is_valid, fvg_down, np.nan),
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


__all__ = ["gaps"]
