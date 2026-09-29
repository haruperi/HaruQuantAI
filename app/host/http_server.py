"""HTTP and WebSocket adapters for one explicitly assembled host.

create_app installs routes, CORS/trusted-host middleware, and an HTTP guard.
The lifespan delegates resource acquisition and cleanup to BootstrapCoordinator.
Protected routes share session authority across browser and CLI; WebSockets
use first-frame credentials rather than query-string tokens. Handlers adapt
host services and never implement quantitative workspace algorithms.

Application API responses use the shared envelope. Framework middleware/static
responses can have other shapes. Public failures omit request and credential
values; callers must still avoid placing secrets in ordinary diagnostic text.
"""

import asyncio
import base64
import json
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, WebSocket
from pydantic import JsonValue, TypeAdapter
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.websockets import WebSocketDisconnect

from app.host.bootstrap import BootstrapCoordinator
from app.host.commands import CommandError, copy_text, open_link
from app.host.envelope import error_payload, new_request_id, success_payload
from app.host.events import ChannelError
from app.host.logging import get_logger
from app.host.resource_store import ResourceRef
from app.host.sessions import SessionError
from app.host.settings import SettingsConflictError, SettingsError

logger = get_logger(__name__)
MAX_USERNAME = 100
MAX_CREDENTIAL = 1024
MAX_AUTH_FRAME = 2048
MAX_BODY = 11 * 1024 * 1024


def response(
    request: Request, data: Any, *, code: str | None = None, status: int = 200
) -> JSONResponse:
    """Construct an API envelope and matching request-ID header.

    Args:
        request: Request carrying the guard-assigned ID, if present.
        data: Success payload or safe error message when code is set.
        code: Error code, or None for success.
        status: HTTP status code independently selected by the handler.

    Returns:
        JSONResponse with the shared envelope and X-Request-Id.
    """
    request_id = getattr(request.state, "request_id", new_request_id())
    payload = (
        success_payload(request_id, data)
        if code is None
        else error_payload(request_id, code, str(data))
    )
    return JSONResponse(
        payload, status_code=status, headers={"X-Request-Id": request_id}
    )


async def body(request: Request) -> dict[str, Any]:
    """Read a streamed request body up to MAX_BODY and decode an object.

    The bounded bytes are buffered until decoding completes. Transport errors
    propagate to the HTTP guard; this helper does not validate endpoint fields.

    Args:
        request: Incoming request whose stream will be consumed.

    Returns:
        Decoded JSON object.

    Raises:
        ValueError: Size limit or JSON decoding fails.
        TypeError: Decoded root is not an object.
    """
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > MAX_BODY:
            raise ValueError("Request body exceeds limit")
    value = json.loads(content)
    if not isinstance(value, dict):
        raise TypeError("Request body must be an object")
    return value


def service(request: Request) -> BootstrapCoordinator:
    """Retrieve the coordinator attached during application assembly.

    Args:
        request: Request associated with a create_app application.

    Returns:
        The app.state.services coordinator; no registry or filesystem lookup occurs.
    """
    result: BootstrapCoordinator = request.app.state.services
    return result


async def status_endpoint(request: Request) -> JSONResponse:
    """Expose unauthenticated process health and stage availability.

    Reads existing state only. A SERVER_READY response does not claim that research
    providers exist or that a client has completed initialization.

    Args:
        request: GET status or health request.

    Returns:
        Envelope with lifecycle status, host version, resource snapshot, and boot
        stages.
    """
    host = service(request)
    return response(
        request,
        {
            "status": host.startup.state,
            "version": "2.1.0",
            **host.resources,
            "boot": host.startup.snapshot().model_dump(mode="json"),
        },
    )


async def login_endpoint(request: Request) -> JSONResponse:
    """Validate bounded credentials and issue a session token.

    Uses the transport peer address, not forwarding headers. Successful login
    does not change boot phases; malformed bodies use the outer request guard.

    Args:
        request: POST request with optional username/password JSON fields.

    Returns:
        Token envelope on success or 401 for rejected credentials/retry limits.
    """
    payload = await body(request)
    username = payload.get("username", "haruquantai")
    password = payload.get("password")
    if (
        not isinstance(username, str)
        or len(username) > MAX_USERNAME
        or (
            password is not None
            and (not isinstance(password, str) or len(password) > MAX_CREDENTIAL)
        )
    ):
        return response(request, "Invalid credentials", code="UNAUTHORIZED", status=401)
    host = service(request)
    try:
        token = host.session_manager().login(
            username, password, peer=request.client.host if request.client else ""
        )
    except SessionError:
        return response(
            request,
            "Invalid credentials or retry limit",
            code="UNAUTHORIZED",
            status=401,
        )
    return response(request, {"token": token})


async def settings_endpoint(request: Request) -> JSONResponse:
    """Read public settings or perform a revision-checked field update.

    Publication follows the committed patch. Private fields are neither exposed
    nor replaced by omission from a client patch.

    Args:
        request: Authenticated GET, or PUT with changes and expected_revision.

    Returns:
        Public snapshot; invalid settings yield 400 and revision conflicts yield 409.
    """
    host = service(request)
    if request.method == "GET":
        return response(request, host.settings.snapshot())
    payload = await body(request)
    changes = payload.get("changes")
    revision = payload.get("expected_revision")
    if not isinstance(changes, dict) or type(revision) is not int:
        return response(
            request,
            "Expected changes and revision",
            code="INVALID_SETTINGS",
            status=400,
        )
    try:
        saved = host.settings.patch(changes, revision, bus=host.events)
    except SettingsConflictError:
        return response(
            request,
            "Settings changed; reload and retry",
            code="SETTINGS_CONFLICT",
            status=409,
        )
    except SettingsError:
        return response(
            request, "Invalid settings", code="INVALID_SETTINGS", status=400
        )
    return response(request, saved)


async def resources_endpoint(request: Request) -> JSONResponse:
    """Read published immutable resources independently of producer installation.

    The browser principal never impersonates a plugin. Private plugin publications
    are absent unless explicitly granted to host.operator or made public.
    """
    store = service(request).resource_store
    if request.method == "GET":
        references = await asyncio.to_thread(store.list, "host.operator")
        return response(request, [ref.model_dump(mode="json") for ref in references])
    reference = ResourceRef.model_validate(await body(request))
    try:
        content, schema = await asyncio.to_thread(
            store.read, "host.operator", reference
        )
    except PermissionError, FileNotFoundError:
        return response(
            request, "Resource unavailable", code="RESOURCE_UNAVAILABLE", status=404
        )
    return response(
        request,
        {"content_base64": base64.b64encode(content).decode("ascii"), "schema": schema},
    )


async def contributions_endpoint(request: Request) -> JSONResponse:
    """Expose accepted execution capabilities, separately from discovered metadata."""
    host = service(request)
    composition = host.composition
    return response(
        request,
        {
            "packages": [
                p.model_dump(mode="json") for p in host.package_inventory.packages
            ],
            "active": {
                key: list(item.operations) for key, item in composition.active.items()
            }
            if composition
            else {},
            "issues": [issue.model_dump(mode="json") for issue in composition.issues]
            if composition
            else [],
        },
    )


async def contribution_operation_endpoint(request: Request) -> JSONResponse:
    """Dispatch to an activated package without mutating data on missing capability."""
    composition = service(request).composition
    owner = request.path_params["owner"]
    operation = request.path_params["operation"]
    if (
        composition is None
        or owner not in composition.active
        or operation not in composition.active[owner].operations
    ):
        return response(
            request, "Missing capability", code="MISSING_CAPABILITY", status=503
        )
    payload: JsonValue = TypeAdapter(JsonValue).validate_python(await body(request))
    return response(request, await composition.invoke(owner, operation, payload))


async def init_endpoint(request: Request) -> JSONResponse:
    """Return the shared browser/CLI initialization payload.

    first_run reflects whether any catalog entry is available, not whether the
    database is empty or whether the user has previously opened the UI.

    Args:
        request: Authenticated initial-state GET request.

    Returns:
        Settings, catalog, presets, boot snapshot, and research setup requirements.
    """
    host = service(request)
    return response(
        request,
        {
            "settings": host.settings.snapshot(),
            "catalog": host.catalog,
            "boot": host.startup.snapshot().model_dump(mode="json"),
            "first_run": not any(item["available"] for item in host.catalog["domains"]),
            "requirements": ["No research providers are available"]
            if not any(item["available"] for item in host.catalog["domains"])
            else [],
            "presets": host.presets,
        },
    )


async def catalog_endpoint(request: Request) -> JSONResponse:
    """Serve the metadata inventory captured during startup.

    Args:
        request: Authenticated catalog GET request.

    Returns:
        The stored catalog snapshot; no rescan or provider activation occurs.
    """
    return response(request, service(request).catalog)


async def loaded_endpoint(request: Request) -> JSONResponse:
    """Acknowledge readiness for a previously attached session.

    Records per-session initialization only. HTTP success means acknowledgment
    was accepted; it does not start shared work or change host readiness.

    Args:
        request: Authenticated POST with session authority attached by the guard.

    Returns:
        Acknowledgment envelope, or 409 if attachment/deadline requirements fail.
    """
    host = service(request)
    try:
        host.startup.acknowledge(request.state.session.key)
    except ValueError:
        return response(
            request,
            "Attach updates and complete readiness within 30 seconds",
            code="CLIENT_NOT_READY",
            status=409,
        )
    return response(request, {"acknowledged": True})


async def shutdown_endpoint(request: Request) -> JSONResponse:
    """Signal graceful host shutdown after HTTP authentication.

    Sets the coordinator event consumed by the server watcher. Does not directly
    terminate the process, close resources, or wait for shutdown completion.

    Args:
        request: Authenticated operator shutdown request.

    Returns:
        Envelope confirming that shutdown was requested.
    """
    service(request).shutdown_event.set()
    logger.info("Authorized shutdown requested")
    return response(request, {"shutdown": "requested"})


async def command_endpoint(request: Request) -> JSONResponse:
    """Validate supported shell mediation requests without executing OS actions.

    Only open-link and copy are supported. The client performs the actual browser
    or clipboard action; the guard converts CommandError to a safe 422 response.

    Args:
        request: Authenticated POST with operation path parameter and url or text
            payload.

    Returns:
        Validated client-side action value, or 503 when no research handler exists.

    Raises:
        CommandError: Required text or command-specific validation fails.
    """
    payload = await body(request)
    operation = request.path_params["operation"]
    if operation not in ("open-link", "copy"):
        return response(
            request,
            "No registered command provider",
            code="MISSING_DEPENDENCY",
            status=503,
        )
    key = "url" if operation == "open-link" else "text"
    value = payload.get(key)
    if not isinstance(value, str):
        raise CommandError("Expected text")
    validated = open_link(value) if key == "url" else copy_text(value)
    logger.info("Shell command validated: %s", operation)
    return response(request, {key: validated})


async def file_endpoint(request: Request) -> JSONResponse:
    """Dispatch bounded text-file exchange through the confined root.

    Write/delete mutate exchange files; they do not import strategies or access
    domain storage. ExchangeFiles validates confinement and size constraints.

    Args:
        request: Authenticated POST selecting read, write, exists, delete, or list.

    Returns:
        Operation-specific envelope, or 404 for an unknown operation.

    Raises:
        CommandError: Path or text arguments are missing or invalid.
    """
    payload = await body(request)
    operation = request.path_params["operation"]
    exchange = service(request).exchange
    path = payload.get("prefix", "") if operation == "list" else payload.get("path")
    if not isinstance(path, str):
        raise CommandError("Expected relative path")
    if operation == "read":
        data: dict[str, Any] = {"content": exchange.read(path)}
    elif operation == "write":
        content = payload.get("content")
        if not isinstance(content, str):
            raise CommandError("Expected text content")
        data = {"bytes": exchange.write(path, content)}
    elif operation == "exists":
        data = {"path": path, **exchange.exists(path)}
    elif operation == "delete":
        data = {"path": path, "deleted": exchange.delete(path)}
    elif operation == "list":
        files = exchange.list_files(path)
        data = {"files": files, "count": len(files)}
    else:
        return response(request, "Unknown file operation", code="NOT_FOUND", status=404)
    return response(request, data)


async def sse_endpoint(request: Request) -> Response:
    """Subscribe an authenticated client to public settings changes.

    The stream rechecks session validity, emits ten-second idle heartbeats, and
    sends reset on queue overflow. Shutdown/disconnect releases its subscription.

    Args:
        request: GET with channels=settings.changed and a bearer header.

    Returns:
        SSE stream, or 400 when the requested channel set is not allowed.
    """
    host = service(request)
    channels = request.query_params.get("channels", "").split(",")
    if channels != ["settings.changed"]:
        return response(
            request, "Only settings.changed is public", code="BAD_REQUEST", status=400
        )
    subscriber = host.events.subscribe(channels)
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")

    async def stream() -> AsyncIterator[bytes]:
        """Yield settings events until shutdown, expiry, overflow, or cancellation.

        Yields:
            Encoded SSE data, idle heartbeat, or reset frames.

        Each iteration owns queue/shutdown wait tasks and cancels them in finally.
        The enclosing subscription is released even when the stream is cancelled.
        """
        try:
            while (
                not host.shutdown_event.is_set()
                and host.session_manager().verify(token) is not None
            ):
                if subscriber.overflow:
                    yield b"event: reset\ndata: {}\n\n"
                    return
                pending = asyncio.create_task(subscriber.queue.get())
                stopped = asyncio.create_task(host.shutdown_event.wait())
                try:
                    done, _ = await asyncio.wait(
                        (pending, stopped),
                        timeout=10,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if stopped in done:
                        return
                    if pending in done:
                        yield (
                            "data: " + json.dumps(pending.result()) + "\n\n"
                        ).encode()
                    else:
                        yield b": heartbeat\n\n"
                finally:
                    pending.cancel()
                    stopped.cancel()
                    await asyncio.gather(pending, stopped, return_exceptions=True)
        finally:
            host.events.unsubscribe(subscriber)

    return StreamingResponse(stream(), media_type="text/event-stream")


async def socket_endpoint(socket: WebSocket) -> None:
    """Authenticate and attach one updates/control WebSocket.

    Rejects untrusted origins and invalid first-frame authority with close 1008.
    Authentication must arrive within five seconds and the bounded frame limit.
    Admitted clients receive a boot snapshot/history and readiness tracking. The
    subscription is always released on disconnect or protocol failure.

    Args:
        socket: ASGI socket carrying an allowed origin and a first-frame token/topics
            object.
    """
    host: BootstrapCoordinator = socket.app.state.services
    origin = socket.headers.get("origin")
    scheme = "https" if socket.url.scheme == "wss" else "http"
    own_origin = f"{scheme}://{socket.url.netloc}"
    if origin is not None and origin not in (*host.config.origins, own_origin):
        await socket.close(code=1008)
        return
    await socket.accept()
    subscriber = None
    try:
        raw = await asyncio.wait_for(socket.receive_text(), timeout=5)
        if len(raw) > MAX_AUTH_FRAME:
            raise ValueError("Oversized authentication")  # noqa: TRY301 -- protocol rejection closes the socket here.
        payload = json.loads(raw)
        token = payload.get("token") if isinstance(payload, dict) else None
        if not isinstance(token, str):
            raise ValueError("Authentication required")  # noqa: TRY301, TRY004 -- uniform protocol failure.
        session = host.session_manager().verify(token)
        if session is None:
            raise ValueError("Invalid session")  # noqa: TRY301 -- uniform protocol failure.
        channels = payload.get("topics", ["boot.progress", "settings.changed"])
        if not isinstance(channels, list) or not all(
            channel in ("boot.progress", "settings.changed") for channel in channels
        ):
            raise ValueError("Topic denied")  # noqa: TRY301 -- uniform protocol failure.
        subscriber = host.events.subscribe(channels)
        host.startup.connected(session.key)
        await socket.send_json(
            {
                "type": "snapshot",
                "boot": host.startup.snapshot().model_dump(mode="json"),
                "history": host.events.replay(),
            }
        )
        await _socket_stream(socket, host, subscriber, token)
    except ValueError, TimeoutError, ChannelError:
        await socket.close(code=1008)
    except WebSocketDisconnect:
        logger.debug("Client socket disconnected")
    finally:
        if subscriber is not None:
            host.events.unsubscribe(subscriber)


async def _socket_stream(
    socket: WebSocket, host: BootstrapCoordinator, subscriber: Any, token: str
) -> None:
    """Multiplex queued events and bounded ping messages for an attached client.

    Emits five-second idle heartbeats and returns a resync marker on overflow.
    Expiry closes with 1008. Owns and cancels receive/queue tasks; outer socket
    handling owns subscription release and disconnect handling.

    Args:
        socket: Accepted authenticated WebSocket.
        host: Coordinator providing live state and session verification.
        subscriber: EventBus subscriber owned by socket_endpoint.
        token: In-memory bearer credential rechecked between waits.

    Raises:
        ValueError: A control frame exceeds limits or is not a ping.
    """
    receive = asyncio.create_task(socket.receive_text())
    try:
        while host.session_manager().verify(token) is not None:
            if subscriber.overflow:
                await socket.send_json({"type": "resync_required"})
                return
            event = asyncio.create_task(subscriber.queue.get())
            try:
                done, _ = await asyncio.wait(
                    (receive, event), timeout=5, return_when=asyncio.FIRST_COMPLETED
                )
                if receive in done:
                    raw = receive.result()
                    if len(raw) > MAX_CREDENTIAL:
                        raise ValueError("Control frame too large")
                    message = json.loads(raw)
                    if not isinstance(message, dict) or message.get("type") != "ping":
                        raise ValueError("Unknown control message")
                    await socket.send_json({"type": "pong"})
                    receive = asyncio.create_task(socket.receive_text())
                if event in done:
                    await socket.send_json(event.result())
                elif not done:
                    await socket.send_json(
                        {"type": "heartbeat", "state": host.startup.state}
                    )
            finally:
                event.cancel()
                await asyncio.gather(event, return_exceptions=True)
        await socket.close(code=1008)
    finally:
        receive.cancel()
        await asyncio.gather(receive, return_exceptions=True)


async def spa_endpoint(request: Request) -> Response:
    """Serve built UI assets or the SPA entrypoint within ui_dist.

    Resolves paths before checking confinement. API/ws paths are never redirected
    to index.html. This serves the built bundle, not the development Vite process.

    Args:
        request: GET with an optional relative path route parameter.

    Returns:
        File response; 404 for escaped/reserved routes, or 503 without a built UI.
    """
    root = service(request).config.ui_dist.resolve()
    relative = request.path_params.get("path", "")
    if relative.startswith(("api/", "ws/")):
        return response(request, "Route not found", code="NOT_FOUND", status=404)
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        return response(request, "Route not found", code="NOT_FOUND", status=404)
    if not target.is_file():
        target = root / "index.html"
    if not target.is_file():
        return response(
            request,
            "UI bundle unavailable; run the Vite client",
            code="UI_UNAVAILABLE",
            status=503,
        )
    return FileResponse(target)


def create_app(host: BootstrapCoordinator) -> FastAPI:
    """Assemble transport routes around an explicitly supplied coordinator.

    Assembly registers handlers but does not bind a socket. Trusted-host and CORS
    configuration come from the injected runtime settings; API docs are disabled.

    Args:
        host: Unstarted coordinator retained in app.state.services.

    Returns:
        FastAPI app configured for lifespan-managed startup and cleanup.
    """

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        """Initialize host services and hold them until ASGI shutdown.

        Args:
            _app: ASGI application supplied by FastAPI; services use the closed-over
                host.

        Yields:
            None once initialization and static-bundle inspection have completed.

        Completes transport preparation before serving, then closes the coordinator;
        initialization failures use the coordinator's own cleanup path and propagate.
        """
        await host.initialize()
        host.startup.mark(
            "transport",
            reason="routes_assembled"
            if (host.config.ui_dist / "index.html").is_file()
            else "ui_bundle_unavailable",
        )
        host.startup.mark("serving", "running")
        try:
            yield
        finally:
            await host.close()

    host.startup.mark("transport", "running")
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.services = host

    app.middleware("http")(request_guard(host))

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[host.config.host, "localhost", "127.0.0.1", "[::1]"],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(host.config.origins),
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id"],
    )
    for path, endpoint, methods in (
        ("status", status_endpoint, ["GET"]),
        ("health", status_endpoint, ["GET"]),
        ("auth/login", login_endpoint, ["POST"]),
        ("settings", settings_endpoint, ["GET", "PUT"]),
        ("init-data", init_endpoint, ["GET"]),
        ("catalog", catalog_endpoint, ["GET"]),
        ("app-loaded", loaded_endpoint, ["POST"]),
        ("shutdown", shutdown_endpoint, ["POST"]),
        ("events", sse_endpoint, ["GET"]),
        ("commands/{operation}", command_endpoint, ["POST"]),
        ("files/{operation}", file_endpoint, ["POST"]),
        ("resources/", resources_endpoint, ["GET"]),
        ("resources/read", resources_endpoint, ["POST"]),
        ("contributions", contributions_endpoint, ["GET"]),
        (
            "contributions/{owner}/{operation}",
            contribution_operation_endpoint,
            ["POST"],
        ),
    ):
        app.add_api_route("/api/v1/" + path, endpoint, methods=methods)
    app.add_api_websocket_route("/ws/updates", socket_endpoint)
    app.add_api_websocket_route("/ws/control", socket_endpoint)
    app.add_api_route("/{path:path}", spa_endpoint, methods=["GET"])
    return app


def request_guard(
    host: BootstrapCoordinator,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """Build authentication and safe API error middleware for one host.

    Args:
        host: Coordinator supplying initialized session authority.

    Returns:
        Async middleware callable accepting a request and downstream handler.
    """

    async def guard(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Assign request identity and enforce protected API session authority.

        Health, status, and login are public. Other /api/ routes require a valid session
        which is attached to request.state. Known downstream errors map to safe codes;
        unexpected downstream exceptions log only the request ID. Non-API requests
        pass through, and CORS/trusted-host checks belong to separate middleware.

        Args:
            request: Incoming HTTP request.
            call_next: Downstream middleware/router continuation.

        Returns:
            Downstream response or a safe 401/422/400/500 API error envelope.
        """
        request.state.request_id = new_request_id()
        if request.url.path.startswith("/api/"):
            if request.url.path not in (
                "/api/v1/status",
                "/api/v1/health",
                "/api/v1/auth/login",
            ):
                token = request.headers.get("Authorization", "").removeprefix("Bearer ")
                session = host.session_manager().verify(token)
                if session is None:
                    return response(
                        request,
                        "Authentication required",
                        code="UNAUTHORIZED",
                        status=401,
                    )
                request.state.session = session
            try:
                return await call_next(request)
            except CommandError:
                return response(
                    request, "Command rejected", code="COMMAND_REJECTED", status=422
                )
            except ValueError, TypeError, UnicodeError:
                return response(
                    request, "Malformed request", code="MALFORMED_REQUEST", status=400
                )
            except Exception:  # noqa: BLE001 -- public error boundary must not leak request/secret details.
                logger.error(  # noqa: TRY400 -- redact by omission at the public boundary.
                    "HTTP request failed; request_id=%s", request.state.request_id
                )
                return response(
                    request, "Host operation failed", code="INTERNAL_ERROR", status=500
                )
        return await call_next(request)

    return guard
