"""Governed Risk kill-switch command bridge and route boundary tests.

Kill-switch and decision reads are covered by ``test_risk_routes.py``. These
tests cover the single governed Risk write: permission, idempotency, the
mandatory approval attestation, fail-closed composition, and the fact that the
gateway never decides or fabricates canonical safety state.
"""

from __future__ import annotations

from typing import Any, ClassVar
from uuid import uuid4

import pytest
from app.contracts.common.models import create_auth_context
from app.kernel.time import utc_now
from app.services.api.identity import require_auth_context
from app.services.api.widgets.risk import orchestration as risk_dependencies
from app.services.api.widgets.risk import routes as risk
from fastapi import FastAPI

from tests.api._support import post_json


def _key() -> str:
    """Return one fresh idempotency key.

    Durable reservations are retained for at least 24 hours, so a literal key
    would only be reservable on the first run of the suite. A unique key per
    call keeps these tests hermetic.

    Returns:
        Unique idempotency key.
    """
    return f"test-{uuid4()}"


_COMMAND = {
    "scope_level": "global",
    "scope": {"tenant": "dev"},
    "command": {"action": "activate", "reason": "operator drill"},
    "attestation": {"attestation_id": "att-1"},
}


def _auth(permissions: tuple[str, ...] = ("risk:read", "risk:kill_switch")) -> Any:
    """Build one authorized Risk operator.

    Args:
        permissions: Granted backend permissions.

    Returns:
        Utils-owned authenticated context.
    """
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="risk-operator",
        principal_type="USER",
        roles=("operator",),
        permissions=permissions,
        scopes=("risk",),
        tenant_or_environment="development",
        runtime_profile="research",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def _app(source: Any, permissions: tuple[str, ...] | None = None) -> FastAPI:
    """Build one router-only application bound to a stub dispatcher.

    Args:
        source: Stub Risk command dispatcher.
        permissions: Optional exact granted permissions.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(risk.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=permissions or ("risk:read", "risk:kill_switch")
    )
    app.dependency_overrides[risk._risk_command_source] = lambda: source
    return app


def test_command_requires_idempotency_key() -> None:
    """A kill-switch command without an idempotency key never reaches Risk."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without an idempotency key")

    status_code, body = post_json(_app(_source), "/api/v1/risk/kill-switch", _COMMAND)
    assert status_code == 422
    assert body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_command_requires_kill_switch_permission() -> None:
    """Risk read permission alone never authorizes a safety transition."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without permission")

    status_code, _body = post_json(
        _app(_source, permissions=("risk:read",)),
        "/api/v1/risk/kill-switch",
        _COMMAND,
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 403


def test_command_requires_approval_attestation() -> None:
    """A command without attestation is refused before any owner call."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without attestation")

    payload = dict(_COMMAND)
    payload.pop("attestation")
    status_code, body = post_json(
        _app(_source),
        "/api/v1/risk/kill-switch",
        payload,
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 422
    assert body["detail"] == "GOVERNANCE_REQUIRED"


def test_command_delegates_once_with_attestation() -> None:
    """An authorized command delegates exactly once carrying its attestation."""
    captured: list[tuple[str, object]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, args[2]))
        return {"status": "active"}

    status_code, _body = post_json(
        _app(_source),
        "/api/v1/risk/kill-switch",
        _COMMAND,
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 200
    assert captured == [("kill_switch", {"attestation_id": "att-1"})]


def test_command_route_fails_closed_without_composition() -> None:
    """An uncomposed command bundle becomes a bounded 503."""

    def _source(operation: str, *args: object) -> object:
        raise RuntimeError("RISK_COMMAND_RUNTIME_UNAVAILABLE")

    status_code, body = post_json(
        _app(_source),
        "/api/v1/risk/kill-switch",
        _COMMAND,
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 503
    assert body["detail"] == "RISK_COMMAND_RUNTIME_UNAVAILABLE"


def test_source_fails_closed_without_bundle() -> None:
    """No composed authority means no kill-switch mutation is attempted."""
    source = risk_dependencies.build_risk_command_source(None)
    with pytest.raises(RuntimeError, match="RISK_COMMAND_RUNTIME_UNAVAILABLE"):
        source("kill_switch", object(), _auth(), None)


def test_source_fails_closed_on_incomplete_bundle() -> None:
    """A partially composed bundle is treated as no authority at all."""
    bundle = risk_dependencies.build_api_risk_dependencies(
        approvals="a", audit="b", store="c", config=None
    )
    source = risk_dependencies.build_risk_command_source(bundle)
    with pytest.raises(RuntimeError, match="RISK_COMMAND_RUNTIME_UNAVAILABLE"):
        source("kill_switch", object(), _auth(), None)


def test_source_rejects_unknown_operation() -> None:
    """Only the registered kill-switch command is dispatchable."""
    source = risk_dependencies.build_risk_command_source(None)
    with pytest.raises(ValueError, match="unsupported Risk operation"):
        source("clear_all", object(), _auth(), None)


def test_source_fails_closed_when_current_state_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing canonical state never becomes an invented starting point."""
    monkeypatch.setattr(
        risk_dependencies, "get_kill_switch_state", lambda _level, _scope: None
    )
    bundle = risk_dependencies.build_api_risk_dependencies(
        approvals="a", audit="b", store="c", config="d"
    )
    source = risk_dependencies.build_risk_command_source(bundle)

    class _Boundary:
        scope_level = "global"
        scope: ClassVar[dict[str, str]] = {"tenant": "dev"}
        command: ClassVar[dict[str, str]] = {"action": "activate"}

    with pytest.raises(RuntimeError, match="KILL_SWITCH_STATE_UNAVAILABLE"):
        source("kill_switch", _Boundary(), _auth(), None)


def test_source_forwards_current_state_and_ports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The dispatcher forwards owner state and every composed port unchanged."""
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        risk_dependencies, "get_kill_switch_state", lambda _level, _scope: "current"
    )
    monkeypatch.setattr(
        risk_dependencies, "create_kill_switch_command", lambda **values: values
    )

    def _apply(
        command: object, current: object, auth: object, *ports: object, **kw: object
    ) -> object:
        captured.update(command=command, current=current, ports=ports, kw=kw)
        return "new-state"

    monkeypatch.setattr(risk_dependencies, "apply_kill_switch_command", _apply)
    bundle = risk_dependencies.build_api_risk_dependencies(
        approvals="approvals", audit="audit", store="store", config="config"
    )
    source = risk_dependencies.build_risk_command_source(bundle)

    class _Boundary:
        scope_level = "global"
        scope: ClassVar[dict[str, str]] = {"tenant": "dev"}
        command: ClassVar[dict[str, str]] = {"action": "activate"}

    assert source("kill_switch", _Boundary(), _auth(), "attestation") == "new-state"
    assert captured["current"] == "current"
    assert captured["ports"] == ("approvals", "audit", "store", "config")
    assert captured["kw"]["attestation"] == "attestation"  # type: ignore[index]
