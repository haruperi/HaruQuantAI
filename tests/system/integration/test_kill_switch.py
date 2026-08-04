"""SYS-WF-005 operator monitoring and kill-switch integration."""

import asyncio
from dataclasses import replace
from datetime import timedelta
from typing import Any

from app.services.api.routes.operator import router
from app.services.risk import (
    apply_kill_switch_command,
    check_risk_kill_switch,
    compute_config_hash,
    create_approval_attestation,
    create_kill_switch_command,
    create_kill_switch_state,
    create_risk_audit_chain,
    get_decision_state,
)
from app.services.trading import resume_strategy
from app.utils import canonical_json

from tests.risk import _support as risk_support
from tests.trading.unit.actions.test_controls import authority, projection
from tests.trading.unit.actions.test_dependencies import (
    MemoryStore,
    dependencies,
    policy,
    request,
)

# Private type-only aliases; Risk exposes functions, not contract classes.
ApprovalAttestation = object
AuthoritySnapshot = Any
KillSwitchCommand = object
KillSwitchState = object
TradingRequest = Any
AuthContext = Any


def _kill_switch_hierarchy(
    request_value: TradingRequest,
    global_state: KillSwitchState,
) -> tuple[KillSwitchState, ...]:
    """Build the exact applicable hierarchy around the real global state."""
    states = [
        global_state,
        create_kill_switch_state(
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
            create_kill_switch_state(
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
            create_kill_switch_state(
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
    audit = create_risk_audit_chain(
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
        current[0] = risk_support.unwrap_risk_response(
            apply_kill_switch_command(
                command,
                current[0],
                auth,
                approvals,
                audit,
                risk_store,
                config,
                attestation=attestation,
                now=workflow_now,
            ),
            operation="apply_kill_switch_command",
        )
        return current[0]

    def sink(value: object, *, idempotency_key: str) -> None:
        """Record the one required activation delivery attempt."""
        del value
        alert_attempts.append(idempotency_key)

    assert "/api/v1/operator/kill-switch" not in {route.path for route in router.routes}
    auth = risk_support._auth(config, clearance=True)
    active_command = create_kill_switch_command(
        action="activate",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="operator safety stop",
        requested_at=workflow_now,
        request_id=risk_support.REQUEST_ID,
        workflow_id=risk_support.WORKFLOW_ID,
        correlation_id=risk_support.CORRELATION_ID,
    )
    active_state = transition(active_command, auth, None)
    sink(active_state, idempotency_key=f"kill-switch:{active_state.state_id}:active")

    def current_states(value: TradingRequest) -> tuple[KillSwitchState, ...]:
        """Return the current canonical Risk state hierarchy."""
        return _kill_switch_hierarchy(value, current[0])

    active_dependencies = replace(
        dependencies(action_policy=resume_policy),
        kill_switch_state_source=current_states,
        clock=lambda: workflow_now,
    )

    blocked = asyncio.run(resume_strategy(trading_request, active_dependencies))
    assert blocked.status == "error"
    assert blocked.error is not None
    assert blocked.error.code == "KILL_SWITCH_ACTIVE"

    attestation = create_approval_attestation(
        attestation_id="clearance-independent-1",
        principal_id="operator-2",
        action="risk.kill.clear",
        scope={"global": "*"},
        policy_ref=risk_support.unwrap_risk_response(
            compute_config_hash(config),
            operation="compute_config_hash",
        ),
        policy_version=config.policy_version,
        issued_at=workflow_now,
        expires_at=workflow_now + timedelta(minutes=1),
        request_id=risk_support.REQUEST_ID,
        workflow_id=risk_support.WORKFLOW_ID,
        correlation_id=risk_support.CORRELATION_ID,
    )
    clear_command = create_kill_switch_command(
        action="clear",
        scope_level="global",
        portfolio_id=None,
        strategy_id=None,
        symbol=None,
        reason="reconciled and independently approved",
        requested_at=workflow_now,
        request_id=risk_support.REQUEST_ID,
        workflow_id=risk_support.WORKFLOW_ID,
        correlation_id=risk_support.CORRELATION_ID,
    )
    clear_state = transition(clear_command, auth, attestation)
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
    risk_recovery = risk_support.unwrap_risk_response(
        check_risk_kill_switch(
            (current[0],),
            {"portfolio_id": "portfolio-1", "symbol": "EURUSD"},
            config,
            risk_support._auth(config),
            reconciled=True,
            now=risk_support.NOW,
        ),
        operation="check_risk_kill_switch",
    )

    assert active_state.state == "active"
    assert len(alert_attempts) == 1
    assert clear_state.state == "inactive"
    assert resumed.status == "success"
    assert risk_recovery.state is get_decision_state("APPROVE")
    assert len(risk_store.records) == 2
