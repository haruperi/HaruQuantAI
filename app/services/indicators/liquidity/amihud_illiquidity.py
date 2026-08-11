"""Amihud illiquidity calculator (OHLCV notional-volume proxy).

Implements spec ``IND-LQ-05``: ``ILLIQ_D = mean(|R_d| / DV_d)`` over a
trailing window of ``D`` intervals, where ``R_d`` is the interval simple
return and ``DV_d`` is the interval dollar/notional volume. The canonical
formula accepts any Data-declared notional-volume source; this domain uses
``close * volume`` as its notional-volume proxy because the current
``MarketDataset``/``OHLCVRecord`` contract carries no separate notional
field. Intervals whose notional volume is exactly zero are excluded from
the window average per the spec's explicit missing-data rule rather than
producing a division error; a window with no admissible interval is
warmup/unavailable, never zero.
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


def _build_config(window: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable Amihud-illiquidity configuration.

    Args:
        window: The window value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="amihud_illiquidity",
        parameters=(("window", window),),
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
            "supplied config disagrees with amihud_illiquidity wrapper arguments",
            {"indicator_id": "amihud_illiquidity"},
        )
    return config


@guard_public_boundary
def amihud_illiquidity(
    data: MarketDataset,
    *,
    window: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate trailing-window Amihud illiquidity from OHLCV notional volume.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        window: Required interval-count window of at least one.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Amihud-illiquidity ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating amihud_illiquidity for %s (window=%d)", data.symbol, window
    )
    resolved_config = _build_config(window, config)
    _unwrap_indicator_response(
        validate_indicator("amihud_illiquidity", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    volume = np.asarray([float(record.volume) for record in records], dtype="float64")
    if (close <= 0).any():
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_OHLC,
            "amihud_illiquidity requires strictly positive close prices",
            {"indicator_id": "amihud_illiquidity"},
        )
    row_count = len(records)

    ret = np.full(row_count, np.nan, dtype="float64")
    ret[1:] = (close[1:] - close[:-1]) / close[:-1]
    notional = close * volume
    illiq_term = np.where(
        notional > 0.0, np.abs(ret) / np.maximum(notional, 1e-300), np.nan
    )
    illiq_term[0] = np.nan

    illiq_series = pd.Series(illiq_term, index=index)
    rolling_mean = illiq_series.rolling(window=window, min_periods=1).mean()
    admissible_count = illiq_series.notna().rolling(window=window, min_periods=1).sum()

    is_valid = np.zeros(row_count, dtype=bool)
    candidate = np.arange(row_count) >= window
    is_valid[candidate] = admissible_count.to_numpy()[candidate] > 0

    values = np.where(is_valid, rolling_mean.to_numpy(dtype="float64"), np.nan)

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

    output_column = f"amihud_illiquidity_{window}"
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


__all__ = ["amihud_illiquidity"]
