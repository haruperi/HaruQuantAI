"""Unit tests for Analytics dashboard payload projection."""

# ruff: noqa: INP001

from app.services.analytics.dashboards.payloads import build_dashboard_payload
from app.utils import logger
from tests.analytics._support import _report


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
