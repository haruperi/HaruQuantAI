"""Standalone API middleware usage examples."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.api import (
    build_request_context_middleware,
    build_route_contract,
    build_route_contract_registry,
    build_secret_redaction_middleware,
)
from app.utils import create_auth_context
from fastapi import FastAPI, Request

_NOW = datetime(2026, 7, 24, 9, 30, 0, tzinfo=UTC)
type AuthContext = Any


def _auth() -> AuthContext:
    """Return one stable authenticated context."""
    return create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="usage-operator-01",
        principal_type="USER",
        roles=("risk_operator",),
        permissions=("risk.kill.activate",),
        scopes=("risk",),
        tenant_or_environment="simulation",
        request_id="req-22222222-2222-4222-8222-222222222222",
        workflow_id="wf-33333333-3333-4333-8333-333333333333",
        correlation_id="cor-44444444-4444-4444-8444-444444444444",
        issued_at=_NOW,
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

        async def send(message: dict[str, object]) -> None:
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
        return int(start["status"]), dict(json.loads(body))

    return asyncio.run(_invoke())


def _public_routes() -> tuple[tuple[str, object], ...]:
    """Create one local route-contract registry."""
    return (
        build_route_contract(
            route_id="api.middleware.redaction",
            method="GET",
            path="/api/middleware/redaction",
            owner="api",
            auth_required=False,
        ),
        build_route_contract(
            route_id="api.middleware.private",
            method="GET",
            path="/api/middleware/private",
            owner="api",
            auth_required=True,
            permission="risk.kill.activate",
        ),
    )


def fr_api_016() -> dict[str, object]:
    """FR-API-016: emit only allowlisted redacted request telemetry fields."""
    events: list[dict[str, object]] = []
    app = FastAPI()

    @app.get("/api/middleware/redaction")
    async def demo() -> dict[str, str]:
        return {"status": "ok"}

    app = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry(_public_routes()),
    )
    app = build_secret_redaction_middleware(
        app,
        event_emitter=events.append,
    )

    status_code, body = _send_get(
        app,
        "/api/middleware/redaction",
        {"authorization": "Bearer usage-token-123"},
    )
    assert status_code == 200
    assert body["status"] == "ok"
    payload = events[0]
    return {
        "method": payload["method"],
        "route_id": payload["route_id"],
        "status": payload["status"],
        "keys": sorted(payload.keys()),
    }


def fr_api_017() -> dict[str, object]:
    """FR-API-017: attach validated IDs and route intent plus protected route context."""
    app = FastAPI()

    @app.get("/api/middleware/private")
    async def protected(request: Request) -> dict[str, object]:
        context = request.state.api_request_context
        return {
            "route_intent": context.route_intent,
            "request_id": context.request_id,
            "correlation_id": context.correlation_id,
            "actor_id": context.actor_id,
            "auth_required": context.auth_required,
        }

    app = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry(_public_routes()),
        auth_context_provider=lambda _: _auth(),
    )

    status_code, body = _send_get(app, "/api/middleware/private")
    assert status_code == 200
    return body


def main() -> None:
    """Run the middleware usage scenarios."""
    print(fr_api_016())
    print(fr_api_017())


if __name__ == "__main__":
    main()
