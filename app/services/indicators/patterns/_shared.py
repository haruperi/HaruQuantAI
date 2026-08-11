# ruff: noqa: PD011, PLR2004
"""Private shared helpers for the ``patterns/`` chart-pattern detectors.

Not part of the public API (no leading-underscore-free export). Every
pattern detector that needs confirmed swing pivots or ATR calls these
helpers rather than recomputing the primitives, per the domain's
no-recalculation-across-category rule (``structure/`` owns pivots,
``volatility/`` owns ATR).

Every pattern output in this module collapses the spec's five-state
``DETECTED``/``FORMING``/``CONFIRMED``/``INVALIDATED``/``EXPIRED`` model to
four numeric codes: ``0``=NONE, ``1``=DETECTED, ``2``=CONFIRMED,
``3``=INVALIDATED. ``FORMING`` (a sub-bar-close state) and ``EXPIRED`` (an
externally scheduled state) are not observable from a closed-bar-only
``MarketDataset``, so they are folded into ``NONE``/``INVALIDATED``
respectively; this is a documented simplification of the spec's full state
machine, consistent with the judgment latitude already used for
``order_flow/``'s and ``liquidity/``'s contract-availability skips.
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
)
from app.services.indicators.structure.pivots import pivots as _pivots
from app.services.indicators.volatility.atr import atr as _atr

if TYPE_CHECKING:
    from app.services.indicators.core.contracts import (
        _MarketDataset as MarketDataset,
    )
    from app.services.indicators.core.contracts import (
        _OHLCVRecord as OHLCVRecord,
    )
    from app.services.indicators.core.results import IndicatorResult

# 0=NONE, 1=DETECTED, 2=CONFIRMED, 3=INVALIDATED
NONE_STATE = 0.0
DETECTED = 1.0
CONFIRMED = 2.0
INVALIDATED = 3.0


def fetch_pivots(
    data: MarketDataset, *, left: int, right: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Fetch confirmed pivot-high/low flags and prices for one dataset.

    Args:
            data: One normalized immutable ``MarketDataset v1``.
            left: Required left-bar count fed to ``structure.pivots``.
            right: Required right-bar count fed to ``structure.pivots``.

    Returns:
            Parallel ``(pivot_high_flag, pivot_high_price, pivot_low_flag,
            pivot_low_price)`` float64 arrays, ``NaN`` where unavailable.

    Raises:
        None.
    """
    result: IndicatorResult = _unwrap_indicator_response(
        _pivots(data, left=left, right=right)
    )
    high_flag = result.values[f"pivot_high_flag_{left}_{right}"].to_numpy("float64")
    high_price = result.values[f"pivot_high_price_{left}_{right}"].to_numpy("float64")
    low_flag = result.values[f"pivot_low_flag_{left}_{right}"].to_numpy("float64")
    low_price = result.values[f"pivot_low_price_{left}_{right}"].to_numpy("float64")
    return high_flag, high_price, low_flag, low_price


def fetch_atr(data: MarketDataset, *, atr_period: int) -> np.ndarray:
    """Fetch the canonical ATR series for one dataset.

    Args:
            data: One normalized immutable ``MarketDataset v1``.
            atr_period: Required smoothing period fed to ``volatility.atr``.

    Returns:
            The float64 ATR array, ``NaN`` during warmup.

    Raises:
        None.
    """
    result: IndicatorResult = _unwrap_indicator_response(_atr(data, period=atr_period))
    return np.asarray(result.values[f"atr_{atr_period}"].to_numpy("float64"))


def build_pattern_config(
    indicator_id: str,
    parameters: tuple[tuple[str, int | float], ...],
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate one immutable parameterized pattern configuration.

    Args:
        indicator_id: The exact official registry identifier.
        parameters: Canonical key-sorted parameter pairs.
        config: Optional explicit configuration matching the arguments.

    Returns:
        The configuration used for calculation.

    Raises:
        IndicatorError: If an explicit configuration disagrees with the
            wrapper's own identity, parameters, or formula version.
    """
    expected = IndicatorConfig(
        indicator_id=indicator_id,
        parameters=parameters,
        source=None,
        formula_version="1.0.0",
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
            f"supplied config disagrees with {indicator_id} wrapper arguments",
            {"indicator_id": indicator_id},
        )
    return config


def causal_series(
    data: MarketDataset, is_valid: np.ndarray
) -> tuple[pd.DatetimeIndex, pd.Series, pd.Series, pd.Series, pd.Series]:
    """Build the standard causal availability series for one result.

    Args:
            data: One normalized immutable ``MarketDataset v1``.
            is_valid: Per-row boolean validity mask.

    Returns:
            ``(index, computed_from_start, computed_from_end, available_at,
            unavailable_reason)`` ready for ``build_indicator_result``.

    Raises:
        None.
    """
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
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
    return (
        index,
        computed_from_start,
        computed_from_end,
        available_at,
        unavailable_reason,
    )


def recent_pivot_points(
    flag: np.ndarray, price: np.ndarray, upto_index: int, count: int
) -> tuple[np.ndarray, np.ndarray]:
    """Collect the most recent confirmed pivots at or before one row.

    Args:
            flag: Confirmed pivot flag array (``1.0`` at confirmation rows).
            price: Confirmed pivot price array, aligned with ``flag``.
            upto_index: Inclusive upper row bound.
            count: Maximum number of most-recent pivots to collect.

    Returns:
            Parallel ``(indices, prices)`` arrays in ascending row order,
            shorter than ``count`` when fewer pivots exist.

    Raises:
        None.
    """
    indices = np.flatnonzero(flag[: upto_index + 1] == 1.0)
    tail = indices[-count:] if len(indices) > count else indices
    return tail, price[tail]


def fit_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float] | None:
    """Fit ``y = a + b*x`` by ordinary least squares.

    Args:
            x: Sample x-coordinates (at least two required, non-degenerate).
            y: Sample y-coordinates, aligned with ``x``.

    Returns:
            ``(slope, intercept)``, or ``None`` if fewer than two points or the
            x-coordinates are degenerate (zero variance).

    Raises:
        None.
    """
    if len(x) < 2 or float(np.ptp(x)) == 0.0:
        return None
    slope, intercept = np.polyfit(x.astype("float64"), y.astype("float64"), 1)
    return float(slope), float(intercept)


__all__: tuple[str, ...] = ()
