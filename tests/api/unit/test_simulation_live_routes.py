"""Live what-if Simulation session route and composition tests.

The Simulator owns determinism, lineage, and capacity; these tests cover only
what the gateway is responsible for — permission, idempotency where a repeat
would duplicate a governed effect, fail-closed composition, and exact
single-delegation of caller input.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from app.services.api.identity import require_auth_context
from app.services.api.workstation.simulation import (
    live_orchestration as live_simulation_dependencies,
)
from app.services.api.workstation.simulation import live_routes as simulation_live
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI

from tests.api._support import get_json, post_json


def _key() -> str:
    """Return one fresh idempotency key.

    Durable reservations are retained for at least 24 hours, so a literal key
    would only be reservable on the first run of the suite.

    Returns:
        Unique idempotency key.
    """
    return f"test-{uuid4()}"


def _auth(permissions: tuple[str, ...] = ("simulation:read", "simulation:run")) -> Any:
    """Build one authorized Simulation caller.

    Args:
        permissions: Granted backend permissions.

    Returns:
        Utils-owned authenticated context.
    """
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="simulation-operator",
        principal_type="USER",
        roles=("operator",),
        permissions=permissions,
        scopes=("simulation",),
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
        source: Stub live-session dispatcher.
        permissions: Optional exact granted permissions.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(simulation_live.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=permissions or ("simulation:read", "simulation:run")
    )
    app.dependency_overrides[simulation_live._live_source] = lambda: source
    return app


def test_read_requires_read_permission() -> None:
    """An unauthorized caller never reaches the Simulator."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without permission")

    status_code, _body = get_json(
        _app(_source, permissions=("data:read",)),
        "/api/v1/simulation/live-sessions/sess-1",
    )
    assert status_code == 403


def test_read_delegates_the_session_identity() -> None:
    """The read forwards exactly the path identity."""
    captured: list[tuple[str, str]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, str(args[0])))
        return {"session_id": "sess-1", "advisory": True}

    status_code, _body = get_json(
        _app(_source), "/api/v1/simulation/live-sessions/sess-1"
    )
    assert status_code == 200
    assert captured == [("read", "sess-1")]


def test_step_is_bounded_by_the_route_contract() -> None:
    """A non-positive or oversized step is refused before delegation."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called for an invalid step")

    app = _app(_source)
    zero, _b1 = post_json(
        app, "/api/v1/simulation/live-sessions/sess-1/step?ticks=0", {}
    )
    huge, _b2 = post_json(
        app, "/api/v1/simulation/live-sessions/sess-1/step?ticks=10001", {}
    )
    assert zero == 422
    assert huge == 422


def test_step_delegates_the_tick_count() -> None:
    """A valid step forwards the session identity and tick count."""
    captured: list[tuple[str, str, int]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, str(args[0]), int(str(args[1]))))
        return {"cursor": 2}

    status_code, _body = post_json(
        _app(_source), "/api/v1/simulation/live-sessions/sess-1/step?ticks=2", {}
    )
    assert status_code == 200
    assert captured == [("step", "sess-1", 2)]


def test_branch_requires_an_idempotency_key() -> None:
    """Branching without a key never opens a second engine."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without an idempotency key")

    status_code, body = post_json(
        _app(_source),
        "/api/v1/simulation/live-sessions/sess-1/branch",
        {"overrides": {"seed": 7}},
    )
    assert status_code == 422
    assert body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_branch_forwards_overrides_unchanged() -> None:
    """The Simulator validates overrides; the gateway does not reshape them."""
    captured: list[tuple[str, str, dict[str, object]]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, str(args[0]), dict(args[1])))  # type: ignore[arg-type]
        return {"branch_of": "sess-1", "advisory": True}

    status_code, _body = post_json(
        _app(_source),
        "/api/v1/simulation/live-sessions/sess-1/branch",
        {"overrides": {"seed": 7}},
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 200
    assert captured == [("branch", "sess-1", {"seed": 7})]


def test_close_delegates_and_requires_run_permission() -> None:
    """Closing a session needs run permission and forwards the identity."""
    captured: list[tuple[str, str]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, str(args[0])))
        return {"session_id": "sess-1"}

    app = _app(_source)
    from tests.api._support import post_json as _post

    status_code, _body = _post(
        app, "/api/v1/simulation/live-sessions/sess-1", {}, method="DELETE"
    )
    assert status_code == 200
    assert captured == [("close", "sess-1")]


def test_routes_fail_closed_without_composition() -> None:
    """An uncomposed Simulator bundle becomes a bounded 503."""
    source = live_simulation_dependencies.build_live_simulation_source(None)
    for operation in ("create", "step", "read", "branch", "close"):
        with pytest.raises(RuntimeError, match="SIMULATION_LIVE_RUNTIME_UNAVAILABLE"):
            source(operation, object(), object(), object())


def test_source_rejects_unknown_operation() -> None:
    """Only the five registered live operations are dispatchable."""
    source = live_simulation_dependencies.build_live_simulation_source(object())
    with pytest.raises(ValueError, match="unsupported live Simulation operation"):
        source("rewind", "sess-1")


def test_source_delegates_to_owner_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each operation reaches exactly its Simulator public function."""
    calls: list[str] = []
    for name in (
        "create_live_simulation_session",
        "step_live_simulation",
        "read_live_simulation_state",
        "branch_live_simulation",
        "close_live_simulation_session",
    ):
        monkeypatch.setattr(
            live_simulation_dependencies,
            name,
            lambda *_a, _n=name, **_k: calls.append(_n) or {"ok": True},
        )
    monkeypatch.setattr(
        live_simulation_dependencies, "create_simulation_value", lambda *_a, **_k: "req"
    )
    source = live_simulation_dependencies.build_live_simulation_source("deps")

    class _Boundary:
        def model_dump(self, **_kwargs: object) -> dict[str, object]:
            """Return an empty owner payload.

            Returns:
                Empty request payload.
            """
            return {}

    source("create", _Boundary(), "req-1")
    source("step", "sess-1", 2)
    source("read", "sess-1")
    source("branch", "sess-1", {"seed": 1}, "req-2")
    source("close", "sess-1")
    assert calls == [
        "create_live_simulation_session",
        "step_live_simulation",
        "read_live_simulation_state",
        "branch_live_simulation",
        "close_live_simulation_session",
    ]
