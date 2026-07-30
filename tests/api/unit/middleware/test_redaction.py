"""Unit tests for API redaction middleware."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from app.services.api import (
    build_request_context_middleware,
    build_route_contract,
    build_route_contract_registry,
    build_secret_redaction_middleware,
)
from fastapi import FastAPI, HTTPException


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
        response_body = b"".join(
            item.get("body", b"")
            for item in messages
            if item["type"] == "http.response.body"
        )
        return int(start["status"]), json.loads(response_body)

    return asyncio.run(_invoke())


def test_tokens_never_logged() -> None:
    """Only allowlisted telemetry fields should be emitted."""

    events: list[dict[str, object]] = []

    app = FastAPI()

    @app.get("/api/middleware/redaction")
    async def demo() -> dict[str, str]:
        return {"ok": "true"}

    app = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry(
            (
                build_route_contract(
                    route_id="api.middleware.redaction",
                    method="GET",
                    path="/api/middleware/redaction",
                    owner="api",
                    auth_required=False,
                ),
            ),
        ),
    )
    app = build_secret_redaction_middleware(
        app,
        event_emitter=events.append,
    )

    status_code, body = _send_get(
        app,
        "/api/middleware/redaction",
        headers={"authorization": "Bearer secret-token-xyz"},
    )
    assert status_code == 200
    assert body == {"ok": "true"}
    assert len(events) == 1
    payload = events[0]
    assert set(payload.keys()) == {
        "method",
        "route",
        "route_id",
        "status",
        "duration_ms",
        "error_code",
        "request_id",
        "correlation_id",
    }
    assert "secret-token-xyz" not in str(payload)


def test_error_status_becomes_error_code() -> None:
    """HTTP failures must be represented by bounded telemetry error codes."""

    events: list[dict[str, object]] = []

    app = FastAPI()

    @app.get("/api/middleware/error")
    async def failure() -> dict[str, str]:
        raise HTTPException(status_code=422, detail="VALIDATION_ERROR")

    app = build_request_context_middleware(
        app,
        route_contract_registry=build_route_contract_registry(),
    )
    app = build_secret_redaction_middleware(
        app,
        event_emitter=events.append,
    )

    status_code, _body = _send_get(app, "/api/middleware/error")
    assert status_code == 422
    assert events[0]["status"] == 422
    assert events[0]["error_code"] == "VALIDATION_ERROR"
