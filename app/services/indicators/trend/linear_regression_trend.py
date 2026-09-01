# ruff: noqa: PLR0915
"""Linear-regression slope and trend-fit calculator.

Implements spec ``IND-TR-02``: canonical OLS slope/intercept/R2 over a
trailing window of ``price`` or ``log_price`` values.
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
_TRANSFORMS = ("price", "log_price")


def _build_config(
    period: int, transform: str, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable linear-regression-trend configuration.

    Args:
        period: The period value.
        transform: The transform value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="linear_regression_trend",
        parameters=(("period", period), ("transform", transform)),
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
            "supplied config disagrees with linear_regression_trend arguments",
            {"indicator_id": "linear_regression_trend"},
        )
    return config


@guard_public_boundary
def linear_regression_trend(
    data: MarketDataset,
    *,
    period: int,
    transform: str = "price",
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate OLS slope, intercept, R2, fitted end value, and direction.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required regression window of at least two.
        transform: Either ``"price"`` or ``"log_price"``.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic linear-regression-trend ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating linear_regression_trend for %s (period=%d, transform=%s)",
        data.symbol,
        period,
        transform,
    )
    if transform not in _TRANSFORMS:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "transform must be price or log_price",
            {"transform": str(transform)},
        )
    resolved_config = _build_config(period, transform, config)
    _unwrap_indicator_response(
        validate_indicator("linear_regression_trend", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    prices = np.log(close) if transform == "log_price" else close
    row_count = len(records)

    x_index = np.arange(period, dtype="float64")
    x_mean = x_index.mean()
    x_centered = x_index - x_mean
    x_var = float((x_centered**2).sum())

    is_valid = np.zeros(row_count, dtype=bool)
    slope_values = np.full(row_count, np.nan, dtype="float64")
    intercept_values = np.full(row_count, np.nan, dtype="float64")
    r_squared_values = np.full(row_count, np.nan, dtype="float64")
    fitted_end_values = np.full(row_count, np.nan, dtype="float64")
    direction = np.full(row_count, np.nan, dtype="float64")

    for position in range(period - 1, row_count):
        window = prices[position - period + 1 : position + 1]
        y_mean = float(window.mean())
        y_centered = window - y_mean
        if x_var == 0.0:
            continue
        beta = float((x_centered * y_centered).sum() / x_var)
        alpha = y_mean - beta * x_mean
        fitted = alpha + beta * x_index
        residual_sum = float(((window - fitted) ** 2).sum())
        total_sum = float((y_centered**2).sum())
        if total_sum == 0.0:
            continue
        r_squared = 1.0 - residual_sum / total_sum
        slope_values[position] = beta
        intercept_values[position] = alpha
        r_squared_values[position] = r_squared
        fitted_end_values[position] = alpha + beta * (period - 1)
        direction[position] = float(np.sign(beta))
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
        f"linear_regression_slope_{period}_{transform}",
        f"linear_regression_intercept_{period}_{transform}",
        f"linear_regression_r_squared_{period}_{transform}",
        f"linear_regression_fitted_end_{period}_{transform}",
        f"linear_regression_direction_{period}_{transform}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: slope_values,
            output_columns[1]: intercept_values,
            output_columns[2]: r_squared_values,
            output_columns[3]: fitted_end_values,
            output_columns[4]: direction,
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


__all__ = ["linear_regression_trend"]
