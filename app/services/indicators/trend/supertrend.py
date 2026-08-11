# ruff: noqa: PD011, PLR0915
"""Supertrend calculator.

Implements spec ``IND-TR-06``'s canonical recurrence over ``HL2`` bands
built from the multiplier and the canonical ``volatility.atr`` public
wrapper (the one approved cross-module dependency for this indicator).
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
from app.services.indicators.volatility.atr import atr as _atr
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
    atr_period: int, multiplier: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable Supertrend configuration.

    Args:
        atr_period: The atr period value.
        multiplier: The multiplier value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="supertrend",
        parameters=(("atr_period", atr_period), ("multiplier", multiplier)),
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
            "supplied config disagrees with supertrend wrapper arguments",
            {"indicator_id": "supertrend"},
        )
    return config


@guard_public_boundary
def supertrend(
    data: MarketDataset,
    *,
    atr_period: int,
    multiplier: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate the Supertrend line and trend direction.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        atr_period: Required smoothing period fed to the canonical ATR.
        multiplier: Required positive ATR band multiplier.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Supertrend ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating supertrend for %s (atr_period=%d, multiplier=%s)",
        data.symbol,
        atr_period,
        multiplier,
    )
    resolved_config = _build_config(atr_period, multiplier, config)
    _unwrap_indicator_response(validate_indicator("supertrend", data, resolved_config))
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")

    atr_result: IndicatorResult = _unwrap_indicator_response(
        _atr(data, period=atr_period)
    )
    atr_values = atr_result.values[f"atr_{atr_period}"].to_numpy(dtype="float64")

    row_count = len(records)
    hl2 = (high + low) / 2.0
    basic_upper = hl2 + multiplier * atr_values
    basic_lower = hl2 - multiplier * atr_values

    final_upper = np.full(row_count, np.nan, dtype="float64")
    final_lower = np.full(row_count, np.nan, dtype="float64")
    line = np.full(row_count, np.nan, dtype="float64")
    direction = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)

    first_atr = (
        int(np.flatnonzero(~np.isnan(atr_values))[0])
        if np.isfinite(atr_values).any()
        else row_count
    )

    for position in range(row_count):
        if position < first_atr:
            continue
        if position == first_atr:
            final_upper[position] = basic_upper[position]
            final_lower[position] = basic_lower[position]
            direction[position] = 1.0 if close[position] >= hl2[position] else -1.0
            line[position] = (
                final_lower[position]
                if direction[position] > 0
                else final_upper[position]
            )
            is_valid[position] = True
            continue
        prev_upper = final_upper[position - 1]
        prev_lower = final_lower[position - 1]
        prev_close = close[position - 1]
        final_upper[position] = (
            basic_upper[position]
            if basic_upper[position] < prev_upper or prev_close > prev_upper
            else prev_upper
        )
        final_lower[position] = (
            basic_lower[position]
            if basic_lower[position] > prev_lower or prev_close < prev_lower
            else prev_lower
        )
        prev_direction = direction[position - 1]
        if prev_direction > 0 and close[position] < final_lower[position]:
            direction[position] = -1.0
        elif prev_direction < 0 and close[position] > final_upper[position]:
            direction[position] = 1.0
        else:
            direction[position] = prev_direction
        line[position] = (
            final_lower[position] if direction[position] > 0 else final_upper[position]
        )
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
        f"supertrend_line_{atr_period}",
        f"supertrend_direction_{atr_period}",
        f"supertrend_upper_{atr_period}",
        f"supertrend_lower_{atr_period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: line,
            output_columns[1]: direction,
            output_columns[2]: final_upper,
            output_columns[3]: final_lower,
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


__all__ = ["supertrend"]
