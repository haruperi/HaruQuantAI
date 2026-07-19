"""Public Analytics domain port."""

from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    DashboardPayload,
    PerformanceReport,
    PortfolioAllocationEvidence,
    RiskFreeRateEvidence,
    StatisticalValidationConfig,
)
from app.services.analytics.reports.builder import build_performance_report

__all__: tuple[str, ...] = (
    "AnalyticsRunConfig",
    "DashboardPayload",
    "PerformanceReport",
    "PortfolioAllocationEvidence",
    "RiskFreeRateEvidence",
    "StatisticalValidationConfig",
    "build_performance_report",
)
