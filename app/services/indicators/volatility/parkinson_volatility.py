"""Parkinson range volatility calculator.

Implements spec ``IND-VOL-05``:

``sigma_P = sqrt(A / (4 * n * ln(2)) * sum_{i=1..n} [ln(H_i / L_i)]^2)``

Assumes no overnight gaps (a Parkinson limitation disclosed here per the
spec's warm-up/invalid-state note).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

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
_DEFAULT_ANNUALIZATION_FACTOR = 252.0


def _build_config(
    period: int, annualization_factor: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable Parkinson volatility configuration.

    Args:
        period: Required rolling window length ``n``.
        annualization_factor: Declared annualization factor ``A``.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    expected = IndicatorConfig(
        indicator_id="parkinson_volatility",
        parameters=(
            ("annualization_factor", annualization_factor),
            ("period", period),
        ),
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
            "supplied config disagrees with parkinson_volatility wrapper arguments",
            {"indicator_id": "parkinson_volatility"},
        )
    return config


@guard_public_boundary
def parkinson_volatility(
    data: MarketDataset,
    *,
    period: int,
    annualization_factor: float = _DEFAULT_ANNUALIZATION_FACTOR,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Parkinson high-low range annualized volatility.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling window length ``n`` of at least two.
        annualization_factor: The declared annualization factor ``A``;
            defaults to 252 trading days but is a profile parameter, never
            a hardcoded constant.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Parkinson volatility ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating parkinson_volatility for %s (period=%d, A=%s)",
        data.symbol,
        period,
        annualization_factor,
    )
    resolved_config = _build_config(period, annualization_factor, config)
    _unwrap_indicator_response(
        validate_indicator("parkinson_volatility", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    log_hl_sq = np.square(np.log(high / low))

    row_count = len(records)
    values = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    if row_count >= period:
        windows = sliding_window_view(log_hl_sq, window_shape=period)
        mean_sq = windows.mean(axis=1)
        values[period - 1 :] = np.sqrt(
            annualization_factor / (4.0 * math.log(2.0)) * mean_sq
        )
        is_valid[period - 1 :] = True

    computed_from_start = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    computed_from_end = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    if is_valid.any():
        row_time = pd.Series(index, index=index)
        computed_from_start[is_valid] = row_time.shift(period - 1)[is_valid]
        computed_from_end[is_valid] = index[is_valid]
    available_at = pd.Series([record.available_at for record in records], index=index)
    if row_count >= period:
        nanos = pd.DatetimeIndex(available_at).asi8
        rolling_max = nanos.copy()
        rolling_max[period - 1 :] = sliding_window_view(nanos, period).max(axis=1)
        available_at[is_valid] = pd.Series(
            pd.to_datetime(rolling_max, unit="us", utc=True), index=index
        )[is_valid]
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_valid] = "warmup"
    output_column = f"parkinson_volatility_{period}"

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


__all__ = ["parkinson_volatility"]
