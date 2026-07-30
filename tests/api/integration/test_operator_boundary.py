"""Operator HTTP boundary integration with canonical Risk authority."""

from datetime import timedelta

from app.services.api.identity import require_auth_context
from app.services.api.routes import operator
from app.services.api.routes.operator import router
from app.services.risk import (
    apply_kill_switch_command,
    compute_config_hash,
    create_approval_attestation,
    create_risk_audit_chain,
)
from app.utils import AuthContext, canonical_json
from fastapi import FastAPI

from tests.api._support import post_json
from tests.risk import _support as risk_support

# Private type-only aliases; Risk exposes functions, not contract classes.
ApprovalAttestation = object
KillSwitchCommand = object
KillSwitchState = object


def test_operator_kill_switch() -> None:
    """Verify activation and distinct-principal clearance delegate to real Risk."""
    config = risk_support._config()
    _, approvals, _ = risk_support._services(config)
    store = risk_support._KillStore()
    audit = create_risk_audit_chain(
        config, store, lambda: risk_support.NOW, canonical_json
    )
    current = [risk_support._inactive_state()]
    alerts: list[str] = []

    def transition(
        command: KillSwitchCommand,
        auth: AuthContext,
        attestation: ApprovalAttestation | None,
    ) -> KillSwitchState:
        """Apply one command through the canonical Risk transition."""
        current[0] = apply_kill_switch_command(
            command,
            current[0],
            auth,
            approvals,
            audit,
            store,
            config,
            attestation=attestation,
            now=risk_support.NOW,
        )
        return current[0]

    def sink(value: object, *, idempotency_key: str) -> None:
        """Record one deterministic activation alert."""
        del value
        alerts.append(idempotency_key)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth_context] = lambda: risk_support._auth(
        config,
        clearance=True,
    )
    app.dependency_overrides[operator._kill_switch_transition] = lambda: transition
    app.dependency_overrides[operator._critical_alert_sink] = lambda: sink

    activation = {
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
        activation,
    )

    attestation = create_approval_attestation(
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
        **activation,
        "action": "clear",
        "reason": "reconciled and independently approved",
        "attestation": attestation.model_dump(mode="json"),
    }
    clear_status, clear_body = post_json(
        app,
        "/api/operator/kill-switch",
        clearance,
    )

    assert active_status == 200, active_body
    assert active_body["state"]["state"] == "active"
    assert clear_status == 200, clear_body
    assert clear_body["state"]["state"] == "inactive"
    assert len(alerts) == 1
    assert len(store.records) == 2
    assert store.state == current[0]
