"""Workflow integration for route facts and readiness aggregation."""

from decimal import Decimal

from app.services.trading import assess_execution_readiness

from tests.trading.conftest import (
    readiness_request,
    readiness_risk,
    readiness_snapshot,
    readiness_switch,
)


def test_unavailable_route_fact_fails_readiness() -> None:
    """Unavailable route evidence remains an explicit readiness failure."""
    snapshot_data = readiness_snapshot().model_dump()
    snapshot_data.update({"available": False, "fresh": False})
    snapshot = type(readiness_snapshot()).model_validate(snapshot_data)
    result = assess_execution_readiness(
        readiness_request(),
        snapshot,
        readiness_risk(),
        readiness_switch(),
        {
            "allowed": True,
            "verdict_id": "verdict-001",
            "action": "submit_order",
            "expires_at": readiness_risk().expires_at.isoformat(),
        },
        {
            "route_snapshot": Decimal(30),
            "risk_decision": Decimal(30),
            "kill_switch": Decimal(30),
        },
    )
    assert result.status == "success"
    assert result.data is not None
    assert "ROUTE_EVIDENCE_UNAVAILABLE" in result.data.failed_check_codes
