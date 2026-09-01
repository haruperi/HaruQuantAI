"""Choppiness Index regime classifier."""

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
# 0=DIRECTIONAL, 1=TRANSITION, 2=CHOPPY_RANGE
_DIRECTIONAL, _TRANSITION, _CHOPPY_RANGE = 0.0, 1.0, 2.0


def _build_config(
    period: int,
    lower_threshold: float,
    upper_threshold: float,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the immutable Choppiness regime configuration.

    Args:
        period: The period value.
        lower_threshold: The lower threshold value.
        upper_threshold: The upper threshold value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="choppiness_regime",
        parameters=(
            ("lower_threshold", lower_threshold),
            ("period", period),
            ("upper_threshold", upper_threshold),
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
            "supplied config disagrees with choppiness_regime wrapper arguments",
            {"indicator_id": "choppiness_regime"},
        )
    return config


def _true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Compute the standard true-range array (see ``volatility.atr``).

    Args:
        high: The high value.
        low: The low value.
        close: The close value.

    Returns:
        The np.ndarray result.

    Raises:
        None.
    """
    previous_close = np.empty(len(close), dtype="float64")
    previous_close[0] = close[0]
    previous_close[1:] = close[:-1]
    return np.asarray(
        np.maximum.reduce(
            (high - low, np.abs(high - previous_close), np.abs(low - previous_close))
        ),
        dtype="float64",
    )


@guard_public_boundary
def choppiness_regime(
    data: MarketDataset,
    *,
    period: int,
    lower_threshold: float,
    upper_threshold: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Classify spec ``IND-RG-02`` Choppiness Index regime.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required window of at least two.
        lower_threshold: Required directional threshold.
        upper_threshold: Required choppy-range threshold (must exceed
            ``lower_threshold``).
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Choppiness-regime ``IndicatorResult`` carrying the
        ``choppiness`` value in ``[0, 100]`` and the regime state
        (``0``=DIRECTIONAL, ``1``=TRANSITION, ``2``=CHOPPY_RANGE).

    Raises:
        IndicatorError: If ``lower_threshold >= upper_threshold``, or on
            validation or atomic calculation failure.
    """
    if lower_threshold >= upper_threshold:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "choppiness_regime requires lower_threshold strictly below upper_threshold",
            {"indicator_id": "choppiness_regime"},
        )
    logger.info("Calculating choppiness_regime for %s (period=%d)", data.symbol, period)
    resolved_config = _build_config(period, lower_threshold, upper_threshold, config)
    _unwrap_indicator_response(
        validate_indicator("choppiness_regime", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    row_count = len(records)

    true_range = _true_range(high, low, close)
    tr_series = pd.Series(true_range, index=index)
    sum_tr = tr_series.rolling(window=period, min_periods=period).sum()
    high_series = pd.Series(high, index=index)
    low_series = pd.Series(low, index=index)
    range_high = high_series.rolling(window=period, min_periods=period).max()
    range_low = low_series.rolling(window=period, min_periods=period).min()
    span = (range_high - range_low).to_numpy("float64")
    sum_tr_values = sum_tr.to_numpy("float64")

    candidate = np.zeros(row_count, dtype=bool)
    candidate[period - 1 :] = True
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(
            span > 0.0, sum_tr_values / np.where(span > 0.0, span, np.nan), np.nan
        )
        choppiness = 100.0 * np.log10(ratio) / np.log10(period)
    is_valid = candidate & np.isfinite(choppiness)

    state = np.select(
        [choppiness <= lower_threshold, choppiness >= upper_threshold],
        [_DIRECTIONAL, _CHOPPY_RANGE],
        default=_TRANSITION,
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

    output_columns = (f"choppiness_{period}", f"choppiness_state_{period}")
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, choppiness, np.nan),
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


__all__ = ["choppiness_regime"]
