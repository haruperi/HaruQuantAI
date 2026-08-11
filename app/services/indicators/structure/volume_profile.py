"""Rolling volume-profile POC/value-area calculator.

Implements spec ``IND-ST-05`` over a trailing ``period``-bar window with
declared bar-close binning: each bar's full volume is allocated to the
equal-width price bin containing its close (the spec-required "approximate
bar-volume allocation" mode, explicitly labeled here rather than a tick/
trade-level allocation, which the current OHLCV-only contract cannot
supply).
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
_DEFAULT_VALUE_AREA_FRACTION = 0.70


def _build_config(
    period: int,
    bins: int,
    value_area_fraction: float,
    config: IndicatorConfig | None,
) -> IndicatorConfig:
    """Build or validate the immutable volume-profile configuration.

    Args:
        period: The period value.
        bins: The bins value.
        value_area_fraction: The value area fraction value.
        config: The config value.

    Returns:
        The IndicatorConfig result.

    Raises:
        IndicatorError: If the operation cannot complete.
    """
    expected = IndicatorConfig(
        indicator_id="volume_profile",
        parameters=(
            ("bins", bins),
            ("period", period),
            ("value_area_fraction", value_area_fraction),
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
            "supplied config disagrees with volume_profile wrapper arguments",
            {"indicator_id": "volume_profile"},
        )
    return config


def _window_profile(
    closes: np.ndarray, volumes: np.ndarray, bins: int, value_area_fraction: float
) -> tuple[float, float, float] | None:
    """Calculate one trailing-window POC/VAL/VAH triple.

    Args:
            closes: Window-ordered close prices.
            volumes: Window-ordered bar volumes.
            bins: Required equal-width bin count.
            value_area_fraction: Required cumulative value-area fraction ``q``.

    Returns:
            The ``(poc, val, vah)`` triple, or ``None`` if total volume is zero.

    Raises:
        None.
    """
    total_volume = float(volumes.sum())
    if total_volume <= 0.0:
        return None
    low = float(closes.min())
    high = float(closes.max())
    if high == low:
        return (low, low, low)
    edges = np.linspace(low, high, bins + 1)
    bin_index = np.clip(np.digitize(closes, edges[1:-1], right=True), 0, bins - 1)
    bin_volume = np.zeros(bins, dtype="float64")
    np.add.at(bin_volume, bin_index, volumes)
    centers = (edges[:-1] + edges[1:]) / 2.0

    poc_bin = int(np.argmax(bin_volume))
    selected = {poc_bin}
    selected_volume = float(bin_volume[poc_bin])
    threshold = value_area_fraction * total_volume
    low_bin = high_bin = poc_bin
    while selected_volume < threshold and (low_bin > 0 or high_bin < bins - 1):
        lower_candidate = low_bin - 1 if low_bin > 0 else None
        upper_candidate = high_bin + 1 if high_bin < bins - 1 else None
        lower_volume = (
            bin_volume[lower_candidate] if lower_candidate is not None else -1.0
        )
        upper_volume = (
            bin_volume[upper_candidate] if upper_candidate is not None else -1.0
        )
        if upper_volume > lower_volume and upper_candidate is not None:
            high_bin = upper_candidate
            selected.add(high_bin)
            selected_volume += float(bin_volume[high_bin])
        elif lower_candidate is not None:
            low_bin = lower_candidate
            selected.add(low_bin)
            selected_volume += float(bin_volume[low_bin])
        else:
            break
    return (float(centers[poc_bin]), float(centers[low_bin]), float(centers[high_bin]))


@guard_public_boundary
def volume_profile(
    data: MarketDataset,
    *,
    period: int,
    bins: int,
    value_area_fraction: float = _DEFAULT_VALUE_AREA_FRACTION,
    config: IndicatorConfig | None = None,
) -> IndicatorResult:
    """Calculate the trailing-window volume-profile POC, VAL, and VAH.

    Args:
        data: One normalized immutable ``MarketDataset v1``.
        period: Required trailing window length of at least two.
        bins: Required equal-width price-bin count of at least one.
        value_area_fraction: Required cumulative value-area fraction ``q``
            in ``(0, 1]``; defaults to ``0.70``.
        config: Optional explicit configuration matching the arguments.

    Returns:
        A deterministic volume-profile ``IndicatorResult``.

    Raises:
        IndicatorError: On validation or atomic calculation failure.
    """
    logger.info(
        "Calculating volume_profile for %s (period=%d, bins=%d)",
        data.symbol,
        period,
        bins,
    )
    resolved_config = _build_config(period, bins, value_area_fraction, config)
    _unwrap_indicator_response(
        validate_indicator("volume_profile", data, resolved_config)
    )
    records = cast("tuple[OHLCVRecord, ...]", data.records)
    index = pd.DatetimeIndex(
        [record.timestamp for record in records], name="timestamp", tz="UTC"
    )
    close = np.asarray([float(record.close) for record in records], dtype="float64")
    volume = np.asarray([float(record.volume) for record in records], dtype="float64")
    row_count = len(records)

    is_valid = np.zeros(row_count, dtype=bool)
    poc = np.full(row_count, np.nan, dtype="float64")
    val = np.full(row_count, np.nan, dtype="float64")
    vah = np.full(row_count, np.nan, dtype="float64")

    for position in range(period - 1, row_count):
        window_close = close[position - period + 1 : position + 1]
        window_volume = volume[position - period + 1 : position + 1]
        profile = _window_profile(
            window_close, window_volume, bins, value_area_fraction
        )
        if profile is None:
            continue
        poc[position], val[position], vah[position] = profile
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
        f"volume_profile_poc_{period}_{bins}",
        f"volume_profile_val_{period}_{bins}",
        f"volume_profile_vah_{period}_{bins}",
    )
    output_values = pd.DataFrame(
        {
            output_columns[0]: poc,
            output_columns[1]: val,
            output_columns[2]: vah,
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


__all__ = ["volume_profile"]
