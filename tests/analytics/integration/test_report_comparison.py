"""Integration evidence for Analytics report comparison."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.analytics.reports.comparison import compare_performance_reports
from app.utils import logger
from tests.analytics.usage.test_usage_reports import _report


def test_report_comparison_uses_actual_common_metrics() -> None:
    """The comparison workflow emits a nonzero actual net-PnL delta."""
    logger.debug("Testing Analytics actual comparison workflow")
    reference, _ = _report(profit=Decimal(10))
    candidate, _ = _report(profit=Decimal(30))
    section = compare_performance_reports(reference, candidate)
    assert any(metric.value == Decimal(20) for metric in section.metrics)
