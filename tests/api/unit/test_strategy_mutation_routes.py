"""Governed Strategy mutation bridge and route boundary tests.

Catalogue and version reads are covered by ``test_strategy_routes.py``. These
tests cover the reintroduced governed mutation boundary: permission,
idempotency, identity binding, fail-closed composition, and exact delegation to
the Strategy public API.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from app.services.api.composition import strategy_dependencies
from app.services.api.identity import require_auth_context
from app.services.api.routes import strategies
from app.utils import create_auth_context, utc_now
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


def _auth(permissions: tuple[str, ...] = ("strategy:read", "strategy:write")) -> Any:
    """Build one authorized Strategy caller.

    Args:
        permissions: Granted backend permissions.

    Returns:
        Utils-owned authenticated context.
    """
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="strategy-operator",
        principal_type="USER",
        roles=("operator",),
        permissions=permissions,
        scopes=("strategy",),
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
        source: Stub Strategy mutation dispatcher.
        permissions: Optional exact granted permissions.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI()
    app.include_router(strategies.router)
    app.dependency_overrides[require_auth_context] = lambda: _auth(
        permissions=permissions or ("strategy:read", "strategy:write")
    )
    app.dependency_overrides[strategies._strategy_mutation_source] = lambda: source
    return app


def test_register_requires_idempotency_key() -> None:
    """Registration without an idempotency key never reaches Strategy."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without an idempotency key")

    status_code, body = post_json(
        _app(_source), "/api/v1/strategies", {"payload": {"strategy_id": "strat-1"}}
    )
    assert status_code == 422
    assert body["detail"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_register_requires_write_permission() -> None:
    """Read permission alone never authorizes a Strategy mutation."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called without permission")

    status_code, _body = post_json(
        _app(_source, permissions=("strategy:read",)),
        "/api/v1/strategies",
        {"payload": {"strategy_id": "strat-1"}},
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 403


def test_register_delegates_payload_unchanged() -> None:
    """The gateway forwards the caller payload without repairing a field."""
    captured: list[tuple[str, dict[str, object]]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, dict(args[0])))  # type: ignore[arg-type]
        return {"status": "success"}

    payload = {"strategy_id": "strat-1", "version": "1.0.0"}
    status_code, _body = post_json(
        _app(_source),
        "/api/v1/strategies",
        {"payload": payload},
        headers={"Idempotency-Key": _key()},
    )
    assert status_code == 200
    assert captured == [("register", payload)]


def test_update_parameters_rejects_identity_mismatch() -> None:
    """A path and payload that disagree on identity fail closed."""

    def _source(operation: str, *args: object) -> object:
        raise AssertionError("source must not be called on identity mismatch")

    status_code, body = post_json(
        _app(_source),
        "/api/v1/strategies/strat-1/parameters",
        {"payload": {"strategy_id": "other-strategy"}},
        headers={"Idempotency-Key": _key()},
        method="PATCH",
    )
    assert status_code == 422
    assert body["detail"] == "STRATEGY_IDENTITY_MISMATCH"


def test_update_parameters_delegates_when_identity_matches() -> None:
    """A matching identity delegates exactly once to the owner boundary."""
    captured: list[tuple[str, dict[str, object]]] = []

    def _source(operation: str, *args: object) -> object:
        captured.append((operation, dict(args[0])))  # type: ignore[arg-type]
        return {"status": "success"}

    status_code, _body = post_json(
        _app(_source),
        "/api/v1/strategies/strat-1/parameters",
        {"payload": {"strategy_id": "strat-1", "parameters": {"period": 14}}},
        headers={"Idempotency-Key": _key()},
        method="PATCH",
    )
    assert status_code == 200
    assert captured[0][0] == "update_parameters"
    assert captured[0][1]["strategy_id"] == "strat-1"


def test_source_fails_closed_without_policy() -> None:
    """No composed validation policy means no Strategy mutation is attempted."""
    source = strategy_dependencies.build_strategy_mutation_source(None)
    with pytest.raises(RuntimeError, match="STRATEGY_RUNTIME_UNAVAILABLE"):
        source("register", {"strategy_id": "strat-1"}, _auth())
    with pytest.raises(RuntimeError, match="STRATEGY_RUNTIME_UNAVAILABLE"):
        source("update_parameters", {"strategy_id": "strat-1"}, _auth())


def test_source_rejects_unknown_operation() -> None:
    """Only the two registered mutation operations are dispatchable."""
    bundle = strategy_dependencies.build_api_strategy_dependencies(
        validation_policy="policy"
    )
    source = strategy_dependencies.build_strategy_mutation_source(bundle)
    with pytest.raises(ValueError, match="unsupported Strategy operation"):
        source("retire", {}, _auth())


def test_source_passes_composed_policy_to_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Registration uses exactly the composed policy, never a gateway default."""
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        strategy_dependencies,
        "create_strategy_registration_request",
        lambda **values: values,
    )
    monkeypatch.setattr(
        strategy_dependencies,
        "register_strategy_version",
        lambda request, _auth, policy: captured.update(request=request, policy=policy),
    )
    bundle = strategy_dependencies.build_api_strategy_dependencies(
        validation_policy="composed-policy"
    )
    source = strategy_dependencies.build_strategy_mutation_source(bundle)
    source("register", {"strategy_id": "strat-1"}, _auth())
    assert captured["policy"] == "composed-policy"
    assert captured["request"] == {"strategy_id": "strat-1"}


def test_source_update_delegates_without_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parameter updates carry no validation policy to the owner boundary."""
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        strategy_dependencies,
        "create_strategy_parameter_update_request",
        lambda **values: values,
    )
    monkeypatch.setattr(
        strategy_dependencies,
        "update_strategy_parameters",
        lambda request, _auth: captured.update(request=request) or "result",
    )
    bundle = strategy_dependencies.build_api_strategy_dependencies(
        validation_policy="policy"
    )
    source = strategy_dependencies.build_strategy_mutation_source(bundle)
    assert source("update_parameters", {"strategy_id": "s"}, _auth()) == "result"
    assert captured["request"] == {"strategy_id": "s"}
