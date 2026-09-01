"""Operator evidence-route tests."""

from typing import Any

from app.contracts.common.models import create_auth_context
from app.kernel.time import utc_now
from app.services.api.identity import require_auth_context
from app.services.api.widgets.operator import routes as operator
from app.services.api.widgets.operator.routes import router
from fastapi import FastAPI

from tests.api._support import get_json

AuthContext = Any


def _auth() -> AuthContext:
    """Build one authorized operator context."""
    return create_auth_context(
        contract_version="v2",
        schema_id="utils.auth_context.v2",
        principal_id="operator-1",
        principal_type="USER",
        roles=("operator",),
        permissions=("ops:audit:read", "ops:events:read", "ops:approve"),
        scopes=("operations",),
        tenant_or_environment="development",
        runtime_profile="research",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=utc_now(),
    )


def test_protected_read_views_delegate_once() -> None:
    """Audit and event reads invoke only their injected owner sources."""
    calls: list[tuple[str, int | None]] = []

    def audit_source(_auth: AuthContext, limit: int) -> tuple[dict[str, str], ...]:
        calls.append(("audit", limit))
        return ({"event": "audit"},)

    def event_source(_auth: AuthContext) -> tuple[dict[str, str], ...]:
        calls.append(("events", None))
        return ({"event": "operational"},)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_auth_context] = _auth
    app.dependency_overrides[operator._audit_source] = lambda: audit_source
    app.dependency_overrides[operator._event_source] = lambda: event_source

    audit_status, audit = get_json(
        app,
        "/api/v1/operator/audit-events",
        query_string="limit=10",
    )
    event_status, events = get_json(app, "/api/v1/operator/events")

    assert (audit_status, audit) == (200, [{"event": "audit"}])
    assert (event_status, events) == (200, [{"event": "operational"}])
    assert calls == [("audit", 10), ("events", None)]
