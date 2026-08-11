# ruff: noqa: PLR0915
r"""Structural-level clustering calculator.

Implements spec ``IND-ST-07``'s adjacent-distance clustering rule over
confirmed swing pivots. This leaf file derives its own confirmed pivots
(fixed two-bar left/right confirmation) from the trailing ``lookback``
window rather than accepting an external pre-confirmed level stream, so it
can run as a single-``MarketDataset`` indicator like every sibling leaf
file; ``structure.pivots`` remains the canonical pivot-confirmation owner
and this file duplicates only the minimal confirmation check needed to
identify cluster members, not a second published pivot series.

For each row, the published cluster is the volume-weight-free,
recency-weighted cluster nearest to the row's close, per
``w_i=w_i^{base}\\cdot 2^{-age_i/half\\_life}``.
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
_CONFIRM_BARS = 2


def _build_config(
    lookback: int, tolerance: float, half_life: float, config: IndicatorConfig | None
) -> IndicatorConfig:
    """Build or validate the immutable level-clustering configuration.

    Args:
        lookback: The lookback value.
        tolerance: The tolerance value.
        half_life: The half life value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="level_clustering",
        parameters=(
            ("half_life", half_life),
            ("lookback", lookback),
            ("tolerance", tolerance),
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
            "supplied config disagrees with level_clustering arguments",
            {"indicator_id": "level_clustering"},
        )
    return config


def _confirmed_pivots(
    high: np.ndarray, low: np.ndarray, up_to: int
) -> list[tuple[int, float]]:
    """Collect confirmed pivot ``(bar_index, price)`` pairs up to a row.

    Args:
        high: The high value.
        low: The low value.
        up_to: The up to value.

    Returns:
        The list[tuple[int, float]] result.

    Raises:
        None.
    """
    levels: list[tuple[int, float]] = []
    for pivot_bar in range(_CONFIRM_BARS, up_to - _CONFIRM_BARS + 1):
        window_slice = slice(pivot_bar - _CONFIRM_BARS, pivot_bar + _CONFIRM_BARS + 1)
        if high[pivot_bar] == high[window_slice].max():
            levels.append((pivot_bar, float(high[pivot_bar])))
        if low[pivot_bar] == low[window_slice].min():
            levels.append((pivot_bar, float(low[pivot_bar])))
    return levels


@guard_public_boundary
def level_clustering(
    data: MarketDataset,
    *,
    lookback: int,
    tolerance: float,
    half_life: float,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate the nearest recency-weighted structural-level cluster.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        lookback: Required trailing bar window of at least ``2*2+1``
            searched for confirmed pivots.
        tolerance: Required positive clustering distance ``tau``.
        half_life: Required positive recency decay half-life in bars.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic level-clustering ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating level_clustering for %s (lookback=%d)", data.symbol, lookback
    )
    resolved_config = _build_config(lookback, tolerance, half_life, config)
    _unwrap_indicator_response(
        validate_indicator("level_clustering", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    high = np.asarray([float(record.high) for record in records], dtype="float64")
    low = np.asarray([float(record.low) for record in records], dtype="float64")
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    row_count = len(records)
    min_bars = 2 * _CONFIRM_BARS + 1

    is_valid = np.zeros(row_count, dtype=bool)
    cluster_price = np.zeros(row_count, dtype="float64")
    cluster_weight = np.zeros(row_count, dtype="float64")
    cluster_flag = np.zeros(row_count, dtype="float64")

    for position in range(min_bars - 1, row_count):
        window_start = max(0, position - lookback + 1)
        levels = _confirmed_pivots(high, low, position + 1)
        levels = [item for item in levels if item[0] >= window_start]
        is_valid[position] = True
        if not levels:
            continue
        levels.sort(key=lambda item: item[1])
        clusters: list[list[tuple[int, float]]] = [[levels[0]]]
        for entry in levels[1:]:
            if entry[1] - clusters[-1][-1][1] <= tolerance:
                clusters[-1].append(entry)
            else:
                clusters.append([entry])

        best_price: float | None = None
        best_weight = 0.0
        best_distance = math_inf = float("inf")
        for members in clusters:
            weights = [
                2.0 ** (-(position - bar_index) / half_life) for bar_index, _ in members
            ]
            total_weight = float(sum(weights))
            weighted_price = float(
                sum(
                    price * weight
                    for (_, price), weight in zip(members, weights, strict=True)
                )
                / total_weight
            )
            distance = abs(close[position] - weighted_price)
            if distance < best_distance:
                best_distance = distance
                best_price = weighted_price
                best_weight = total_weight
        del math_inf
        if best_price is not None:
            cluster_price[position] = best_price
            cluster_weight[position] = best_weight
            cluster_flag[position] = 1.0

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
        "level_cluster_price",
        "level_cluster_weight",
        "level_cluster_flag",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: cluster_price,
            output_columns[1]: cluster_weight,
            output_columns[2]: cluster_flag,
        },
        index=index,
    )
    for column in output_columns:
        output_values.loc[~is_valid, column] = np.nan

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


__all__ = ["level_clustering"]
