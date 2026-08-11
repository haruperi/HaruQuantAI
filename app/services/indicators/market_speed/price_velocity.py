"""Log-price velocity calculator."""

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


def _build_config(
    k: int, unit_seconds: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable price-velocity configuration.

    Args:
        k: The k value.
        unit_seconds: The unit seconds value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="price_velocity",
        parameters=(("k", k), ("unit_seconds", unit_seconds)),
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
            "supplied config disagrees with price_velocity wrapper arguments",
            {"indicator_id": "price_velocity"},
        )
    return config


@guard_public_boundary
def price_velocity(
    data: MarketDataset,
    *,
    k: int,
    unit_seconds: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate spec ``IND-MS-01`` log-price velocity per time unit.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        k: Required lag of at least one bar.
        unit_seconds: Required positive output time-unit denominator, in
            seconds (for example ``60.0`` publishes velocity per minute).
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic price-velocity ``IndicatorResult`` carrying
        ``price_velocity_{k}_{unit_seconds}`` and its signed
        ``price_velocity_direction_{k}_{unit_seconds}``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating price_velocity for %s (k=%d, unit_seconds=%s)",
        data.symbol,
        k,
        unit_seconds,
    )
    resolved_config = _build_config(k, unit_seconds, config)
    _unwrap_indicator_response(
        validate_indicator("price_velocity", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    if (close <= 0).any():
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_OHLC,
            "price_velocity requires strictly positive close prices",
            {"indicator_id": "price_velocity"},
        )
    row_count = len(records)
    epoch_seconds = np.array(
        [ts.timestamp() for ts in [record.timestamp for record in records]],
        dtype="float64",
    )

    velocity = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    if row_count > k:
        elapsed = (epoch_seconds[k:] - epoch_seconds[:-k]) / unit_seconds
        log_return = np.log(close[k:]) - np.log(close[:-k])
        safe_elapsed = np.where(elapsed > 0.0, elapsed, np.nan)
        computed = log_return / safe_elapsed
        velocity[k:] = computed
        is_valid[k:] = np.isfinite(computed)

    direction = np.where(is_valid, np.sign(velocity), np.nan)

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
        f"price_velocity_{k}",
        f"price_velocity_direction_{k}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, velocity, np.nan),
            output_columns[1]: np.where(is_valid, direction, np.nan),
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


__all__ = ["price_velocity"]
