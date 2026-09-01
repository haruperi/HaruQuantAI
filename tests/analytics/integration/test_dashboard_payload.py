"""Workflow integration test for Analytics dashboard projection."""

from app.composition.logging import get_logger
from app.services.analytics import build_dashboard_payload

logger = get_logger(__name__)
from tests.analytics._support import _report, unwrap  # noqa: E402


def test_dashboard_uses_report_sections_without_recomputation() -> None:
    """WF-ANLT-005 preserves report identity, evidence, and non-binding status."""
    logger.debug("Testing Analytics report-to-dashboard workflow")
    report, _ = _report()
    payload = unwrap(build_dashboard_payload(report))
    classes = {section["payload_class"] for section in payload.sections}
    assert {"summary_table", "equity_curve", "warnings", "quality_flags"} <= classes
    assert payload.warnings == report.caveats
    assert payload.quality_flags == report.quality_flags
    assert payload.non_binding is True
