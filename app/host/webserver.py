"""Host application: routing, auth, access logging, and static UI serving.

This module is the **composition root** of the host: it imports every
feature module to register their endpoints, which is exactly why it may not
export anything those modules need (that would be circular) — shared
helpers live in ``envelope.py`` (wire contract) and ``http.py`` (HTTP
glue).

Responsibilities, and nothing more: the route table (17 host commands plus
catalog-mounted domain routes), bearer-token enforcement, per-request
access logging, SPA-fallback static serving of the built UI, and the
fail-closed error handlers that turn 404/405/malformed/unexpected
conditions into error envelopes. Feature behavior lives in the feature
modules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, override

from starlette.applications import Starlette
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute, Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.types import ASGIApp, Receive, Scope, Send

from app.host.catalog import (
    CatalogService,
    CatalogView,
    DomainManifest,
    catalog_endpoint,
    domain_routes,
)
from app.host.commands import (
    ExchangeFiles,
    copy_endpoint,
    files_delete_endpoint,
    files_exists_endpoint,
    files_list_endpoint,
    files_read_endpoint,
    files_write_endpoint,
    open_link_endpoint,
)
from app.host.envelope import ValidationIssue, error_payload, success_payload
from app.host.events import EventBus, publish_event, subscribe_events
from app.host.http import (
    MalformedRequestError,
    envelope_response,
    read_json_body,
    request_id_of,
)
from app.host.lifecycle import LifecycleState, shutdown_endpoint, status_endpoint
from app.host.sessions import SessionError, SessionManager
from app.host.settings import SettingsStore, get_settings, put_settings
from app.host.telemetry import LOGGER_NAME

HOST_VERSION = "2.1.0"
AUTH_EXEMPT_PATHS = frozenset(
    {"/api/v1/health", "/api/v1/status", "/api/v1/auth/login"}
)
_BEARER_PREFIX = "Bearer "


@dataclass
class HostServices:
    """Every feature service the application is wired with.

    Bundled so the composition stays explicit and injectable: tests build
    isolated bundles from temporary configuration instead of touching real
    ``data/`` paths.

    Attributes:
        sessions: Session manager backing login and the auth middleware.
        events: Event hub serving SSE and in-process publishes.
        settings: File-backed settings store.
        catalog: Domain discovery service (routes mount from its view).
        exchange: Sandboxed file-exchange jail root.
        lifecycle: Status/shutdown state.
        ui_dist: Built-UI directory served at ``/``, or ``None``.
        cors_origins: Allowed browser origins for CORS preflight and requests.
    """

    sessions: SessionManager
    events: EventBus
    settings: SettingsStore
    catalog: CatalogService
    exchange: ExchangeFiles
    lifecycle: LifecycleState
    ui_dist: Path | None = None
    cors_origins: tuple[str, ...] = (
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    )


async def health(request: Request) -> JSONResponse:
    """Handle ``GET /api/v1/health``: host readiness and version."""
    request_id = request_id_of(request)
    lifecycle: LifecycleState = request.app.state.services.lifecycle
    services_map: dict[str, str] = {
        "host": "ready",
        "ui": "ready" if lifecycle.ui_ready else "pending",
    }
    data = {
        "status": "ready",
        "version": HOST_VERSION,
        "services": services_map,
    }
    return envelope_response(request_id, success_payload(request_id, data))


async def login(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/auth/login`` {username, password?}."""
    body = await read_json_body(request)
    request_id = request_id_of(request)
    username = body.get("username")
    if not isinstance(username, str):
        raise MalformedRequestError("Body must carry a string 'username'")
    password = body.get("password")
    manager: SessionManager = request.app.state.services.sessions
    try:
        token = manager.login(username, password if isinstance(password, str) else None)
    except SessionError:
        return envelope_response(
            request_id,
            error_payload(request_id, "UNAUTHORIZED", "Invalid credentials"),
            status_code=401,
        )
    return envelope_response(request_id, success_payload(request_id, {"token": token}))


async def app_loaded(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/app-loaded``: record UI readiness."""
    await read_json_body(request)
    request_id = request_id_of(request)
    lifecycle: LifecycleState = request.app.state.services.lifecycle
    lifecycle.mark_ui_ready()
    logger: logging.Logger = request.app.state.logger
    logger.info("UI reported readiness (request %s)", request_id)
    return envelope_response(
        request_id,
        success_payload(request_id, {"acknowledged": True}),
    )


class AuthMiddleware:
    """Pure-ASGI bearer-token enforcement for non-exempt API routes.

    Exemptions are deliberate and minimal: the liveness probes (``health``,
    ``status``), ``auth/login`` itself, and every non-``/api`` path so the
    static UI loads before a session exists. Anything else under ``/api``
    without a valid ``Authorization: Bearer`` token receives a ``401``
    error envelope. Implemented as raw ASGI (not ``BaseHTTPMiddleware``) so
    streaming responses — the SSE endpoint — pass through unbuffered.
    """

    def __init__(self, app: ASGIApp, manager: SessionManager) -> None:
        self.app = app
        self.manager = manager

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Enforce a bearer session for non-exempt API requests."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return
        path: str = scope["path"]
        if path in AUTH_EXEMPT_PATHS or not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        authorization = headers.get("Authorization", "")
        token = (
            authorization[len(_BEARER_PREFIX) :]
            if authorization.startswith(_BEARER_PREFIX)
            else ""
        )
        session = self.manager.verify(token) if token else None
        if session is None:
            request_id = headers.get("X-Request-Id") or request_id_of(Request(scope))
            response = envelope_response(
                request_id,
                error_payload(request_id, "UNAUTHORIZED", "Valid session required"),
                status_code=401,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


class AccessLogMiddleware:
    """Pure-ASGI per-request access logging (method, path, status, request id).

    One line per handled request, read from the response so the echoed
    request id is captured even when the host generated it. Payloads are
    never logged. Positioned outside the auth middleware, rejections are
    logged too.
    """

    def __init__(self, app: ASGIApp, logger: logging.Logger) -> None:
        self.app = app
        self.logger = logger

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Serve the request and log method, path, status, and request id."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        status_holder = {"status": 0, "request_id": "-"}

        async def send_wrapper(message: Any) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = int(message["status"])
                response_headers = Headers(raw=message["headers"])
                status_holder["request_id"] = response_headers.get("X-Request-Id", "-")
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            self.logger.info(
                "%s %s -> %s (%s)",
                scope["method"],
                scope["path"],
                status_holder["status"],
                status_holder["request_id"],
            )


class SPAStaticFiles(StaticFiles):
    """Static file server that falls back to ``index.html`` for SPA routes."""

    SPA_FALLBACK_STATUS = 404

    @override
    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except HTTPException as err:
            if err.status_code != self.SPA_FALLBACK_STATUS:
                raise
            return await super().get_response("index.html", scope)
        if response.status_code == self.SPA_FALLBACK_STATUS:
            return await super().get_response("index.html", scope)
        return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert HTTP exceptions (404, 405, ...) into error envelopes."""
    request_id = request_id_of(request)
    code_by_status = {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
    }
    code = code_by_status.get(exc.status_code, f"HTTP_{exc.status_code}")
    message = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return envelope_response(
        request_id,
        error_payload(request_id, code, message),
        status_code=exc.status_code,
    )


async def malformed_request_handler(
    request: Request, exc: MalformedRequestError
) -> JSONResponse:
    """Convert malformed-body failures into a 400 error envelope."""
    request_id = request_id_of(request)
    return envelope_response(
        request_id,
        error_payload(request_id, "MALFORMED_REQUEST", str(exc)),
        status_code=400,
    )


async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fail closed on unexpected errors without leaking internals."""
    request_id = request_id_of(request)
    logger: logging.Logger = request.app.state.logger
    logger.error("Unhandled error while serving request %s", request_id, exc_info=exc)
    return envelope_response(
        request_id,
        error_payload(request_id, "INTERNAL_ERROR", "Internal host error"),
        status_code=500,
    )


def _mounted_domains(
    view: CatalogView, host_routes: list[BaseRoute]
) -> tuple[list[BaseRoute], CatalogView]:
    """Mount nonconflicting domains and freeze the view exposed by this app."""
    mounts: list[BaseRoute] = []
    accepted: list[DomainManifest] = []
    issues = list(view.issues)
    reserved = tuple(route.path for route in host_routes if isinstance(route, Route))
    for manifest in view.domains:
        base = manifest.route_base.rstrip("/")
        if any(
            base == path or path.startswith(f"{base}/") or base.startswith(f"{path}/")
            for path in reserved
        ):
            issues.append(
                ValidationIssue(
                    path=f"{manifest.domain_id}:route_base",
                    code="reserved_route",
                    message=(
                        f"Domain route {manifest.route_base!r} conflicts "
                        "with a host route"
                    ),
                )
            )
            continue
        accepted.append(manifest)
        if manifest.module is None:
            continue
        mounts.append(domain_routes(manifest))
    return mounts, CatalogView(domains=tuple(accepted), issues=tuple(issues))


def create_app(
    services: HostServices, logger: logging.Logger | None = None
) -> Starlette:
    """Build the host application with every feature wired in.

    Route order is: the 14 host commands, then catalog-mounted domain
    routes, then — only when ``ui_dist`` contains an ``index.html`` — the
    SPA static mount at ``/``. Middleware ordering matters: auth sits
    inside the access log, so unauthorized attempts are logged; the access
    log sits inside Starlette's server-error handler, so crashes are too.

    Args:
        services: The fully assembled feature bundle.
        logger: Logger for app-side records; defaults to the shared host
            logger.

    Returns:
        A ready-to-serve Starlette application with ``state.services``,
        ``state.logger``, and ``state.version`` attached.
    """
    routes: list[BaseRoute] = [
        Route("/api/v1/health", health, methods=["GET"]),
        Route("/api/v1/status", status_endpoint, methods=["GET"]),
        Route("/api/v1/auth/login", login, methods=["POST"]),
        Route("/api/v1/app-loaded", app_loaded, methods=["POST"]),
        Route("/api/v1/settings", get_settings, methods=["GET"]),
        Route("/api/v1/settings", put_settings, methods=["PUT"]),
        Route("/api/v1/events", subscribe_events, methods=["GET"]),
        Route("/api/v1/events/publish", publish_event, methods=["POST"]),
        Route("/api/v1/catalog", catalog_endpoint, methods=["GET"]),
        Route("/api/v1/commands/open-link", open_link_endpoint, methods=["POST"]),
        Route("/api/v1/commands/copy", copy_endpoint, methods=["POST"]),
        Route("/api/v1/files/read", files_read_endpoint, methods=["POST"]),
        Route("/api/v1/files/write", files_write_endpoint, methods=["POST"]),
        Route("/api/v1/files/exists", files_exists_endpoint, methods=["POST"]),
        Route("/api/v1/files/list", files_list_endpoint, methods=["POST"]),
        Route("/api/v1/files/delete", files_delete_endpoint, methods=["POST"]),
        Route("/api/v1/shutdown", shutdown_endpoint, methods=["POST"]),
    ]
    mounts, catalog_view = _mounted_domains(services.catalog.view, routes)
    routes.extend(mounts)

    if services.ui_dist is not None and (services.ui_dist / "index.html").is_file():
        routes.append(
            Mount("/", SPAStaticFiles(directory=services.ui_dist, html=True), name="ui")
        )

    resolved_logger = logger if logger is not None else logging.getLogger(LOGGER_NAME)
    handlers: dict[type[Exception], Any] = {
        HTTPException: http_exception_handler,
        MalformedRequestError: malformed_request_handler,
        Exception: internal_error_handler,
    }
    app = Starlette(
        routes=routes,
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=list(services.cors_origins),
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
            Middleware(AuthMiddleware, manager=services.sessions),
            Middleware(AccessLogMiddleware, logger=resolved_logger),
        ],
        exception_handlers=handlers,
    )
    app.state.services = services
    app.state.catalog_view = catalog_view
    app.state.logger = resolved_logger
    app.state.version = HOST_VERSION
    return app
