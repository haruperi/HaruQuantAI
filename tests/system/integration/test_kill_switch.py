"""SYS-WF-005 operator monitoring and kill-switch integration."""

import asyncio
from dataclasses import replace
from datetime import timedelta

import pytest
from app.services.api.identity import require_auth_context
from app.services.api.routes import operator
from app.services.api.routes.operator import router
from app.services.risk import (
    ApprovalAttestation,
    DecisionState,
    KillSwitchCommand,
    KillSwitchState,
    RiskAuditChain,
    apply_kill_switch_command,
    check_risk_kill_switch,
    compute_config_hash,
)
from app.services.trading.actions import resume_strategy
from app.services.trading.contracts import TradingError, TradingRequest
from app.services.trading.reconciliation import AuthoritySnapshot
from app.utils import AuthContext, canonical_json
from fastapi import FastAPI

from tests.api._support import post_json
from tests.risk import _support as risk_support
from tests.trading.unit.actions.test_controls import authority, projection
from tests.trading.unit.actions.test_dependencies import (
    MemoryStore,
    dependencies,
    policy,
    request,
)


def test_operator_activation_halts_and_clearance_requires_reconciliation() -> None:
    """Execute UI/API → Risk → Trading → UI/API activation and recovery."""
    config = risk_support._config()
    _, approvals, _ = risk_support._services(config)
    risk_store = risk_support._KillStore()
    audit = RiskAuditChain(
        config,
        risk_store,
        lambda: risk_support.NOW,
        canonical_json,
    )
    current = [risk_support._inactive_state()]
    alert_attempts: list[str] = []

    def transition(
        command: KillSwitchCommand,
        auth: AuthContext,
        attestation: ApprovalAttestation | None,
    ) -> KillSwitchState:
        """Apply the command through real Risk authority and persistence."""
        current[0] = apply_kill_switch_command(
            command,
            current[0],
            auth,
            approvals,
            audit,
            risk_store,
            config,
            attestation=attestation,
            now=risk_support.NOW,
        )
        return current[0]

    def sink(value: object, *, idempotency_key: str) -> None:
        """Record the one required activation delivery attempt."""
        del value
        alert_attempts.append(idempotency_key)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth_context] = lambda: risk_support._auth(
        config,
        clearance=True,
    )
    app.dependency_overrides[operator._kill_switch_transition] = lambda: transition
    app.dependency_overrides[operator._critical_alert_sink] = lambda: sink
    payload = {
        "action": "activate",
        "scope_level": "global",
        "portfolio_id": None,
        "strategy_id": None,
        "symbol": None,
        "reason": "operator safety stop",
        "requested_at": risk_support.NOW.isoformat(),
        "attestation": None,
    }

    active_status, active_body = post_json(
        app,
        "/api/operator/kill-switch",
        payload,
    )
    trading_request = request(action="resume_strategy")

    def current_states(value: TradingRequest) -> tuple[KillSwitchState, ...]:
        """Return the current canonical Risk state hierarchy."""
        del value
        return (current[0],)

    active_dependencies = replace(
        dependencies(action_policy=policy("resume_strategy")),
        kill_switch_state_source=current_states,
    )

    with pytest.raises(TradingError, match="KILL_SWITCH_ACTIVE"):
        asyncio.run(resume_strategy(trading_request, active_dependencies))

    attestation = ApprovalAttestation(
        attestation_id="clearance-independent-1",
        principal_id="operator-2",
        action="risk.kill.clear",
        scope={"global": "*"},
        policy_ref=compute_config_hash(config),
        policy_version=config.policy_version,
        issued_at=risk_support.NOW,
        expires_at=risk_support.NOW + timedelta(minutes=1),
        request_id=risk_support.REQUEST_ID,
        workflow_id=risk_support.WORKFLOW_ID,
        correlation_id=risk_support.CORRELATION_ID,
    )
    clearance = {
        **payload,
        "action": "clear",
        "reason": "reconciled and independently approved",
        "attestation": attestation.model_dump(mode="json"),
    }
    clear_status, clear_body = post_json(
        app,
        "/api/operator/kill-switch",
        clearance,
    )
    trading_store = MemoryStore()
    trading_store.projection = projection()

    def reconciled_authority(value: TradingRequest) -> AuthoritySnapshot:
        """Return matching current route authority evidence."""
        del value
        return authority()

    recovered_dependencies = replace(
        dependencies(
            store=trading_store,
            action_policy=policy("resume_strategy"),
        ),
        kill_switch_state_source=current_states,
        reconciliation_source=reconciled_authority,
    )
    resumed = asyncio.run(resume_strategy(trading_request, recovered_dependencies))
    risk_recovery = check_risk_kill_switch(
        (current[0],),
        {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
        config,
        risk_support._auth(config),
        reconciled=True,
        now=risk_support.NOW,
    )

    assert active_status == 200, active_body
    assert active_body["state"]["state"] == "active"
    assert len(alert_attempts) == 1
    assert clear_status == 200, clear_body
    assert clear_body["state"]["state"] == "inactive"
    assert resumed.status == "success"
    assert risk_recovery.state is DecisionState.APPROVE
    assert len(risk_store.records) == 2
