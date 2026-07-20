"""Benchmark comparison package for Analytics.

Exposes alignment boundary policies, FX/UTC controls, and benchmark-relative metrics.
"""

from __future__ import annotations

from app.services.analytics.benchmarks.alignment import (
    _align_series,
    bench_alignment_boundary,
)
from app.services.analytics.benchmarks.metrics import (
    alpha,
    batting_average,
    beta,
    calculate_benchmark_metrics,
    information_ratio,
    r_squared,
    tracking_error,
    up_down_capture,
)

__all__ = [
    "_align_series",
    "alpha",
    "batting_average",
    "bench_alignment_boundary",
    "beta",
    "calculate_benchmark_metrics",
    "information_ratio",
    "r_squared",
    "tracking_error",
    "up_down_capture",
]
