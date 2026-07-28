"""Workflow integration for immutable execution evidence reporting."""

# ruff: noqa: INP001
from app.services.trading import build_trading_report
from tests.trading.conftest import ReportStore, trading_request


def test_report_contains_only_execution_evidence() -> None:
    """Report preserves official execution facts and adds no Analytics metrics."""
    outcome = build_trading_report(
        trading_request(action="sync_positions"), ReportStore()
    )
    assert outcome.status == "success"
    assert outcome.data is not None
    assert outcome.data.schema_id == "trading.execution_evidence_report.v1"
    assert set(outcome.data.evidence) == {
        "incidents",
        "readiness",
        "receipts",
        "reconciliation",
        "trade_records",
        "unresolved_actions",
        "warnings",
    }
    assert "performance" not in str(outcome.data).lower()
