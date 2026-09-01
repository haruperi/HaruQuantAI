"""Aggressive trade imbalance calculator (OHLCV close/open sign proxy).

Implements a documented OHLCV-derived approximation of spec ``IND-OF-04``.
The canonical formula requires buyer-initiated/seller-initiated trade
volume, which the current ``MarketDataset``/``OHLCVRecord`` contract does
not carry (no trade-level aggressor field). This file uses the same
bar-sign volume proxy as ``order_flow.cumulative_volume_delta``
(``epsilon_t = sign(close_t - open_t)``) to approximate buy/sell volume
per bar over a trailing window. This is NOT the canonical trade-level
formula and must not be presented as verified aggressor-side imbalance.
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
    """Build or validate the immutable ATI configuration.

    Args:
        window: The window value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="aggressive_trade_imbalance",
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
            "supplied config disagrees with aggressive_trade_imbalance arguments",
            {"indicator_id": "aggressive_trade_imbalance"},
        )
    return config


@guard_public_boundary
def aggressive_trade_imbalance(
    data: MarketDataset,
    *,
    window: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate the trailing-window bar-sign aggressive trade imbalance.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        window: Required rolling window of at least one bar.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic ATI ``IndicatorResult`` (bar-sign proxy; see the
        module docstring for the exact approximation used).

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating aggressive_trade_imbalance for %s (window=%d)",
        data.symbol,
        window,
    )
    resolved_config = _build_config(window, config)
    _unwrap_indicator_response(
        validate_indicator("aggressive_trade_imbalance", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    open_price = np.asarray([float(record.open) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    volume = np.asarray([float(record.volume) for record in records], dtype="float64")
    row_count = len(records)

    buy_volume = np.where(close >= open_price, volume, 0.0)
    sell_volume = np.where(close < open_price, volume, 0.0)

    rolling_buy = (
        pd.Series(buy_volume, index=index)
        .rolling(window=window, min_periods=window)
        .sum()
        .to_numpy(dtype="float64")
    )
    rolling_sell = (
        pd.Series(sell_volume, index=index)
        .rolling(window=window, min_periods=window)
        .sum()
        .to_numpy(dtype="float64")
    )

    is_valid = np.zeros(row_count, dtype=bool)
    total = rolling_buy + rolling_sell
    candidate_valid = np.zeros(row_count, dtype=bool)
    candidate_valid[window - 1 :] = True
    is_valid = candidate_valid & (total > 0.0)

    ati = np.full(row_count, np.nan, dtype="float64")
    ati[is_valid] = (rolling_buy[is_valid] - rolling_sell[is_valid]) / total[is_valid]

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
        f"aggressive_trade_imbalance_{window}",
        f"aggressive_trade_imbalance_buy_volume_{window}",
        f"aggressive_trade_imbalance_sell_volume_{window}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: ati,
            output_columns[1]: np.where(is_valid, rolling_buy, np.nan),
            output_columns[2]: np.where(is_valid, rolling_sell, np.nan),
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


__all__ = ["aggressive_trade_imbalance"]
