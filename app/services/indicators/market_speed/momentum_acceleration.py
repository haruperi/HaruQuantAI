# ruff: noqa: PD011
"""Momentum acceleration calculator.

Implements spec ``IND-MS-02`` as the discrete second difference of the
canonical ``market_speed.price_velocity`` public wrapper (the one approved
cross-module/self-module dependency for this indicator, matching the
``supertrend``-consumes-``atr`` convention already used elsewhere in this
domain).
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
from app.services.indicators.market_speed.price_velocity import (
    price_velocity as _price_velocity,
)

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
    """Build or validate the immutable momentum-acceleration configuration.

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
        indicator_id="momentum_acceleration",
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
            "supplied config disagrees with momentum_acceleration wrapper arguments",
            {"indicator_id": "momentum_acceleration"},
        )
    return config


@guard_public_boundary
def momentum_acceleration(
    data: MarketDataset,
    *,
    k: int,
    unit_seconds: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate spec ``IND-MS-02`` momentum acceleration.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        k: Required lag of at least one bar, shared with the underlying
            price velocity.
        unit_seconds: Required positive output time-unit denominator.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic momentum-acceleration ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating momentum_acceleration for %s (k=%d, unit_seconds=%s)",
        data.symbol,
        k,
        unit_seconds,
    )
    resolved_config = _build_config(k, unit_seconds, config)
    _unwrap_indicator_response(
        validate_indicator("momentum_acceleration", data, resolved_config)
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

    pv_result: IndicatorResult = _unwrap_indicator_response(
        _price_velocity(data, k=k, unit_seconds=unit_seconds)
    )
    pv_column = f"price_velocity_{k}"
    velocity = pv_result.values[pv_column].to_numpy(dtype="float64")
    pv_valid = np.isfinite(velocity)

    acceleration = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    if row_count > k:
        candidate = pv_valid[k:] & pv_valid[:-k]
        elapsed = (epoch_seconds[k:] - epoch_seconds[:-k]) / unit_seconds
        safe_elapsed = np.where(elapsed > 0.0, elapsed, np.nan)
        diff = (velocity[k:] - velocity[:-k]) / safe_elapsed
        acceleration[k:] = np.where(candidate, diff, np.nan)
        is_valid[k:] = candidate & np.isfinite(acceleration[k:])

    acceleration_state = np.where(is_valid, np.sign(acceleration), np.nan)

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
        f"price_acceleration_{k}",
        f"acceleration_state_{k}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, acceleration, np.nan),
            output_columns[1]: np.where(is_valid, acceleration_state, np.nan),
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


__all__ = ["momentum_acceleration"]
