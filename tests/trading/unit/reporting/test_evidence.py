"""Unit tests for immutable Trading report evidence packaging."""

# ruff: noqa: INP001
import json

from app.services.trading.reporting import build_trading_report
from tests.trading.unit.actions.test_dependencies import MemoryStore, request


class ReportStore(MemoryStore):
    """Store fixture returning exact official report evidence."""

    def __init__(self, evidence=None) -> None:
        """Initialize exact stored evidence and observable query scope."""
        super().__init__()
        self.evidence = (
            evidence
            if evidence is not None
            else {
                "receipts": [{"receipt_id": "receipt-001"}],
                "trade_records": [{"commission": "1.25", "cost_unit": "USD"}],
                "readiness": {"reconciled": True},
                "reconciliation": {"state": "reconciled"},
                "incidents": [],
                "warnings": ["provider attribution retained"],
                "unresolved_actions": [],
            }
        )
        self.report_scope = None

    def load_report_evidence(self, scope):
        """Return exact stored facts for one observed scope."""
        self.report_scope = scope
        return self.evidence


def test_report_does_not_compute_analytics_metrics() -> None:
    """Report returns exact factual costs without deriving PnL or TCA."""
    store = ReportStore()
    outcome = build_trading_report(request(action="sync_positions"), store)
    assert outcome.data is not None
    report = outcome.data
    evidence = report.evidence
    assert evidence["trade_records"] == [{"commission": "1.25", "cost_unit": "USD"}]
    assert "pnl" not in str(outcome.data).lower()
    assert "tca" not in str(outcome.data).lower()
    assert store.report_scope == ("sim", "account-001", "simulation")
    assert report.contract_version == "v1"
    assert report.schema_id == "trading.execution_evidence_report.v1"


def test_report_fails_closed_on_missing_evidence() -> None:
    """Missing official evidence is explicit and blocks packaging."""
    store = ReportStore(evidence={"receipts": []})
    result = build_trading_report(request(action="sync_positions"), store)
    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == "RECONCILIATION_REQUIRED"


def test_report_redacts_stored_sensitive_evidence() -> None:
    """Stored report evidence is redacted immediately before emission."""
    evidence = ReportStore().evidence
    evidence["incidents"] = [{"password": "p", "access_token": "t"}]
    outcome = build_trading_report(
        request(action="sync_positions"), ReportStore(evidence=evidence)
    )
    serialized = json.dumps(outcome.model_dump(mode="json"))
    assert '"p"' not in serialized
    assert '"t"' not in serialized
    assert outcome.metadata.extensions["redaction_applied"] is True
