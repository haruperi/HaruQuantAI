"""Trading consumer compatibility tests for package-root Risk contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.risk import (
    create_action_policy_verdict,
    create_kill_switch_state,
    create_risk_decision_package,
    get_decision_state,
)
from app.services.trading import (
    assess_execution_readiness,
    create_route_snapshot,
    create_trading_request,
)
from pydantic import ValidationError

NOW = datetime(2026, 8, 6, 8, 0, tzinfo=UTC)
BOUNDS = {
    "route_snapshot": Decimal(30),
    "risk_decision": Decimal(30),
    "kill_switch": Decimal(30),
}


def _request() -> object:
    """Build the Trading request that consumes Risk authority references."""
    return create_trading_request(
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route="sim",
        action="submit_order",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity=Decimal("1.00"),
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="compatibility-key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _decision(*, expires_at: datetime | None = None) -> object:
    """Build a producer-owned approving Risk decision."""
    resolved_expiry = expires_at or NOW + timedelta(minutes=1)
    issued_at = min(NOW, resolved_expiry - timedelta(minutes=1))
    return create_risk_decision_package(
        decision_id="risk-001",
        intent_id="intent-001",
        state=get_decision_state("APPROVE"),
        requested_size=Decimal("1.00"),
        approved_size=Decimal("1.00"),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"portfolio": "snapshot-001"},
        config_hash="a" * 64,
        concurrency_disclosure="risk-store",
        recommendations=(),
        issued_at=issued_at,
        expires_at=resolved_expiry,
        token=None,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _switch(*, state: str = "inactive") -> object:
    """Build producer-owned kill-switch evidence."""
    return create_kill_switch_state(
        state_id="switch-001",
        scope_level="global",
        scope={},
        state=state,
        reason="compatibility-test",
        version=1,
        updated_at=NOW,
    )


def _verdict(*, allowed: bool = True) -> object:
    """Build a producer-owned action-policy verdict."""
    return create_action_policy_verdict(
        verdict_id="verdict-001",
        attestation_id="attestation-001",
        decision_id="risk-001",
        reservation_id="reservation-001",
        action="submit_order",
        allowed=allowed,
        reasons=() if allowed else ("policy-denied",),
        scope={"strategy_id": "strategy-001"},
        policy_version="v1",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _snapshot() -> object:
    """Build current route evidence required by the consumer."""
    return create_route_snapshot(
        route="sim",
        provider_id=None,
        account_id="account-001",
        symbol="EURUSD",
        facts={"permission": "allowed"},
        source_id="data-source-001",
        authority_id="simulator",
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        available=True,
        fresh=True,
        capabilities=("submit_order",),
    )


def _policy_projection(verdict: object) -> dict[str, object]:
    """Project the documented Risk verdict into Trading readiness input."""
    return {
        "allowed": verdict.allowed,
        "verdict_id": verdict.verdict_id,
        "action": verdict.action,
        "expires_at": verdict.expires_at.isoformat(),
    }


def test_trading_readiness_consumes_compatible_risk_contracts() -> None:
    """Compatible producer contracts pass the real Trading readiness operation."""
    verdict = _verdict()
    response = assess_execution_readiness(
        _request(),
        _snapshot(),
        _decision(),
        _switch(),
        _policy_projection(verdict),
        BOUNDS,
    )

    assert response.status == "success"
    assert response.data is not None
    assert response.data.passed is True
    assert response.data.failed_check_codes == ()


@pytest.mark.parametrize(
    ("decision", "switch", "verdict", "failure_code"),
    [
        (_decision(expires_at=NOW), _switch(), _verdict(), "RISK_DECISION_STALE"),
        (_decision(), _switch(state="active"), _verdict(), "KILL_SWITCH_BLOCKING"),
        (_decision(), _switch(), _verdict(allowed=False), "ACTION_POLICY_DENIED"),
    ],
)
def test_trading_readiness_fails_closed_on_risk_contract_state(
    decision: object,
    switch: object,
    verdict: object,
    failure_code: str,
) -> None:
    """Valid but non-authorizing Risk states are rejected by Trading."""
    response = assess_execution_readiness(
        _request(),
        _snapshot(),
        decision,
        switch,
        _policy_projection(verdict),
        BOUNDS,
    )

    assert response.status == "success"
    assert response.data is not None
    assert response.data.passed is False
    assert failure_code in response.data.failed_check_codes


def test_risk_producer_rejects_incompatible_contract_version() -> None:
    """The producer rejects a contract version Trading does not support."""
    with pytest.raises(ValidationError):
        create_risk_decision_package(
            contract_version="v2",
            decision_id="risk-001",
            intent_id="intent-001",
            state="approve",
            requested_size="1.0",
            approved_size="1.0",
            ordered_checks=(),
            primary_failure_limit=None,
            composite_breach_flags=(),
            evidence_refs={},
            config_hash="a" * 64,
            concurrency_disclosure="none",
            recommendations=(),
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=5),
            token=None,
            request_id="req-11111111-1111-4111-8111-111111111111",
            workflow_id="wf-22222222-2222-4222-8222-222222222222",
            correlation_id="cor-33333333-3333-4333-8333-333333333333",
        )
