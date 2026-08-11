"""Rogers-Satchell range volatility calculator.

Implements spec ``IND-VOL-07``:

``sigma_RS = sqrt(A/n * sum_{i=1..n} [ln(H_i/O_i)*ln(H_i/C_i) +
ln(L_i/O_i)*ln(L_i/C_i)])``

The Rogers-Satchell estimator is drift-independent and its per-bar term is
theoretically non-negative for well-formed OHLC bars, but a windowed mean
that goes negative from finite-precision arithmetic is clamped only within
a declared tiny tolerance; anything beyond that tolerance marks the row
unavailable with reason ``negative_variance`` rather than being silently
square-rooted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

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
_DEFAULT_ANNUALIZATION_FACTOR = 252.0
_NEGATIVE_VARIANCE_TOLERANCE = -1e-12


def _build_config(
    period: int, annualization_factor: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable Rogers-Satchell volatility configuration.

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
        indicator_id="rogers_satchell_volatility",
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
            "supplied config disagrees with rogers_satchell_volatility "
            "wrapper arguments",
            {"indicator_id": "rogers_satchell_volatility"},
        )
    return config


@guard_public_boundary
def rogers_satchell_volatility(
    data: MarketDataset,
    *,
    period: int,
    annualization_factor: float = _DEFAULT_ANNUALIZATION_FACTOR,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate Rogers-Satchell OHLC-range annualized volatility.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling window length ``n`` of at least two.
        annualization_factor: The declared annualization factor ``A``;
            defaults to 252 trading days but is a profile parameter, never
            a hardcoded constant.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Rogers-Satchell volatility ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating rogers_satchell_volatility for %s (period=%d, A=%s)",
        data.symbol,
        period,
        annualization_factor,
    )
    resolved_config = _build_config(period, annualization_factor, config)
    _unwrap_indicator_response(
        validate_indicator("rogers_satchell_volatility", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    open_ = np.asarray([float(record.open) for record in records], dtype="float64")
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    per_bar = np.log(high / open_) * np.log(high / close) + np.log(
        low / open_
    ) * np.log(low / close)

    row_count = len(records)
    values = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[:] = "warmup"
    if row_count >= period:
        windows = sliding_window_view(per_bar, window_shape=period)
        mean_variance = windows.mean(axis=1)
        window_positions = np.arange(period - 1, row_count)
        negative_beyond_tolerance = mean_variance < _NEGATIVE_VARIANCE_TOLERANCE
        clamped = np.where(mean_variance < 0.0, 0.0, mean_variance)
        computed = np.sqrt(annualization_factor / period * clamped)
        valid_positions = window_positions[~negative_beyond_tolerance]
        invalid_positions = window_positions[negative_beyond_tolerance]
        values[valid_positions] = computed[~negative_beyond_tolerance]
        is_valid[valid_positions] = True
        unavailable_reason.iloc[valid_positions] = pd.NA
        unavailable_reason.iloc[invalid_positions] = "negative_variance"

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
    output_column = f"rogers_satchell_volatility_{period}"

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


__all__ = ["rogers_satchell_volatility"]
