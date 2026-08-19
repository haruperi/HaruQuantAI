"""Unit tests for Analytics dashboard payload projection."""

from app.services.analytics.dashboards.payloads import build_dashboard_payload
from app.utils import get_logger

logger = get_logger(__name__)

from tests.analytics._support import _report  # noqa: E402


def test_dashboard_payload_does_not_recompute_metrics() -> None:
    """Summary and equity values are copied from the canonical report."""
    logger.debug("Testing Analytics dashboard projection fidelity")
    report, _ = _report()
    payload = build_dashboard_payload(report)
    summary = next(
        section
        for section in payload.sections
        if section["payload_class"] == "summary_table"
    )
    equity = next(
        section
        for section in payload.sections
        if section["payload_class"] == "equity_curve"
    )
    net_pnl = next(
        metric
        for row in summary["rows"]
        for metric in row["metrics"]
        if metric["metric_key"] == "net_pnl" and metric["source_context"] == "all"
    )
    assert net_pnl["value"] == "9"
    assert tuple(equity["points"]) == tuple(
        report.precision_metadata["presentation_series"]["equity_curve"]
    )
    assert payload.report_id == report.report_id


def test_drawdown_and_monthly_payload_sections_are_completed() -> None:
    """Drawdown and monthly-returns projections are completed from owner series."""
    report, _ = _report()
    payload = build_dashboard_payload(report)
    drawdown = next(
        section
        for section in payload.sections
        if section["payload_class"] == "drawdown_chart"
    )
    monthly = next(
        section
        for section in payload.sections
        if section["payload_class"] == "monthly_returns_table"
    )
    assert drawdown["status"] == "completed"
    assert monthly["status"] == "completed"
    assert tuple(drawdown["points"]) == tuple(
        report.precision_metadata["presentation_series"]["drawdown_curve"]
    )
    assert tuple(monthly["rows"]) == tuple(
        report.precision_metadata["presentation_series"]["monthly_returns"]
    )
    assert any(
        row.get("payload_class") == "equity_curve"
        for row in payload.truncation_metadata
    )
