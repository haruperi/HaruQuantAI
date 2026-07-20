"""Report composition and serialization package for Analytics.

Exposes sections orchestration, partial report logic, hashing, formatting,
and downstream API converters.
"""

from __future__ import annotations

from app.services.analytics.reports.formatters import (
    ReportFormat,
    SerializedReport,
    build_backtest_report,
    format_summary_as_rows,
    print_statistical_validation_report,
    serialize_report,
)
from app.services.analytics.reports.hashes import (
    HashPolicy,
    compute_report_hash,
)
from app.services.analytics.reports.sections import (
    AnalyticsReport,
    PortfolioAnalyticsReport,
    build_analytics_report,
    build_portfolio_analytics_report,
    calculate_prop_firm_compliance,
    calculate_statistical_validation,
    compare_analytics_reports,
    request_id,
)

__all__ = [
    "AnalyticsReport",
    "HashPolicy",
    "PortfolioAnalyticsReport",
    "ReportFormat",
    "SerializedReport",
    "build_analytics_report",
    "build_backtest_report",
    "build_portfolio_analytics_report",
    "calculate_prop_firm_compliance",
    "calculate_statistical_validation",
    "compare_analytics_reports",
    "compute_report_hash",
    "format_summary_as_rows",
    "print_statistical_validation_report",
    "request_id",
    "serialize_report",
]
