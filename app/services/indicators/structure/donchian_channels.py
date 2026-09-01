"""Donchian channel level calculator.

Implements spec ``IND-ST-02``: ``upper=max(H[t-n+1:t])``,
``lower=min(L[t-n+1:t])``, ``middle=(upper+lower)/2``, over a declared
``include_current`` window mode.
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
    period: int, include_current: int, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable Donchian-channels configuration.

    Args:
        period: The period value.
        include_current: The include current value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="donchian_channels",
        parameters=(("include_current", include_current), ("period", period)),
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
            "supplied config disagrees with donchian_channels wrapper arguments",
            {"indicator_id": "donchian_channels"},
        )
    return config


@guard_public_boundary
def donchian_channels(
    data: MarketDataset,
    *,
    period: int,
    include_current: bool = True,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate the Donchian channel upper, lower, and middle bounds.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required window length ``n`` of at least two.
        include_current: Whether the current bar's high/low is part of the
            window; ``False`` uses only the prior ``n`` bars, which is the
            required mode for self-reference-free breakout testing.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic Donchian-channels ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating donchian_channels for %s (period=%d, include_current=%s)",
        data.symbol,
        period,
        include_current,
    )
    resolved_config = _build_config(period, int(include_current), config)
    _unwrap_indicator_response(
        validate_indicator("donchian_channels", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = pd.Series(
        [float(record.high) for record in records], index=index, dtype="float64"
    )
    low = pd.Series(
        [float(record.low) for record in records], index=index, dtype="float64"
    )
    row_count = len(records)

    if include_current:
        rolling_high = high.rolling(window=period, min_periods=period).max()
        rolling_low = low.rolling(window=period, min_periods=period).min()
        is_valid = np.zeros(row_count, dtype=bool)
        is_valid[period - 1 :] = True
    else:
        rolling_high = high.shift(1).rolling(window=period, min_periods=period).max()
        rolling_low = low.shift(1).rolling(window=period, min_periods=period).min()
        is_valid = np.zeros(row_count, dtype=bool)
        is_valid[period:] = True

    upper = rolling_high.to_numpy(dtype="float64")
    lower = rolling_low.to_numpy(dtype="float64")
    middle = (upper + lower) / 2.0

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
        f"donchian_upper_{period}",
        f"donchian_lower_{period}",
        f"donchian_middle_{period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, upper, np.nan),
            output_columns[1]: np.where(is_valid, lower, np.nan),
            output_columns[2]: np.where(is_valid, middle, np.nan),
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


__all__ = ["donchian_channels"]
