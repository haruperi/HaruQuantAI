"""Trading session route and production-exclusion tests."""

from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.api.identity import require_auth_context
from app.services.api.widgets.trading import orchestration as trading_dependencies
from app.services.api.widgets.trading import routes as trading
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI, HTTPException

from tests.api._support import get_json


def _auth() -> Any:
    """Build one authorized Trading reader."""
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="trading-reader",
        principal_type="USER",
        roles=("operator",),
        permissions=("trading:read", "trading:write"),
        scopes=("trading",),
        tenant_or_environment="development",
        runtime_profile="demo",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def test_session_read_delegates_exact_scope() -> None:
    """The route derives tenant authority only from authenticated context."""
    captured: list[tuple[str, str, str]] = []

    def source(route: str, tenant: str, authority: str, _auth: Any) -> object:
        captured.append((route, tenant, authority))
        return {"orders": {}, "positions": {}}

    app = FastAPI()
    app.include_router(trading.router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[trading._trading_session_source] = lambda: source
    status, payload = get_json(
        app,
        "/api/v1/trading/session",
        query_string="authority_id=account-1&route=demo",
    )
    assert (status, payload) == (200, {"orders": {}, "positions": {}})
    assert captured == [("demo", "development", "account-1")]


def _active_mode(monkeypatch: pytest.MonkeyPatch, route: str) -> None:
    """Pin the operator-selected account mode both boundaries resolve.

    Args:
        monkeypatch: Test patcher.
        route: Execution route the active account mode maps to.
    """
    monkeypatch.setattr(trading, "resolve_execution_route", lambda **_: route)
    monkeypatch.setattr(
        trading_dependencies, "resolve_execution_route", lambda **_: route
    )


def _mutation(route: str) -> Any:
    """Build one boundary request declaring its governed route.

    Args:
        route: Caller-declared sim, demo, or live route.

    Returns:
        Minimal stand-in for the Trading mutation boundary DTO.
    """
    return cast("Any", SimpleNamespace(route=route, idempotency_key="mutation-1"))


def test_live_request_is_refused_while_the_app_is_in_sim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A request never elects a route the operator has not selected."""
    _active_mode(monkeypatch, "sim")
    with pytest.raises(HTTPException) as raised:
        trading._governed_preflight(_mutation("live"), "mutation-1")
    assert raised.value.status_code == 503
    assert raised.value.detail == "EXECUTION_ROUTE_NOT_CONFIGURED"


def test_live_request_is_admitted_when_live_is_the_selected_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Selecting LIVE is what admits a live order.

    No separate live-enablement flag is consulted: Risk is the sole authority
    on whether the order proceeds, and demo versus live is decided by which
    credentials the operator supplied.
    """
    _active_mode(monkeypatch, "live")
    trading._governed_preflight(_mutation("live"), "mutation-1")


def test_demo_request_is_refused_while_the_app_is_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The route match is symmetric: a live app refuses a demo order."""
    _active_mode(monkeypatch, "live")
    with pytest.raises(HTTPException) as raised:
        trading._governed_preflight(_mutation("demo"), "mutation-1")
    assert raised.value.status_code == 503
    assert raised.value.detail == "EXECUTION_ROUTE_NOT_CONFIGURED"


def test_sim_request_is_admitted_while_the_app_is_in_sim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sim is a first-class route, not an absence of one."""
    _active_mode(monkeypatch, "sim")
    trading._governed_preflight(_mutation("sim"), "mutation-1")


def test_mismatched_idempotency_key_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The transport header must agree with the body it claims to key."""
    _active_mode(monkeypatch, "demo")
    with pytest.raises(HTTPException) as raised:
        trading._governed_preflight(_mutation("demo"), "a-different-key")
    assert raised.value.status_code == 422
    assert raised.value.detail == "IDEMPOTENCY_KEY_REQUIRED"


# --- Composed runtime-policy enforcement (Section 5 shared policy) ------------


def _policy() -> Any:
    """Build one composed gateway runtime policy stand-in.

    Returns:
        Object standing in for validated gateway runtime settings.
    """
    return SimpleNamespace(runtime_profile="demo", execution_route="demo")


def _body(route: str | None = "demo") -> Any:
    """Build one boundary request declaring its governed route.

    Args:
        route: Caller-declared route, or None when authority is absent.

    Returns:
        Minimal stand-in for the Trading mutation boundary DTO.
    """
    return SimpleNamespace(route=route)


def test_runtime_policy_allows_a_matching_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A request agreeing with the active mode passes the boundary check."""
    _active_mode(monkeypatch, "demo")
    trading_dependencies._enforce_runtime_policy(_policy(), _body())


def test_runtime_policy_rejects_route_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gateway never relays a request declaring a different route."""
    _active_mode(monkeypatch, "demo")
    with pytest.raises(RuntimeError, match="TRADING_EXECUTION_ROUTE_MISMATCH"):
        trading_dependencies._enforce_runtime_policy(_policy(), _body(route="live"))


def test_runtime_policy_rejects_missing_route_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A request without a declared route fails closed."""
    _active_mode(monkeypatch, "demo")
    with pytest.raises(RuntimeError, match="TRADING_EXECUTION_ROUTE_MISSING"):
        trading_dependencies._enforce_runtime_policy(_policy(), _body(route=None))


def test_runtime_policy_admits_live_without_any_enablement_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Live routing is admitted purely by the elected mode."""
    _active_mode(monkeypatch, "live")
    trading_dependencies._enforce_runtime_policy(_policy(), _body(route="live"))


def test_runtime_policy_is_skipped_when_none_is_composed() -> None:
    """Without a composed policy the gateway adds no rule of its own."""
    trading_dependencies._enforce_runtime_policy(None, _body(route="live"))
