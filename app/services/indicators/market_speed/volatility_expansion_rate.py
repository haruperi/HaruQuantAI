# ruff: noqa: PD011
"""Volatility expansion rate calculator.

Implements spec ``IND-MS-06`` as the log rate of change of the canonical
``volatility.atr`` public wrapper (the one approved cross-module dependency
for this indicator, matching the ``supertrend``-consumes-``atr``
convention already used elsewhere in this domain). ``volatility/`` owns
ATR; this module owns only the rate of change of the published value.
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
_STABLE_EPSILON = 1e-9


def _build_config(
    atr_period: int, k: int, unit_seconds: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable volatility-expansion-rate configuration.

    Args:
        atr_period: The atr period value.
        k: The k value.
        unit_seconds: The unit seconds value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="volatility_expansion_rate",
        parameters=(
            ("atr_period", atr_period),
            ("k", k),
            ("unit_seconds", unit_seconds),
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
            "supplied config disagrees with volatility_expansion_rate arguments",
            {"indicator_id": "volatility_expansion_rate"},
        )
    return config


@guard_public_boundary
def volatility_expansion_rate(
    data: MarketDataset,
    *,
    atr_period: int,
    k: int,
    unit_seconds: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate spec ``IND-MS-06`` volatility expansion rate from ATR.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        atr_period: Required smoothing period fed to the canonical ATR.
        k: Required lag of at least one bar.
        unit_seconds: Required positive output time-unit denominator.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic volatility-expansion-rate ``IndicatorResult``
        carrying the rate and a signed ``EXPANDING``/``CONTRACTING``/
        ``STABLE`` direction code (``1``/``-1``/``0``).

    Raises:
        IndicatorError: On validation, atomic calculation, or non-positive
            ATR failure.
    """
    logger.info(
        "Calculating volatility_expansion_rate for %s "
        "(atr_period=%d, k=%d, unit_seconds=%s)",
        data.symbol,
        atr_period,
        k,
        unit_seconds,
    )
    resolved_config = _build_config(atr_period, k, unit_seconds, config)
    _unwrap_indicator_response(
        validate_indicator("volatility_expansion_rate", data, resolved_config)
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

    atr_result: IndicatorResult = _unwrap_indicator_response(
        _atr(data, period=atr_period)
    )
    atr_values = atr_result.values[f"atr_{atr_period}"].to_numpy(dtype="float64")
    atr_valid = np.isfinite(atr_values)
    if atr_valid.any() and (atr_values[atr_valid] <= 0).any():
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_OHLC,
            "volatility_expansion_rate requires strictly positive source ATR",
            {"indicator_id": "volatility_expansion_rate"},
        )

    rate = np.full(row_count, np.nan, dtype="float64")
    is_valid = np.zeros(row_count, dtype=bool)
    if row_count > k:
        candidate = atr_valid[k:] & atr_valid[:-k]
        elapsed = (epoch_seconds[k:] - epoch_seconds[:-k]) / unit_seconds
        safe_elapsed = np.where(elapsed > 0.0, elapsed, np.nan)
        log_diff = np.log(atr_values[k:]) - np.log(atr_values[:-k])
        computed = log_diff / safe_elapsed
        rate[k:] = np.where(candidate, computed, np.nan)
        is_valid[k:] = candidate & np.isfinite(rate[k:])

    direction = np.where(
        is_valid,
        np.where(
            rate > _STABLE_EPSILON, 1.0, np.where(rate < -_STABLE_EPSILON, -1.0, 0.0)
        ),
        np.nan,
    )

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
        f"volatility_expansion_rate_{atr_period}_{k}",
        f"volatility_expansion_direction_{atr_period}_{k}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, rate, np.nan),
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


__all__ = ["volatility_expansion_rate"]
