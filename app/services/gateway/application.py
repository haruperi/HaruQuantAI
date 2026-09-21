"""FastAPI ASGI application supervisor and lifecycle feature.

Feature:
    FEAT-GATEWAY-APPLICATION

Purpose:
    Provides the central ASGI application lifecycle, route mounting, static UI
    asset hosting, GZip transport compression, and standard liveness/readiness
    health probes (`/healthz`, `/readyz`, `/api/v1/status`) under capability
    `gateway.application@1`.

Key capabilities:
    * Asynchronous ASGI application hosting with FastAPI and Uvicorn.
    * Loopback-default binding (127.0.0.1:8000) matching SQX WebServerPortUsed.
    * GZip transport compression middleware for payload optimization.
    * Health and readiness diagnostics endpoints.
    * Dynamic router and static UI asset mounting.

Python API usage:
    gateway = ctx.require(GATEWAY_APPLICATION)
    app = gateway.get_app()
    info = gateway.get_server_info()

CLI usage:
    uv run python -m tests.examples.05_gateway
"""

from __future__ import annotations

import asyncio
import gzip
import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

import uvicorn
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.staticfiles import StaticFiles

from app.contracts.gateway import (
    GATEWAY_APPLICATION,
    GATEWAY_AUTHORIZATION,
    GATEWAY_ERRORS,
    HTTP_SERVER,
    AuthenticationError,
    GatewayAuthorization,
    ProblemMapper,
    ServerInfo,
)
from app.contracts.gateway import (
    GatewayApplication as IGatewayApplication,
)
from app.contracts.workspace import (
    WORKSPACE_DIAGNOSTICS,
    DiagnosticsService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

_HTTP_BAD_REQUEST = 400
_HTTP_UNAUTHORIZED = 401
_HTTP_FORBIDDEN = 403

_MIN_PORT: int = 1
_MAX_PORT: int = 65535


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ApplicationConfig:
    """Runtime configuration for the Gateway ASGI application."""

    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    enable_docs: bool = True
    enable_gzip: bool = True
    gzip_minimum_size: int = 500
    static_ui_dir: Path | None = None
    allowed_origins: tuple[str, ...] = (
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    )

    def __post_init__(self) -> None:
        """Validate configuration constraints."""
        if not (_MIN_PORT <= self.port <= _MAX_PORT):
            msg = f"Port must be between {_MIN_PORT} and {_MAX_PORT}; got {self.port}"
            raise ValueError(msg)
        if not self.host or not self.host.strip():
            msg = "Host cannot be empty"
            raise ValueError(msg)
        if self.gzip_minimum_size < 0:
            msg = f"gzip_minimum_size must be >= 0; got {self.gzip_minimum_size}"
            raise ValueError(msg)
        if not self.allowed_origins:
            msg = "allowed_origins cannot be empty"
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# Middlewares
# ---------------------------------------------------------------------------


class GZipRequestDecompressionMiddleware:
    """ASGI middleware to decompress inbound gzip request bodies."""

    def __init__(self, app: Any) -> None:
        """Initialize middleware wrapping the ASGI application."""
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Process ASGI request, decompressing body if Content-Encoding is gzip."""
        if scope["type"] == "http":
            headers_list: list[tuple[bytes, bytes]] = scope.get("headers", [])
            headers_dict = dict(headers_list)
            encoding = (
                headers_dict.get(b"content-encoding", b"").decode("latin-1").lower()
            )
            if "gzip" in encoding:
                body_chunks: list[bytes] = []
                while True:
                    message = await receive()
                    if message["type"] == "http.request":
                        body_chunks.append(message.get("body", b""))
                        if not message.get("more_body", False):
                            break
                compressed_body = b"".join(body_chunks)
                try:
                    decompressed_body = gzip.decompress(compressed_body)
                except (
                    gzip.BadGzipFile,
                    zlib.error,
                    OSError,
                    EOFError,
                    ValueError,
                ) as exc:
                    logger.warning("gzip_decompression_failed", error=str(exc))
                    problem_bytes = (
                        b'{"type":"https://datatracker.ietf.org/doc/html/rfc7807",'
                        b'"title":"Bad Request",'
                        b'"status":400,'
                        b'"detail":"Invalid gzip compressed request payload"}'
                    )
                    await send(
                        {
                            "type": "http.response.start",
                            "status": _HTTP_BAD_REQUEST,
                            "headers": [
                                (b"content-type", b"application/problem+json"),
                                (
                                    b"content-length",
                                    str(len(problem_bytes)).encode("ascii"),
                                ),
                            ],
                        }
                    )
                    await send(
                        {
                            "type": "http.response.body",
                            "body": problem_bytes,
                        }
                    )
                    return

                new_headers = [
                    (k, v)
                    for k, v in headers_list
                    if k.lower() not in (b"content-encoding", b"content-length")
                ]
                new_headers.append(
                    (b"content-length", str(len(decompressed_body)).encode("ascii"))
                )
                scope["headers"] = new_headers

                sent = False

                async def decompressed_receive() -> dict[str, Any]:
                    nonlocal sent
                    if not sent:
                        sent = True
                        return {
                            "type": "http.request",
                            "body": decompressed_body,
                            "more_body": False,
                        }
                    return {"type": "http.request", "body": b"", "more_body": False}

                await self.app(scope, decompressed_receive, send)
                return

        await self.app(scope, receive, send)


class GatewayAuthMiddleware:
    """ASGI middleware enforcing transport authentication and network origin policy."""

    _EXEMPT_PREFIXES: tuple[str, ...] = (
        "/health",
        "/healthz",
        "/readyz",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/ui",
        "/favicon.ico",
    )

    def __init__(self, app: Any, auth_service: GatewayAuthorization) -> None:
        """Initialize middleware with target app and authorization service."""
        self.app = app
        self.auth_service = auth_service

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Authenticate request headers and host before proceeding to endpoints."""
        if scope["type"] == "http":
            path = scope.get("path", "")
            if any(
                path == prefix or path.startswith(prefix + "/")
                for prefix in self._EXEMPT_PREFIXES
            ):
                await self.app(scope, receive, send)
                return

            client = scope.get("client")
            client_host = client[0] if client else "127.0.0.1"

            headers: dict[str, str] = {}
            for k, v in scope.get("headers", []):
                headers[k.decode("latin-1").lower()] = v.decode("latin-1")

            try:
                auth_context = self.auth_service.authenticate_request(
                    headers=headers,
                    client_host=client_host,
                )
                state = scope.setdefault("state", {})
                state["auth_context"] = auth_context
            except AuthenticationError as exc:
                is_remote_disabled = "Remote access is disabled" in str(exc)
                status_code = (
                    _HTTP_FORBIDDEN if is_remote_disabled else _HTTP_UNAUTHORIZED
                )
                title = "Forbidden" if is_remote_disabled else "Unauthorized"
                detail = str(exc)
                body = (
                    f'{{"type":"https://datatracker.ietf.org/doc/html/rfc7807",'
                    f'"title":"{title}",'
                    f'"status":{status_code},'
                    f'"detail":"{detail}"}}'
                ).encode()
                await send(
                    {
                        "type": "http.response.start",
                        "status": status_code,
                        "headers": [
                            (b"content-type", b"application/problem+json"),
                            (b"content-length", str(len(body)).encode("ascii")),
                        ],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": body,
                    }
                )
                return

        await self.app(scope, receive, send)


# ---------------------------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------------------------


class ApplicationService(IGatewayApplication):
    """Implement the public GatewayApplication capability."""

    def __init__(
        self,
        config: ApplicationConfig,
        diagnostics: DiagnosticsService | None = None,
        errors: ProblemMapper | None = None,
        auth: GatewayAuthorization | None = None,
    ) -> None:
        """Initialize the API service with configuration and route setup.

        Args:
            config: Runtime configuration options.
            diagnostics: Optional diagnostics service for readiness checks.
            errors: Optional problem mapper for RFC 7807 handler registration.
            auth: Optional transport authorization service.
        """
        self._config = config
        self._diagnostics = diagnostics
        self._errors = errors
        self._auth = auth

        docs_url = "/docs" if config.enable_docs else None
        redoc_url = "/redoc" if config.enable_docs else None

        self._app = FastAPI(
            title="HaruQuant Gateway",
            description="Modular Monolith Quantitative Engine Gateway",
            version="1.0.0",
            docs_url=docs_url,
            redoc_url=redoc_url,
        )

        # 1. Transport authorization middleware (if auth service provided)
        if self._auth is not None:
            self._app.add_middleware(
                GatewayAuthMiddleware,
                auth_service=self._auth,
            )

        # 2. Inbound gzip request decompression middleware
        if config.enable_gzip:
            self._app.add_middleware(GZipRequestDecompressionMiddleware)

        # 3. Transport response compression (matching SQX gzip support)
        if config.enable_gzip:
            self._app.add_middleware(
                GZipMiddleware,
                minimum_size=config.gzip_minimum_size,
            )

        # 4. CORS configuration for localhost / loopback
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=list(config.allowed_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 5. Register problem details exception handlers if available
        if self._errors is not None:
            self._errors.register_handlers(self._app)

        self._server: uvicorn.Server | None = None
        self._setup_system_routes()

        # 4. Mount static UI assets if configured and existing
        if config.static_ui_dir and config.static_ui_dir.is_dir():
            self.mount_static("/ui", config.static_ui_dir)

    def _setup_system_routes(self) -> None:
        """Register built-in health, readiness, and diagnostic routes."""

        @self._app.get("/health", tags=["System"])
        @self._app.get("/healthz", tags=["System"])
        async def health_check() -> dict[str, str]:
            """Return standard system health check status."""
            return {
                "status": "ok",
                "timestamp": datetime.now(UTC).isoformat(),
                "version": "1.0.0",
            }

        @self._app.get("/readyz", tags=["System"])
        @self._app.get("/api/v1/status", tags=["System"])
        async def status_check() -> dict[str, Any]:
            """Return server configuration and diagnostic status."""
            health = (
                self._diagnostics.get_health()
                if self._diagnostics is not None
                else None
            )
            return {
                "status": "ready",
                "host": self._config.host,
                "port": self._config.port,
                "timestamp": datetime.now(UTC).isoformat(),
                "diagnostics": {
                    "health_status": health.status,
                    "memory_pct": health.memory_pct,
                    "active_jobs": health.active_jobs,
                }
                if health is not None
                else None,
            }

    @override
    def get_server_info(self) -> ServerInfo:
        """Return runtime status information about the HTTP server.

        Returns:
            Current `ServerInfo` snapshot.
        """
        routes: list[str] = []
        for route in self._app.routes:
            p = getattr(route, "path", None)
            if p is not None:
                routes.append(str(p))
            elif hasattr(route, "original_router") and hasattr(
                route, "include_context"
            ):
                prefix = getattr(route.include_context, "prefix", "")
                for sub in getattr(route.original_router, "routes", []):
                    sub_p = getattr(sub, "path", "")
                    routes.append(f"{prefix}{sub_p}")

        is_running = self._server is not None and self._server.started
        is_loopback = self._config.host in {"127.0.0.1", "::1", "localhost"}
        return ServerInfo(
            host=self._config.host,
            port=self._config.port,
            running=is_running,
            active_routes=tuple(sorted(routes)),
            loopback_only=is_loopback,
        )

    @override
    def get_app(self) -> FastAPI:
        """Return the underlying ASGI FastAPI application.

        Returns:
            The configured FastAPI application instance.
        """
        return self._app

    @override
    def mount_router(
        self,
        prefix: str,
        router: APIRouter,
        tags: Sequence[str] | None = None,
    ) -> None:
        """Mount a versioned router onto the application.

        Args:
            prefix: URL prefix (e.g. '/api/v1').
            router: APIRouter instance to mount.
            tags: Optional OpenAPI tags for documentation.
        """
        self._app.include_router(router, prefix=prefix, tags=list(tags or []))
        logger.info("gateway_router_mounted", prefix=prefix)

    @override
    def mount_static(self, path: str, directory: Path) -> None:
        """Mount a local directory for serving static web assets.

        Args:
            path: URL path mount point (e.g. '/static').
            directory: Local filesystem directory containing static files.
        """
        if not directory.is_dir():
            msg = f"Static directory {directory} does not exist"
            raise ValueError(msg)
        self._app.mount(
            path, StaticFiles(directory=str(directory), html=True), name="static_ui"
        )
        logger.info("gateway_static_mounted", path=path, directory=str(directory))

    @override
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
            "gateway_server_starting",
            host=self._config.host,
            port=self._config.port,
        )
        try:
            await self._server.serve()
        except asyncio.CancelledError:
            logger.info("gateway_server_cancelled")
            self.stop()
            raise
        finally:
            logger.info("gateway_server_stopped")

    @override
    def stop(self) -> None:
        """Signal the Uvicorn server to stop gracefully."""
        if self._server is not None:
            self._server.should_exit = True


# ---------------------------------------------------------------------------
# Feature Specification and Wiring
# ---------------------------------------------------------------------------

SPEC = FeatureSpec(
    name="gateway.application",
    provides=frozenset({GATEWAY_APPLICATION, HTTP_SERVER}),
    requires=frozenset({WORKSPACE_DIAGNOSTICS}),
    optional=frozenset({GATEWAY_ERRORS, GATEWAY_AUTHORIZATION}),
    description=(
        "FastAPI ASGI application hosting, route mounting, and lifecycle supervisor."
    ),
)


class ApplicationFeature:
    """Wire the Gateway application into the composition lifecycle."""

    def __init__(self, config: ApplicationConfig | None = None) -> None:
        """Initialize the feature with optional configuration.

        Args:
            config: Optional `ApplicationConfig` (defaults to standard settings).
        """
        self._config = config or ApplicationConfig()
        self._service: ApplicationService | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the feature and publish its capabilities.

        Args:
            context: Feature context for managing lifecycles and capabilities.
        """
        diagnostics = context.require(WORKSPACE_DIAGNOSTICS)
        errors = context.optional(GATEWAY_ERRORS)
        auth = context.optional(GATEWAY_AUTHORIZATION)

        service = ApplicationService(
            config=self._config,
            diagnostics=diagnostics,
            errors=errors,
            auth=auth,
        )
        self._service = service

        context.provide(GATEWAY_APPLICATION, service)
        context.provide(HTTP_SERVER, service)

        # Spawn background ASGI server loop managed by the feature scope
        context.spawn(service.serve())
        logger.info("gateway_application_started", port=self._config.port)

    async def stop(self) -> None:
        """Gracefully terminate the Uvicorn server on shutdown."""
        if self._service is not None:
            self._service.stop()


def feature() -> ApplicationFeature:
    """Factory creating the default ApplicationFeature.

    Returns:
        Configured feature instance.
    """
    return ApplicationFeature()
