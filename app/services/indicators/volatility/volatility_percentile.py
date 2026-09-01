"""Volatility percentile and z-score calculator.

Implements spec ``IND-VOL-09`` over an internally computed close-to-close
realized volatility series (the file's own canonical volatility source;
it does not call the sibling ``rolling_volatility`` public function, per
the package's no-sibling-call convention):

``Pct_t = 100 * (#{x_i < x_t} + 0.5*#{x_i = x_t}) / n``
``Z_t = (x_t - mean_n(x)) / std_n(x)``

Both outputs are published from one atomic result, so a constant reference
window (undefined z-score per spec) marks the whole row unavailable with
reason ``zero_reference_std`` rather than leaving ``percentile`` populated
while ``z_score`` is ``NaN`` within the same row.
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
_SAMPLE_DDOF = 1


def _build_config(
    reference_period: int,
    vol_period: int,
    annualization_factor: float,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the immutable volatility percentile configuration.

    Args:
        reference_period: Required historical comparison window ``n``.
        vol_period: Required inner realized-volatility window.
        annualization_factor: Declared annualization factor ``A`` for the
            inner realized volatility series.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    expected = IndicatorConfig(
        indicator_id="volatility_percentile",
        parameters=(
            ("annualization_factor", annualization_factor),
            ("reference_period", reference_period),
            ("vol_period", vol_period),
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
            "supplied config disagrees with volatility_percentile wrapper arguments",
            {"indicator_id": "volatility_percentile"},
        )
    return config


def _realized_volatility_series(
    close: np.ndarray, vol_period: int, annualization_factor: float
) -> np.ndarray:
    """Compute the file's internal close-to-close realized volatility series.

    Args:
            close: Row-ordered close prices.
            vol_period: Number of consecutive log returns per window.
            annualization_factor: Declared annualization factor ``A``.

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
    windows = sliding_window_view(log_returns, window_shape=vol_period)
    stds = windows.std(axis=1, ddof=_SAMPLE_DDOF)
    series[vol_period:] = stds * math.sqrt(annualization_factor)
    return series


def _percentile_and_zscore(
    series: np.ndarray, reference_period: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the trailing percentile rank and z-score of one series.

    Args:
            series: A volatility series with ``nan`` warmup rows.
            reference_period: Trailing comparison window length ``n``.

    Returns:
            A ``(percentile, z_score, is_valid)`` triple.

    Raises:
        None.
    """
    row_count = len(series)
    percentile = np.full(row_count, np.nan, dtype="float64")
    z_score = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    for position in range(row_count):
        if np.isnan(series[position]):
            continue
        window_start = position - reference_period + 1
        if window_start < 0:
            continue
        window = series[window_start : position + 1]
        if np.isnan(window).any():
            continue
        current = series[position]
        less = float(np.sum(window < current))
        equal = float(np.sum(window == current))
        percentile[position] = 100.0 * (less + 0.5 * equal) / reference_period
        std = float(window.std(ddof=_SAMPLE_DDOF))
        if std <= 0.0:
            continue
        z_score[position] = (current - float(window.mean())) / std
        is_valid[position] = True
    return percentile, z_score, is_valid


@guard_public_boundary
def volatility_percentile(
    data: MarketDataset,
    *,
    reference_period: int,
    vol_period: int,
    annualization_factor: float = _DEFAULT_ANNUALIZATION_FACTOR,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate the trailing percentile rank and z-score of realized volatility.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        reference_period: Required trailing comparison window ``n`` of at
            least two.
        vol_period: Required inner realized-volatility window of at least
            two consecutive log returns.
        annualization_factor: The declared annualization factor ``A`` for
            the inner realized volatility series; defaults to 252 trading
            days but is a profile parameter, never a hardcoded constant.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic two-column ``IndicatorResult`` carrying
        ``percentile`` and ``z_score``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating volatility_percentile for %s "
        "(reference_period=%d, vol_period=%d, A=%s)",
        data.symbol,
        reference_period,
        vol_period,
        annualization_factor,
    )
    resolved_config = _build_config(
        reference_period, vol_period, annualization_factor, config
    )
    _unwrap_indicator_response(
        validate_indicator("volatility_percentile", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    inner_series = _realized_volatility_series(close, vol_period, annualization_factor)
    percentile, z_score, is_valid = _percentile_and_zscore(
        inner_series, reference_period
    )

    computed_from_start = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    computed_from_end = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    if is_valid.any():
        computed_from_start[is_valid] = records[0].timestamp
        computed_from_end[is_valid] = index[is_valid]
    available_at = pd.Series([record.available_at for record in records], index=index)
    cumulative_available = available_at.cummax()
    available_at[is_valid] = cumulative_available[is_valid]
    unavailable_reason = pd.Series("warmup", index=index, dtype=object)
    unavailable_reason[is_valid] = pd.NA
    has_series_but_undefined_zscore = (~is_valid) & ~np.isnan(percentile)
    unavailable_reason[has_series_but_undefined_zscore] = "zero_reference_std"

    output_columns = (
        f"volatility_percentile_{reference_period}_{vol_period}",
        f"volatility_zscore_{reference_period}_{vol_period}",
    )
    percentile_masked = np.where(is_valid, percentile, np.nan)
    zscore_masked = np.where(is_valid, z_score, np.nan)

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=output_columns,
        output_values=pd.DataFrame(
            {
                output_columns[0]: percentile_masked,
                output_columns[1]: zscore_masked,
            },
            index=index,
        ),
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["volatility_percentile"]
