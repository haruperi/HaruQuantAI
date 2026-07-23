"""Unit tests for actual Analytics report comparison."""

# ruff: noqa: INP001

from decimal import Decimal

from app.services.analytics.reports.comparison import compare_performance_reports
from app.utils import logger
from tests.analytics._support import _report


def test_comparison_calculates_real_deltas() -> None:
    """Candidate-minus-reference deltas reflect changed ledger evidence."""
    logger.debug("Testing actual Analytics report deltas")
    reference, _ = _report(profit=Decimal(10))
    candidate, _ = _report(profit=Decimal(20))
    section = compare_performance_reports(reference, candidate)
    net_pnl = next(
        metric
        for metric in section.metrics
        if metric.metric_key == "net_pnl" and metric.source_context == "all"
    )
    assert net_pnl.value == Decimal(10)
