"""Bollinger BandWidth calculator.

Implements spec ``IND-VOL-08``. Ownership of the bandwidth percentage
metric belongs to ``volatility/`` per the spec, distinct from
``trend.bollinger_bands`` which owns the raw band levels (left
untouched this phase). This file computes its own close-price SMA/sample
standard deviation bands internally rather than calling the sibling
``trend.bollinger_bands`` public function, per the package's
no-sibling-call convention.

``Middle_t = SMA_n(C)_t``
``Upper_t = Middle_t + k*std_n(C)_t``, ``Lower_t = Middle_t - k*std_n(C)_t``
``BBW_t = 100 * (Upper_t - Lower_t) / Middle_t``
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

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


def _build_config(
    period: int, std_dev: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable Bollinger BandWidth configuration.

    Args:
        period: Required rolling period.
        std_dev: Positive standard-deviation multiplier ``k``.
        config: Optional explicit configuration.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper arguments.
    """
    expected = IndicatorConfig(
        indicator_id="bollinger_bandwidth",
        parameters=(("period", period), ("std_dev", std_dev)),
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
            "supplied config disagrees with bollinger_bandwidth wrapper arguments",
            {"indicator_id": "bollinger_bandwidth"},
        )
    return config


def _rolling_available_at(
    records: tuple[OHLCVRecord, ...], index: pd.DatetimeIndex, period: int
) -> pd.Series:
    """Return the inclusive rolling maximum availability timestamp.

    Args:
            records: Validated OHLCV records.
            index: Canonical result index.
            period: Inclusive rolling window size.

    Returns:
            Row-aligned UTC availability timestamps.

    Raises:
        None.
    """
    nanos = pd.DatetimeIndex([record.available_at for record in records]).asi8
    result = nanos.copy()
    if len(records) >= period:
        result[period - 1 :] = sliding_window_view(nanos, period).max(axis=1)
    return pd.Series(pd.to_datetime(result, unit="us", utc=True), index=index)


@guard_public_boundary
def bollinger_bandwidth(
    data: MarketDataset,
    *,
    period: int,
    std_dev: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate close-price Bollinger BandWidth (percentage envelope width).

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required rolling period of at least two.
        std_dev: Positive standard-deviation multiplier ``k``.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic four-column Bollinger BandWidth ``IndicatorResult``
        carrying ``upper``, ``middle``, ``lower``, and ``bandwidth_percent``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating bollinger_bandwidth for %s (period=%d, std_dev=%s)",
        data.symbol,
        period,
        std_dev,
    )
    resolved_config = _build_config(period, std_dev, config)
    _unwrap_indicator_response(
        validate_indicator("bollinger_bandwidth", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = pd.Series(
        [float(record.close) for record in records], index=index, dtype="float64"
    )
    middle = close.rolling(window=period, min_periods=period).mean()
    deviation = close.rolling(window=period, min_periods=period).std(ddof=1)
    upper = middle + std_dev * deviation
    lower = middle - std_dev * deviation

    is_period_valid = np.arange(len(records)) >= period - 1
    middle_array = middle.to_numpy(dtype="float64")
    non_positive_middle = is_period_valid & ~(middle_array > 0.0)
    is_valid = is_period_valid & ~non_positive_middle

    bandwidth_percent = pd.Series(np.nan, index=index, dtype="float64")
    bandwidth_percent[is_valid] = (
        100.0 * (upper[is_valid] - lower[is_valid]) / middle[is_valid]
    )
    upper_masked = pd.Series(np.where(is_valid, upper.to_numpy(), np.nan), index=index)
    middle_masked = pd.Series(
        np.where(is_valid, middle.to_numpy(), np.nan), index=index
    )
    lower_masked = pd.Series(np.where(is_valid, lower.to_numpy(), np.nan), index=index)

    row_time = pd.Series(index, index=index)
    computed_from_start = row_time.shift(period - 1)
    computed_from_start[~is_valid] = pd.NaT
    computed_from_end = row_time.copy()
    computed_from_end[~is_valid] = pd.NaT
    available_at = pd.Series([record.available_at for record in records], index=index)
    rolling_available = _rolling_available_at(records, index, period)
    available_at[is_valid] = rolling_available[is_valid]
    unavailable_reason = pd.Series(pd.NA, index=index, dtype=object)
    unavailable_reason[~is_period_valid] = "warmup"
    unavailable_reason[non_positive_middle] = "non_positive_middle"

    output_columns = (
        f"bollinger_bandwidth_upper_{period}",
        f"bollinger_bandwidth_middle_{period}",
        f"bollinger_bandwidth_lower_{period}",
        f"bollinger_bandwidth_percent_{period}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: upper_masked,
            output_columns[1]: middle_masked,
            output_columns[2]: lower_masked,
            output_columns[3]: bandwidth_percent,
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


__all__ = ["bollinger_bandwidth"]
