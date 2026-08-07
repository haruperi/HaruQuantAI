"""Trading session route and production-exclusion tests."""

from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.api.composition import trading_dependencies
from app.services.api.identity import require_auth_context
from app.services.api.routes import trading
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

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
        runtime_profile="paper",
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
        query_string="authority_id=account-1&route=paper",
    )
    assert (status, payload) == (200, {"orders": {}, "positions": {}})
    assert captured == [("paper", "development", "account-1")]


def _preflight_request(
    execution_route: str,
    runtime_profile: str,
    allow_live_mutations: bool,
) -> Request:
    """Build one request bound to a deployment's runtime settings.

    Args:
        execution_route: Deployment execution route.
        runtime_profile: Deployment runtime profile.
        allow_live_mutations: Whether live mutation is explicitly enabled.

    Returns:
        Starlette request carrying the settings the preflight reads.
    """
    app = FastAPI()
    app.state.api_settings = SimpleNamespace(
        execution_route=execution_route,
        runtime_profile=runtime_profile,
        allow_live_mutations=allow_live_mutations,
    )
    return Request({"type": "http", "app": app})


def test_live_request_is_refused_by_a_paper_deployment() -> None:
    """A paper deployment never relays a live order, even when asked."""
    request = _preflight_request("paper", "paper", allow_live_mutations=False)
    body = cast("Any", SimpleNamespace(route="live", idempotency_key="mutation-1"))
    with pytest.raises(HTTPException) as raised:
        trading._governed_preflight(body, request, "mutation-1")
    assert raised.value.status_code == 503
    assert raised.value.detail == "EXECUTION_ROUTE_NOT_CONFIGURED"


def test_live_execution_requires_explicit_enablement() -> None:
    """A live deployment still refuses until live mutation is enabled.

    Paper and live share one execution path, so the only thing standing between
    a correctly routed request and real capital is this flag. It is therefore
    checked independently of the route match.
    """
    request = _preflight_request("live", "live", allow_live_mutations=False)
    body = cast("Any", SimpleNamespace(route="live", idempotency_key="mutation-1"))
    with pytest.raises(HTTPException) as raised:
        trading._governed_preflight(body, request, "mutation-1")
    assert raised.value.status_code == 403
    assert raised.value.detail == "LIVE_MUTATIONS_DISABLED"


def test_live_execution_is_admitted_only_when_every_gate_is_set() -> None:
    """All gates aligned admits the request to the owner boundary."""
    request = _preflight_request("live", "live", allow_live_mutations=True)
    body = cast("Any", SimpleNamespace(route="live", idempotency_key="mutation-1"))
    trading._governed_preflight(body, request, "mutation-1")


def test_paper_request_is_refused_by_a_live_deployment() -> None:
    """The route match is symmetric: a live deployment refuses a paper order."""
    request = _preflight_request("live", "live", allow_live_mutations=True)
    body = cast("Any", SimpleNamespace(route="paper", idempotency_key="mutation-1"))
    with pytest.raises(HTTPException) as raised:
        trading._governed_preflight(body, request, "mutation-1")
    assert raised.value.status_code == 503
    assert raised.value.detail == "EXECUTION_ROUTE_NOT_CONFIGURED"


# --- Composed runtime-policy enforcement (Section 5 shared policy) ------------


def _policy(
    runtime_profile: str = "paper",
    execution_route: str = "paper",
    allow_live_mutations: bool = False,
) -> Any:
    """Build one validated gateway runtime policy stand-in.

    Args:
        runtime_profile: Deployment runtime profile.
        execution_route: Deployment execution route.
        allow_live_mutations: Whether live mutation is explicitly enabled.

    Returns:
        Object exposing the three shared policy attributes.
    """
    return SimpleNamespace(
        runtime_profile=runtime_profile,
        execution_route=execution_route,
        allow_live_mutations=allow_live_mutations,
    )


def _body(route: str = "paper") -> Any:
    """Build one boundary request declaring its governed route.

    Args:
        route: Caller-declared paper or live route.

    Returns:
        Minimal stand-in for the Trading mutation boundary DTO.
    """
    return SimpleNamespace(route=route)


def test_runtime_policy_allows_a_matching_request() -> None:
    """A request agreeing with the deployment passes the boundary check."""
    trading_dependencies._enforce_runtime_policy(_policy(), _body())


def test_runtime_policy_rejects_route_mismatch() -> None:
    """A deployment never relays a request declaring a different route."""
    with pytest.raises(RuntimeError, match="TRADING_EXECUTION_ROUTE_MISMATCH"):
        trading_dependencies._enforce_runtime_policy(_policy(), _body(route="live"))


def test_runtime_policy_rejects_missing_route_authority() -> None:
    """A deployment without mutation-route authority fails closed."""
    with pytest.raises(RuntimeError, match="TRADING_EXECUTION_ROUTE_MISSING"):
        trading_dependencies._enforce_runtime_policy(
            _policy(execution_route="none"), _body()
        )


def test_runtime_policy_requires_explicit_live_enablement() -> None:
    """Live routing stays refused until it is deliberately enabled."""
    live_policy = _policy(runtime_profile="live", execution_route="live")
    with pytest.raises(RuntimeError, match="TRADING_LIVE_MUTATIONS_DISABLED"):
        trading_dependencies._enforce_runtime_policy(live_policy, _body(route="live"))
    enabled = _policy(
        runtime_profile="live", execution_route="live", allow_live_mutations=True
    )
    trading_dependencies._enforce_runtime_policy(enabled, _body(route="live"))


def test_runtime_policy_is_skipped_when_none_is_composed() -> None:
    """Without a composed policy the gateway adds no rule of its own."""
    trading_dependencies._enforce_runtime_policy(None, _body(route="live"))
