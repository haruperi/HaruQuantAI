"""Volatility of volatility calculator.

Implements spec ``IND-VOL-10`` over an internally computed close-to-close
realized volatility series (this file's own canonical volatility source;
it does not call the sibling ``rolling_volatility`` public function, per
the package's no-sibling-call convention). Annualization is disabled by
default per the spec.

``u_t = ln(sigma_t / sigma_{t-1})``
``VoV_t = std_n(u)``

A non-positive or missing inner volatility value invalidates the affected
log-change (no zero substitution); rows preceding a fully valid trailing
window of log-changes remain warmup.
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
_SAMPLE_DDOF = 1


def _build_config(
    period: int, vol_period: int, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable volatility-of-volatility configuration.

    Args:
        period: Required outer log-change standard-deviation window ``n``.
        vol_period: Required inner realized-volatility window.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    expected = IndicatorConfig(
        indicator_id="volatility_of_volatility",
        parameters=(("period", period), ("vol_period", vol_period)),
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
            "supplied config disagrees with volatility_of_volatility wrapper arguments",
            {"indicator_id": "volatility_of_volatility"},
        )
    return config


def _realized_volatility_series(close: np.ndarray, vol_period: int) -> np.ndarray:
    """Compute the file's internal unannualized realized volatility series.

    Args:
            close: Row-ordered close prices.
            vol_period: Number of consecutive log returns per window.

    Returns:
            A float64 volatility series with ``nan`` warmup rows.

    Raises:
        None.
    """
    row_count = len(close)
    series = np.full(row_count, np.nan, dtype="float64")
    if row_count < vol_period + 1:
        return series
    log_returns = np.diff(np.log(close))
    for position in range(vol_period, row_count):
        window = log_returns[position - vol_period : position]
        series[position] = float(window.std(ddof=_SAMPLE_DDOF))
    return series


@guard_public_boundary
def volatility_of_volatility(
    data: MarketDataset,
    *,
    period: int,
    vol_period: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate the trailing standard deviation of volatility log-changes.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required outer log-change standard-deviation window ``n``
            of at least two.
        vol_period: Required inner realized-volatility window of at least
            two consecutive log returns.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic volatility-of-volatility ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating volatility_of_volatility for %s (period=%d, vol_period=%d)",
        data.symbol,
        period,
        vol_period,
    )
    resolved_config = _build_config(period, vol_period, config)
    _unwrap_indicator_response(
        validate_indicator("volatility_of_volatility", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    inner_series = _realized_volatility_series(close, vol_period)

    row_count = len(records)
    log_change = np.full(row_count, np.nan, dtype="float64")
    for position in range(1, row_count):
        previous = inner_series[position - 1]
        current = inner_series[position]
        if np.isnan(previous) or np.isnan(current) or previous <= 0.0 or current <= 0.0:
            continue
        log_change[position] = float(np.log(current / previous))

    values = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    for position in range(row_count):
        window_start = position - period + 1
        if window_start < 1:
            continue
        window = log_change[window_start : position + 1]
        if np.isnan(window).any():
            continue
        values[position] = float(window.std(ddof=_SAMPLE_DDOF))
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
    output_column = f"volatility_of_volatility_{period}_{vol_period}"

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


__all__ = ["volatility_of_volatility"]
