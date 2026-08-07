"""Integration tests for Portfolio package-root compatibility with Risk contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.risk import (
    create_allocation_risk_decision,
    create_kill_switch_state,
    create_strategy_operational_eligibility_decision,
    get_decision_state,
)


def test_portfolio_consumes_risk_allocation_eligibility_contracts() -> None:
    """Verify Portfolio package-root acceptance of Risk allocation and eligibility contracts."""
    now = datetime.now(UTC)

    alloc = create_allocation_risk_decision(
        decision_id="alloc-dec-1",
        portfolio_id="port-1",
        reviewed_version="v1.0",
        state=get_decision_state("approve"),
        capped_weights={"strategy-1": Decimal("0.5")},
        risk_budget_projection={"max_drawdown": Decimal("0.05")},
        conditions=(),
        policy_version="v1",
        evidence_refs={"market": "ev-1"},
        issued_at=now,
        expires_at=now + timedelta(days=1),
        active=True,
        predecessor_version=None,
        audit_ref="aud-1",
    )
    assert alloc.portfolio_id == "port-1"
    assert alloc.state == get_decision_state("approve")
    assert alloc.contract_version == "v1"
    assert alloc.schema_id == "risk.allocation_risk_decision.v1"

    elig = create_strategy_operational_eligibility_decision(
        decision_id="elig-dec-1",
        strategy_id="strat-1",
        strategy_version="1.0.0",
        scope={"symbol": "EURUSD"},
        state=get_decision_state("approve"),
        conditions=(),
        policy_version="v1",
        evidence_refs={"market": "ev-1"},
        issued_at=now,
        expires_at=now + timedelta(days=30),
        suspended=False,
        audit_ref="aud-1",
    )
    assert elig.decision_id == "elig-dec-1"
    assert elig.state == get_decision_state("approve")
    assert elig.contract_version == "v1"
    assert elig.schema_id == "risk.strategy_operational_eligibility_decision.v1"

    ks = create_kill_switch_state(
        state_id="ks-1",
        scope_level="portfolio",
        scope={"portfolio_id": "port-1"},
        state="inactive",
        version=1,
        reason="normal operations",
        updated_at=now,
    )
    assert ks.scope_level == "portfolio"
    assert ks.contract_version == "v1"
    assert ks.schema_id == "risk.kill_switch_state.v1"


def test_portfolio_rejects_incompatible_risk_contract_version() -> None:
    """Verify that Portfolio rejects Risk allocation decisions with incompatible schema versions or shapes."""
    import pytest
    from pydantic import ValidationError

    raw_invalid = {
        "contract_version": "v2",  # Incompatible version
        "decision_id": "alloc-dec-1",
        "portfolio_id": "port-1",
        "reviewed_version": "v1.0",
        "state": "approve",
        "capped_weights": {"strategy-1": "0.5"},
        "risk_budget_projection": {},
        "conditions": [],
        "policy_version": "v1",
        "evidence_refs": {},
        "issued_at": datetime.now(UTC).isoformat(),
        "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "active": True,
        "audit_ref": "aud-1",
    }
    with pytest.raises(ValidationError):
        create_allocation_risk_decision(**raw_invalid)
