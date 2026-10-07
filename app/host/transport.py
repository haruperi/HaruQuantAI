"""Unified HTTP and event transport subsystem for the HaruQuantAI platform host.

Description:
    Provides the central HTTP transport middleware, versioned request/response
    correlation, session authentication, in-memory multi-channel event bus, and
    authenticated Server-Sent Events (SSE) streaming engine for the HaruQuantAI
    subsystem. In quantitative trading systems and browser-based control shells,
    reliable bidirectional communication, deterministic event sequencing, request
    correlation, and non-blocking backpressure isolation are critical. This module
    unifies HTTP envelope enforcement with asynchronous real-time event
    distribution into a single canonical host component.

    Externally, it serves the contracts expected by the web application shell:
    session login (`POST /auth/login`), event streaming (`GET /events`), event
    publication (`POST /events/publish`), and channel snapshot queries
    (`GET /events/snapshot`). It consumes the canonical `StandardResponse[T]`
    envelope from `app.host.response` to guarantee consistent API schemas,
    machine-readable error codes, and structured telemetry across all routes.
    Internally, the `EventBus` assigns monotonically increasing event sequence
    cursors, retains a bounded ring buffer for snapshot replay and gap detection,
    and isolates slow or unresponsive consumers through bounded subscriber queues
    (`asyncio.Queue(maxsize=256)`).

Purpose:
    FEAT-HOST-TRANSPORT: Unified HTTP and Event Transport Subsystem.
    Provides canonical API response correlation, session authentication, in-memory
    event dispatching, and authenticated Server-Sent Events streaming.

Key Capabilities:
    - FR-HOST-TRANSPORT-MIDDLEWARE: Request ID correlation and response timing ASGI
      middleware.
      Associated: `[TransportMiddleware]`, `[register_transport_exception_handlers()]`
      Logging: Emits INFO on request completion with duration and correlation ID;
      ERROR on unhandled server exceptions.
    - FR-HOST-TRANSPORT-SESSION-AUTH: Token-based session authentication and bearer
      validation.
      Associated: `[SessionTokenManager.create_token()]`,
      `[SessionTokenManager.verify_token()]`, `[TransportService.handle_login()]`
      Logging: Emits INFO on token creation; WARNING on missing, invalid, or expired
      session credentials.
    - FR-HOST-TRANSPORT-EVENT-BUS: In-memory multi-channel event broker with
      monotonic cursors and ring buffer.
      Associated: `[EventBus.publish()]`, `[EventBus.subscribe()]`
      Logging: Emits DEBUG on event publication; INFO on subscriber registration
      and unregistration.
    - FR-HOST-TRANSPORT-SSE-STREAMING: Server-Sent Events streaming with channel demux
      and gap detection.
      Associated: `[sse_event_generator()]`,
      `[TransportService.handle_events_stream()]`
      Logging: Emits INFO on stream connect/disconnect; WARNING on slow-consumer
    - FR-HOST-TRANSPORT-REST-PROJECTION: FastAPI transport router exposing
      endpoints `/auth/login`, `/events`, `/events/publish`, and `/events/snapshot`.
      Associated: `[create_transport_router()]`
      Logging: Emits DEBUG on transport router composition.

Python API Usage:
    ```python
    from app.host.transport import (
        EventBus,
        SessionTokenManager,
        TransportMiddleware,
        create_transport_router,
    )
    from fastapi import FastAPI

    app = FastAPI()
    bus = EventBus(ring_capacity=1024)
    tokens = SessionTokenManager()

    app.add_middleware(TransportMiddleware)
    router = create_transport_router(event_bus=bus, token_manager=tokens)
    app.include_router(router, prefix="/api/v1")

    # Publish an event
    event = bus.publish(
        channel="settings.changed",
        event_type="update",
        payload={"revision": 2},
    )
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.transport --help
    ```
"""

from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import sys
import threading
import time
from collections import deque
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse

__all__ = [
    "ApiResponse",
    "AuthenticationError",
    "EventBus",
    "EventSnapshot",
    "EventStreamError",
    "HostEvent",
    "LoginRequest",
    "LoginResponse",
    "PublishEventRequest",
    "SessionExpiredError",
    "SessionTokenManager",
    "SlowConsumerError",
    "TransportError",
    "TransportMiddleware",
    "TransportService",
    "ValidationIssue",
    "create_transport_router",
    "get_event_bus",
    "get_global_event_bus",
    "get_global_token_manager",
    "register_transport_exception_handlers",
]

logger = get_logger(__name__)

# Type alias: ApiResponse is synonymous with StandardResponse
ApiResponse = StandardResponse

DEFAULT_RING_CAPACITY: Final[int] = 1024
DEFAULT_MAX_QUEUE_SIZE: Final[int] = 256
DEFAULT_TOKEN_TTL_SEC: Final[int] = 86400  # 24 hours
DEFAULT_HEARTBEAT_SEC: Final[float] = 15.0


def _now_utc_iso() -> str:
    """Return current UTC timestamp formatted as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class TransportError(Exception):
    """Base exception for all transport-layer failures."""


class AuthenticationError(TransportError):
    """Raised when authentication credentials or tokens are invalid."""


class SessionExpiredError(AuthenticationError):
    """Raised when an active session token has expired."""


class EventStreamError(TransportError):
    """Raised when an SSE event streaming failure occurs."""


class SlowConsumerError(TransportError):
    """Raised when a subscriber cannot consume events fast enough."""


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------


class ValidationIssue(BaseModel):
    """Structured field-level validation problem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(description="Field path that failed validation")
    code: str = Field(description="Issue code identifier")
    message: str = Field(description="Human-readable description of the problem")


class LoginRequest(BaseModel):
    """Credentials submitted for session authentication."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    username: str = Field(default="operator", description="Operator username")
    password: str = Field(default="", description="Operator password")


class LoginResponse(BaseModel):
    """Session credentials issued upon successful authentication."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    token: str = Field(description="Opaque bearer session token")
    username: str = Field(description="Authenticated username")
    expires_at: str = Field(description="ISO 8601 UTC expiration timestamp")


class HostEvent(BaseModel):
    """Discrete, monotonic event broadcast across host and plugins."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cursor: int = Field(description="Monotonic sequence number assigned to this event")
    channel: str = Field(description="Target channel topic, e.g. settings.changed")
    event_type: str = Field(description="Event classification, e.g. update, reset")
    timestamp: str = Field(description="ISO 8601 UTC event generation timestamp")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Event payload dictionary"
    )


class EventSnapshot(BaseModel):
    """State snapshot for a specific channel with high-water cursor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    channel: str = Field(description="Channel name")
    newest_cursor: int = Field(description="Highest monotonic cursor on channel")
    events: list[HostEvent] = Field(
        default_factory=list, description="Recent retained events"
    )
    has_gap: bool = Field(
        default=False,
        description="True if events were pruned before requested cursor",
    )


class PublishEventRequest(BaseModel):
    """Payload submitted to publish an event to the host event bus."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    channel: str = Field(description="Target channel topic")
    event_type: str = Field(default="update", description="Event classification slug")
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary payload"
    )


# -----------------------------------------------------------------------------
# Session Token Manager
# -----------------------------------------------------------------------------


class SessionTokenManager:
    """Thread-safe in-memory session token store with TTL expiration."""

    def __init__(self, default_ttl_sec: int = DEFAULT_TOKEN_TTL_SEC) -> None:
        self.default_ttl_sec = default_ttl_sec
        self._tokens: dict[str, tuple[str, datetime]] = {}
        self._lock = threading.Lock()

    def create_token(self, username: str, ttl_sec: int | None = None) -> LoginResponse:
        """Create and store a new opaque session token for the user."""
        ttl = ttl_sec if ttl_sec is not None else self.default_ttl_sec
        token = secrets.token_hex(32)
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
        with self._lock:
            self._tokens[token] = (username, expires_at)
        logger.info(
            "SessionTokenManager created token: username=%s expires_at=%s",
            username,
            expires_at.isoformat(),
            extra={"requirement": "FR-HOST-TRANSPORT-SESSION-AUTH"},
        )
        return LoginResponse(
            token=token,
            username=username,
            expires_at=expires_at.isoformat(),
        )

    def verify_token(self, token: str) -> str:
        """Validate token and return username.

        Raises:
            AuthenticationError: If token does not exist.
            SessionExpiredError: If token has passed expiration.
        """
        with self._lock:
            record = self._tokens.get(token)
            if not record:
                logger.warning(
                    "SessionTokenManager rejected token: token not found",
                    extra={"requirement": "FR-HOST-TRANSPORT-SESSION-AUTH"},
                )
                raise AuthenticationError("Invalid or missing session token.")
            username, expires_at = record
            if datetime.now(UTC) > expires_at:
                self._tokens.pop(token, None)
                logger.warning(
                    "SessionTokenManager rejected token: expired for username=%s",
                    username,
                    extra={"requirement": "FR-HOST-TRANSPORT-SESSION-AUTH"},
                )
                raise SessionExpiredError("Session token has expired.")
            return username

    def is_valid(self, token: str) -> bool:
        """Return True if token exists and is not expired."""
        try:
            self.verify_token(token)
            return True
        except AuthenticationError, SessionExpiredError:
            return False

    def revoke_token(self, token: str) -> bool:
        """Revoke a token, returning True if it was present."""
        with self._lock:
            return self._tokens.pop(token, None) is not None

    def clear(self) -> None:
        """Clear all active tokens."""
        with self._lock:
            self._tokens.clear()


# -----------------------------------------------------------------------------
# In-Memory Event Bus
# -----------------------------------------------------------------------------


class EventBus:
    """In-memory multi-channel event broker with monotonic cursors and ring buffer."""

    def __init__(
        self,
        ring_capacity: int = DEFAULT_RING_CAPACITY,
        max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
    ) -> None:
        self.ring_capacity = ring_capacity
        self.max_queue_size = max_queue_size
        self._lock = threading.Lock()
        self._cursor_seq: int = 0
        self._ring: deque[HostEvent] = deque(maxlen=ring_capacity)
        self._subscribers: dict[str, tuple[set[str], asyncio.Queue[HostEvent]]] = {}

    @property
    def current_cursor(self) -> int:
        """Return current monotonic cursor value."""
        with self._lock:
            return self._cursor_seq

    def publish(
        self,
        channel: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> HostEvent:
        """Publish an event across matching subscribers and append to ring buffer."""
        with self._lock:
            self._cursor_seq += 1
            cursor = self._cursor_seq
            resolved_ts = timestamp or _now_utc_iso()
            event = HostEvent(
                cursor=cursor,
                channel=channel,
                event_type=event_type,
                timestamp=resolved_ts,
                payload=dict(payload) if payload else {},
            )
            self._ring.append(event)
            active_subscribers = list(self._subscribers.items())

        logger.debug(
            "EventBus.publish: cursor=%d channel=%s type=%s subscribers=%d",
            cursor,
            channel,
            event_type,
            len(active_subscribers),
            extra={"requirement": "FR-HOST-TRANSPORT-EVENT-BUS"},
        )

        for sub_id, (channels, queue) in active_subscribers:
            if "*" in channels or channel in channels:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    logger.warning(
                        "EventBus dropped event for slow subscriber: "
                        "sub_id=%s cursor=%d channel=%s",
                        sub_id,
                        cursor,
                        channel,
                        extra={"requirement": "FR-HOST-TRANSPORT-SSE-STREAMING"},
                    )

        return event

    def subscribe(
        self,
        channels: Sequence[str] | set[str],
        since_cursor: int | None = None,
        max_queue_size: int | None = None,
    ) -> tuple[str, asyncio.Queue[HostEvent], list[HostEvent], bool]:
        """Subscribe to channels with optional historical playback from since_cursor.

        Returns:
            Tuple of (subscriber_id, queue, replay_events, has_gap).
        """
        chan_set = set(channels)
        queue_size = max_queue_size or self.max_queue_size
        queue: asyncio.Queue[HostEvent] = asyncio.Queue(maxsize=queue_size)
        sub_id = f"sub-{secrets.token_hex(8)}"

        replay_events: list[HostEvent] = []
        has_gap = False

        with self._lock:
            if since_cursor is not None and since_cursor >= 0 and self._ring:
                oldest_cursor = self._ring[0].cursor
                if since_cursor < oldest_cursor - 1:
                    has_gap = True

                replay_events.extend(
                    ev
                    for ev in self._ring
                    if ev.cursor > since_cursor
                    and ("*" in chan_set or ev.channel in chan_set)
                )

            self._subscribers[sub_id] = (chan_set, queue)

        logger.info(
            "EventBus.subscribe: subscriber_id=%s channels=%s replay=%d gap=%s",
            sub_id,
            sorted(chan_set),
            len(replay_events),
            has_gap,
            extra={"requirement": "FR-HOST-TRANSPORT-EVENT-BUS"},
        )

        return sub_id, queue, replay_events, has_gap

    def unsubscribe(self, subscriber_id: str) -> None:
        """Unsubscribe a client queue."""
        with self._lock:
            removed = self._subscribers.pop(subscriber_id, None)

        if removed:
            logger.info(
                "EventBus.unsubscribe: subscriber_id=%s",
                subscriber_id,
                extra={"requirement": "FR-HOST-TRANSPORT-EVENT-BUS"},
            )

    def get_snapshot(
        self,
        channel: str,
        since_cursor: int | None = None,
        limit: int = 100,
    ) -> EventSnapshot:
        """Retrieve historical snapshot for a channel."""
        with self._lock:
            newest = self._cursor_seq
            events: list[HostEvent] = []
            has_gap = False
            if self._ring:
                oldest = self._ring[0].cursor
                if since_cursor is not None and since_cursor < oldest - 1:
                    has_gap = True

                events.extend(
                    ev
                    for ev in self._ring
                    if (channel in ("*", ev.channel))
                    and (since_cursor is None or ev.cursor > since_cursor)
                )

            retained = events[-limit:] if len(events) > limit else events
            return EventSnapshot(
                channel=channel,
                newest_cursor=newest,
                events=retained,
                has_gap=has_gap,
            )

    def clear(self) -> None:
        """Clear all events and active subscribers."""
        with self._lock:
            self._ring.clear()
            self._subscribers.clear()


# -----------------------------------------------------------------------------
# Lazy Global Singletons (Inert at import time)
# -----------------------------------------------------------------------------


@dataclass
class _TransportState:
    event_bus: EventBus | None = None
    token_manager: SessionTokenManager | None = None


_STATE = _TransportState()
_SINGLETON_LOCK = threading.Lock()


def get_global_event_bus() -> EventBus:
    """Return the host global EventBus singleton."""
    if _STATE.event_bus is None:
        with _SINGLETON_LOCK:
            if _STATE.event_bus is None:
                _STATE.event_bus = EventBus()
    return _STATE.event_bus


get_event_bus = get_global_event_bus


def get_global_token_manager() -> SessionTokenManager:
    """Return the host global SessionTokenManager singleton."""
    if _STATE.token_manager is None:
        with _SINGLETON_LOCK:
            if _STATE.token_manager is None:
                _STATE.token_manager = SessionTokenManager()
    return _STATE.token_manager


# -----------------------------------------------------------------------------
# SSE Generator
# -----------------------------------------------------------------------------


async def sse_event_generator(
    event_bus: EventBus,
    channels: Sequence[str],
    since_cursor: int | None,
    request: Request,
    *,
    heartbeat_interval_sec: float = DEFAULT_HEARTBEAT_SEC,
    limit: int | None = None,
) -> AsyncGenerator[str]:
    """Generate Server-Sent Events stream frames for client subscription."""
    sub_id, queue, replay_events, has_gap = event_bus.subscribe(
        channels=channels,
        since_cursor=since_cursor,
    )

    logger.info(
        "SSE stream connected: sub_id=%s channels=%s",
        sub_id,
        channels,
        extra={"requirement": "FR-HOST-TRANSPORT-SSE-STREAMING"},
    )

    yielded_count = 0
    try:
        if has_gap:
            gap_payload = {
                "channel": "system",
                "event_type": "gap",
                "message": (
                    "Event history gap detected; state resynchronization recommended."
                ),
            }
            yield f"event: system.gap\ndata: {json.dumps(gap_payload)}\n\n"

        for ev in replay_events:
            yield (
                f"id: {ev.cursor}\n"
                f"event: {ev.channel}\n"
                f"data: {ev.model_dump_json()}\n\n"
            )
            yielded_count += 1
            if limit is not None and yielded_count >= limit:
                return

        while True:
            if await request.is_disconnected():
                break

            try:
                event = await asyncio.wait_for(
                    queue.get(), timeout=heartbeat_interval_sec
                )
                yield (
                    f"id: {event.cursor}\n"
                    f"event: {event.channel}\n"
                    f"data: {event.model_dump_json()}\n\n"
                )
                yielded_count += 1
                if limit is not None and yielded_count >= limit:
                    break
            except TimeoutError:
                yield ": heartbeat\n\n"

    except asyncio.CancelledError:
        pass
    finally:
        event_bus.unsubscribe(sub_id)
        logger.info(
            "SSE stream disconnected: sub_id=%s",
            sub_id,
            extra={"requirement": "FR-HOST-TRANSPORT-SSE-STREAMING"},
        )


# -----------------------------------------------------------------------------
# ASGI Transport Middleware & Exception Handlers
# -----------------------------------------------------------------------------


class TransportMiddleware:
    """ASGI middleware for X-Request-Id correlation and response timing."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Intercept HTTP requests to inject correlation headers and timing."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        req_id = request.headers.get("x-request-id")
        if not req_id or not req_id.strip():
            req_id = f"req-{int(time.time() * 1000)}-{secrets.token_hex(4)}"

        start_time = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                headers = MutableHeaders(scope=message)
                headers["X-Request-Id"] = req_id
                headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                "HTTP request completed: method=%s path=%s duration_ms=%.2f req_id=%s",
                request.method,
                request.url.path,
                duration_ms,
                req_id,
                extra={"requirement": "FR-HOST-TRANSPORT-MIDDLEWARE"},
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception(
                "Unhandled exception in HTTP transport",
                extra={"requirement": "FR-HOST-TRANSPORT-MIDDLEWARE"},
            )
            err = StandardError(
                code="INTERNAL_SERVER_ERROR",
                message=str(exc) or "Internal server error occurred.",
                details={"exception_type": type(exc).__name__},
            )
            resp = StandardResponse.failure(
                message="Internal server error.",
                error=err,
                request_id=req_id,
                duration_ms=duration_ms,
            )
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=resp.to_dict(),
                headers={
                    "X-Request-Id": req_id,
                    "X-Response-Time-Ms": f"{duration_ms:.2f}",
                },
            )
            await response(scope, receive, send)


def register_transport_exception_handlers(app: FastAPI) -> None:
    """Attach standard exception handlers wrapping errors into StandardResponse."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        req_id = request.headers.get("x-request-id") or f"req-{int(time.time() * 1000)}"
        err = StandardError(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
        )
        resp = StandardResponse.failure(
            message=str(exc.detail),
            error=err,
            request_id=req_id,
        )
        return JSONResponse(status_code=exc.status_code, content=resp.to_dict())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = request.headers.get("x-request-id") or f"req-{int(time.time() * 1000)}"
        issues = [
            ValidationIssue(
                path=".".join(str(p) for p in err.get("loc", [])),
                code=err.get("type", "value_error"),
                message=err.get("msg", "Validation error"),
            ).model_dump()
            for err in exc.errors()
        ]
        err = StandardError(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details={"issues": issues},
        )
        resp = StandardResponse.failure(
            message="Request validation failed.",
            error=err,
            request_id=req_id,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=resp.to_dict(),
        )


# -----------------------------------------------------------------------------
# Transport Service Handler Operations
# -----------------------------------------------------------------------------


class TransportService:
    """Coordinates authentication and event routing for HTTP transport."""

    def __init__(self, bus: EventBus, tokens: SessionTokenManager) -> None:
        self.bus = bus
        self.tokens = tokens

    def resolve_token(self, request: Request, token_query: str | None) -> str | None:
        """Extract token from Authorization Bearer header or query parameter."""
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()
        if token_query and token_query.strip():
            return token_query.strip()
        return None

    async def handle_login(
        self, credentials: LoginRequest, request: Request
    ) -> JSONResponse:
        """Handle session authentication request."""
        req_id = request.headers.get("x-request-id")
        if not credentials.username or not credentials.username.strip():
            err = StandardError(
                code="INVALID_CREDENTIALS",
                message="Username cannot be empty.",
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=StandardResponse.failure(
                    message="Invalid credentials.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        login_resp = self.tokens.create_token(username=credentials.username.strip())
        resp = StandardResponse.success(
            data=login_resp.model_dump(),
            message="Authentication successful.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_auth_status(
        self, request: Request, token: str | None = None
    ) -> JSONResponse:
        """Query status of active session token."""
        req_id = request.headers.get("x-request-id")
        resolved = self.resolve_token(request, token)
        if not resolved or not self.tokens.is_valid(resolved):
            err = StandardError(
                code="UNAUTHORIZED",
                message="No active session token.",
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=StandardResponse.failure(
                    message="Unauthorized.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )
        username = self.tokens.verify_token(resolved)
        resp = StandardResponse.success(
            data={"authenticated": True, "username": username},
            message="Session active.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_events_stream(
        self,
        request: Request,
        channels: str = Query(
            default="*", description="Comma-separated channel filter"
        ),
        since_cursor: int | None = Query(
            default=None, description="Replay starting after this cursor"
        ),
        token: str | None = Query(
            default=None, description="Optional bearer token in query"
        ),
        limit: int | None = Query(
            default=None, description="Optional maximum number of events to receive"
        ),
    ) -> Response:
        """Stream real-time server-sent events for authorized subscribers."""
        req_id = request.headers.get("x-request-id")
        resolved = self.resolve_token(request, token)
        if not resolved or not self.tokens.is_valid(resolved):
            err = StandardError(
                code="UNAUTHORIZED",
                message="Host session required or expired.",
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=StandardResponse.failure(
                    message="Unauthorized.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        last_id = request.headers.get("last-event-id")
        effective_cursor = since_cursor
        if effective_cursor is None and last_id and last_id.isdigit():
            effective_cursor = int(last_id)

        parsed_channels = [c.strip() for c in channels.split(",") if c.strip()]
        if not parsed_channels:
            parsed_channels = ["*"]

        return StreamingResponse(
            sse_event_generator(
                event_bus=self.bus,
                channels=parsed_channels,
                since_cursor=effective_cursor,
                request=request,
                limit=limit,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def handle_publish(
        self, event_in: PublishEventRequest, request: Request
    ) -> JSONResponse:
        """Publish an event to the host event bus."""
        req_id = request.headers.get("x-request-id")
        event = self.bus.publish(
            channel=event_in.channel,
            event_type=event_in.event_type,
            payload=event_in.payload,
        )
        resp = StandardResponse.success(
            data=event.model_dump(),
            message="Event published successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_snapshot(
        self,
        request: Request,
        channel: str = Query(default="*", description="Target channel name"),
        since_cursor: int | None = Query(
            default=None, description="Cursor lower bound"
        ),
        limit: int = Query(default=100, ge=1, le=1000),
    ) -> JSONResponse:
        """Query channel snapshot and retained history."""
        req_id = request.headers.get("x-request-id")
        snapshot = self.bus.get_snapshot(
            channel=channel, since_cursor=since_cursor, limit=limit
        )
        resp = StandardResponse.success(
            data=snapshot.model_dump(),
            message="Snapshot retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


# -----------------------------------------------------------------------------
# FastAPI Router Factory
# -----------------------------------------------------------------------------


def create_transport_router(
    event_bus: EventBus | None = None,
    token_manager: SessionTokenManager | None = None,
) -> APIRouter:
    """Create FastAPI router exposing auth and event transport endpoints."""
    bus = event_bus if event_bus is not None else get_global_event_bus()
    tokens = token_manager if token_manager is not None else get_global_token_manager()
    service = TransportService(bus, tokens)
    router = APIRouter(tags=["transport"])

    router.add_api_route("/auth/login", service.handle_login, methods=["POST"])
    router.add_api_route("/login", service.handle_login, methods=["POST"])
    router.add_api_route("/auth/status", service.handle_auth_status, methods=["GET"])
    router.add_api_route("/events", service.handle_events_stream, methods=["GET"])
    router.add_api_route("/events/publish", service.handle_publish, methods=["POST"])
    router.add_api_route("/events/snapshot", service.handle_snapshot, methods=["GET"])

    logger.debug(
        "create_transport_router composed",
        extra={"requirement": "FR-HOST-TRANSPORT-REST-PROJECTION"},
    )
    return router


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """CLI utility for checking transport status."""
    parser = argparse.ArgumentParser(description="HaruQuantAI Host Transport CLI")
    parser.add_argument(
        "--test-bus", action="store_true", help="Run self-test on event bus"
    )
    args = parser.parse_args(argv)

    if args.test_bus:
        bus = EventBus()
        ev = bus.publish("system.test", "ping", {"time": _now_utc_iso()})
        print(f"Published test event: cursor={ev.cursor} channel={ev.channel}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
