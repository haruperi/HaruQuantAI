"""Public contracts, protocols, DTOs, and capabilities for the Gateway domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from app.kernel.capability import Capability

if TYPE_CHECKING:
    from fastapi import FastAPI


class GatewayError(Exception):
    """Base exception for all gateway domain operations."""


class ServerStartupError(GatewayError):
    """Raised when the HTTP server fails to initialize or bind."""


@dataclass(frozen=True, slots=True)
class ServerInfo:
    """Snapshot of active HTTP server status."""

    host: str
    port: int
    running: bool
    active_routes: tuple[str, ...]


class HttpServerService(Protocol):
    """Public protocol for the HTTP/ASGI server capability."""

    def get_server_info(self) -> ServerInfo:
        """Return runtime status information about the HTTP server.

        Returns:
            Current `ServerInfo` snapshot.
        """
        ...

    def get_app(self) -> FastAPI:
        """Return the underlying ASGI FastAPI application.

        Returns:
            The FastAPI application instance.
        """
        ...


HTTP_SERVER: Capability[HttpServerService] = Capability("gateway.http_server@1")

__all__ = [
    "HTTP_SERVER",
    "GatewayError",
    "HttpServerService",
    "ServerInfo",
    "ServerStartupError",
]
