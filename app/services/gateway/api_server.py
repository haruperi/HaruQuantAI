"""Gateway API server feature module.

Purpose:
    Provides the HTTP and ASGI gateway boundary for HaruQuant, assembling
    the FastAPI application and managing the lifecycle of the Uvicorn server.

Key capabilities:
    * Asynchronous ASGI application hosting with FastAPI.
    * Standard health probe (`/health`) and diagnostic endpoints (`/api/v1/status`).
    * Lifecycle-managed background execution via `FeatureContext.spawn_task()`.

Python API usage:
    server_service = ctx.require(HTTP_SERVER)
    info = server_service.get_server_info()
    app = server_service.get_app()

CLI usage:
    uv run python -m tests.examples.gateway_usage
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, override

import uvicorn
from fastapi import FastAPI

from app.contracts.gateway import (
    HTTP_SERVER,
    HttpServerService,
    ServerInfo,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


_MIN_PORT: int = 1
_MAX_PORT: int = 65535


@dataclass(frozen=True, slots=True)
class ApiServerConfig:
    """Runtime configuration for the Gateway API server."""

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    enable_docs: bool = True

    def __post_init__(self) -> None:
        """Validate configuration constraints."""
        if not (_MIN_PORT <= self.port <= _MAX_PORT):
            msg = f"Port must be between {_MIN_PORT} and {_MAX_PORT}; got {self.port}"
            raise ValueError(msg)
        if not self.host or not self.host.strip():
            msg = "Host cannot be empty"
            raise ValueError(msg)


class ApiServerService(HttpServerService):
    """Implement the public HTTP/ASGI server capability."""

    def __init__(self, config: ApiServerConfig) -> None:
        """Initialize the API service with configuration and route setup.

        Args:
            config: Runtime configuration options.
        """
        self._config = config
        docs_url = "/docs" if config.enable_docs else None
        redoc_url = "/redoc" if config.enable_docs else None

        self._app = FastAPI(
            title="HaruQuant Gateway",
            description="Modular Monolith Quantitative Engine Gateway",
            version="0.1.0",
            docs_url=docs_url,
            redoc_url=redoc_url,
        )
        self._server: uvicorn.Server | None = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Register built-in health and runtime diagnostic routes."""

        @self._app.get("/health", tags=["System"])
        async def health_check() -> dict[str, str]:
            """Return standard system health check status."""
            return {
                "status": "ok",
                "timestamp": datetime.now(UTC).isoformat(),
                "version": "0.1.0",
            }

        @self._app.get("/api/v1/status", tags=["System"])
        async def status_check() -> dict[str, Any]:
            """Return server configuration and diagnostic status."""
            return {
                "status": "ready",
                "host": self._config.host,
                "port": self._config.port,
            }

    @override
    def get_server_info(self) -> ServerInfo:
        """Return runtime status information about the HTTP server.

        Returns:
            Current `ServerInfo` snapshot.
        """
        routes = [
            str(route.path) for route in self._app.routes if hasattr(route, "path")
        ]
        is_running = self._server is not None and self._server.started
        return ServerInfo(
            host=self._config.host,
            port=self._config.port,
            running=is_running,
            active_routes=tuple(sorted(routes)),
        )

    @override
    def get_app(self) -> FastAPI:
        """Return the underlying ASGI FastAPI application.

        Returns:
            The configured FastAPI application instance.
        """
        return self._app

    async def serve(self) -> None:
        """Execute the Uvicorn ASGI server loop asynchronously."""
        config = uvicorn.Config(
            app=self._app,
            host=self._config.host,
            port=self._config.port,
            log_level=self._config.log_level.lower(),
            access_log=False,
        )
        self._server = uvicorn.Server(config)
        logger.info(
            "http_server_starting",
            host=self._config.host,
            port=self._config.port,
        )
        try:
            await self._server.serve()
        except asyncio.CancelledError:
            logger.info("http_server_cancelled")
            self.stop()
            raise
        finally:
            logger.info("http_server_stopped")

    def stop(self) -> None:
        """Signal the Uvicorn server to stop gracefully."""
        if self._server is not None:
            self._server.should_exit = True


SPEC = FeatureSpec(
    name="gateway.api_server",
    provides=frozenset({HTTP_SERVER}),
    requires=frozenset(),
    optional=frozenset(),
    description="Asynchronous FastAPI HTTP and ASGI server supervisor.",
)


class ApiServerFeature:
    """Wire the Gateway API server into the composition lifecycle."""

    def __init__(self, config: ApiServerConfig | None = None) -> None:
        """Initialize the feature with optional configuration.

        Args:
            config: Optional `ApiServerConfig` (defaults to standard settings).
        """
        self._config = config or ApiServerConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the feature and publish its capability.

        Args:
            context: Feature context for managing lifecycles and capabilities.
        """
        service = ApiServerService(self._config)
        context.on_close(service.stop)
        context.spawn(service.serve(), name="gateway_uvicorn_server")
        context.provide(HTTP_SERVER, service)
        logger.info(
            "gateway_feature_started",
            host=self._config.host,
            port=self._config.port,
        )


def feature() -> ApiServerFeature:
    """Return a new unmounted feature instance.

    Returns:
        Unmounted `ApiServerFeature` instance.
    """
    return ApiServerFeature()


__all__ = [
    "SPEC",
    "ApiServerConfig",
    "ApiServerFeature",
    "ApiServerService",
    "feature",
]
