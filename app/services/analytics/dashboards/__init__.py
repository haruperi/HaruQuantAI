"""Presentation-payload and UI-ready dashboard generation package for Analytics.

Exposes overview payload formatters, chart/table conversions, size-limit checks,
and deterministic downsampling / series truncation algorithms.
"""

from __future__ import annotations

from app.services.analytics.dashboards.overview import (
    DashboardConfig,
    DashboardPayload,
    TruncationMetadata,
    build_overview_payload,
)
from app.services.analytics.dashboards.truncation import (
    ChartPoint,
    TruncatedSeries,
    TruncationPolicy,
    _downsample_curve,
    truncate_series,
)

__all__ = [
    "ChartPoint",
    "DashboardConfig",
    "DashboardPayload",
    "TruncatedSeries",
    "TruncationMetadata",
    "TruncationPolicy",
    "_downsample_curve",
    "build_overview_payload",
    "truncate_series",
]
