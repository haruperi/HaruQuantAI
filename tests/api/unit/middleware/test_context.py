"""Unit tests for API request context middleware."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.services.api import (
    build_request_context_middleware,
    build_route_contract,
    build_route_contract_registry,
)
from app.utils import create_auth_context
from fastapi import FastAPI, Request

type AuthContext = Any


def _auth() -> AuthContext:
    """Return one stable authenticated context."""
    return create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="operator-01",
        principal_type="USER",
        roles=("ops",),
        permissions=("risk.kill.activate",),
        scopes=("risk",),
        tenant_or_environment="simulation",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        issued_at=datetime(
            2026,
            7,
            24,
            9,
            0,
            0,
            tzinfo=UTC,
        ),
    )


def _send_get(
    app: FastAPI,
    path: str,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, object]]:
    """Submit one in-memory GET request and return status/body."""

    async def _invoke() -> tuple[int, dict[str, object]]:
        request_sent = False
        messages: list[dict[str, object]] = []

        async def receive() -> dict[str, Any]:
            nonlocal request_sent
            if request_sent:
                return {"type": "http.disconnect"}
            request_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict[str, Any]) -> None:
            messages.append(message)

        await app(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "GET",
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("utf-8"),
                "query_string": b"",
                "headers": tuple(
                    (name.lower().encode("utf-8"), value.encode("utf-8"))
                    for name, value in (headers or {}).items()
                ),
                "client": ("127.0.0.1", 50000),
                "server": ("testserver", 80),
                "root_path": "",
            },
            receive,
            send,
        )
        start = next(item for item in messages if item["type"] == "http.response.start")
        body = b"".join(
            item.get("body", b"")
            for item in messages
            if item["type"] == "http.response.body"
        )
        return int(start["status"]), dict(__import__("json").loads(body))

    return asyncio.run(_invoke())


def test_unknown_route_has_bounded_metadata() -> None:
    """Missing route contracts should still emit bounded canonical context."""

    app = FastAPI()

    @app.get("/api/middleware/demo")
    async def demo(request: Request) -> dict[str, object]:
        context = request.state.api_request_context
        return {
            "route_id": context.route_id,
            "route_intent": context.route_intent,
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
            "method": context.method,
        }

    contract = build_route_contract(
        route_id="api.middleware.protected",
        method="GET",
        path="/api/middleware/protected",
        owner="api",
    )
    app = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry((contract,)),
        request_id_header="x-request-id",
        correlation_id_header="x-correlation-id",
    )

    status_code, body = _send_get(app, "/api/middleware/demo")
    assert status_code == 200
    assert body["route_id"] is None
    assert body["route_intent"] == "unknown"
    assert len(str(body["request_id"])) <= 128
    assert len(str(body["correlation_id"])) <= 128


def test_missing_request_ids_are_generated_for_untrusted_clients() -> None:
    """Untrusted clients without IDs should receive generated identifiers."""

    app = FastAPI()

    @app.get("/api/middleware/anonymous")
    async def anonymous(request: Request) -> dict[str, object]:
        context = request.state.api_request_context
        return {
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
        }

    app = build_request_context_middleware(
        app, route_contract_registry=build_route_contract_registry()
    )
    status_code, body = _send_get(app, "/api/middleware/anonymous")
    assert status_code == 200
    assert body["request_id"].startswith("req-")
    assert body["correlation_id"].startswith("cor-")


def test_canonical_request_id_is_accepted() -> None:
    """Canonical prefixed UUID4 request IDs should cross the API boundary."""

    request_id = "req-11111111-1111-4111-8111-111111111111"
    app = FastAPI()

    @app.get("/api/middleware/identified")
    async def identified(request: Request) -> dict[str, object]:
        return {"request_id": request.state.api_request_context.request_id}

    app = build_request_context_middleware(
        app, route_contract_registry=build_route_contract_registry()
    )
    status_code, body = _send_get(
        app,
        "/api/middleware/identified",
        headers={"x-request-id": request_id},
    )
    assert status_code == 200
    assert body["request_id"] == request_id


def test_obsolete_request_id_is_rejected_before_authentication() -> None:
    """Obsolete frontend IDs must fail before authentication or persistence."""

    calls: list[str] = []

    def _provider(_: Request) -> AuthContext:
        calls.append("called")
        return _auth()

    app = FastAPI()

    @app.get("/api/middleware/protected")
    async def protected() -> dict[str, bool]:
        return {"ok": True}

    contract = build_route_contract(
        route_id="api.middleware.protected",
        method="GET",
        path="/api/middleware/protected",
        owner="api",
        auth_required=True,
    )
    app = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry((contract,)),
        auth_context_provider=_provider,
    )
    status_code, body = _send_get(
        app,
        "/api/middleware/protected",
        headers={"x-request-id": "req_6qzCQpkvKQJ5"},
    )
    assert status_code == 400
    assert body["detail"] == "VALIDATION_ERROR"
    assert calls == []


def test_request_context_calls_auth_provider_for_protected_route() -> None:
    """Authenticated routes must execute the requested provider once."""

    calls: list[str] = []

    def _provider(_: Request) -> AuthContext:
        calls.append("called")
        return _auth()

    app = FastAPI()

    @app.get("/api/middleware/admin")
    async def admin(request: Request) -> dict[str, object]:
        context = request.state.api_request_context
        return {
            "actor_id": context.actor_id,
            "auth_required": context.auth_required,
            "tenant": context.tenant,
            "route_intent": context.route_intent,
        }

    protected = build_route_contract(
        route_id="api.middleware.admin",
        method="GET",
        path="/api/middleware/admin",
        owner="api",
        auth_required=True,
        permission="ops:read",
    )
    app = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry((protected,)),
        auth_context_provider=_provider,
    )

    status_code, body = _send_get(app, "/api/middleware/admin")
    assert status_code == 200
    assert calls == ["called"]
    assert body["actor_id"] == "operator-01"
    assert body["auth_required"] is True
    assert body["route_intent"] == "protected"


def test_request_context_rejects_auth_required_route_without_provider() -> None:
    """Protected routes without an auth provider must fail closed."""

    app = FastAPI()

    @app.get("/api/middleware/locked")
    async def locked() -> dict[str, str]:
        return {"ok": "true"}

    protected = build_route_contract(
        route_id="api.middleware.locked",
        method="GET",
        path="/api/middleware/locked",
        owner="api",
        auth_required=True,
        permission="ops:read",
    )
    app = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry((protected,)),
    )

    status_code, body = _send_get(app, "/api/middleware/locked")
    assert status_code == 401
    assert body["detail"] == "AUTHENTICATION_REQUIRED"
