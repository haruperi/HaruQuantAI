"""Market-event arrival rate calculator (bar-arrival proxy).

Implements a documented OHLCV-bar-arrival approximation of spec
``IND-MS-04``. The canonical formula counts sequenced trades, ticks, or
order-book events with event-level timestamps; the current
``MarketDataset``/``OHLCVRecord`` contract carries no event stream, only
closed bars. Per the same judgment rule already applied to
``order_flow.cumulative_volume_delta``, this file treats each closed bar as
one coarse "event" and counts bar arrivals within a trailing wall-clock
window. This is NOT a tick/event-level arrival rate and must not be
presented as measured market micro-activity; it degrades to a
near-constant rate whenever bars are evenly spaced.
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
    window_seconds: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable event-arrival-rate configuration.

    Args:
        window_seconds: The window seconds value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="market_event_arrival_rate",
        parameters=(("window_seconds", window_seconds),),
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
            "supplied config disagrees with market_event_arrival_rate arguments",
            {"indicator_id": "market_event_arrival_rate"},
        )
    return config


@guard_public_boundary
def market_event_arrival_rate(
    data: MarketDataset,
    *,
    window_seconds: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate the bar-arrival-proxy market event rate.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        window_seconds: Required positive rolling wall-clock duration.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic bar-arrival-rate ``IndicatorResult`` (proxy; see
        the module docstring for the exact approximation used).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating market_event_arrival_rate for %s (window_seconds=%s)",
        data.symbol,
        window_seconds,
    )
    resolved_config = _build_config(window_seconds, config)
    _unwrap_indicator_response(
        validate_indicator("market_event_arrival_rate", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    row_count = len(records)
    epoch_seconds = np.array(
        [ts.timestamp() for ts in [record.timestamp for record in records]],
        dtype="float64",
    )

    counts = np.zeros(row_count, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    left = 0
    for position in range(row_count):
        while epoch_seconds[position] - epoch_seconds[left] > window_seconds:
            left += 1
        counts[position] = float(position - left + 1)
        elapsed_covered = epoch_seconds[position] - epoch_seconds[left]
        is_valid[position] = elapsed_covered >= window_seconds

    events_per_second = np.where(is_valid, counts / window_seconds, np.nan)

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

    output_column = "events_per_second"
    return build_indicator_result(
        data=data,
        config=resolved_config,
        indicator_version=_INDICATOR_VERSION,
        output_columns=(output_column,),
        output_values=pd.DataFrame({output_column: events_per_second}, index=index),
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


__all__ = ["market_event_arrival_rate"]
