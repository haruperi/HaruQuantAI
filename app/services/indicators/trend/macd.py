"""MACD (Moving Average Convergence Divergence) calculator.

Implements spec ``IND-TR-05``: ``MACD_t = EMA_nf(P)_t - EMA_ns(P)_t``,
``Signal_t = EMA_nsig(MACD)_t``, ``Histogram_t = MACD_t - Signal_t``.

Computes its own internal EMA primitive rather than calling the sibling
``trend.ema`` public wrapper, per the package's no-sibling-call convention.
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


def _build_config(
    fast_period: int,
    slow_period: int,
    signal_period: int,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the immutable MACD configuration.

    Args:
        fast_period: The fast period value.
        slow_period: The slow period value.
        signal_period: The signal period value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="macd",
        parameters=(
            ("fast_period", fast_period),
            ("signal_period", signal_period),
            ("slow_period", slow_period),
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
            "supplied config disagrees with macd wrapper arguments",
            {"indicator_id": "macd"},
        )
    return config


def _ema_full(prices: np.ndarray, period: int) -> np.ndarray:
    """Calculate the internal SMA-seeded EMA primitive, ``nan`` warmup.

    Args:
        prices: The prices value.
        period: The period value.

    Returns:
        The np.ndarray result.

    Raises:
        None.
    """
    values = np.full(len(prices), np.nan, dtype="float64")
    if len(prices) >= period:
        alpha = 2.0 / (period + 1)
        previous = float(prices[:period].mean())
        values[period - 1] = previous
        for position in range(period, len(prices)):
            previous = prices[position] * alpha + previous * (1.0 - alpha)
            values[position] = previous
    return values


@guard_public_boundary
def macd(
    data: MarketDataset,
    *,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate MACD, signal, and histogram on close.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        fast_period: Required fast EMA period; defaults to 12.
        slow_period: Required slow EMA period; defaults to 26.
        signal_period: Required signal EMA period; defaults to 9.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic MACD ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating macd for %s (fast=%d, slow=%d, signal=%d)",
        data.symbol,
        fast_period,
        slow_period,
        signal_period,
    )
    if fast_period >= slow_period:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "fast_period must be strictly less than slow_period",
            {"indicator_id": "macd"},
        )
    resolved_config = _build_config(fast_period, slow_period, signal_period, config)
    _unwrap_indicator_response(validate_indicator("macd", data, resolved_config))
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")

    fast_ema = _ema_full(close, fast_period)
    slow_ema = _ema_full(close, slow_period)
    macd_line = fast_ema - slow_ema
    macd_valid = ~np.isnan(macd_line)

    row_count = len(records)
    signal_line = np.full(row_count, np.nan, dtype="float64")
    if macd_valid.any():
        first_valid = int(np.flatnonzero(macd_valid)[0])
        tail = macd_line[first_valid:]
        signal_tail = _ema_full(tail, signal_period)
        signal_line[first_valid:] = signal_tail

    histogram = macd_line - signal_line
    is_valid = ~np.isnan(signal_line)

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
        f"macd_{fast_period}_{slow_period}",
        f"macd_signal_{fast_period}_{slow_period}_{signal_period}",
        f"macd_histogram_{fast_period}_{slow_period}_{signal_period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, macd_line, np.nan),
            output_columns[1]: np.where(is_valid, signal_line, np.nan),
            output_columns[2]: np.where(is_valid, histogram, np.nan),
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


__all__ = ["macd"]
