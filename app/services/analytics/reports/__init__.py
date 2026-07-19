"""Approved canonical reporting feature API for Analytics."""

from app.services.analytics.reports.allocation import (
    build_portfolio_allocation_evidence,
)
from app.services.analytics.reports.builder import build_performance_report
from app.services.analytics.reports.comparison import compare_performance_reports
from app.services.analytics.reports.hashes import compute_reproducibility_hashes
from app.services.analytics.reports.portfolio import build_portfolio_performance_report
from app.services.analytics.reports.serialization import serialize_report

__all__ = (
    "build_performance_report",
    "build_portfolio_allocation_evidence",
    "build_portfolio_performance_report",
    "compare_performance_reports",
    "compute_reproducibility_hashes",
    "serialize_report",
)
