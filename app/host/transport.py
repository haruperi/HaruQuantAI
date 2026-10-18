# ruff: noqa: INP001
"""FastAPI gateway, uniform response middleware, and asynchronous EventBus.

Description:
    Implements the unified HTTP/REST gateway, ASGI request-correlation and
    exception-envelope middleware, in-memory multi-channel asynchronous
    ``EventBus``, Server-Sent Events (SSE) stream generator (``/events``), and
    bidirectional WebSocket gateway (``/ws``) for the HaruQuantAI host platform.

    Internal workflow:
        1. ``TransportMiddleware`` intercepts incoming HTTP requests, assigns or
           preserves ``X-Request-Id``, measures ``X-Response-Time-Ms``, and
           catches unhandled exceptions into ``StandardResponse.failure(...)``
           envelopes from ``app.host.response``.
        2. ``register_transport_exception_handlers`` binds ``HTTPException`` and
           ``RequestValidationError`` handlers that format all errors into
           canonical ``StandardResponse`` / ``StandardError`` payloads with
           structured ``ValidationIssue`` items.
        3. ``EventBus`` sequences events across core host channels (``jobs``,
           ``system``, ``logs``, ``databanks``, ``settings.changed``) using
           monotonic cursors, a bounded ``collections.deque`` ring buffer for
           cursor replay and gap detection, and bounded ``asyncio.Queue``
           subscriber queues for slow-consumer isolation.
        4. ``create_transport_router`` and ``create_host_app`` mount session
           authentication (``/auth/login``, ``/sessions/me``), shell status
           (``/status``, ``/readiness``, ``/app-loaded``, ``/about``), SSE
           (``/events``), event publication/snapshots (``/events/publish``,
           ``/events/snapshot``, ``/events/channels``), and WebSocket (``/ws``)
           routes at root, ``/api/v1``, and ``/api/v2``.

    External workflow:
        - Browser shell components (``ui/app/host/transport.ts``,
          ``HostConnection.tsx``, ``hostSettings.ts``) authenticate via
          ``POST /api/v1/auth/login``, verify sessions via
          ``GET /api/v1/sessions/me``, query ``GET /api/v1/status``, acknowledge
          boot via ``POST /api/v1/app-loaded``, and subscribe to live updates over
          ``GET /api/v1/events`` (SSE) or ``WS /api/v1/ws`` (WebSocket).

Purpose:
    FEAT-HOST-TRANSPORT — Provide the FastAPI gateway, uniform envelope
    middleware, and asynchronous multi-channel EventBus (SSE & WebSocket).

Key Capabilities:
    - FR-HOST-TRANSPORT-MIDDLEWARE: Inject ``X-Request-Id`` correlation and
      ``X-Response-Time-Ms`` headers and isolate unhandled server exceptions into
      canonical 500 error envelopes.
    - FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE: Transform ``HTTPException`` and
      ``RequestValidationError`` into ``StandardResponse.failure`` envelopes with
      field-level ``ValidationIssue`` diagnostics.
    - FR-HOST-TRANSPORT-EVENT-BUS: Publish and subscribe to multi-channel host
      events (``jobs``, ``system``, ``logs``, ``databanks``,
      ``settings.changed``) with monotonic cursors, ring-buffer replay, and
      slow-consumer queue isolation.
    - FR-HOST-TRANSPORT-SSE-STREAMING: Stream real-time Server-Sent Events over
      ``GET /events`` with cursor replay, gap notification, and heartbeats.
    - FR-HOST-TRANSPORT-WS-STREAMING: Stream bidirectional JSON events and
      control frames over ``WebSocket /ws`` with dynamic channel subscriptions.
    - FR-HOST-TRANSPORT-SESSION-AUTH: Authenticate operator credentials on
      ``POST /auth/login`` and validate bearer tokens on ``GET /sessions/me``
      via ``app.host.session.SessionManager``.
    - FR-HOST-TRANSPORT-GATEWAY-APP: Assemble the FastAPI host gateway app and
      shell status endpoints (``/status``, ``/readiness``, ``/app-loaded``,
      ``/about``) mounted across root, ``/api/v1``, and ``/api/v2``.
    - FR-HOST-TRANSPORT-CONNECTION-TEST: Validate remote and local endpoint
      connectivity, measure round-trip latency, and diagnose network/DNS failures.
    - FR-HOST-TRANSPORT-SERVLET-CONNECTION: REST endpoint router and controller
      for broker and exchange connection configurations and connectivity checks.
    - FR-HOST-TRANSPORT-SERVLET-CONSTANTS: Expose system constants, runtime
      environment paths, hardware specs, and supported timeframes.

Python API Usage:
    from app.host.transport import (
        ConnectionTest,
        EventBus,
        ServletConnection,
        ServletConstants,
        create_host_app,
    )

    bus = EventBus()
    app = create_host_app(event_bus=bus)
    bus.publish("settings.changed", "update", {"revision": 2})

CLI Usage:
    uv run python -m app.host.transport --test-bus
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import socket
import sys
import threading
import time
import urllib.parse
from collections import deque
from collections.abc import AsyncGenerator, Callable, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from app.host.logging import get_access_logger, get_logger, redact_secrets
from app.host.persistence.read import get_host_job, list_host_jobs
from app.host.resources import (
    check_memory_headroom,
    get_system_health,
    get_worker_capacity,
    probe_hardware,
)
from app.host.response import StandardError, StandardResponse
from app.host.session import (
    SessionManager,
    SessionRecord,
    session_manager,
    verify_password,
)
from app.host.settings import RevisionConflictError, settings
from fastapi import (
    APIRouter,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

__all__ = [
    "ConnectionTest",
    "EventBus",
    "HostEvent",
    "ServletConnection",
    "ServletConstants",
    "SettingsBatchUpdatePayload",
    "TransportMiddleware",
    "create_host_app",
    "create_transport_router",
    "register_transport_exception_handlers",
]

logger = get_logger(__name__)
access_logger = get_access_logger()

CORE_EVENT_CHANNELS: Final[tuple[str, ...]] = (
    "jobs",
    "system",
    "logs",
    "databanks",
    "settings.changed",
)
DEFAULT_RING_CAPACITY: Final[int] = 1024
DEFAULT_MAX_QUEUE_SIZE: Final[int] = 256
DEFAULT_HEARTBEAT_SEC: Final[float] = 15.0


def _now_utc_iso() -> str:
    """Return current UTC timestamp formatted as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()


def _format_iso_expiry(expires_at_utc: str) -> str:
    """Convert ``YYYY-MM-DD HH:MM:SS`` session expiry to ISO-8601 UTC format."""
    if "T" in expires_at_utc:
        return expires_at_utc
    try:
        dt = datetime.strptime(expires_at_utc, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        return dt.isoformat()
    except ValueError:
        return expires_at_utc


def extract_bearer_token(
    auth_header: str | None, query_token: str | None = None
) -> str | None:
    """Extract a bearer token from an ``Authorization`` header or query string."""
    if auth_header:
        scheme, _, remainder = auth_header.strip().partition(" ")
        if scheme.lower() == "bearer" and remainder.strip():
            return remainder.strip()
    if query_token and query_token.strip():
        return query_token.strip()
    return None


# ============================================================================
# Transport Exceptions & Pydantic Models
# ============================================================================


class TransportError(Exception):
    """Base exception for transport-layer failures."""


class EventStreamError(TransportError):
    """Raised when an SSE or WebSocket streaming failure occurs."""


class SlowConsumerError(TransportError):
    """Raised when a subscriber queue overflows."""


class ValidationIssue(BaseModel):
    """Structured field-level validation problem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(..., description="Field path that failed validation.")
    code: str = Field(..., description="Machine-readable issue code.")
    message: str = Field(..., description="Human-readable validation message.")


class LoginRequestPayload(BaseModel):
    """Credentials payload submitted to ``POST /auth/login``."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    username: str | None = Field(
        default=None, description="Optional operator username."
    )
    password: str = Field(default="", description="Operator password.")


class SettingsBatchUpdatePayload(BaseModel):
    """Batch settings update payload submitted to ``PUT /settings``."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    revision: int | None = Field(
        default=None,
        description="Expected settings revision for optimistic concurrency check.",
    )
    settings: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Nested {scope: {key: value}} settings updates.",
    )


class HostEvent(BaseModel):
    """Discrete, monotonically sequenced event broadcast on the host EventBus."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cursor: int = Field(
        ..., description="Monotonic sequence cursor assigned to this event."
    )
    channel: str = Field(
        ...,
        description="Target channel topic (e.g., 'jobs', 'settings.changed').",
    )
    event_type: str = Field(
        default="update",
        description="Event classification slug (e.g., 'update', 'progress').",
    )
    timestamp: str = Field(
        default_factory=_now_utc_iso,
        description="ISO-8601 UTC timestamp when the event was published.",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured JSON-serializable event payload.",
    )


class EventSnapshot(BaseModel):
    """Historical snapshot of retained events for a channel."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    channel: str = Field(..., description="Channel name or '*' wildcard.")
    newest_cursor: int = Field(
        ..., description="Highest monotonic cursor published on the bus."
    )
    events: list[HostEvent] = Field(
        default_factory=list, description="Retained events matching the query."
    )
    has_gap: bool = Field(
        default=False,
        description="True if older events were pruned before since_cursor.",
    )


class PublishEventRequest(BaseModel):
    """Request payload for ``POST /events/publish``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    channel: str = Field(..., min_length=1, description="Target channel topic.")
    event_type: str = Field(
        default="update", min_length=1, description="Event classification."
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, description="Event payload dictionary."
    )


# ============================================================================
# Asynchronous Multi-Channel EventBus (FR-HOST-TRANSPORT-EVENT-BUS)
# ============================================================================


class EventBus:
    """In-memory multi-channel pub/sub event bus with monotonic cursors."""

    def __init__(
        self,
        ring_capacity: int = DEFAULT_RING_CAPACITY,
        max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
    ) -> None:
        """Initialize the EventBus with bounded ring buffer and queue sizes."""
        self.ring_capacity = max(1, ring_capacity)
        self.max_queue_size = max(1, max_queue_size)
        self._lock = threading.RLock()
        self._cursor_seq: int = 0
        self._ring: deque[HostEvent] = deque(maxlen=self.ring_capacity)
        self._subscribers: dict[str, tuple[set[str], asyncio.Queue[HostEvent]]] = {}
        self._channels: set[str] = set(CORE_EVENT_CHANNELS)
        self._subscriber_loops: dict[str, asyncio.AbstractEventLoop] = {}
        self._pending_deliveries: dict[str, int] = {}

    @property
    def current_cursor(self) -> int:
        """Return the highest monotonic cursor sequence value."""
        with self._lock:
            return self._cursor_seq

    @property
    def channels(self) -> list[str]:
        """Return sorted list of known event channels."""
        with self._lock:
            return sorted(self._channels)

    def publish(
        self,
        channel: str,
        event_type: str = "update",
        payload: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> HostEvent:
        """Publish an event to matching subscribers and append to the ring buffer."""
        with self._lock:
            self._cursor_seq += 1
            cursor = self._cursor_seq
            self._channels.add(channel)
            event = HostEvent(
                cursor=cursor,
                channel=channel,
                event_type=event_type,
                timestamp=timestamp or _now_utc_iso(),
                payload=dict(payload) if payload else {},
            )
            self._ring.append(event)
            active_subscribers = [
                (sub_id, set(chans), queue)
                for sub_id, (chans, queue) in self._subscribers.items()
            ]
            for sub_id, chans, queue in active_subscribers:
                if "*" in chans or channel in chans:
                    self._schedule_delivery(sub_id, queue, event)

        logger.debug(
            "FR-HOST-TRANSPORT-EVENT-BUS: Published cursor=%d channel='%s' "
            "type='%s' (subscribers=%d).",
            cursor,
            channel,
            event_type,
            len(active_subscribers),
            extra={"fr_id": "FR-HOST-TRANSPORT-EVENT-BUS"},
        )

        return event

    def _schedule_delivery(
        self, sub_id: str, queue: asyncio.Queue[HostEvent], event: HostEvent
    ) -> None:
        """Bound pending callbacks and deliver on the subscriber's owning loop."""
        pending = self._pending_deliveries.get(sub_id, 0)
        if queue.qsize() + pending >= queue.maxsize:
            logger.warning(
                "FR-HOST-TRANSPORT-EVENT-BUS: Dropped cursor=%d for slow subscriber %s",
                event.cursor,
                sub_id,
                extra={"fr_id": "FR-HOST-TRANSPORT-EVENT-BUS"},
            )
            return
        loop = self._subscriber_loops.get(sub_id)
        if loop is None:
            queue.put_nowait(event)
            return
        if loop.is_closed():
            return
        self._pending_deliveries[sub_id] = pending + 1
        try:
            loop.call_soon_threadsafe(self._deliver_event, sub_id, queue, event)
        except RuntimeError:
            self._pending_deliveries[sub_id] -= 1
            logger.warning(
                "FR-HOST-TRANSPORT-EVENT-BUS: Subscriber loop closed during delivery",
                extra={"fr_id": "FR-HOST-TRANSPORT-EVENT-BUS"},
            )

    def _deliver_event(
        self, sub_id: str, queue: asyncio.Queue[HostEvent], event: HostEvent
    ) -> None:
        """Execute queue operations on the owning event loop only."""
        with self._lock:
            if sub_id not in self._subscribers:
                return
            self._pending_deliveries[sub_id] -= 1
            queue.put_nowait(event)

    def subscribe(
        self,
        channels: Sequence[str] | set[str] | None = None,
        since_cursor: int | None = None,
        max_queue_size: int | None = None,
    ) -> tuple[str, asyncio.Queue[HostEvent], list[HostEvent], bool]:
        """Subscribe to channels with optional replay from ``since_cursor``."""
        chan_set = set(channels) if channels else {"*"}
        queue_size = max_queue_size or self.max_queue_size
        queue: asyncio.Queue[HostEvent] = asyncio.Queue(maxsize=queue_size)
        sub_id = f"sub-{secrets.token_hex(8)}"

        replay_events: list[HostEvent] = []
        has_gap = False

        with self._lock:
            for ch in chan_set:
                if ch != "*":
                    self._channels.add(ch)

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
            self._pending_deliveries[sub_id] = 0
            try:
                self._subscriber_loops[sub_id] = asyncio.get_running_loop()
            except RuntimeError:
                # Synchronous replay/test subscribers have no event-loop owner.
                self._subscriber_loops.pop(sub_id, None)

        logger.info(
            "FR-HOST-TRANSPORT-EVENT-BUS: Registered subscriber '%s' "
            "channels=%s replay=%d gap=%s.",
            sub_id,
            sorted(chan_set),
            len(replay_events),
            has_gap,
            extra={"fr_id": "FR-HOST-TRANSPORT-EVENT-BUS"},
        )
        return sub_id, queue, replay_events, has_gap

    def update_subscription(
        self, subscriber_id: str, channels: Sequence[str] | set[str]
    ) -> bool:
        """Update the channel set for an active subscriber."""
        with self._lock:
            entry = self._subscribers.get(subscriber_id)
            if entry is None:
                return False
            _, queue = entry
            new_chans = set(channels) if channels else {"*"}
            for ch in new_chans:
                if ch != "*":
                    self._channels.add(ch)
            self._subscribers[subscriber_id] = (new_chans, queue)
        logger.info(
            "FR-HOST-TRANSPORT-EVENT-BUS: Updated subscriber '%s' channels=%s.",
            subscriber_id,
            sorted(new_chans),
            extra={"fr_id": "FR-HOST-TRANSPORT-EVENT-BUS"},
        )
        return True

    def unsubscribe(self, subscriber_id: str) -> None:
        """Remove a subscriber queue from the EventBus."""
        with self._lock:
            removed = self._subscribers.pop(subscriber_id, None)
            self._subscriber_loops.pop(subscriber_id, None)
            self._pending_deliveries.pop(subscriber_id, None)
        if removed is not None:
            logger.info(
                "FR-HOST-TRANSPORT-EVENT-BUS: Unsubscribed '%s'.",
                subscriber_id,
                extra={"fr_id": "FR-HOST-TRANSPORT-EVENT-BUS"},
            )

    def get_snapshot(
        self,
        channel: str = "*",
        since_cursor: int | None = None,
        limit: int = 100,
    ) -> EventSnapshot:
        """Return retained historical events for ``channel``."""
        bounded_limit = max(1, min(limit, self.ring_capacity))
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
                    if channel in ("*", ev.channel)
                    and (since_cursor is None or ev.cursor > since_cursor)
                )
            retained = (
                events[-bounded_limit:] if len(events) > bounded_limit else events
            )
            return EventSnapshot(
                channel=channel,
                newest_cursor=newest,
                events=retained,
                has_gap=has_gap,
            )

    def clear(self) -> None:
        """Clear all retained events and active subscribers."""
        with self._lock:
            self._ring.clear()
            self._subscribers.clear()
            self._subscriber_loops.clear()
            self._pending_deliveries.clear()


@dataclass
class _GlobalTransportState:
    event_bus: EventBus | None = None


_GLOBAL_STATE = _GlobalTransportState()
_GLOBAL_LOCK = threading.Lock()


def get_global_event_bus() -> EventBus:
    """Return the lazily initialized global host ``EventBus``."""
    if _GLOBAL_STATE.event_bus is None:
        with _GLOBAL_LOCK:
            if _GLOBAL_STATE.event_bus is None:
                _GLOBAL_STATE.event_bus = EventBus()
    return _GLOBAL_STATE.event_bus


# ============================================================================
# ASGI Middleware & Exception Envelopes
# ============================================================================


class TransportMiddleware:
    """ASGI middleware injecting ``X-Request-Id`` and ``X-Response-Time-Ms``."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware around ``app``."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Intercept HTTP requests for correlation headers and error boundary."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        req_id = request.headers.get("x-request-id", "").strip()
        if not req_id:
            req_id = f"req-{int(time.time() * 1000)}-{secrets.token_hex(4)}"

        start_time = time.perf_counter()

        async def _send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                duration_ms = (time.perf_counter() - start_time) * 1000.0
                headers = MutableHeaders(scope=message)
                headers["X-Request-Id"] = req_id
                headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
            await send(message)

        try:
            await self.app(scope, receive, _send_wrapper)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            access_logger.info(
                "FR-HOST-TRANSPORT-MIDDLEWARE: HTTP %s %s completed in %.2fms "
                "(req_id=%s).",
                request.method,
                request.url.path,
                duration_ms,
                req_id,
                extra={"fr_id": "FR-HOST-TRANSPORT-MIDDLEWARE"},
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception(
                "FR-HOST-TRANSPORT-MIDDLEWARE: Unhandled exception on %s %s "
                "(req_id=%s)",
                request.method,
                request.url.path,
                req_id,
                extra={"fr_id": "FR-HOST-TRANSPORT-MIDDLEWARE"},
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
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "Referrer-Policy": "no-referrer",
                },
            )
            await response(scope, receive, send)


def register_transport_exception_handlers(app: FastAPI) -> None:
    """Register ``HTTPException`` and ``RequestValidationError`` envelope handlers."""
    logger.info(
        "FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE: Registered transport exception "
        "handlers on FastAPI app.",
        extra={"fr_id": "FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE"},
    )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        req_id = request.headers.get("x-request-id") or f"req-{int(time.time() * 1000)}"
        raw_detail: Any = exc.detail
        detail_msg = (
            raw_detail if isinstance(raw_detail, str) else json.dumps(raw_detail)
        )
        detail_dict: dict[str, Any] | None = (
            raw_detail if isinstance(raw_detail, dict) else None
        )
        err = StandardError(
            code=f"HTTP_{exc.status_code}",
            message=detail_msg or f"HTTP {exc.status_code}",
            details=detail_dict,
        )
        resp = StandardResponse.failure(
            message=err.message,
            error=err,
            request_id=req_id,
        )
        logger.warning(
            "FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE: HTTPException %d on %s: %s",
            exc.status_code,
            request.url.path,
            err.message,
            extra={"fr_id": "FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE"},
        )
        return JSONResponse(status_code=exc.status_code, content=resp.to_dict())

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = request.headers.get("x-request-id") or f"req-{int(time.time() * 1000)}"
        issues = [
            ValidationIssue(
                path=".".join(str(p) for p in item.get("loc", [])),
                code=str(item.get("type", "value_error")),
                message=str(item.get("msg", "Validation error")),
            ).model_dump()
            for item in exc.errors()
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
        payload = resp.to_dict()
        if isinstance(payload.get("error"), dict):
            payload["error"]["issues"] = issues
        logger.warning(
            "FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE: RequestValidationError on %s "
            "(%d issues).",
            request.url.path,
            len(issues),
            extra={"fr_id": "FR-HOST-TRANSPORT-EXCEPTION-ENVELOPE"},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=payload,
        )


# ============================================================================
# SSE & WebSocket Streaming Generators
# ============================================================================


def _format_sse_event(ev: HostEvent) -> str:
    """Format a ``HostEvent`` into an SSE wire frame."""
    return f"id: {ev.cursor}\nevent: {ev.channel}\ndata: {ev.model_dump_json()}\n\n"


def _build_gap_sse_frame() -> str:
    """Return a formatted SSE ``system.gap`` notification frame."""
    gap_frame = {
        "channel": "system",
        "event_type": "gap",
        "message": "Event history gap detected; resynchronize state.",
    }
    return f"event: system.gap\ndata: {json.dumps(gap_frame)}\n\n"


async def sse_event_generator(
    event_bus: EventBus,
    channels: Sequence[str],
    since_cursor: int | None,
    request: Request,
    *,
    heartbeat_interval_sec: float = DEFAULT_HEARTBEAT_SEC,
    limit: int | None = None,
    session_valid: Callable[[], bool] | None = None,
) -> AsyncGenerator[str]:
    """Generate Server-Sent Events (SSE) frames for a connected client."""
    sub_id, queue, replay_events, has_gap = event_bus.subscribe(
        channels=channels,
        since_cursor=since_cursor,
    )
    logger.info(
        "FR-HOST-TRANSPORT-SSE-STREAMING: SSE client connected "
        "(sub_id=%s channels=%s).",
        sub_id,
        list(channels),
        extra={"fr_id": "FR-HOST-TRANSPORT-SSE-STREAMING"},
    )

    yielded = 0
    try:
        if has_gap:
            yield _build_gap_sse_frame()

        for ev in replay_events:
            if not _is_session_ok(session_valid):
                return
            yield _format_sse_event(ev)
            yielded += 1
            if _limit_reached(yielded, limit):
                return

        while await _can_continue_sse(request, session_valid):
            frame, did_yield = await _next_sse_frame(
                queue, heartbeat_interval_sec, session_valid
            )
            if frame is None:
                break
            yield frame
            yielded += 1 if did_yield else 0
            if _limit_reached(yielded, limit):
                break
    except asyncio.CancelledError:
        pass
    finally:
        event_bus.unsubscribe(sub_id)
        logger.info(
            "FR-HOST-TRANSPORT-SSE-STREAMING: SSE client disconnected (sub_id=%s).",
            sub_id,
            extra={"fr_id": "FR-HOST-TRANSPORT-SSE-STREAMING"},
        )


def _is_session_ok(session_valid: Callable[[], bool] | None) -> bool:
    """Return True if no session callback is configured or it evaluates True."""
    return session_valid is None or session_valid()


def _limit_reached(yielded: int, limit: int | None) -> bool:
    """Return True if an optional event stream limit has been reached."""
    return limit is not None and yielded >= limit


async def _can_continue_sse(
    request: Request, session_valid: Callable[[], bool] | None
) -> bool:
    """Return True if SSE session remains valid and client is still connected."""
    if session_valid is not None and not session_valid():
        return False
    return not await request.is_disconnected()


async def _next_sse_frame(
    queue: asyncio.Queue[HostEvent],
    heartbeat_interval_sec: float,
    session_valid: Callable[[], bool] | None,
) -> tuple[str | None, bool]:
    """Wait for the next ``HostEvent`` or emit an SSE heartbeat comment."""
    try:
        ev = await asyncio.wait_for(queue.get(), timeout=heartbeat_interval_sec)
    except TimeoutError:
        return ": heartbeat\n\n", False
    if session_valid is not None and not session_valid():
        return None, False
    return _format_sse_event(ev), True


def _parse_channels_param(raw_channels: str | None) -> list[str]:
    """Parse a comma-separated ``channels`` query parameter."""
    if not raw_channels or not raw_channels.strip():
        return ["*"]
    parsed = [c.strip() for c in raw_channels.split(",") if c.strip()]
    return parsed or ["*"]


def _resolve_since_cursor(
    since_cursor: int | None, last_event_id: str | None
) -> int | None:
    """Resolve ``since_cursor`` from query param or ``Last-Event-ID`` header."""
    if since_cursor is not None:
        return since_cursor
    if last_event_id and last_event_id.strip().isdigit():
        return int(last_event_id.strip())
    return None


# ============================================================================
# Platform Connectivity & Infrastructure Servlets (Phase 1.2 / 1.4)
# ============================================================================

CONNECTION_TEST_FR: Final[str] = "FR-HOST-TRANSPORT-CONNECTION-TEST"
SERVLET_CONNECTION_FR: Final[str] = "FR-HOST-TRANSPORT-SERVLET-CONNECTION"
SERVLET_CONSTANTS_FR: Final[str] = "FR-HOST-TRANSPORT-SERVLET-CONSTANTS"

SUPPORTED_TIMEFRAMES: Final[tuple[str, ...]] = (
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
    "1w",
)


class ConnectionTest:
    """Network reachability, latency probe, and socket diagnostic utility."""

    @staticmethod
    def ping_endpoint(endpoint: str, timeout: float = 3.0) -> dict[str, Any]:
        """Ping remote or local server endpoint to verify network connectivity."""
        raw_endpoint = endpoint.strip()
        parsed = urllib.parse.urlparse(
            raw_endpoint if "://" in raw_endpoint else f"tcp://{raw_endpoint}"
        )
        host = parsed.hostname or raw_endpoint
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                latency_ms = (time.perf_counter() - start) * 1000.0
                logger.info(
                    "%s: Endpoint %s is reachable (latency=%.2fms).",
                    CONNECTION_TEST_FR,
                    raw_endpoint,
                    latency_ms,
                    extra={"fr_id": CONNECTION_TEST_FR, "endpoint": raw_endpoint},
                )
                return {
                    "endpoint": raw_endpoint,
                    "host": host,
                    "port": port,
                    "reachable": True,
                    "latency_ms": round(latency_ms, 2),
                    "error": None,
                }
        except OSError as err:
            latency_ms = (time.perf_counter() - start) * 1000.0
            logger.warning(
                "%s: Endpoint %s is unreachable: %s",
                CONNECTION_TEST_FR,
                raw_endpoint,
                err,
                extra={
                    "fr_id": CONNECTION_TEST_FR,
                    "endpoint": raw_endpoint,
                    "error": str(err),
                },
            )
            return {
                "endpoint": raw_endpoint,
                "host": host,
                "port": port,
                "reachable": False,
                "latency_ms": round(latency_ms, 2),
                "error": str(err),
            }

    @staticmethod
    def check_latency(
        endpoint: str, samples: int = 3, timeout: float = 3.0
    ) -> dict[str, Any]:
        """Measure round-trip latency across multiple samples and report packet loss."""
        num_samples = max(1, min(samples, 10))
        latencies: list[float] = []
        failures = 0
        for _ in range(num_samples):
            res = ConnectionTest.ping_endpoint(endpoint, timeout=timeout)
            if res["reachable"]:
                latencies.append(float(res["latency_ms"]))
            else:
                failures += 1

        packet_loss_pct = (failures / num_samples) * 100.0
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        min_lat = min(latencies) if latencies else 0.0
        max_lat = max(latencies) if latencies else 0.0

        logger.info(
            "%s: Latency check on %s: avg=%.2fms loss=%.1f%%.",
            CONNECTION_TEST_FR,
            endpoint,
            avg_lat,
            packet_loss_pct,
            extra={"fr_id": CONNECTION_TEST_FR, "endpoint": endpoint},
        )
        return {
            "endpoint": endpoint,
            "samples": num_samples,
            "packet_loss_pct": round(packet_loss_pct, 2),
            "avg_latency_ms": round(avg_lat, 2),
            "min_latency_ms": round(min_lat, 2),
            "max_latency_ms": round(max_lat, 2),
            "successful_samples": len(latencies),
        }

    @staticmethod
    def diagnose_network(host: str, port: int | None = None) -> dict[str, Any]:
        """Diagnose DNS resolution and socket connection parameters."""
        resolved_ips: list[str] = []
        dns_ok = False
        dns_error: str | None = None

        try:
            addr_info = socket.getaddrinfo(host, port or 80, proto=socket.IPPROTO_TCP)
            for item in addr_info:
                ip = item[4][0]
                if str(ip) not in resolved_ips:
                    resolved_ips.append(str(ip))
            dns_ok = True
        except (socket.gaierror, OSError) as err:
            dns_error = str(err)

        probe_port = port or 80
        reachable = False
        reach_err: str | None = None
        if dns_ok and resolved_ips:
            try:
                with socket.create_connection(
                    (resolved_ips[0], probe_port), timeout=2.0
                ):
                    reachable = True
            except OSError as err:
                reach_err = str(err)

        logger.info(
            "%s: Network diagnostic for host=%s: dns=%s reachable=%s.",
            CONNECTION_TEST_FR,
            host,
            dns_ok,
            reachable,
            extra={"fr_id": CONNECTION_TEST_FR, "host": host},
        )
        return {
            "host": host,
            "port": probe_port,
            "dns_resolved": dns_ok,
            "ip_addresses": resolved_ips,
            "reachable": reachable,
            "dns_error": dns_error,
            "connection_error": reach_err,
        }


class ServletConnection:
    """REST endpoint handler for broker and exchange connection configurations."""

    def __init__(self, host_settings: Any = None) -> None:
        """Initialize ServletConnection with optional settings container."""
        self.settings = host_settings or settings
        self._in_memory_connections: dict[str, dict[str, Any]] = {}

    def list_connections(self) -> list[dict[str, Any]]:
        """List existing broker and exchange connections."""
        conns: dict[str, Any] = {}
        try:
            scope_data = self.settings.get_scope("connections")
            if isinstance(scope_data, dict):
                conns.update(scope_data)
        except AttributeError, KeyError, RuntimeError:
            pass
        conns.update(self._in_memory_connections)
        records: list[dict[str, Any]] = []
        for cid, cdata in conns.items():
            if isinstance(cdata, dict):
                item = dict(cdata)
                item.setdefault("connection_id", cid)
                records.append(redact_secrets(item))
            else:
                records.append({"connection_id": cid, "value": cdata})
        logger.info(
            "%s: Listed %d connections.",
            SERVLET_CONNECTION_FR,
            len(records),
            extra={"fr_id": SERVLET_CONNECTION_FR, "count": len(records)},
        )
        return records

    def save_connection(
        self, connection_id: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Save or update connection credentials in host settings."""
        record = dict(data)
        record["connection_id"] = connection_id
        record["updated_at_utc"] = _now_utc_iso()
        try:
            self.settings.update_batch({"connections": {connection_id: record}})
        except RevisionConflictError, RuntimeError, ValueError:
            if hasattr(self.settings, "set_in_memory"):
                self.settings.set_in_memory("connections", connection_id, record)
        self._in_memory_connections[connection_id] = record
        logger.info(
            "%s: Saved connection '%s'.",
            SERVLET_CONNECTION_FR,
            connection_id,
            extra={"fr_id": SERVLET_CONNECTION_FR, "connection_id": connection_id},
        )
        redacted = redact_secrets(record)
        return dict(redacted) if isinstance(redacted, dict) else record

    def delete_connection(self, connection_id: str) -> bool:
        """Delete connection configuration and cached tokens."""
        existed = False
        try:
            scope = self.settings.get_scope("connections")
            if connection_id in scope:
                existed = True
                self.settings.update_batch({"connections": {connection_id: {}}})
        except RevisionConflictError, RuntimeError, ValueError:
            pass
        if connection_id in self._in_memory_connections:
            existed = True
            del self._in_memory_connections[connection_id]
        logger.info(
            "%s: Deleted connection '%s' (existed=%s).",
            SERVLET_CONNECTION_FR,
            connection_id,
            existed,
            extra={"fr_id": SERVLET_CONNECTION_FR, "connection_id": connection_id},
        )
        return existed

    def test_connection(
        self, connection_id: str | None = None, endpoint: str | None = None
    ) -> dict[str, Any]:
        """Test connection credentials and report latency status."""
        target_endpoint = endpoint
        if not target_endpoint and connection_id:
            conns = self.list_connections()
            for c in conns:
                if c.get("connection_id") == connection_id:
                    target_endpoint = c.get("endpoint") or c.get("host")
                    break
        if not target_endpoint:
            target_endpoint = "127.0.0.1"

        result = ConnectionTest.ping_endpoint(str(target_endpoint))
        logger.info(
            "%s: Tested connection (id=%s endpoint=%s reachable=%s).",
            SERVLET_CONNECTION_FR,
            connection_id,
            target_endpoint,
            result["reachable"],
            extra={"fr_id": SERVLET_CONNECTION_FR, "connection_id": connection_id},
        )
        return {
            "connection_id": connection_id,
            "endpoint": target_endpoint,
            "test_result": result,
            "timestamp": _now_utc_iso(),
        }


class ServletConstants:
    """System constants, environment paths, and runtime metadata endpoints."""

    def __init__(
        self,
        session_mgr: SessionManager | None = None,
        resource_mgr: Any | None = None,
    ) -> None:
        """Initialize ServletConstants with session and resource managers."""
        self.session_mgr = session_mgr or session_manager
        self.resource_mgr = resource_mgr

    def get_constants(self) -> dict[str, Any]:
        """Expose application version, build timestamp, and runtime paths."""
        data = {
            "application": "HaruQuantAI",
            "version": "1.0.0",
            "build_timestamp": "2026-10-18T00:00:00Z",
            "runtime": f"CPython {sys.version.split()[0]} (FastAPI)",
            "host_instance_id": self.session_mgr.host_instance_id,
            "data_directory": str(Path.cwd() / "data"),
            "core_channels": list(CORE_EVENT_CHANNELS),
            "supported_timeframes": list(SUPPORTED_TIMEFRAMES),
        }
        logger.info(
            "%s: Retrieved system constants.",
            SERVLET_CONSTANTS_FR,
            extra={"fr_id": SERVLET_CONSTANTS_FR},
        )
        return data

    def get_system_specs(self) -> dict[str, Any]:
        """Serve system resource limits, concurrency specs, and supported timeframes."""
        cpu_count = max(1, os.cpu_count() or 1)
        specs: dict[str, Any] = {
            "cpu_cores": cpu_count,
            "hardware_concurrency": cpu_count,
            "supported_timeframes": list(SUPPORTED_TIMEFRAMES),
            "memory_headroom": check_memory_headroom(),
            "worker_capacity": get_worker_capacity(),
            "system_health": get_system_health(),
        }
        logger.info(
            "%s: Retrieved system specs (cores=%d).",
            SERVLET_CONSTANTS_FR,
            cpu_count,
            extra={"fr_id": SERVLET_CONSTANTS_FR, "cpu_cores": cpu_count},
        )
        return specs


# ============================================================================
# Transport Service & FastAPI Router (FR-HOST-TRANSPORT-GATEWAY-APP)
# ============================================================================


class TransportGatewayService:
    """Coordinates session auth, shell status, SSE, and WebSocket endpoints."""

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        session_mgr: SessionManager | None = None,
        resource_mgr: Any | None = None,
        job_mgr: Any | None = None,
        password_hash: str | None = None,
        require_auth: bool = False,
        heartbeat_sec: float = DEFAULT_HEARTBEAT_SEC,
    ) -> None:
        """Initialize the transport gateway service."""
        self.event_bus = event_bus if event_bus is not None else get_global_event_bus()
        self.session_mgr = session_mgr if session_mgr is not None else session_manager
        self.resource_mgr = resource_mgr
        self.job_mgr = job_mgr
        self.password_hash = password_hash
        self.require_auth = require_auth
        self.heartbeat_sec = heartbeat_sec
        self.started_at = time.monotonic()
        self.app_loaded_acknowledged = False
        self.connection_servlet = ServletConnection(host_settings=settings)
        self.constants_servlet = ServletConstants(
            session_mgr=self.session_mgr, resource_mgr=self.resource_mgr
        )

    def verify_request_session(
        self, request: Request, query_token: str | None = None
    ) -> SessionRecord | None:
        """Validate bearer token from request headers or query parameters."""
        token = extract_bearer_token(request.headers.get("authorization"), query_token)
        if token is None:
            return None
        return self.session_mgr.validate_token(token)

    def _check_password(self, candidate_password: str) -> bool:
        """Verify ``candidate_password`` against configured or DB password hash."""
        configured_hash = self.password_hash
        if configured_hash is None:
            db_hash = settings.get("user_access", "password_hash", None)
            if isinstance(db_hash, str) and "$" in db_hash:
                configured_hash = db_hash

        if configured_hash is not None:
            return verify_password(candidate_password, configured_hash)
        return True

    async def handle_login(
        self, payload: LoginRequestPayload, request: Request
    ) -> JSONResponse:
        """Authenticate operator credentials and issue a 24h session token."""
        req_id = request.headers.get("x-request-id")
        if not self._check_password(payload.password):
            logger.warning(
                "FR-HOST-TRANSPORT-SESSION-AUTH: Rejected login attempt from %s.",
                request.client.host if request.client else "unknown",
                extra={"fr_id": "FR-HOST-TRANSPORT-SESSION-AUTH"},
            )
            err = StandardError(
                code="INVALID_CREDENTIALS",
                message="Invalid host password.",
            )
            resp = StandardResponse.failure(
                message="Authentication failed.",
                error=err,
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=resp.to_dict(),
            )

        default_user = str(
            settings.get("user_access", "username", "haruquantai") or "haruquantai"
        )
        username = (
            payload.username.strip()
            if payload.username and payload.username.strip()
            else default_user
        )
        peer_id = request.client.host if request.client else "127.0.0.1"
        raw_token, record = self.session_mgr.create_session(
            username=username, peer_id=peer_id
        )
        logger.info(
            "FR-HOST-TRANSPORT-SESSION-AUTH: Issued session '%s' for user '%s'.",
            record.session_id,
            record.username,
            extra={"fr_id": "FR-HOST-TRANSPORT-SESSION-AUTH"},
        )
        ok_resp = StandardResponse.success(
            data={
                "token": raw_token,
                "expires_at": _format_iso_expiry(record.expires_at_utc),
                "session_id": record.session_id,
                "username": record.username,
            },
            message="Session authenticated.",
            request_id=req_id,
            side_effects=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=ok_resp.to_dict())

    async def handle_session_me(self, request: Request) -> JSONResponse:
        """Validate the caller's bearer token and return session metadata."""
        req_id = request.headers.get("x-request-id")
        record = self.verify_request_session(request)
        if record is None:
            logger.warning(
                "FR-HOST-TRANSPORT-SESSION-AUTH: Unauthorized /sessions/me call.",
                extra={"fr_id": "FR-HOST-TRANSPORT-SESSION-AUTH"},
            )
            err = StandardError(
                code="UNAUTHORIZED",
                message="A valid active host session token is required.",
            )
            resp = StandardResponse.failure(
                message="Session validation failed.",
                error=err,
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=resp.to_dict(),
            )

        logger.info(
            "FR-HOST-TRANSPORT-SESSION-AUTH: Verified active session '%s'.",
            record.session_id,
            extra={"fr_id": "FR-HOST-TRANSPORT-SESSION-AUTH"},
        )
        data = record.to_dict()
        data["expires_at"] = _format_iso_expiry(record.expires_at_utc)
        ok_resp = StandardResponse.success(
            data=data,
            message="Active session verified.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=ok_resp.to_dict())

    async def handle_status(self, request: Request) -> JSONResponse:
        """Return host status, CPU core count, and runtime instance metadata."""
        req_id = request.headers.get("x-request-id")
        uptime = max(0.0, time.monotonic() - self.started_at)
        resp = StandardResponse.success(
            data={
                "state": "READY",
                "is_ready": True,
                "host_instance_id": self.session_mgr.host_instance_id,
                "cpu_count": max(1, os.cpu_count() or 1),
                "uptime_seconds": round(uptime, 3),
                "version": "1.0.0",
                "app_loaded": self.app_loaded_acknowledged,
            },
            message="Host status retrieved.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_readiness(self, request: Request) -> JSONResponse:
        """Return host readiness probe assessment."""
        req_id = request.headers.get("x-request-id")
        uptime = max(0.0, time.monotonic() - self.started_at)
        resp = StandardResponse.success(
            data={
                "state": "READY",
                "is_ready": True,
                "host_instance_id": self.session_mgr.host_instance_id,
                "uptime_seconds": round(uptime, 3),
                "channels": self.event_bus.channels,
            },
            message="Host is ready.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_app_loaded(self, request: Request) -> JSONResponse:
        """Acknowledge browser shell startup completion."""
        req_id = request.headers.get("x-request-id")
        if self.require_auth and self.verify_request_session(request) is None:
            err = StandardError(
                code="UNAUTHORIZED",
                message="Active session required for /app-loaded.",
            )
            resp = StandardResponse.failure(
                message="Unauthorized.", error=err, request_id=req_id
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=resp.to_dict(),
            )

        self.app_loaded_acknowledged = True
        self.event_bus.publish(
            channel="system",
            event_type="app_loaded",
            payload={"host_instance_id": self.session_mgr.host_instance_id},
        )
        logger.info(
            "FR-HOST-TRANSPORT-GATEWAY-APP: Browser shell /app-loaded "
            "acknowledged (host=%s).",
            self.session_mgr.host_instance_id,
            extra={"fr_id": "FR-HOST-TRANSPORT-GATEWAY-APP"},
        )
        ok_resp = StandardResponse.success(
            data={
                "acknowledged": True,
                "host_instance_id": self.session_mgr.host_instance_id,
            },
            message="Application load acknowledged.",
            request_id=req_id,
            side_effects=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=ok_resp.to_dict())

    async def handle_about(self, request: Request) -> JSONResponse:
        """Return application identity and clean-room architecture metadata."""
        req_id = request.headers.get("x-request-id")
        resp = StandardResponse.success(
            data={
                "application": "HaruQuantAI",
                "version": "1.0.0",
                "runtime": f"CPython {sys.version.split()[0]} (FastAPI)",
                "host_instance_id": self.session_mgr.host_instance_id,
                "core_channels": list(CORE_EVENT_CHANNELS),
            },
            message="About metadata retrieved.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def _require_scope(self, request: Request, scope: str) -> JSONResponse | None:
        """Enforce configured authentication and capability scope before access."""
        if not self.require_auth:
            return None
        session = self.verify_request_session(request)
        if session is not None and self.session_mgr.authorize(session, scope):
            return None
        code = "UNAUTHORIZED" if session is None else "FORBIDDEN"
        response = StandardResponse.failure(
            message="Access denied.",
            error=StandardError(
                code=code, message="Active authorized session required."
            ),
            request_id=request.headers.get("x-request-id"),
        )
        return JSONResponse(
            status_code=401 if session is None else 403, content=response.to_dict()
        )

    async def handle_get_settings(self, request: Request) -> JSONResponse:
        """Return redacted host settings snapshot and current revision."""
        req_id = request.headers.get("x-request-id")
        denied = self._require_scope(request, "settings:read")
        if denied is not None:
            return denied

        redacted = redact_secrets(settings.as_dict())
        ok_resp = StandardResponse.success(
            data={
                "revision": settings.revision,
                "settings": redacted,
            },
            message="Host settings retrieved.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=ok_resp.to_dict())

    async def handle_put_settings(
        self, payload: SettingsBatchUpdatePayload, request: Request
    ) -> JSONResponse:
        """Atomically update batch settings with revision conflict checking."""
        req_id = request.headers.get("x-request-id")
        denied = self._require_scope(request, "settings:write")
        if denied is not None:
            return denied

        try:
            new_rev = settings.update_batch(
                payload.settings,
                expected_revision=payload.revision,
            )
        except RevisionConflictError as exc:
            logger.warning(
                "FR-HOST-TRANSPORT-GATEWAY-APP: Settings revision conflict "
                "(expected=%s current=%d).",
                exc.expected_revision,
                exc.current_revision,
                extra={"fr_id": "FR-HOST-TRANSPORT-GATEWAY-APP"},
            )
            conflict_err = StandardError(
                code="REVISION_CONFLICT",
                message=str(exc),
                details={
                    "expected_revision": exc.expected_revision,
                    "current_revision": exc.current_revision,
                },
            )
            conflict_resp = StandardResponse.failure(
                message="Settings revision conflict.",
                error=conflict_err,
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=conflict_resp.to_dict(),
            )

        self.event_bus.publish(
            channel="settings.changed",
            event_type="updated",
            payload={
                "revision": new_rev,
                "scopes": sorted(payload.settings.keys()),
            },
        )
        ok_resp = StandardResponse.success(
            data={
                "revision": new_rev,
                "settings": redact_secrets(settings.as_dict()),
            },
            message="Host settings updated.",
            request_id=req_id,
            side_effects=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=ok_resp.to_dict())

    async def handle_list_connections(self, request: Request) -> JSONResponse:
        """List configured broker and exchange connections."""
        req_id = request.headers.get("x-request-id")
        denied = self._require_scope(request, "connections:read")
        if denied is not None:
            return denied
        records = self.connection_servlet.list_connections()
        resp = StandardResponse.success(
            data={"connections": records, "count": len(records)},
            message="Connections retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_save_connection(self, request: Request) -> JSONResponse:
        """Save or update broker/exchange connection credentials."""
        req_id = request.headers.get("x-request-id")
        denied = self._require_scope(request, "connections:write")
        if denied is not None:
            return denied
        raw_body: Any = None
        with suppress(ValueError):
            raw_body = await request.json()
        body: dict[str, Any] = raw_body if isinstance(raw_body, dict) else {}
        cid = str(body.get("connection_id") or f"conn-{secrets.token_hex(4)}")
        saved = self.connection_servlet.save_connection(cid, body)
        resp = StandardResponse.success(
            data=saved,
            message=f"Connection '{cid}' saved successfully.",
            request_id=req_id,
            side_effects=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_delete_connection(
        self, connection_id: str, request: Request
    ) -> JSONResponse:
        """Delete broker/exchange connection configuration."""
        req_id = request.headers.get("x-request-id")
        denied = self._require_scope(request, "connections:write")
        if denied is not None:
            return denied
        deleted = self.connection_servlet.delete_connection(connection_id)
        if not deleted:
            err = StandardError(
                code="NOT_FOUND",
                message=f"Connection '{connection_id}' not found.",
            )
            fail_resp = StandardResponse.failure(
                message="Connection deletion failed.",
                error=err,
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content=fail_resp.to_dict()
            )
        deleted_data: dict[str, Any] = {
            "connection_id": connection_id,
            "deleted": True,
        }
        ok_resp = StandardResponse.success(
            data=deleted_data,
            message=f"Connection '{connection_id}' deleted successfully.",
            request_id=req_id,
            side_effects=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=ok_resp.to_dict())

    async def handle_test_connection(
        self, request: Request, connection_id: str | None = None
    ) -> JSONResponse:
        """Test network reachability and latency for a connection or endpoint."""
        req_id = request.headers.get("x-request-id")
        denied = self._require_scope(request, "connections:read")
        if denied is not None:
            return denied
        endpoint = None
        with suppress(ValueError):
            body = await request.json()
            if isinstance(body, dict):
                endpoint = body.get("endpoint")
                if not connection_id:
                    connection_id = body.get("connection_id")
        res = self.connection_servlet.test_connection(connection_id, endpoint)
        resp = StandardResponse.success(
            data=res,
            message="Connection reachability test completed.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_get_constants(self, request: Request) -> JSONResponse:
        """Expose application constants, version, and runtime paths."""
        req_id = request.headers.get("x-request-id")
        data = self.constants_servlet.get_constants()
        resp = StandardResponse.success(
            data=data,
            message="Constants retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_get_system_specs(self, request: Request) -> JSONResponse:
        """Expose system resource limits, concurrency specs, and timeframes."""
        req_id = request.headers.get("x-request-id")
        data = self.constants_servlet.get_system_specs()
        resp = StandardResponse.success(
            data=data,
            message="System specs retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def _resolve_resource_mgr(self, request: Request) -> Any | None:
        """Return configured ResourceManager or resolve from FastAPI app.state."""
        if self.resource_mgr is not None:
            return self.resource_mgr
        runtime = getattr(request.app.state, "runtime", None)
        return getattr(runtime, "resource_manager", None)

    def _resolve_job_mgr(self, request: Request) -> Any | None:
        """Return configured JobManager or resolve from FastAPI app.state."""
        if self.job_mgr is not None:
            return self.job_mgr
        runtime = getattr(request.app.state, "runtime", None)
        return getattr(runtime, "job_manager", None)

    async def handle_diagnostics(self, request: Request) -> JSONResponse:
        """Return hardware probes, worker allocation, memory watchdog, and health."""
        denied = self._require_scope(request, "diagnostics:read")
        if denied is not None:
            return denied
        req_id = request.headers.get("x-request-id")
        res_mgr = self._resolve_resource_mgr(request)
        hw = probe_hardware()
        cap = get_worker_capacity()
        wd = (
            res_mgr.check_memory_headroom()
            if res_mgr is not None
            else check_memory_headroom()
        )
        health = (
            res_mgr.get_system_health() if res_mgr is not None else get_system_health()
        )
        resp = StandardResponse.success(
            data={
                "status": health.status,
                "hardware": asdict(hw),
                "worker_capacity": asdict(cap),
                "memory_watchdog": asdict(wd),
                "database": asdict(health.database),
                "storage": asdict(health.storage),
            },
            message="System diagnostics and resource governance retrieved.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_list_jobs(
        self,
        request: Request,
        status_filter: str | None = None,
        limit: int = 50,
    ) -> JSONResponse:
        """List recent background jobs from JobManager or persistence."""
        denied = self._require_scope(request, "jobs:read")
        if denied is not None:
            return denied
        req_id = request.headers.get("x-request-id")
        jm = self._resolve_job_mgr(request)
        if jm is not None:
            records = jm.list_jobs(status=status_filter, limit=limit)
            jobs_list = [r.to_dict() for r in records]
        else:
            jobs_list = list_host_jobs(status=status_filter, limit=limit)

        resp = StandardResponse.success(
            data={
                "count": len(jobs_list),
                "jobs": jobs_list,
            },
            message="Host jobs listed.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_get_job(self, job_id: str, request: Request) -> JSONResponse:
        """Retrieve a specific background job by ID."""
        denied = self._require_scope(request, "jobs:read")
        if denied is not None:
            return denied
        req_id = request.headers.get("x-request-id")
        job_data: dict[str, Any] | None = None
        jm = self._resolve_job_mgr(request)
        if jm is not None:
            rec = jm.get_job(job_id)
            if rec is not None:
                job_data = rec.to_dict()
        else:
            job_data = get_host_job(job_id)

        if job_data is None:
            err = StandardError(
                code="JOB_NOT_FOUND",
                message=f"Job '{job_id}' was not found.",
            )
            not_found = StandardResponse.failure(
                message="Job not found.",
                error=err,
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=not_found.to_dict(),
            )

        resp = StandardResponse.success(
            data=job_data,
            message="Host job retrieved.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_cancel_job(self, job_id: str, request: Request) -> JSONResponse:
        """Signal cooperative cancellation for a running or queued job."""
        denied = self._require_scope(request, "jobs:write")
        if denied is not None:
            return denied
        req_id = request.headers.get("x-request-id")
        cancelled = False
        jm = self._resolve_job_mgr(request)
        if jm is not None:
            cancelled = bool(jm.cancel_job(job_id))

        if not cancelled:
            err = StandardError(
                code="JOB_NOT_CANCELLABLE",
                message=f"Job '{job_id}' could not be cancelled or does not exist.",
            )
            fail_resp = StandardResponse.failure(
                message="Job cancellation failed.",
                error=err,
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=fail_resp.to_dict(),
            )

        self.event_bus.publish(
            channel="jobs",
            event_type="cancelled",
            payload={"job_id": job_id},
        )
        ok_resp = StandardResponse.success(
            data={"job_id": job_id, "cancelled": True},
            message=f"Signaled cancellation for job '{job_id}'.",
            request_id=req_id,
            side_effects=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=ok_resp.to_dict())

    async def handle_events_stream(
        self,
        request: Request,
        channels: str | None = None,
        since_cursor: int | None = None,
        limit: int | None = None,
        token: str | None = None,
    ) -> StreamingResponse | JSONResponse:
        """Stream Server-Sent Events (SSE) for requested channels."""
        auth_header = request.headers.get("authorization")
        raw_token = extract_bearer_token(auth_header, token)
        if (self.require_auth or raw_token is not None) and (
            raw_token is None or self.session_mgr.validate_token(raw_token) is None
        ):
            req_id = request.headers.get("x-request-id")
            err = StandardError(
                code="UNAUTHORIZED",
                message="Valid session token required for SSE stream.",
            )
            resp = StandardResponse.failure(
                message="Unauthorized SSE request.",
                error=err,
                request_id=req_id,
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=resp.to_dict(),
            )

        parsed_channels = _parse_channels_param(channels)
        resolved_cursor = _resolve_since_cursor(
            since_cursor, request.headers.get("last-event-id")
        )
        session_check: Callable[[], bool] | None = (
            (lambda: self.session_mgr.validate_token(raw_token) is not None)
            if raw_token is not None
            else None
        )

        generator = sse_event_generator(
            event_bus=self.event_bus,
            channels=parsed_channels,
            since_cursor=resolved_cursor,
            request=request,
            heartbeat_interval_sec=self.heartbeat_sec,
            limit=limit,
            session_valid=session_check,
        )
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def handle_publish(
        self, body: PublishEventRequest, request: Request
    ) -> JSONResponse:
        """Publish an event to the host EventBus via REST."""
        req_id = request.headers.get("x-request-id")
        ev = self.event_bus.publish(
            channel=body.channel,
            event_type=body.event_type,
            payload=body.payload,
        )
        resp = StandardResponse.success(
            data=ev.model_dump(),
            message="Event published.",
            request_id=req_id,
            side_effects=True,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_snapshot(
        self,
        request: Request,
        channel: str = "*",
        since_cursor: int | None = None,
        limit: int = 100,
    ) -> JSONResponse:
        """Return retained historical events for ``channel``."""
        req_id = request.headers.get("x-request-id")
        snapshot = self.event_bus.get_snapshot(
            channel=channel, since_cursor=since_cursor, limit=limit
        )
        resp = StandardResponse.success(
            data=snapshot.model_dump(),
            message="Event snapshot retrieved.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_channels(self, request: Request) -> JSONResponse:
        """Return registered EventBus channels and current cursor."""
        req_id = request.headers.get("x-request-id")
        resp = StandardResponse.success(
            data={
                "core_channels": list(CORE_EVENT_CHANNELS),
                "active_channels": self.event_bus.channels,
                "current_cursor": self.event_bus.current_cursor,
            },
            message="Event channels listed.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    async def handle_websocket(
        self,
        websocket: WebSocket,
        channels: str | None = None,
        since_cursor: int | None = None,
        token: str | None = None,
    ) -> None:
        """Stream bidirectional JSON events and commands over ``WebSocket /ws``."""
        raw_token = extract_bearer_token(websocket.headers.get("authorization"), token)
        if self.require_auth and (
            raw_token is None or self.session_mgr.validate_token(raw_token) is None
        ):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        parsed_channels = _parse_channels_param(channels)
        sub_id, queue, replay_events, has_gap = self.event_bus.subscribe(
            channels=parsed_channels,
            since_cursor=since_cursor,
        )
        logger.info(
            "FR-HOST-TRANSPORT-WS-STREAMING: WebSocket connected "
            "(sub_id=%s channels=%s).",
            sub_id,
            parsed_channels,
            extra={"fr_id": "FR-HOST-TRANSPORT-WS-STREAMING"},
        )

        try:
            await _send_ws_initial_frames(websocket, replay_events, has_gap)
            await self._run_ws_loop(websocket, sub_id, queue)
        except WebSocketDisconnect:
            pass
        finally:
            self.event_bus.unsubscribe(sub_id)
            logger.info(
                "FR-HOST-TRANSPORT-WS-STREAMING: WebSocket disconnected (sub_id=%s).",
                sub_id,
                extra={"fr_id": "FR-HOST-TRANSPORT-WS-STREAMING"},
            )

    async def _run_ws_loop(
        self,
        websocket: WebSocket,
        sub_id: str,
        queue: asyncio.Queue[HostEvent],
    ) -> None:
        """Multiplex incoming WebSocket commands and outgoing EventBus events."""
        while True:
            recv_task = asyncio.create_task(websocket.receive_json())
            queue_task = asyncio.create_task(queue.get())
            done, pending = await asyncio.wait(
                {recv_task, queue_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

            if queue_task in done:
                ev = queue_task.result()
                await websocket.send_json(ev.model_dump())

            if recv_task in done:
                msg = recv_task.result()
                if not await self._handle_ws_client_message(websocket, sub_id, msg):
                    break

    async def _handle_ws_client_message(
        self,
        websocket: WebSocket,
        sub_id: str,
        msg: Any,
    ) -> bool:
        """Process a client JSON control message on ``/ws``; return False to close."""
        if not isinstance(msg, dict):
            return True

        action = str(msg.get("action", "")).lower()
        if action == "close":
            return False
        if action == "ping":
            await websocket.send_json(
                {
                    "channel": "system",
                    "event_type": "pong",
                    "timestamp": _now_utc_iso(),
                    "payload": {},
                }
            )
        elif action == "subscribe":
            raw_chans = msg.get("channels")
            if isinstance(raw_chans, list):
                chans = [str(c) for c in raw_chans if str(c).strip()]
                self.event_bus.update_subscription(sub_id, chans or ["*"])
                await websocket.send_json(
                    {
                        "channel": "system",
                        "event_type": "subscribed",
                        "timestamp": _now_utc_iso(),
                        "payload": {"channels": chans or ["*"]},
                    }
                )
        elif action == "publish":
            channel = str(msg.get("channel", "system"))
            event_type = str(msg.get("event_type", "update"))
            payload = msg["payload"] if isinstance(msg.get("payload"), dict) else {}
            self.event_bus.publish(
                channel=channel, event_type=event_type, payload=payload
            )
        return True


async def _send_ws_initial_frames(
    websocket: WebSocket,
    replay_events: list[HostEvent],
    has_gap: bool,
) -> None:
    """Send initial gap warning and replay events over an accepted WebSocket."""
    if has_gap:
        await websocket.send_json(
            {
                "channel": "system",
                "event_type": "gap",
                "timestamp": _now_utc_iso(),
                "payload": {
                    "message": "Event history gap detected; resynchronize state."
                },
            }
        )
    for ev in replay_events:
        await websocket.send_json(ev.model_dump())


def create_transport_router(
    *,
    event_bus: EventBus | None = None,
    session_mgr: SessionManager | None = None,
    resource_mgr: Any | None = None,
    job_mgr: Any | None = None,
    password_hash: str | None = None,
    require_auth: bool = False,
    heartbeat_sec: float = DEFAULT_HEARTBEAT_SEC,
    prefix: str = "",
) -> APIRouter:
    """Create a FastAPI ``APIRouter`` exposing host auth, shell, SSE, and WS routes."""
    service = TransportGatewayService(
        event_bus=event_bus,
        session_mgr=session_mgr,
        resource_mgr=resource_mgr,
        job_mgr=job_mgr,
        password_hash=password_hash,
        require_auth=require_auth,
        heartbeat_sec=heartbeat_sec,
    )
    router = APIRouter(prefix=prefix, tags=["host-transport"])

    router.add_api_route("/auth", service.handle_session_me, methods=["GET"])
    router.add_api_route("/auth", service.handle_login, methods=["POST"])
    router.add_api_route("/auth/login", service.handle_login, methods=["POST"])
    router.add_api_route("/sessions/me", service.handle_session_me, methods=["GET"])
    router.add_api_route("/status", service.handle_status, methods=["GET"])
    router.add_api_route("/readiness", service.handle_readiness, methods=["GET"])
    router.add_api_route("/app-loaded", service.handle_app_loaded, methods=["POST"])
    router.add_api_route("/about", service.handle_about, methods=["GET"])
    router.add_api_route("/settings", service.handle_get_settings, methods=["GET"])
    router.add_api_route("/settings", service.handle_put_settings, methods=["PUT"])
    router.add_api_route("/diagnostics", service.handle_diagnostics, methods=["GET"])
    router.add_api_route("/resources", service.handle_diagnostics, methods=["GET"])
    router.add_api_route("/jobs", service.handle_list_jobs, methods=["GET"])
    router.add_api_route("/jobs/{job_id}", service.handle_get_job, methods=["GET"])
    router.add_api_route(
        "/jobs/{job_id}/cancel", service.handle_cancel_job, methods=["POST"]
    )
    router.add_api_route(
        "/events",
        service.handle_events_stream,
        methods=["GET"],
        response_model=None,
    )
    router.add_api_route("/events/publish", service.handle_publish, methods=["POST"])
    router.add_api_route("/events/snapshot", service.handle_snapshot, methods=["GET"])
    router.add_api_route("/events/channels", service.handle_channels, methods=["GET"])
    router.add_api_route(
        "/connections", service.handle_list_connections, methods=["GET"]
    )
    router.add_api_route(
        "/connections", service.handle_save_connection, methods=["POST"]
    )
    router.add_api_route(
        "/connections/test", service.handle_test_connection, methods=["POST"]
    )
    router.add_api_route(
        "/connections/{connection_id}",
        service.handle_delete_connection,
        methods=["DELETE"],
    )
    router.add_api_route(
        "/connections/{connection_id}/test",
        service.handle_test_connection,
        methods=["POST"],
    )
    router.add_api_route("/constants", service.handle_get_constants, methods=["GET"])
    router.add_api_route("/specs", service.handle_get_system_specs, methods=["GET"])
    router.add_api_websocket_route("/ws", service.handle_websocket)

    logger.info(
        "FR-HOST-TRANSPORT-GATEWAY-APP: Created transport router (prefix='%s').",
        prefix or "/",
        extra={"fr_id": "FR-HOST-TRANSPORT-GATEWAY-APP"},
    )
    return router


def create_host_app(
    *,
    event_bus: EventBus | None = None,
    session_mgr: SessionManager | None = None,
    resource_mgr: Any | None = None,
    job_mgr: Any | None = None,
    password_hash: str | None = None,
    require_auth: bool = False,
    heartbeat_sec: float = DEFAULT_HEARTBEAT_SEC,
    extra_routers: Sequence[APIRouter] | None = None,
) -> FastAPI:
    """Create the configured FastAPI host gateway application."""
    bus = event_bus if event_bus is not None else get_global_event_bus()
    sessions = session_mgr if session_mgr is not None else session_manager

    app = FastAPI(
        title="HaruQuantAI Host Platform Gateway",
        version="1.0.0",
    )
    app.state.event_bus = bus
    app.state.session_manager = sessions

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TransportMiddleware)
    register_transport_exception_handlers(app)

    for route_prefix in ("", "/api/v1", "/api/v2"):
        app.include_router(
            create_transport_router(
                event_bus=bus,
                session_mgr=sessions,
                resource_mgr=resource_mgr,
                job_mgr=job_mgr,
                password_hash=password_hash,
                require_auth=require_auth,
                heartbeat_sec=heartbeat_sec,
                prefix=route_prefix,
            )
        )

    if extra_routers:
        for extra in extra_routers:
            app.include_router(extra)

    logger.info(
        "FR-HOST-TRANSPORT-GATEWAY-APP: Initialized FastAPI host gateway "
        "(instance=%s).",
        sessions.host_instance_id,
        extra={"fr_id": "FR-HOST-TRANSPORT-GATEWAY-APP"},
    )
    return app


# ============================================================================
# Standalone CLI Entrypoint
# ============================================================================


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for verifying the host EventBus and transport gateway."""
    parser = argparse.ArgumentParser(
        prog="app.host.transport",
        description="HaruQuantAI Host Transport & EventBus CLI",
    )
    parser.add_argument(
        "--test-bus",
        action="store_true",
        help="Publish a test event across core channels and print snapshot JSON.",
    )
    args = parser.parse_args(argv)

    bus = EventBus()
    if args.test_bus:
        for ch in CORE_EVENT_CHANNELS:
            bus.publish(ch, "self_test", {"channel": ch, "ok": True})
        snap = bus.get_snapshot("*")
        print(json.dumps(snap.model_dump(), indent=2))
        return 0

    print(
        json.dumps(
            {
                "core_channels": list(CORE_EVENT_CHANNELS),
                "ring_capacity": bus.ring_capacity,
                "max_queue_size": bus.max_queue_size,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
