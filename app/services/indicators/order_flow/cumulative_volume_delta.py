"""Cumulative volume delta calculator (OHLCV close/open sign proxy).

Implements a documented OHLCV-derived approximation of spec ``IND-OF-03``.
The canonical formula requires trades with a verified aggressor sign
(``epsilon_t in {-1, +1}``), which the current ``MarketDataset``/
``OHLCVRecord`` contract (see ``core/contracts.py``) does not carry — there
is no trade-level bid/ask-initiator field, only bar OHLCV. Per the session
plan's explicit guidance, this file implements the documented bar-sign
proxy convention (``epsilon_t = sign(close_t - open_t)``, ties assigned to
the sell side) rather than fabricating a verified aggressor stream. This
is NOT the canonical formula and must not be presented as tick-verified
CVD; it is a coarse per-bar directional-volume accumulator.
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


def _build_config(window: int, config: IndicatorConfig | None) -> IndicatorConfig:
    """Build or validate the immutable CVD configuration.

    Args:
        window: The window value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="cumulative_volume_delta",
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
            "supplied config disagrees with cumulative_volume_delta arguments",
            {"indicator_id": "cumulative_volume_delta"},
        )
    return config


@guard_public_boundary
def cumulative_volume_delta(
    data: MarketDataset,
    *,
    window: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate cumulative and rolling-window bar-sign volume delta.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        window: Required rolling window of at least one bar.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic CVD ``IndicatorResult`` (bar-sign proxy; see the
        module docstring for the exact approximation used).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating cumulative_volume_delta for %s (window=%d)",
        data.symbol,
        window,
    )
    resolved_config = _build_config(window, config)
    _unwrap_indicator_response(
        validate_indicator("cumulative_volume_delta", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    open_price = np.asarray([float(record.open) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    volume = np.asarray([float(record.volume) for record in records], dtype="float64")
    row_count = len(records)

    sign = np.where(close >= open_price, 1.0, -1.0)
    delta = sign * volume
    buy_volume = np.where(sign > 0, volume, 0.0)
    sell_volume = np.where(sign < 0, volume, 0.0)
    cvd = np.cumsum(delta)

    rolling_delta = (
        pd.Series(delta, index=index)
        .rolling(window=window, min_periods=window)
        .sum()
        .to_numpy(dtype="float64")
    )

    is_valid = np.zeros(row_count, dtype=bool)
    is_valid[window - 1 :] = True

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
        f"cvd_{window}",
        f"cvd_rolling_delta_{window}",
        f"cvd_buy_volume_{window}",
        f"cvd_sell_volume_{window}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, cvd, np.nan),
            output_columns[1]: np.where(is_valid, rolling_delta, np.nan),
            output_columns[2]: np.where(is_valid, buy_volume, np.nan),
            output_columns[3]: np.where(is_valid, sell_volume, np.nan),
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


__all__ = ["cumulative_volume_delta"]
