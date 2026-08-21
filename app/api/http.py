"""System domain HTTP control plane and health endpoints."""

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

    profile_name = status.profile if status is not None else "unknown"
    missing = list(status.missing_profile_capabilities) if status is not None else []
    return (
        503,
        {
            "status": "degraded",
            "profile": profile_name,
            "is_ready": False,
            "missing_capabilities": missing,
        },
    )


def _handle_capabilities(api: HaruQuantAPI) -> tuple[int, dict[str, Any]]:
    caps = api.system.list_capabilities()
    res_caps: dict[str, dict[str, Any]] = {}
    for cap_id, info in caps.items():
        res_caps[cap_id] = {
            "identifier": info.identifier,
            "is_available": info.is_available,
            "provider_feature_id": info.provider_feature_id,
            "generation": info.generation,
            "registered_at": (
                info.registered_at.isoformat() if info.registered_at else None
            ),
        }
    return 200, {"capabilities": res_caps}


def _handle_features(api: HaruQuantAPI) -> tuple[int, dict[str, Any]]:
    status = api.system.get_runtime_status()
    feature_ids: set[str] = set()
    if status is not None:
        feature_ids.update(status.feature_states.keys())
        feature_ids.update(status.active_features)
        feature_ids.update(status.package_dependency_errors.keys())
        feature_ids.update(status.capability_dependency_errors.keys())

    features_report: dict[str, dict[str, Any]] = {}
    for fid in sorted(feature_ids):
        diag = api.system.inspect_feature(fid)
        features_report[fid] = {
            "feature_id": diag.feature_id,
            "is_active": diag.is_active,
            "state": diag.state,
            "package_error": diag.package_error,
            "capability_error": diag.capability_error,
        }
    return 200, {"features": features_report}


def handle_system_request(
    api: HaruQuantAPI,
    path: str,
    method: str = "GET",
) -> tuple[int, dict[str, str], dict[str, Any]]:
    """Route and handle system control plane HTTP requests.

    Args:
        api: HaruQuantAPI facade instance.
        path: Request URI path.
        method: HTTP request method (default GET).

    Returns:
        Tuple of (status_code, response_headers, response_body_dict).
    """
    headers = {"Content-Type": "application/json"}

    if method != "GET":
        return 405, headers, {"error": "Method Not Allowed"}

    clean_path = path.split("?", maxsplit=1)[0].rstrip("/")
    if not clean_path:
        clean_path = "/"

    routes: dict[str, Callable[[], tuple[int, dict[str, Any]]]] = {
        "/system/liveness": _handle_liveness,
        "/system/readiness": lambda: _handle_readiness(api),
        "/system/capabilities": lambda: _handle_capabilities(api),
        "/system/features": lambda: _handle_features(api),
    }

    handler = routes.get(clean_path)
    if handler is not None:
        status_code, body = handler()
        return status_code, headers, body

    return 404, headers, {"error": "Not Found", "path": path}


class SystemHttpServer:
    """Lightweight async HTTP control plane server for system endpoints."""

    def __init__(
        self,
        api: HaruQuantAPI,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> None:
        """Initialize the control plane server.

        Args:
            api: HaruQuantAPI instance.
            host: Host interface to bind.
            port: Port to bind (0 for ephemeral OS selection).
        """
        self._api = api
        self._host = host
        self._port = port
        self._server: asyncio.Server | None = None

    @property
    def port(self) -> int:
        """Return bound listening port."""
        if self._server is not None and self._server.sockets:
            sock = self._server.sockets[0]
            addr = sock.getsockname()
            if isinstance(addr, tuple):
                return int(addr[1])
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
                    writer.close()
                    with suppress(Exception):
                        await writer.wait_closed()
                    return

                request_line = line.decode("utf-8", errors="replace").strip()
                parts = request_line.split()
                method, path = (
                    (parts[0], parts[1])
                    if len(parts) >= MIN_REQUEST_PARTS
                    else ("GET", "/")
                )

                # Drain remaining HTTP headers
                while True:
                    header_line = await reader.readline()
                    if not header_line or header_line in (b"\r\n", b"\n"):
                        break

                status_code, headers, body = handle_system_request(
                    self._api, path, method
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
                    f"Connection: close\r\n"
                    f"\r\n"
                ).encode() + body_bytes

                writer.write(response)
                await writer.drain()
        finally:
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()

    async def start(self) -> None:
        """Start listening for incoming control plane HTTP requests."""
        if self._server is None:
            self._server = await asyncio.start_server(
                self._handle_client,
                self._host,
                self._port,
            )

    async def stop(self) -> None:
        """Stop listening and close all active server sockets."""
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def serve_forever(self) -> None:
        """Serve control plane requests until cancelled."""
        await self.start()
        if self._server is not None:
            async with self._server:
                await self._server.serve_forever()
