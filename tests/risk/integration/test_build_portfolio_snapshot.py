"""Workflow integration test for external evidence to Risk snapshot."""

from app.services.risk import build_portfolio_risk_snapshot

from tests.risk._support import unwrap_risk_response
from tests.risk.unit.test_snapshot import NOW, _config, _state


def test_build_portfolio_snapshot_from_external_evidence() -> None:
    """Build the WF-RISK-001 output from Data-owned account and FX evidence."""
    snapshot = unwrap_risk_response(
        build_portfolio_risk_snapshot(_state(), _config(), now=NOW),
        operation="build_portfolio_risk_snapshot",
    )
    assert snapshot.coverage["account"] == "complete"
    assert snapshot.coverage["fx"] == "complete"
    assert snapshot.coverage["returns"] == "complete"
