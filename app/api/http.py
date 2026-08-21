"""Lightweight HTTP control plane for lifecycle and readiness diagnostics."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.api.facade import HaruQuantAPI

MIN_REQUEST_PARTS = 2


def _handle_liveness() -> tuple[int, dict[str, Any]]:
    return (
        200,
        {
            "status": "ok",
            "kernel": "active",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


def _handle_readiness(api: HaruQuantAPI) -> tuple[int, dict[str, Any]]:
    status = api.system.get_runtime_status()
    if status is not None and status.is_ready:
        return (
            200,
            {
                "status": "ready",
                "profile": status.profile,
                "is_ready": True,
                "missing_capabilities": list(status.missing_profile_capabilities),
            },
        )
    return (
        503,
        {
            "status": "degraded",
            "profile": status.profile if status is not None else "unknown",
            "is_ready": False,
            "missing_capabilities": (
                list(status.missing_profile_capabilities) if status is not None else []
            ),
        },
    )


def _handle_capabilities(api: HaruQuantAPI) -> tuple[int, dict[str, Any]]:
    capabilities = {
        identifier: {
            "identifier": info.identifier,
            "is_available": info.is_available,
            "provider_feature_id": info.provider_feature_id,
            "generation": info.generation,
            "registered_at": (
                info.registered_at.isoformat() if info.registered_at else None
            ),
        }
        for identifier, info in api.system.list_capabilities().items()
    }
    return 200, {"capabilities": capabilities}


def _handle_features(api: HaruQuantAPI) -> tuple[int, dict[str, Any]]:
    status = api.system.get_runtime_status()
    feature_ids: set[str] = set()
    if status is not None:
        feature_ids.update(status.feature_states)
        feature_ids.update(status.active_features)
        feature_ids.update(status.package_dependency_errors)
        feature_ids.update(status.capability_dependency_errors)
        feature_ids.update(status.runtime_failures)
        feature_ids.update(status.replacement_reports)

    features: dict[str, dict[str, Any]] = {}
    for feature_id in sorted(feature_ids):
        diagnostic = api.system.inspect_feature(feature_id)
        features[feature_id] = {
            "feature_id": diagnostic.feature_id,
            "is_active": diagnostic.is_active,
            "state": diagnostic.state,
            "package_error": diagnostic.package_error,
            "capability_error": diagnostic.capability_error,
            "runtime_error": diagnostic.runtime_error,
            "replacement_status": diagnostic.replacement_status,
            "cleanup_errors": list(diagnostic.cleanup_errors),
            "consumer_errors": list(diagnostic.consumer_errors),
        }
    return 200, {"features": features}


def handle_system_request(
    api: HaruQuantAPI,
    path: str,
    method: str = "GET",
) -> tuple[int, dict[str, str], dict[str, Any]]:
    """Route one system control-plane request."""
    headers = {"Content-Type": "application/json"}
    if method != "GET":
        return 405, headers, {"error": "Method Not Allowed"}

    clean_path = path.split("?", maxsplit=1)[0].rstrip("/") or "/"
    routes: dict[str, Callable[[], tuple[int, dict[str, Any]]]] = {
        "/system/liveness": _handle_liveness,
        "/system/readiness": lambda: _handle_readiness(api),
        "/system/capabilities": lambda: _handle_capabilities(api),
        "/system/features": lambda: _handle_features(api),
    }
    handler = routes.get(clean_path)
    if handler is None:
        return 404, headers, {"error": "Not Found", "path": path}
    status_code, body = handler()
    return status_code, headers, body


class SystemHttpServer:
    """Minimal asynchronous HTTP server for system diagnostics."""

    def __init__(
        self,
        api: HaruQuantAPI,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> None:
        """Initialize the server without binding a socket."""
        self._api = api
        self._host = host
        self._port = port
        self._server: asyncio.Server | None = None

    @property
    def port(self) -> int:
        """Return the bound port, including an OS-selected ephemeral port."""
        if self._server is not None and self._server.sockets:
            address = self._server.sockets[0].getsockname()
            if isinstance(address, tuple):
                return int(address[1])
        return self._port

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            with suppress(Exception):
                line = await reader.readline()
                if not line:
                    return
                request_line = line.decode("utf-8", errors="replace").strip()
                parts = request_line.split()
                method, path = (
                    (parts[0], parts[1])
                    if len(parts) >= MIN_REQUEST_PARTS
                    else ("GET", "/")
                )
                while True:
                    header_line = await reader.readline()
                    if not header_line or header_line in (b"\r\n", b"\n"):
                        break

                status_code, headers, body = handle_system_request(
                    self._api,
                    path,
                    method,
                )
                body_bytes = json.dumps(body).encode()
                status_text = {
                    200: "OK",
                    404: "Not Found",
                    405: "Method Not Allowed",
                    503: "Service Unavailable",
                }.get(status_code, "Unknown")
                content_type = headers.get("Content-Type", "application/json")
                response = (
                    f"HTTP/1.1 {status_code} {status_text}\r\n"
                    f"Content-Type: {content_type}\r\n"
                    f"Content-Length: {len(body_bytes)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode() + body_bytes
                writer.write(response)
                await writer.drain()
        finally:
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()

    async def start(self) -> None:
        """Bind and start accepting control-plane requests."""
        if self._server is None:
            self._server = await asyncio.start_server(
                self._handle_client,
                self._host,
                self._port,
            )

    async def stop(self) -> None:
        """Close the listening server."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def serve_forever(self) -> None:
        """Serve until cancelled."""
        await self.start()
        if self._server is not None:
            async with self._server:
                await self._server.serve_forever()
