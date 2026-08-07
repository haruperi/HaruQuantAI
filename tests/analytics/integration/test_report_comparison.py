"""Integration evidence for Analytics report comparison."""

from decimal import Decimal

from app.services.analytics import compare_performance_reports
from app.utils import get_logger

logger = get_logger(__name__)
from tests.analytics._support import _report, unwrap  # noqa: E402


def test_report_comparison_uses_actual_common_metrics() -> None:
    """The comparison workflow emits a nonzero actual net-PnL delta."""
    logger.debug("Testing Analytics actual comparison workflow")
    reference, _ = _report(profit=Decimal(10))
    candidate, _ = _report(profit=Decimal(30))
    section = unwrap(compare_performance_reports(reference, candidate))
    assert any(metric.value == Decimal(20) for metric in section.metrics)
