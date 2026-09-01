# ruff: noqa: PD011
"""EMA and ATR-normalized EMA slope calculator.

Implements spec ``IND-TR-01``: ``EMA_t = alpha*P_t + (1-alpha)*EMA_{t-1}``,
``alpha = 2/(n+1)``, and ``Slope^ATR_{t,k} = (EMA_t - EMA_{t-k}) / (k*ATR_t)``.

Computes its own internal EMA primitive rather than calling the sibling
``trend.ema`` public wrapper, per the package's no-sibling-call convention.
The normalized slope explicitly consumes the canonical ``volatility.atr``
public wrapper (the one approved cross-module dependency for this
indicator) rather than recomputing ATR.
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
from app.services.indicators.volatility.atr import atr as _atr

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
    period: int, lag: int, atr_period: int, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable EMA-slope configuration.

    Args:
        period: The period value.
        lag: The lag value.
        atr_period: The atr period value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="ema_slope",
        parameters=(
            ("atr_period", atr_period),
            ("lag", lag),
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
            "supplied config disagrees with ema_slope wrapper arguments",
            {"indicator_id": "ema_slope"},
        )
    return config


def _ema(prices: np.ndarray, period: int) -> np.ndarray:
    """Calculate the internal SMA-seeded EMA primitive.

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
def ema_slope(
    data: MarketDataset,
    *,
    period: int,
    lag: int,
    atr_period: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate EMA, raw slope, ATR-normalized slope, and direction.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required EMA smoothing period of at least two.
        lag: Required slope lag ``k`` of at least one.
        atr_period: Required smoothing period fed to the canonical ATR.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic EMA-slope ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating ema_slope for %s (period=%d, lag=%d, atr_period=%d)",
        data.symbol,
        period,
        lag,
        atr_period,
    )
    resolved_config = _build_config(period, lag, atr_period, config)
    _unwrap_indicator_response(validate_indicator("ema_slope", data, resolved_config))
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    ema_values = _ema(close, period)

    atr_result: IndicatorResult = _unwrap_indicator_response(
        _atr(data, period=atr_period)
    )
    atr_column = f"atr_{atr_period}"
    atr_values = atr_result.values[atr_column].to_numpy(dtype="float64")

    row_count = len(records)
    is_valid = np.zeros(row_count, dtype=bool)
    raw_slope = np.full(row_count, np.nan, dtype="float64")
    normalized_slope = np.full(row_count, np.nan, dtype="float64")
    direction = np.full(row_count, np.nan, dtype="float64")

    for position in range(row_count):
        if position < period - 1 or position < lag:
            continue
        prior = position - lag
        if prior < period - 1:
            continue
        atr_value = atr_values[position]
        if not np.isfinite(atr_value) or atr_value == 0.0:
            continue
        slope = (ema_values[position] - ema_values[prior]) / lag
        raw_slope[position] = slope
        normalized_slope[position] = slope / (lag * atr_value)
        direction[position] = float(np.sign(slope))
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
        f"ema_slope_ema_{period}",
        f"ema_slope_raw_{period}_{lag}",
        f"ema_slope_normalized_{period}_{lag}_{atr_period}",
        f"ema_slope_direction_{period}_{lag}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, ema_values, np.nan),
            output_columns[1]: raw_slope,
            output_columns[2]: normalized_slope,
            output_columns[3]: direction,
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


__all__ = ["ema_slope"]
