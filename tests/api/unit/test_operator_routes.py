"""Governed operator route tests."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.services.api import CriticalAlertSink
from app.services.api.identity import require_auth_context
from app.services.api.routes import operator
from app.services.api.routes.operator import router
from app.services.risk import ApprovalAttestation, KillSwitchCommand, KillSwitchState
from app.utils import AuthContext
from fastapi import FastAPI

from tests.api._support import get_json, post_json

NOW = datetime(2026, 7, 24, 9, tzinfo=UTC)
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


def _auth(*, principal_id: str = "operator-1") -> AuthContext:
    """Build one fully authorized human operator.

    Args:
        principal_id: Authenticated operator identity.

    Returns:
        Valid shared authentication context.
    """
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id=principal_id,
        principal_type="USER",
        roles=("risk_operator",),
        permissions=(
            "risk.kill.activate",
            "risk.kill.clear",
            "ops:read",
            "ops:audit:read",
            "ops:events:read",
        ),
        scopes=("risk",),
        tenant_or_environment="simulation",
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        issued_at=NOW,
    )


def _state(
    state: Literal["active", "inactive", "unknown"] = "active",
) -> KillSwitchState:
    """Build one canonical global state.

    Args:
        state: Active or inactive state value.

    Returns:
        Canonical Risk state.
    """
    return KillSwitchState(
        state_id=f"global-{state}-2",
        scope_level="global",
        scope={},
        state=state,
        reason="operator action",
        version=2,
        updated_at=NOW,
    )


def _app(
    transition: Callable[
        [KillSwitchCommand, AuthContext, ApprovalAttestation | None],
        KillSwitchState,
    ],
    *,
    sink: CriticalAlertSink | None = None,
) -> FastAPI:
    """Build one fully composed operator test application.

    Args:
        transition: Injected canonical Risk transition.
        sink: Optional alert recorder accepting the idempotency keyword.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[operator._kill_switch_transition] = lambda: transition
    if sink is not None:
        app.dependency_overrides[operator._critical_alert_sink] = lambda: sink
    app.dependency_overrides[operator._readiness_source] = lambda: (
        lambda auth: {"status": "ready", "environment": auth.tenant_or_environment}
    )

    def audit_source(auth: AuthContext, limit: int) -> tuple[()]:
        """Return an empty bounded audit page."""
        del auth, limit
        return ()

    def event_source(auth: AuthContext) -> tuple[()]:
        """Return an empty bounded event page."""
        del auth
        return ()

    app.dependency_overrides[operator._audit_source] = lambda: audit_source
    app.dependency_overrides[operator._event_source] = lambda: event_source
    return app


def _payload(action: str = "activate") -> dict[str, object]:
    """Build one global operator request payload.

    Args:
        action: Requested transition action.

    Returns:
        JSON-compatible request payload.
    """
    return {
        "action": action,
        "scope_level": "global",
        "portfolio_id": None,
        "strategy_id": None,
        "symbol": None,
        "reason": "operator safety stop",
        "requested_at": NOW.isoformat(),
        "attestation": None,
    }


def test_kill_switch_scope_and_clearance_attestation_are_required() -> None:
    """Verify missing scoped identity and clearance evidence fail before Risk."""
    calls: list[KillSwitchCommand] = []

    def transition(
        command: KillSwitchCommand,
        auth: AuthContext,
        attestation: ApprovalAttestation | None,
    ) -> KillSwitchState:
        """Record an unexpected Risk delegation."""
        del auth, attestation
        calls.append(command)
        return _state()

    app = _app(transition)
    missing_scope = _payload()
    missing_scope["scope_level"] = "portfolio"
    status_code, _ = post_json(app, "/api/operator/kill-switch", missing_scope)
    assert status_code == 422

    status_code, body = post_json(
        app,
        "/api/operator/kill-switch",
        _payload("clear"),
    )
    assert status_code == 422
    assert body["detail"] == "CLEARANCE_ATTESTATION_REQUIRED"
    assert calls == []


def test_kill_switch_clearance_requires_distinct_principals() -> None:
    """Verify same-principal clearance is rejected before Risk delegation."""
    calls: list[KillSwitchCommand] = []

    def transition(
        command: KillSwitchCommand,
        auth: AuthContext,
        attestation: ApprovalAttestation | None,
    ) -> KillSwitchState:
        """Record an unexpected Risk delegation."""
        del auth, attestation
        calls.append(command)
        return _state("inactive")

    attestation = ApprovalAttestation(
        attestation_id="attestation-clear-1",
        principal_id="operator-1",
        action="risk.kill.clear",
        scope={"global": "*"},
        policy_ref="policy-hash",
        policy_version="policy-1",
        issued_at=NOW - timedelta(seconds=1),
        expires_at=NOW + timedelta(minutes=1),
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
    )
    payload = _payload("clear")
    payload["attestation"] = attestation.model_dump(mode="json")

    status_code, body = post_json(
        _app(transition),
        "/api/operator/kill-switch",
        payload,
    )

    assert status_code == 403
    assert body["detail"] == "DISTINCT_PRINCIPAL_REQUIRED"
    assert calls == []


def test_activation_delegates_exact_command_and_surfaces_alert_delivery() -> None:
    """Verify activation delegates immediately and reports one alert attempt."""
    commands: list[KillSwitchCommand] = []
    deliveries: list[str] = []

    def transition(
        command: KillSwitchCommand,
        auth: AuthContext,
        attestation: ApprovalAttestation | None,
    ) -> KillSwitchState:
        """Return owner truth after recording exact command context."""
        assert auth.principal_id == "operator-1"
        assert attestation is None
        commands.append(command)
        return _state()

    def sink(value: object, *, idempotency_key: str) -> None:
        """Record one channel-neutral delivery."""
        del value
        deliveries.append(idempotency_key)

    status_code, body = post_json(
        _app(transition, sink=sink),
        "/api/operator/kill-switch",
        _payload(),
    )

    assert status_code == 200, body
    assert commands[0].request_id == REQUEST_ID
    assert commands[0].scope_level == "global"
    assert body["state"]["state"] == "active"
    assert body["delivery"]["status"] == "delivered"
    assert deliveries == [body["alert"]["alert_id"]]


def test_protected_read_views_delegate_without_direct_storage_access() -> None:
    """Verify readiness, audit, and events require the injected owner views."""

    def transition(
        command: KillSwitchCommand,
        auth: AuthContext,
        attestation: ApprovalAttestation | None,
    ) -> KillSwitchState:
        """Provide an unused transition dependency."""
        del command, auth, attestation
        return _state()

    app = _app(transition)

    readiness_status, readiness = get_json(app, "/api/operator/readiness")
    audit_status, audit = get_json(
        app,
        "/api/operator/audit-events",
        query_string="limit=10",
    )
    event_status, events = get_json(app, "/api/operator/events")

    assert (readiness_status, readiness) == (
        200,
        {"status": "ready", "environment": "simulation"},
    )
    assert (audit_status, audit) == (200, [])
    assert (event_status, events) == (200, [])
