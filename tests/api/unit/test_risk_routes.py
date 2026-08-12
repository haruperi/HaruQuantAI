"""Authenticated Risk read-route tests."""

from typing import Any

from app.services.api.identity import require_auth_context
from app.services.api.workstation.risk import routes as risk
from app.utils import create_auth_context, utc_now
from fastapi import FastAPI

from tests.api._support import get_json


def _auth() -> Any:
    """Build one authorized Risk reader."""
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="risk-reader",
        principal_type="USER",
        roles=("operator",),
        permissions=("risk:read",),
        scopes=("risk",),
        tenant_or_environment="development",
        runtime_profile="research",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def test_risk_reads_delegate_to_composed_owner_source() -> None:
    """Kill-switch and decisions preserve exact query parameters."""
    calls: list[tuple[str, dict[str, object]]] = []

    def source(operation: str, parameters: dict[str, object], _auth: Any) -> object:
        calls.append((operation, parameters))
        return {"state": "inactive"} if operation == "kill-switch" else ({"id": 1},)

    app = FastAPI()
    app.include_router(risk.router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[risk._risk_source] = lambda: source
    state_status, state = get_json(app, "/api/v1/risk/kill-switch")
    decisions_status, decisions = get_json(
        app, "/api/v1/risk/decisions", query_string="limit=10"
    )
    assert (state_status, state) == (200, {"state": "inactive"})
    assert (decisions_status, decisions) == (200, [{"id": 1}])
    assert calls[1] == ("decisions", {"limit": 10})
