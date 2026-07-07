"""Deterministic chart downsampling/truncation for Analytics.

Preserves first/last points, peak/trough extrema, and drawdown troughs.
All functions are stateless pure functions.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ChartPoint:
    """Data point representation in charts.

    Args:
        time: Timestamp representation (ISO-8601 or unix timestamp).
        equity: Metric value at this timestamp.
    """

    time: float | int | str
    equity: float


@dataclass(frozen=True, slots=True)
class TruncationPolicy:
    """Configured downsampling and truncation policy limits.

    Args:
        max_points: Maximum number of display points allowed in charts.
        method: Resampling algorithm to use.
    """

    max_points: int = 100
    method: str = "deterministic_decimation_with_extrema"


@dataclass(frozen=True, slots=True)
class TruncatedSeries:
    """Container for downsampled series response data.

    Args:
        curve: Filtered/downsampled chart data points.
        truncated: True if points count was reduced.
        original_count: Pre-truncated size.
        returned_count: Post-truncated size.
        truncation_method: The downsampling algorithm name.
        truncation_reason: Cause description for the downsample trigger.
    """

    curve: list[dict[str, Any]] | list[ChartPoint]
    truncated: bool
    original_count: int
    returned_count: int
    truncation_method: str | None
    truncation_reason: str | None


def truncate_series(
    points: Sequence[ChartPoint] | list[dict[str, Any]],
    policy: TruncationPolicy | None = None,
) -> TruncatedSeries:
    """Deterministic downsampling of series points preserving key extrema."""
    pol = policy or TruncationPolicy()
    max_points = pol.max_points
    n = len(points)
    if n <= max_points:
        return TruncatedSeries(
            curve=list(points),  # type: ignore[arg-type]
            truncated=False,
            original_count=n,
            returned_count=n,
            truncation_method=None,
            truncation_reason=None,
        )

    # Convert input to dictionary representations for extrema checks
    curve_dicts: list[dict[str, Any]] = []
    is_object = False
    for p in points:
        if isinstance(p, dict):
            curve_dicts.append(p)
        else:
            is_object = True
            curve_dicts.append({
                "time": getattr(p, "time", 0.0),
                "equity": getattr(p, "equity", 0.0),
            })

    # Find peak and trough indexes
    peak_idx = 0
    trough_idx = 0
    peak_val = float(curve_dicts[0].get("equity") or 0.0)
    trough_val = peak_val
    for i in range(1, n):
        val = float(curve_dicts[i].get("equity") or 0.0)
        if val > peak_val:
            peak_val = val
            peak_idx = i
        if val < trough_val:
            trough_val = val
            trough_idx = i

    # Step-based decimation
    step = max(n // (max_points - 4), 1)
    indices = {0, n - 1, peak_idx, trough_idx}
    for i in range(0, n, step):
        indices.add(i)

    sorted_indices = sorted(indices)

    if is_object:
        downsampled = [points[idx] for idx in sorted_indices]
    else:
        downsampled = [curve_dicts[idx] for idx in sorted_indices]

    return TruncatedSeries(
        curve=downsampled,  # type: ignore[arg-type]
        truncated=True,
        original_count=n,
        returned_count=len(downsampled),
        truncation_method=pol.method,
        truncation_reason=(
            f"Points count {n} exceeded maximum allowed points {max_points}."
        ),
    )


def _downsample_curve(
    curve: list[dict[str, Any]], max_points: int = 100
) -> dict[str, Any]:
    """Backward-compatible wrapper for downsampling a curve dict list."""
    res = truncate_series(curve, TruncationPolicy(max_points=max_points))
    return {
        "curve": res.curve,
        "truncated": res.truncated,
        "original_count": res.original_count,
        "returned_count": res.returned_count,
        "truncation_method": res.truncation_method,
        "truncation_reason": res.truncation_reason,
    }

