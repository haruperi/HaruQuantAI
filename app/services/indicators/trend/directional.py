"""ADX — approved Average Directional Index calculator.

Computes the official ADX, +DI, and -DI trio through a stateless batch
function. Validates the whole request through Core before touching any
formula, and assembles its result through the shared Core result builder
so identity, checksum, and finalization logic is never duplicated here.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd

from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.core.results import build_indicator_result
from app.services.indicators.core.validation import validate_indicator
from app.utils import logger

if TYPE_CHECKING:
    from app.services.data.contracts import MarketDataset, OHLCVRecord
    from app.services.indicators.core.results import IndicatorResult

_FORMULA_VERSION = "1.0.0"
_INDICATOR_VERSION = "1.0.0"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _build_config(period: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the complete immutable config for one ``adx`` call.

    Public wrappers own convenience arguments and construct the complete
    config before validation. If an explicitly supplied config disagrees
    with the wrapper's own period or formula version, the call fails
    closed with no silent override.

    Args:
        period: The wrapper's convenience period argument.
        config: An optional explicitly supplied calculation configuration.

    Returns:
        The complete immutable ``IndicatorConfig`` to validate and use.

    Raises:
        IndicatorError: ``IND_INVALID_CONFIG`` if a supplied config
            disagrees with ``indicator_id``, ``period``, or the approved
            formula version.
    """
    logger.debug("Building config for adx (period=%s)", period)
    expected = IndicatorConfig(
        indicator_id="adx",
        parameters=(("period", period),),
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
        config.indicator_id != "adx"
        or config.parameters != expected.parameters
        or config.source is not None
        or config.formula_version != _FORMULA_VERSION
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "supplied config disagrees with wrapper indicator_id, period, "
            "source, or formula_version",
            {"indicator_id": "adx"},
        )
    return config


def _timestamps_and_available(
    data: MarketDataset,
) -> tuple[pd.DatetimeIndex, list[datetime], list[datetime]]:
    """Project one dataset's row timestamps and availability timestamps.

    Args:
        data: One normalized, validated ``MarketDataset v1``.

    Returns:
        A UTC ``DatetimeIndex`` plus parallel lists of row timestamps and
        row ``available_at`` timestamps, all in dataset row order.
    """
    logger.debug("Projecting timestamps and availability for %s", data.symbol)
    timestamps = [record.timestamp for record in data.records]
    available_ats = [record.available_at for record in data.records]
    index = pd.DatetimeIndex(timestamps, name="timestamp", tz="UTC")
    return index, timestamps, available_ats


def _epoch_micros(available_ats: list[datetime]) -> np.ndarray:
    """Convert row ``available_at`` timestamps to exact epoch microseconds.

    Uses exact integer ``timedelta`` division so no floating-point epoch
    conversion can lose precision.

    Args:
        available_ats: Row-ordered ``available_at`` timestamps.

    Returns:
        An ``int64`` array of exact epoch-microsecond values.
    """
    logger.debug(
        "Converting %d available_at timestamps to epoch micros", len(available_ats)
    )
    return np.array(
        [(moment - _EPOCH) // timedelta(microseconds=1) for moment in available_ats],
        dtype="int64",
    )


def _cumulative_max_available_at(
    available_ats: list[datetime], index: pd.DatetimeIndex
) -> pd.Series:
    """Compute the cumulative maximum ``available_at`` up to each row.

    Args:
        available_ats: Row-ordered ``available_at`` timestamps.
        index: The result's UTC row index.

    Returns:
        A UTC datetime64 Series of the running maximum ``available_at``.
    """
    logger.debug(
        "Computing cumulative max available_at over %d rows", len(available_ats)
    )
    micros = _epoch_micros(available_ats)
    cumulative = np.maximum.accumulate(micros)
    return pd.Series(pd.to_datetime(cumulative, unit="us", utc=True), index=index)


def _true_range_and_directional_moves(
    high: np.ndarray, low: np.ndarray, close: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorize the per-row true range and directional movement arrays.

    Observation 1 has true range ``high-low`` with no directional move.
    Later rows use the standard true-range and +DM/-DM conventions.

    Args:
        high: Row-ordered high prices.
        low: Row-ordered low prices.
        close: Row-ordered close prices.

    Returns:
        Parallel ``(true_range, plus_dm, minus_dm)`` arrays.
    """
    logger.debug("Computing true range and directional moves over %d rows", len(high))
    row_count = len(high)
    previous_close = np.full(row_count, np.nan, dtype="float64")
    previous_close[1:] = close[:-1]
    range_high_low = high - low
    range_high_prior_close = np.abs(high - previous_close)
    range_low_prior_close = np.abs(low - previous_close)
    stacked_ranges = np.vstack(
        [range_high_low, range_high_prior_close, range_low_prior_close]
    )
    true_range = np.nanmax(stacked_ranges, axis=0)

    up_move = np.zeros(row_count, dtype="float64")
    down_move = np.zeros(row_count, dtype="float64")
    up_move[1:] = high[1:] - high[:-1]
    down_move[1:] = low[:-1] - low[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    return true_range, plus_dm, minus_dm


def _wilder_adx(
    true_range: np.ndarray, plus_dm: np.ndarray, minus_dm: np.ndarray, period: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute Wilder-smoothed +DI, -DI, DX, and ADX arrays.

    Wilder smoothing and the DX/ADX chain are recursive, mathematically
    stateful dependencies that cannot be vectorized safely; this function
    is that documented exception (NFR-INDI-005).

    Args:
        true_range: Per-row true range.
        plus_dm: Per-row +DM.
        minus_dm: Per-row -DM.
        period: The approved smoothing period.

    Returns:
        Parallel ``(plus_di, minus_di, adx_values, is_valid)`` arrays,
        where ``is_valid`` marks rows at or after observation
        ``2 * period``.
    """
    logger.debug(
        "Computing Wilder ADX chain over %d rows (period=%d)", len(true_range), period
    )
    row_count = len(true_range)
    plus_di = np.full(row_count, np.nan, dtype="float64")
    minus_di = np.full(row_count, np.nan, dtype="float64")
    dx = np.full(row_count, np.nan, dtype="float64")
    adx_values = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)

    if row_count < 2 * period:
        return plus_di, minus_di, adx_values, is_valid

    smoothed_tr = float(true_range[1 : period + 1].sum())
    smoothed_plus_dm = float(plus_dm[1 : period + 1].sum())
    smoothed_minus_dm = float(minus_dm[1 : period + 1].sum())
    for position in range(period, row_count):
        if position > period:
            smoothed_tr = smoothed_tr - smoothed_tr / period + true_range[position]
            smoothed_plus_dm = (
                smoothed_plus_dm - smoothed_plus_dm / period + plus_dm[position]
            )
            smoothed_minus_dm = (
                smoothed_minus_dm - smoothed_minus_dm / period + minus_dm[position]
            )
        if smoothed_tr != 0:
            plus_di[position] = 100.0 * smoothed_plus_dm / smoothed_tr
            minus_di[position] = 100.0 * smoothed_minus_dm / smoothed_tr
        else:
            plus_di[position] = 0.0
            minus_di[position] = 0.0
        di_sum = plus_di[position] + minus_di[position]
        dx[position] = (
            100.0 * abs(plus_di[position] - minus_di[position]) / di_sum
            if di_sum != 0
            else 0.0
        )

    adx_values[2 * period - 1] = float(dx[period : 2 * period].mean())
    for position in range(2 * period, row_count):
        adx_values[position] = (
            adx_values[position - 1] * (period - 1) + dx[position]
        ) / period
    is_valid[2 * period - 1 :] = True
    return plus_di, minus_di, adx_values, is_valid


def adx(
    data: MarketDataset,
    *,
    period: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate ADX, +DI, and -DI for one validated dataset.

    Uses the standard true-range and Wilder-smoothed directional movement
    conventions. Observation 1 has true range ``high-low``; the first
    smoothed TR/+DM/-DM values use observations 2 through ``period+1``;
    the first ADX is the arithmetic mean of the first ``period`` DX values
    and is emitted on observation ``2*period``. Zero true range produces
    zero directional values.

    Args:
        data: One normalized, immutable ``MarketDataset v1``.
        period: Required smoothing period; must be an integer of at least
            two.
        config: An optional explicitly supplied calculation configuration;
            it must agree with ``period`` and the approved formula
            version.

    Returns:
        The deterministic ``IndicatorResult`` carrying ``adx_{period}``,
        ``plus_di_{period}``, and ``minus_di_{period}``.

    Raises:
        IndicatorError: On validation, formula-version, resource-limit, or
            atomic calculation failure.
    """
    logger.info("Calculating adx for %s (period=%d)", data.symbol, period)
    resolved_config = _build_config(period, config)
    validate_indicator("adx", data, resolved_config)
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index, timestamps, available_ats = _timestamps_and_available(data)
    high = np.array([float(record.high) for record in records], dtype="float64")
    low = np.array([float(record.low) for record in records], dtype="float64")
    close = np.array([float(record.close) for record in records], dtype="float64")

    true_range, plus_dm, minus_dm = _true_range_and_directional_moves(high, low, close)
    plus_di, minus_di, adx_values, is_valid = _wilder_adx(
        true_range, plus_dm, minus_dm, period
    )

    computed_from_start = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    computed_from_end = pd.Series(pd.NaT, index=index, dtype="datetime64[ns, UTC]")
    computed_from_start[is_valid] = timestamps[0]
    computed_from_end[is_valid] = index[is_valid]
    available_at = pd.Series(available_ats, index=index)
    cumulative_available = _cumulative_max_available_at(available_ats, index)
    available_at[is_valid] = cumulative_available[is_valid]
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_valid] = "warmup"

    output_columns = (
        f"adx_{period}",
        f"plus_di_{period}",
        f"minus_di_{period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, adx_values, np.nan),
            output_columns[1]: np.where(is_valid, plus_di, np.nan),
            output_columns[2]: np.where(is_valid, minus_di, np.nan),
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


__all__ = ["adx"]
