"""Unified ASGI Application Factory, Wire Protocol Envelopes, and Command Mediation.

Description:
    This module provides the HTTP and WebSocket wire protocol adaptation layer
    for the HaruQuantAI host process. It exists to guarantee uniform API envelope
    packaging, request correlation tracing, sandboxed command execution, jailed
    file exchange, and resilient real-time WebSocket communication. Externally,
    it mediates all communications between client interfaces (browser UI, CLI
    tools, testing harnesses) and the backend host subsystems (`BootstrapCoordinator`,
    `SessionManager`, `SettingsStore`, `ResourceStore`, and `EventBus`). During
    startup, `app.main` passes the initialized `BootstrapCoordinator` to
    `create_app()`, and the resulting FastAPI ASGI application's lifespan manages
    the asynchronous boot and graceful teardown sequences. Internally, `request_guard()`
    assigns unique `X-Request-Id` tracing headers and verifies bearer sessions;
    standardized envelope builders (`success()`, `failure()`, `render_error()`)
    enforce wire schema consistency; `ExchangeFiles` enforces path jail confinement
    for file exchanges; and `handle_command()` dispatches mediated system commands.

Purpose:
    FEAT-HOST-TRANSPORT: Uniform API Envelopes, Command Mediation, and ASGI Transport.
    Provides standard JSON API envelopes, request correlation tracing, jailed
    file exchange, sandboxed command dispatch, and WebSocket event streaming.

Key Capabilities:
    - FR-HOST-TRANSPORT-UNIFORM-ENVELOPE: Standardized JSON Wire Envelopes
      Associated: `success()`, `failure()`, `render_error()`, `response()`
      Logging: Emits debug log on response rendering and warning log on
      validation or error response packaging.
    - FR-HOST-TRANSPORT-REQUEST-TRACING: Correlation Tracing and Request Guard
      Associated: `request_guard()`, `new_request_id()`
      Logging: Emits debug log with correlation ID on request arrival and
      warning log on unauthorized access or authentication rejection.
    - FR-HOST-TRANSPORT-COMMAND-MEDIATION: Sandboxed Command Dispatch
      Associated: `handle_command()`, `COMMAND_HANDLERS`
      Logging: Emits info log on command dispatch completion and warning
      log on command validation or execution error.
    - FR-HOST-TRANSPORT-JAILED-EXCHANGE: Confined Filesystem File Exchange
      Associated: `ExchangeFiles.read()`, `ExchangeFiles.write()`,
      `ExchangeFiles.delete()`
      Logging: Emits info log when exchange files are written or deleted
      within the storage jail.
    - FR-HOST-TRANSPORT-WEBSOCKET-STREAM: Authenticated Live Event Streaming
      Associated: `socket_endpoint()`, `_socket_stream()`
      Logging: Emits debug logs on socket connection, subscription dispatch,
      and graceful client disconnection.
    - FR-HOST-TRANSPORT-LIFESPAN-MANAGEMENT: ASGI Lifecycle Coordination
      Associated: `_lifespan()`, `create_app()`
      Logging: Emits info logs during ASGI lifespan startup and shutdown
      transitions.

Python API Usage:
    ```python
    from app.host.bootstrap import BootstrapCoordinator
    from app.host.settings import HostSettings
    from app.host.transport import create_app

    # 1. Instantiate coordinator and create ASGI application
    settings = HostSettings()
    coordinator = BootstrapCoordinator(settings)
    app = create_app(coordinator)

    # 2. Run via ASGI server (e.g. Uvicorn)
    # uvicorn.run(app, host=settings.host, port=settings.port)
    ```

CLI Usage:
    The transport layer is activated when running the main application:
    ```bash
    # Launch ASGI web server
    uv run python -m app.main --host 127.0.0.1 --port 8000

    # Test API health endpoint via curl
    curl -s http://127.0.0.1:8000/health
    ```
"""

from __future__ import annotations

import asyncio
import base64
import json
import secrets
import time
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from fastapi import FastAPI, Request, WebSocket
from pydantic import JsonValue, TypeAdapter
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.websockets import WebSocketDisconnect

from app.host.events import ChannelError
from app.host.logging import get_logger
from app.host.sessions import SessionError
from app.host.settings import SettingsConflictError, SettingsError
from app.persistence.resources import ResourceRef

if TYPE_CHECKING:
    from app.host.bootstrap import BootstrapCoordinator

logger = get_logger(__name__)

# --- API Envelope Contracts ---

API_VERSION = "1.0"


@dataclass(frozen=True)
class ValidationIssue:
    """A single structured validation problem tied to a payload location.

    Attributes:
        path: JSON-Pointer-like location of the problem (for example
            ``$.nodes`` for documents, or the offending field name).
        code: Stable machine-readable problem code (for example ``required``,
            ``invalid``, ``too_large``).
        message: Human-readable explanation safe to show to a user.
    """

    path: str
    code: str
    message: str

    def to_json(self) -> dict[str, str]:
        """Return the wire representation of this issue.

        Returns:
            A fresh ``{"path", "code", "message"}`` object.
        """
        return {"path": self.path, "code": self.code, "message": self.message}


@dataclass(frozen=True)
class ErrorBody:
    """The error half of the envelope, mirroring the UI ``ApiClientError``.

    Attributes:
        code: Stable machine-readable error code (for example ``NOT_FOUND``,
            ``UNAUTHORIZED``, ``MALFORMED_REQUEST``).
        message: Human-readable error text safe to display.
        issues: Optional structured validation detail; empty when the error
            is not tied to specific payload locations.
    """

    code: str
    message: str
    issues: tuple[ValidationIssue, ...] = ()

    def to_json(self) -> dict[str, Any]:
        """Return the wire representation of this error body.

        Returns:
            A fresh object with ``code``, ``message``, and a list of
            serialized :class:`ValidationIssue` entries.
        """
        return {
            "code": self.code,
            "message": self.message,
            "issues": [issue.to_json() for issue in self.issues],
        }


def new_request_id() -> str:
    """Generate a timestamped diagnostic request identifier.

    Uses wall-clock nanoseconds and random entropy to reduce collisions. It is a
    correlation label, not an authentication token or a uniqueness guarantee.

    Returns:
        req-<timestamp-nanos>-<hex> with four random bytes encoded as hex.
    """
    return f"req-{time.time_ns()}-{secrets.token_hex(4)}"


def success_payload(request_id: str, data: Any) -> dict[str, Any]:
    """Build a success envelope body carrying ``data``.

    Args:
        request_id: The request id echoed into the envelope.
        data: Any JSON-serializable payload to return to the caller.

    Returns:
        The envelope object with ``status: "success"``.
    """
    return {
        "api_version": API_VERSION,
        "request_id": request_id,
        "status": "success",
        "data": data,
    }


def error_payload(
    request_id: str,
    code: str,
    message: str,
    issues: Sequence[ValidationIssue] = (),
) -> dict[str, Any]:
    """Build an error envelope body carrying a structured error.

    Args:
        request_id: The request id echoed into the envelope.
        code: Stable machine-readable error code.
        message: Human-readable error text safe to display.
        issues: Optional structured validation detail.

    Returns:
        The envelope object with ``status: "error"``.
    """
    body_obj = ErrorBody(code=code, message=message, issues=tuple(issues))
    return {
        "api_version": API_VERSION,
        "request_id": request_id,
        "status": "error",
        "error": body_obj.to_json(),
    }


# --- Command Mediation and File Exchange ---

MAX_TEXT_BYTES = 8 * 1024
MAX_LIST_ENTRIES = 4096
MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_LINK_SCHEMES = ("http", "https")


class CommandError(Exception):
    """Signal rejected command input or a wrapped exchange-file failure.

    The HTTP guard emits a generic COMMAND_REJECTED response rather than exposing
    raw filesystem exception text. Direct callers may inspect the exception but
    must avoid forwarding sensitive path details into public diagnostics.
    """


def open_link(url: str) -> str:
    """Validate ``url`` as an openable http/https link and return it.

    Args:
        url: Candidate URL supplied by the client.

    Returns:
        The same URL when it carries an allowed scheme and a host.

    Raises:
        CommandError: When the scheme is not http/https or the host is
            empty.
    """
    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_LINK_SCHEMES or not parts.netloc:
        raise CommandError("Only http/https URLs with a host can be opened")
    return url


def copy_text(text: str) -> str:
    """Validate length-capped copy text and return it.

    Args:
        text: Text the client intends to place on its clipboard.

    Returns:
        The same text when within the byte cap.

    Raises:
        CommandError: When the UTF-8 encoded text exceeds
            ``MAX_TEXT_BYTES``.
    """
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise CommandError(f"Copy text exceeds {MAX_TEXT_BYTES} bytes")
    return text


@dataclass(frozen=True)
class ExchangeFiles:
    """Read/write file access jailed to one root directory.

    The jail is enforced by construction: every path is resolved against
    ``root`` and must land inside it (checked after resolution, so symlinks
    and ``..`` segments cannot smuggle paths out). Subdirectories are
    created on write; reads of missing files fail closed.
    """

    root: Path

    def _resolve(self, relative: str) -> Path:
        """Resolve an exchange-relative path and enforce current containment.

        Resolution follows file links before confinement checks. This does not reserve
        the path against concurrent replacement by another filesystem actor.

        Args:
            relative: Relative path without a drive, colon, or parent traversal
                component.

        Returns:
            Resolved path inside the configured root; existence is not required.

        Raises:
            CommandError: The path is absolute, contains forbidden components, or
                resolves outside root.
        """
        candidate = Path(relative)
        if (
            candidate.is_absolute()
            or candidate.drive
            or ":" in relative
            or ".." in candidate.parts
        ):
            raise CommandError(
                "Path must be relative and stay inside the exchange root"
            )
        resolved = (self.root / candidate).resolve()
        root_resolved = self.root.resolve()
        if resolved != root_resolved and root_resolved not in resolved.parents:
            raise CommandError("Path escapes the exchange root")
        return resolved

    def read(self, relative: str) -> str:
        """Read a UTF-8 text file inside the jail.

        Args:
            relative: Jail-relative path of the file.

        Returns:
            The file's text content.

        Raises:
            CommandError: If the path escapes the jail, the file is missing,
                it exceeds ``MAX_FILE_BYTES``, or it cannot be decoded.
        """
        target = self._resolve(relative)
        if not target.is_file():
            raise CommandError("File does not exist in the exchange root")
        if target.stat().st_size > MAX_FILE_BYTES:
            raise CommandError(f"File exceeds {MAX_FILE_BYTES} bytes")
        try:
            return target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            raise CommandError(f"Cannot read file: {err}") from err

    def write(self, relative: str, content: str) -> int:
        """Atomically write a UTF-8 text file inside the jail.

        Args:
            relative: Jail-relative destination path (parents created).
            content: Text to write.

        Returns:
            The number of UTF-8 bytes written.

        Raises:
            CommandError: If the content exceeds ``MAX_FILE_BYTES`` or the
                path escapes the jail.
        """
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise CommandError(f"Content exceeds {MAX_FILE_BYTES} bytes")
        target = self._resolve(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w", dir=target.parent, encoding="utf-8", delete=False
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(content)
        try:
            temp_path.replace(target)
        finally:
            temp_path.unlink(missing_ok=True)
        logger.info("Exchange file written")
        return len(content.encode("utf-8"))

    def exists(self, relative: str) -> dict[str, Any]:
        """Check whether a file exists inside the jail.

        Args:
            relative: Jail-relative candidate path.

        Returns:
            Dict with ``exists`` (bool) and ``size_bytes`` (int | None).

        Raises:
            CommandError: If the path escapes the exchange jail.
        """
        target = self._resolve(relative)
        if target.is_file():
            return {"exists": True, "size_bytes": target.stat().st_size}
        return {"exists": False, "size_bytes": None}

    def list_files(self, prefix: str = "") -> list[dict[str, Any]]:
        """List regular files beneath an exchange-relative directory.

        Args:
            prefix: Jail-relative directory path (empty for root); files are not
                prefix-matched.

        Returns:
            List of dicts with ``path`` (relative), ``size_bytes``,
            and ``modified_at`` (UTC ISO 8601 string). A missing or non-directory
            prefix returns an empty list; enumeration order is not guaranteed.

        Raises:
            CommandError: If ``prefix`` escapes the jail or the listing exceeds
                MAX_LIST_ENTRIES.
            OSError: Filesystem enumeration or metadata access fails.
        """
        target_dir = self._resolve(prefix) if prefix else self.root.resolve()
        if not target_dir.is_dir():
            return []
        results: list[dict[str, Any]] = []
        root_resolved = self.root.resolve()
        for path in target_dir.rglob("*", recurse_symlinks=False):
            if len(results) >= MAX_LIST_ENTRIES:
                raise CommandError("File listing exceeds limit")
            if path.is_file() and path.resolve().is_relative_to(root_resolved):
                rel = path.relative_to(root_resolved).as_posix()
                st = path.stat()
                results.append(
                    {
                        "path": rel,
                        "size_bytes": st.st_size,
                        "modified_at": datetime.fromtimestamp(
                            st.st_mtime, tz=UTC
                        ).isoformat(),
                    }
                )
        return results

    def delete(self, relative: str) -> bool:
        """Delete a file inside the jail if present (idempotent).

        Args:
            relative: Jail-relative path.

        Returns:
            ``True`` if the file existed and was removed, ``False`` if
            missing.

        Raises:
            CommandError: If the path escapes the jail or deletion fails.
        """
        target = self._resolve(relative)
        if not target.exists():
            return False
        if not target.is_file():
            raise CommandError("Path is not a regular file")
        try:
            target.unlink()
            logger.info("Exchange file deleted")
            return True
        except OSError as err:
            raise CommandError(f"Cannot delete file: {err}") from err


# --- HTTP and WebSocket Handlers ---

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
        {
            "content_base64": base64.b64encode(content).decode("ascii"),
            "schema": schema,
        },
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
        request: Authenticated POST with an exchange operation in the path.

    Returns:
        Operation outcome envelope, or 404 for an unknown file operation.

    Raises:
        CommandError: Confinement, size, or path validation fails.
    """
    exchange = service(request).exchange
    operation = request.path_params["operation"]
    payload = await body(request)
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
    except asyncio.CancelledError, WebSocketDisconnect:
        logger.info("Client socket disconnected")
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
    except asyncio.CancelledError:
        logger.info("Socket stream cancelled")
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
