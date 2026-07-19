"""Runnable usage example for immutable Trading report evidence."""

from app.services.trading.reporting import build_trading_report
from tests.trading.unit.actions.test_dependencies import request
from tests.trading.unit.reporting.test_evidence import ReportStore


def test_usage_evidence_build_trading_report() -> None:
    """Query exact Trading evidence through the injected store port."""
    outcome = build_trading_report(request(action="sync_positions"), ReportStore())
    assert outcome.status == "success"
    assert outcome.data["schema_id"] == "trading.execution_evidence_report.v1"
