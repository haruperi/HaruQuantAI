# ruff: noqa: PD011
"""Volatility-liquidity stress regime classifier (reduced-input variant).

Implements a documented reduced-input variant of spec ``IND-RG-05``. The
canonical formula requires volatility percentile, relative-spread
percentile/z-score, depth percentile, quote freshness, and scheduled-event
state. The current ``MarketDataset``/``OHLCVRecord`` contract carries none
of the spread/depth/quote-freshness/event-calendar inputs (see
``liquidity/__init__.py`` and ``order_flow/__init__.py``), so this file
consumes only the canonical ``volatility.volatility_percentile`` public
wrapper plus this domain's own ``liquidity.amihud_illiquidity`` (rank-
converted into a rolling percentile locally, since Amihud has no percentile
transform of its own). Per the plan's explicit allowance, this is a
reduced-input classifier rather than a skip: the ``EVENT`` and
``DATA_DEGRADED`` branches are never reachable (no calendar/staleness
input exists to trigger them), and every row that would otherwise need
those unavailable inputs is a warmup/unavailable row rather than a
fabricated ``NORMAL_CONDITIONS`` classification.
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
from app.services.indicators.liquidity.amihud_illiquidity import (
    amihud_illiquidity as _amihud_illiquidity,
)
from app.services.indicators.volatility.volatility_percentile import (
    volatility_percentile as _volatility_percentile,
)
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
# 0=NORMAL_CONDITIONS, 1=LOW_LIQUIDITY, 2=UNSTABLE
_NORMAL_CONDITIONS, _LOW_LIQUIDITY, _UNSTABLE = 0.0, 1.0, 2.0


def _build_config(
    vol_reference_period: int,
    vol_period: int,
    amihud_window: int,
    p_vol_extreme: float,
    p_illiquidity_extreme: float,
    p_illiquidity_high: float,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the immutable stress-regime configuration.

    Args:
        vol_reference_period: The vol reference period value.
        vol_period: The vol period value.
        amihud_window: The amihud window value.
        p_vol_extreme: The p vol extreme value.
        p_illiquidity_extreme: The p illiquidity extreme value.
        p_illiquidity_high: The p illiquidity high value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="volatility_liquidity_stress_regime",
        parameters=(
            ("amihud_window", amihud_window),
            ("p_illiquidity_extreme", p_illiquidity_extreme),
            ("p_illiquidity_high", p_illiquidity_high),
            ("p_vol_extreme", p_vol_extreme),
            ("vol_period", vol_period),
            ("vol_reference_period", vol_reference_period),
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
            "supplied config disagrees with volatility_liquidity_stress_regime "
            "arguments",
            {"indicator_id": "volatility_liquidity_stress_regime"},
        )
    return config


def _rolling_percentile_rank(values: np.ndarray, window: int) -> np.ndarray:
    """Compute the trailing-window percentile rank of the last observation.

    Args:
        values: The values value.
        window: The window value.

    Returns:
        The np.ndarray result.

    Raises:
        None.
    """
    row_count = len(values)
    output = np.full(row_count, np.nan, dtype="float64")
    for position in range(window - 1, row_count):
        sample = values[position - window + 1 : position + 1]
        if np.isnan(sample).any():
            continue
        current = sample[-1]
        rank = float(np.sum(sample < current) + 0.5 * np.sum(sample == current))
        output[position] = 100.0 * rank / window
    return output


@guard_public_boundary
def volatility_liquidity_stress_regime(
    data: MarketDataset,
    *,
    vol_reference_period: int,
    vol_period: int,
    amihud_window: int,
    p_vol_extreme: float,
    p_illiquidity_extreme: float,
    p_illiquidity_high: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Classify the reduced-input spec ``IND-RG-05`` stress regime.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        vol_reference_period: Reference window fed to the canonical
            volatility percentile, and reused as this file's local Amihud
            percentile-rank window.
        vol_period: Realized-volatility window fed to the canonical
            volatility percentile.
        amihud_window: Window fed to this domain's Amihud illiquidity.
        p_vol_extreme: Required volatility-percentile stress threshold.
        p_illiquidity_extreme: Required Amihud-percentile stress threshold.
        p_illiquidity_high: Required Amihud-percentile low-liquidity
            threshold (must not exceed ``p_illiquidity_extreme``).
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic reduced-input stress-regime ``IndicatorResult``
        carrying the state (``0``=NORMAL_CONDITIONS, ``1``=LOW_LIQUIDITY,
        ``2``=UNSTABLE) plus the two contributing percentiles.

    Raises:
        IndicatorError: If threshold ordering is invalid, or on validation
            or atomic calculation failure.
    """
    if p_illiquidity_high > p_illiquidity_extreme:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_CONFIG,
            "volatility_liquidity_stress_regime requires "
            "p_illiquidity_high <= p_illiquidity_extreme",
            {"indicator_id": "volatility_liquidity_stress_regime"},
        )
    logger.info("Calculating volatility_liquidity_stress_regime for %s", data.symbol)
    resolved_config = _build_config(
        vol_reference_period,
        vol_period,
        amihud_window,
        p_vol_extreme,
        p_illiquidity_extreme,
        p_illiquidity_high,
        config,
    )
    _unwrap_indicator_response(
        validate_indicator("volatility_liquidity_stress_regime", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )

    vol_result: IndicatorResult = _unwrap_indicator_response(
        _volatility_percentile(
            data, reference_period=vol_reference_period, vol_period=vol_period
        )
    )
    vol_percentile = vol_result.values[
        f"volatility_percentile_{vol_reference_period}_{vol_period}"
    ].to_numpy("float64")

    amihud_result: IndicatorResult = _unwrap_indicator_response(
        _amihud_illiquidity(data, window=amihud_window)
    )
    amihud_values = amihud_result.values[
        f"amihud_illiquidity_{amihud_window}"
    ].to_numpy("float64")
    illiquidity_percentile = _rolling_percentile_rank(
        amihud_values, vol_reference_period
    )

    is_valid = np.isfinite(vol_percentile) & np.isfinite(illiquidity_percentile)

    unstable = (vol_percentile >= p_vol_extreme) | (
        illiquidity_percentile >= p_illiquidity_extreme
    )
    low_liquidity = (~unstable) & (illiquidity_percentile >= p_illiquidity_high)
    state = np.select(
        [unstable, low_liquidity],
        [_UNSTABLE, _LOW_LIQUIDITY],
        default=_NORMAL_CONDITIONS,
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

    suffix = f"{vol_reference_period}_{vol_period}_{amihud_window}"
    output_columns = (
        f"stress_regime_{suffix}",
        f"stress_volatility_percentile_{suffix}",
        f"stress_illiquidity_percentile_{suffix}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: np.where(is_valid, state, np.nan),
            output_columns[1]: np.where(is_valid, vol_percentile, np.nan),
            output_columns[2]: np.where(is_valid, illiquidity_percentile, np.nan),
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


__all__ = ["volatility_liquidity_stress_regime"]
