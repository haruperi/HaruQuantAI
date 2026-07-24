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
from app.services.trading import (
    AuthoritySnapshot,
    TradingError,
    TradingRequest,
    resume_strategy,
)
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


def _kill_switch_hierarchy(
    request_value: TradingRequest,
    global_state: KillSwitchState,
) -> tuple[KillSwitchState, ...]:
    """Build the exact applicable hierarchy around the real global state."""
    states = [
        global_state,
        KillSwitchState(
            state_id="strategy-state-1",
            scope_level="strategy",
            scope={"strategy_id": request_value.strategy_id},
            state="inactive",
            reason="normal operation",
            version=1,
            updated_at=request_value.system_time,
        ),
    ]
    if request_value.portfolio_id is not None:
        states.append(
            KillSwitchState(
                state_id="portfolio-state-1",
                scope_level="portfolio",
                scope={"portfolio_id": request_value.portfolio_id},
                state="inactive",
                reason="normal operation",
                version=1,
                updated_at=request_value.system_time,
            )
        )
    if request_value.symbol is not None:
        states.append(
            KillSwitchState(
                state_id="symbol-state-1",
                scope_level="symbol",
                scope={"symbol": request_value.symbol},
                state="inactive",
                reason="normal operation",
                version=1,
                updated_at=request_value.system_time,
            )
        )
    return tuple(states)


def test_operator_activation_halts_and_clearance_requires_reconciliation() -> None:
    """Execute UI/API → Risk → Trading → UI/API activation and recovery."""
    workflow_now = risk_support.NOW
    trading_request = request(
        action="resume_strategy",
        system_time=workflow_now,
        valid_until=workflow_now + timedelta(minutes=10),
    )
    resume_policy = policy("resume_strategy").model_copy(
        update={
            "issued_at": workflow_now - timedelta(minutes=1),
            "expires_at": workflow_now + timedelta(minutes=10),
        }
    )
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
            now=workflow_now,
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
        "requested_at": workflow_now.isoformat(),
        "attestation": None,
    }

    active_status, active_body = post_json(
        app,
        "/api/operator/kill-switch",
        payload,
    )

    def current_states(value: TradingRequest) -> tuple[KillSwitchState, ...]:
        """Return the current canonical Risk state hierarchy."""
        return _kill_switch_hierarchy(value, current[0])

    active_dependencies = replace(
        dependencies(action_policy=resume_policy),
        kill_switch_state_source=current_states,
        clock=lambda: workflow_now,
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
        issued_at=workflow_now,
        expires_at=workflow_now + timedelta(minutes=1),
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
    trading_store.projection = projection().model_copy(
        update={"updated_at": workflow_now}
    )

    def reconciled_authority(value: TradingRequest) -> AuthoritySnapshot:
        """Return matching current route authority evidence."""
        del value
        return authority().model_copy(
            update={
                "observed_at": workflow_now,
                "expires_at": workflow_now + timedelta(minutes=5),
            }
        )

    recovered_dependencies = replace(
        dependencies(
            store=trading_store,
            action_policy=resume_policy,
        ),
        kill_switch_state_source=current_states,
        reconciliation_source=reconciled_authority,
        clock=lambda: workflow_now,
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
