"""Rolling volatility — approved return-based volatility calculator.

Computes the official annualized rolling log-return volatility through a
stateless, fully vectorized batch function. Validates the whole request
through Core before touching any formula, and assembles its result
through the shared Core result builder so identity, checksum, and
finalization logic is never duplicated here.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
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
_INDICATOR_VERSION = "1.1.0"
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_DEFAULT_ANNUALIZATION_FACTOR = 252.0
_SAMPLE_DDOF = 1


def _build_config(
    period: int,
    source: str,
    annualization_factor: float,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the complete immutable config for one wrapper call.

    Public wrappers own convenience arguments and construct the complete
    config before validation. If an explicitly supplied config disagrees
    with the wrapper's own period, source, annualization factor, or formula
    version, the call fails closed with no silent override.

    Args:
        period: The wrapper's convenience period argument.
        source: The wrapper's convenience source argument.
        annualization_factor: The declared annualization factor ``A``.
        config: An optional explicitly supplied calculation configuration.

    Returns:
        The complete immutable ``IndicatorConfig`` to validate and use.

    Raises:
        IndicatorError: ``IND_INVALID_CONFIG`` if a supplied config
            disagrees with ``indicator_id``, ``period``, ``source``,
            ``annualization_factor``, or the approved formula version.
    """
    expected = IndicatorConfig(
        indicator_id="rolling_volatility",
        parameters=(
            ("annualization_factor", annualization_factor),
            ("period", period),
        ),
        source=source,
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
        config.indicator_id != "rolling_volatility"
        or config.parameters != expected.parameters
        or config.source != source
        or config.formula_version != _FORMULA_VERSION
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "supplied config disagrees with wrapper indicator_id, period, "
            "source, annualization_factor, or formula_version",
            {"indicator_id": "rolling_volatility"},
        )
    return config


def _resolve_output_column(source: str, period: int) -> str:
    """Resolve the deterministic source-qualified output column name.

    Args:
            source: Selected price source.
            period: Validated formula period.

    Returns:
            ``rolling_volatility_{period}`` when ``source`` is ``close``, else
            ``rolling_volatility_{source}_{period}``.

    Raises:
        None.
    """
    if source == "close":
        return f"rolling_volatility_{period}"
    return f"rolling_volatility_{source}_{period}"


def _timestamps_and_available(
    data: MarketDataset,
) -> tuple[pd.DatetimeIndex, list[datetime], list[datetime]]:
    """Project one dataset's row timestamps and availability timestamps.

    Args:
            data: One normalized, validated ``MarketDataset v1``.

    Returns:
            A UTC ``DatetimeIndex`` plus parallel lists of row timestamps and
            row ``available_at`` timestamps, all in dataset row order.

    Raises:
        None.
    """
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

    Raises:
        None.
    """
    return np.array(
        [(moment - _EPOCH) // timedelta(microseconds=1) for moment in available_ats],
        dtype="int64",
    )


def _rolling_max_available_at(
    available_ats: list[datetime], index: pd.DatetimeIndex, window: int
) -> pd.Series:
    """Compute the inclusive rolling maximum ``available_at`` per row.

        Rows before the window fills carry each row's own ``available_at`` as
        a harmless placeholder; callers only read this result at valid
        (non-warmup) row positions.

    Args:
            available_ats: Row-ordered ``available_at`` timestamps.
            index: The result's UTC row index.
            window: Inclusive rolling window size, in price observations.

    Returns:
            A UTC datetime64 Series of the rolling maximum ``available_at``.

    Raises:
        None.
    """
    micros = _epoch_micros(available_ats)
    result = micros.copy()
    if len(micros) >= window:
        windows = sliding_window_view(micros, window_shape=window)
        result[window - 1 :] = windows.max(axis=1)
    return pd.Series(pd.to_datetime(result, unit="us", utc=True), index=index)


def _rolling_log_return_volatility(
    prices: np.ndarray, period: int, annualization_factor: float
) -> tuple[np.ndarray, np.ndarray]:
    """Compute annualized sample-stdev rolling log-return volatility.

    Args:
            prices: Row-ordered selected source prices.
            period: The approved number of consecutive log returns.
            annualization_factor: The declared annualization factor ``A``; a
                profile-declared parameter, never a hardcoded constant.

    Returns:
            A ``(values, is_valid)`` pair where ``is_valid`` marks rows at or
            after observation ``period + 1``.

    Raises:
        None.
    """
    row_count = len(prices)
    values = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    if row_count < period + 1:
        return values, is_valid

    log_returns = np.diff(np.log(prices))
    windows = sliding_window_view(log_returns, window_shape=period)
    stds = windows.std(axis=1, ddof=_SAMPLE_DDOF)
    values[period:] = stds * math.sqrt(annualization_factor)
    is_valid[period:] = True
    return values, is_valid


@guard_public_boundary
def rolling_volatility(
    data: MarketDataset,
    *,
    period: int,
    source: str = "close",
    annualization_factor: float = _DEFAULT_ANNUALIZATION_FACTOR,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate rolling volatility for one validated dataset.

    Uses ``period`` consecutive log returns (``period + 1`` prices),
    sample standard deviation (``ddof=1``), and annualization by
    ``sqrt(annualization_factor)``. Constant prices produce zero volatility.

    Args:
        data: One normalized, immutable ``MarketDataset v1``.
        period: Required number of consecutive log returns; must be an
            integer of at least two.
        source: Selected price source among ``open``, ``high``, ``low``,
            or ``close``.
        annualization_factor: The declared annualization factor ``A``;
            defaults to 252 trading days but is a profile parameter, never
            a hardcoded constant.
        config: An optional explicitly supplied calculation configuration;
            it must agree with ``period``, ``source``,
            ``annualization_factor``, and the approved formula version.

    Returns:
        The deterministic ``IndicatorResult`` carrying
        ``rolling_volatility_{period}`` or the exact source-qualified
        output column.

    Raises:
        IndicatorError: On validation, formula-version, resource-limit, or
            atomic calculation failure.
    """
    logger.info(
        "Calculating rolling_volatility for %s (period=%d, source=%s, A=%s)",
        data.symbol,
        period,
        source,
        annualization_factor,
    )
    resolved_config = _build_config(period, source, annualization_factor, config)
    _unwrap_indicator_response(
        validate_indicator("rolling_volatility", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index, _timestamps, available_ats = _timestamps_and_available(data)
    prices = np.array(
        [float(getattr(record, source)) for record in records], dtype="float64"
    )
    resolved_annualization_factor = float(
        dict(resolved_config.parameters)["annualization_factor"]
    )

    values, is_valid = _rolling_log_return_volatility(
        prices, period, resolved_annualization_factor
    )

    raw_row_time = pd.Series(index, index=index)
    computed_from_start = raw_row_time.shift(period)
    computed_from_start[~is_valid] = pd.NaT
    computed_from_end = raw_row_time.copy()
    computed_from_end[~is_valid] = pd.NaT
    available_at = pd.Series(available_ats, index=index)
    rolling_available = _rolling_max_available_at(available_ats, index, period + 1)
    available_at[is_valid] = rolling_available[is_valid]
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_valid] = "warmup"

    output_column = _resolve_output_column(source, period)
    output_values = pd.DataFrame({output_column: values}, index=index)

    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=(output_column,),
        output_values=output_values,
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["rolling_volatility"]
