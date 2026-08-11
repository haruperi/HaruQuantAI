# ruff: noqa: PLR2004
"""Hurst persistence regime classifier (rescaled-range estimator)."""

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
# 0=RANDOM_LIKE, 1=PERSISTENT, 2=ANTI_PERSISTENT
_RANDOM_LIKE, _PERSISTENT, _ANTI_PERSISTENT = 0.0, 1.0, 2.0


def _build_config(
    window: int,
    min_scale: int,
    max_scale: int,
    scale_count: int,
    lower_threshold: float,
    upper_threshold: float,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the immutable Hurst-regime configuration.

    Args:
        window: The window value.
        min_scale: The min scale value.
        max_scale: The max scale value.
        scale_count: The scale count value.
        lower_threshold: The lower threshold value.
        upper_threshold: The upper threshold value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="hurst_regime",
        parameters=(
            ("lower_threshold", lower_threshold),
            ("max_scale", max_scale),
            ("min_scale", min_scale),
            ("scale_count", scale_count),
            ("upper_threshold", upper_threshold),
            ("window", window),
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
            "supplied config disagrees with hurst_regime wrapper arguments",
            {"indicator_id": "hurst_regime"},
        )
    return config


def _resolve_scales(
    min_scale: int, max_scale: int, scale_count: int
) -> tuple[int, ...]:
    """Resolve a sorted, de-duplicated, at-least-two-value integer scale set.

    Args:
        min_scale: The min scale value.
        max_scale: The max scale value.
        scale_count: The scale count value.

    Returns:
        The tuple[int, ...] result.

    Raises:
        None.
    """
    raw = np.unique(
        np.round(np.linspace(min_scale, max_scale, num=scale_count)).astype("int64")
    )
    return tuple(int(value) for value in raw if value >= 2)


def _rescaled_range(sample: np.ndarray, scale: int) -> float | None:
    """Compute the average rescaled range for one scale over one sample.

    Args:
        sample: The sample value.
        scale: The scale value.

    Returns:
        The float | None result.

    Raises:
        None.
    """
    block_count = len(sample) // scale
    if block_count < 1:
        return None
    ratios: list[float] = []
    for block_index in range(block_count):
        block = sample[block_index * scale : (block_index + 1) * scale]
        mean = block.mean()
        deviations = np.cumsum(block - mean)
        block_range = float(deviations.max() - deviations.min())
        block_std = float(block.std(ddof=0))
        if block_std > 0.0:
            ratios.append(block_range / block_std)
    if not ratios:
        return None
    return float(np.mean(ratios))


def _hurst_exponent(sample: np.ndarray, scales: tuple[int, ...]) -> float | None:
    """Estimate the Hurst exponent as the OLS slope of ``log(R/S)`` on ``log(N)``.

    Args:
        sample: The sample value.
        scales: The scales value.

    Returns:
        The float | None result.

    Raises:
        None.
    """
    log_n: list[float] = []
    log_rs: list[float] = []
    for scale in scales:
        rescaled = _rescaled_range(sample, scale)
        if rescaled is not None and rescaled > 0.0:
            log_n.append(np.log(scale))
            log_rs.append(np.log(rescaled))
    if len(log_n) < 2:
        return None
    slope, _intercept = np.polyfit(np.asarray(log_n), np.asarray(log_rs), 1)
    return float(slope)


@guard_public_boundary
def hurst_regime(
    data: MarketDataset,
    *,
    window: int,
    min_scale: int,
    max_scale: int,
    scale_count: int,
    lower_threshold: float,
    upper_threshold: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Classify spec ``IND-RG-03`` Hurst persistence regime.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        window: Required trailing log-return sample size of at least
            ``2 * max_scale``.
        min_scale: Required minimum rescaled-range block size, at least 2.
        max_scale: Required maximum rescaled-range block size, at least
            ``min_scale``.
        scale_count: Required number of scales sampled between
            ``min_scale`` and ``max_scale``, at least 2.
        lower_threshold: Required anti-persistence threshold.
        upper_threshold: Required persistence threshold (must exceed
            ``lower_threshold``).
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Hurst-regime ``IndicatorResult`` carrying the
        estimated ``hurst_exponent`` and the regime state
        (``0``=RANDOM_LIKE, ``1``=PERSISTENT, ``2``=ANTI_PERSISTENT).

    Raises:
        IndicatorError: If threshold or scale ordering is invalid, or on
            validation or atomic calculation failure.
    """
    if lower_threshold >= upper_threshold:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "hurst_regime requires lower_threshold strictly below upper_threshold",
            {"indicator_id": "hurst_regime"},
        )
    if min_scale < 2 or max_scale < min_scale:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "hurst_regime requires 2 <= min_scale <= max_scale",
            {"indicator_id": "hurst_regime"},
        )
    logger.info("Calculating hurst_regime for %s (window=%d)", data.symbol, window)
    resolved_config = _build_config(
        window,
        min_scale,
        max_scale,
        scale_count,
        lower_threshold,
        upper_threshold,
        config,
    )
    _unwrap_indicator_response(
        validate_indicator("hurst_regime", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    if (close <= 0).any():
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_OHLC,
            "hurst_regime requires strictly positive close prices",
            {"indicator_id": "hurst_regime"},
        )
    row_count = len(records)
    log_return = np.full(row_count, np.nan, dtype="float64")
    log_return[1:] = np.log(close[1:]) - np.log(close[:-1])
    scales = _resolve_scales(min_scale, max_scale, scale_count)

    exponent = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    for position in range(row_count):
        if position + 1 < window:
            continue
        sample = log_return[position - window + 1 : position + 1]
        if np.isnan(sample).any():
            continue
        result = _hurst_exponent(sample, scales)
        if result is not None:
            exponent[position] = result
            is_valid[position] = True

    state = np.select(
        [exponent > upper_threshold, exponent < lower_threshold],
        [_PERSISTENT, _ANTI_PERSISTENT],
        default=_RANDOM_LIKE,
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

    output_columns = (f"hurst_exponent_{window}", f"hurst_state_{window}")
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, exponent, np.nan),
            output_columns[1]: np.where(is_valid, state, np.nan),
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


__all__ = ["hurst_regime"]
