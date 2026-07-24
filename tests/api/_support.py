"""Dependency-free ASGI test request support."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI


def post_json(
    app: FastAPI,
    path: str,
    payload: Mapping[str, Any],
) -> tuple[int, dict[str, Any]]:
    """Submit one JSON request through the complete ASGI boundary.

    Args:
        app: Configured FastAPI application.
        path: Exact request path.
        payload: JSON-compatible request body.

    Returns:
        HTTP status and decoded JSON response.
    """

    async def _invoke() -> tuple[int, dict[str, Any]]:
        body = json.dumps(payload).encode("utf-8")
        request_sent = False
        messages: list[dict[str, Any]] = []

        async def receive() -> dict[str, Any]:
            nonlocal request_sent
            if request_sent:
                return {"type": "http.disconnect"}
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message: dict[str, Any]) -> None:
            messages.append(message)

        await app(
            {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": "POST",
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("ascii"),
                "query_string": b"",
                "headers": (
                    (b"host", b"testserver"),
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
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


def get_json(
    app: FastAPI,
    path: str,
    *,
    query_string: str = "",
) -> tuple[int, object]:
    """Submit one GET request through the complete ASGI boundary.

    Args:
        app: Configured FastAPI application.
        path: Exact request path.
        query_string: Optional encoded query string without a leading question mark.

    Returns:
        HTTP status and decoded JSON response.
    """

    async def _invoke() -> tuple[int, object]:
        request_sent = False
        messages: list[dict[str, Any]] = []

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
                "raw_path": path.encode("ascii"),
                "query_string": query_string.encode("ascii"),
                "headers": ((b"host", b"testserver"),),
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
