"""Trading session route and production-exclusion tests."""

from types import SimpleNamespace
from typing import Any, cast

import pytest
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


def test_production_execution_is_rejected_before_owner_delegation() -> None:
    """The API bridge never authorizes production-capital execution."""
    app = FastAPI()
    app.state.api_settings = SimpleNamespace(
        execution_route="live",
        runtime_profile="live",
    )
    request = Request({"type": "http", "app": app})
    body = cast(
        "Any",
        SimpleNamespace(route="live", idempotency_key="mutation-1"),
    )
    with pytest.raises(HTTPException) as raised:
        trading._governed_preflight(body, request, "mutation-1")
    assert raised.value.status_code == 403
    assert raised.value.detail == "PRODUCTION_EXECUTION_EXCLUDED"
