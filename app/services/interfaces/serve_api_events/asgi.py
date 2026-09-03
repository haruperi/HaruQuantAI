"""ASGI mounting surface for the serve-api-events transport.

Purpose:
    Serve the ratified external boundary over raw ASGI without a
    framework or monolithic gateway: JSON snapshot envelopes
    (``ApiResponse``/``ApiMetadata``/``ApiError``) and SSE stream frames
    (``StreamEvent``), resolving capabilities from the live registry per
    request and translating absence to the stable
    ``CAPABILITY_UNAVAILABLE`` failure.

Key capabilities:
    * Serve ``GET /api/v1/market/ticks`` (canonical snapshot JSON).
    * Serve ``GET /api/v1/market/ticks/stream`` and the adopted alias
      ``GET /api/v1/data/snapshot-stream`` as ordered SSE frames.
    * Mirror ``X-Request-Id``/``X-Trace-Id`` into every envelope.
    * Release subscriptions exactly on client disconnect or provider end.

Python API usage:
    app = create_api_asgi_app(registry)

CLI usage:
    uv run haruquantai  (composes the runtime and serves this adapter)
"""

from __future__ import annotations

import asyncio
import contextlib
import re
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import parse_qs
from uuid import uuid4, uuid7

from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_CATALOGUE_CAPABILITY,
    OBSERVE_MARKET_DATA_CAPABILITY,
)
from app.contracts.interfaces.models import (
    ApiError,
    ApiMetadata,
    ApiResponse,
    MarketTickSnapshot,
    ObserveMarketCatalogueRequest,
    ObserveMarketCatalogueSuccess,
    ObserveMarketDataEventSubscription,
    ObserveMarketDataRequest,
    ObserveMarketDataSuccess,
    StreamEvent,
)

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from typing import Any

    from app.contracts.interfaces.errors import InterfaceFailure
    from app.contracts.interfaces.ports import ObserveMarketDataCapability
    from app.kernel.capability import CapabilityKey
    from app.kernel.registry import ServiceRegistry

type Scope = MutableMapping[str, Any]
type Message = MutableMapping[str, Any]
type Receive = Callable[[], Awaitable[Message]]
type Send = Callable[[Message], Awaitable[None]]
type AsgiApp = Callable[[Scope, Receive, Send], Awaitable[None]]

_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
_MAX_SYMBOLS = 200
_MAX_CATALOGUE_PAGE_SIZE = 500
_UUID7_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)

_SNAPSHOT_ROUTE = "/api/v1/market/ticks"
_STREAM_ROUTE = "/api/v1/market/ticks/stream"
_ALIAS_STREAM_ROUTE = "/api/v1/data/snapshot-stream"
_STREAM_ROUTES = frozenset({_STREAM_ROUTE, _ALIAS_STREAM_ROUTE})
_CATALOGUE_ROUTES = ("/api/v1/market/catalogue", "/api/v1/data/markets")
_CATALOGUE_OPERATION = "api.market.catalogue"
_PROVIDER_CATALOGUE_SOURCE_ID = CATALOG_INSTRUMENTS_CAPABILITY.identifier


def _utc_now() -> str:
    """Return the current instant as a canonical wire timestamp.

    Returns:
        Fixed-width UTC timestamp string.
    """
    return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)


def _header(scope: Scope, name: str) -> str | None:
    """Read one request header case-insensitively.

    Args:
        scope: ASGI connection scope.
        name: Lowercase header name.

    Returns:
        Decoded header value, or None when absent.
    """
    wanted = name.encode("latin-1")
    headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
    for raw_name, raw_value in headers:
        if raw_name.lower() == wanted:
            return raw_value.decode("latin-1")
    return None


def _parse_symbols(scope: Scope) -> tuple[str, ...]:
    """Parse the comma-joined symbols query parameter.

    Args:
        scope: ASGI connection scope.

    Returns:
        Tuple of non-empty symbol filters; empty selects everything.
    """
    query = parse_qs(scope.get("query_string", b"").decode("latin-1"))
    raw = query.get("symbols", [""])[0]
    return tuple(symbol.strip() for symbol in raw.split(",") if symbol.strip())


def _snapshot_payload(snapshot: MarketTickSnapshot) -> dict[str, Any]:
    """Project one snapshot into the adopted wire payload shape.

    Args:
        snapshot: Gateway snapshot projection.

    Returns:
        Payload mapping with quotes, source identity, gap, and staleness.
    """
    return {
        "quotes": [quote.model_dump(mode="json") for quote in snapshot.quotes],
        "source_id": snapshot.source_id,
        "gap": snapshot.gap,
        "stale": snapshot.stale,
    }


def _metadata(
    request_id: str,
    route: str,
    operation: str,
    side_effect: str,
    stale: bool,
    stale_reason: str | None,
    trace_id: str | None,
) -> ApiMetadata:
    """Build the response metadata envelope.

    Args:
        request_id: Mirrored or generated request identifier.
        route: Served route path.
        operation: Canonical operation name.
        side_effect: Route side-effect classification.
        stale: Whether the served projection is stale.
        stale_reason: Explicit staleness reason when stale.
        trace_id: Optional mirrored trace identifier.

    Returns:
        Validated metadata envelope.
    """
    return ApiMetadata(
        request_id=request_id,
        route=route,
        operation=operation,
        trace_id=trace_id,
        side_effect=side_effect,  # type: ignore[arg-type]
        timestamp=_utc_now(),
        stale=stale,
        stale_reason=stale_reason,
    )


def _error_response(
    request_id: str,
    route: str,
    operation: str,
    status: HTTPStatus,
    code: str,
    message: str,
    trace_id: str | None,
) -> ApiResponse:
    """Build a uniform JSON error envelope.

    Args:
        request_id: Mirrored or generated request identifier.
        route: Served route path.
        operation: Canonical operation name.
        status: HTTP status code.
        code: Stable machine error code.
        message: Bounded human-readable message.
        trace_id: Optional mirrored trace identifier.

    Returns:
        Error ApiResponse envelope.
    """
    return ApiResponse(
        status="error",
        message=HTTPStatus(status).phrase,
        error=ApiError(
            code=code,
            message=message,
            request_id=request_id,
            trace_id=trace_id,
            retryable=status >= HTTPStatus.INTERNAL_SERVER_ERROR,
        ),
        metadata=_metadata(request_id, route, operation, "read", False, None, trace_id),
    )


async def _send_json(send: Send, status: HTTPStatus, envelope: ApiResponse) -> None:
    """Emit one complete JSON response.

    Args:
        send: ASGI send callable.
        status: HTTP status code.
        envelope: Response envelope to serialize.
    """
    body = envelope.model_dump_json().encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _send_error(
    send: Send,
    status: HTTPStatus,
    code: str,
    message: str,
    route: str,
    operation: str,
    trace_id: str | None,
) -> None:
    """Emit one uniform JSON error response.

    Args:
        send: ASGI send callable.
        status: HTTP status code.
        code: Stable machine error code.
        message: Bounded human-readable message.
        route: Served route path.
        operation: Canonical operation name.
        trace_id: Optional mirrored trace identifier.
    """
    envelope = _error_response(
        f"req-{uuid4()}",
        route,
        operation,
        status,
        code,
        message,
        trace_id,
    )
    await _send_json(send, status, envelope)


async def _wait_disconnect(receive: Receive) -> None:
    """Consume request messages until the client disconnects.

    Args:
        receive: ASGI receive callable.
    """
    while True:
        message = await receive()
        if message.get("type") == "http.disconnect":
            return


@dataclass(frozen=True, slots=True)
class _SseContext:
    """Shared per-request SSE emission state."""

    send: Send
    request_id: str
    trace_id: str | None
    route: str


async def _emit_frame(
    ctx: _SseContext,
    event_type: str,
    payload: dict[str, Any] | None,
    error: dict[str, Any] | None,
    sequence: int,
    cursor: str | None,
) -> None:
    """Emit one SSE frame carrying the ratified stream contract.

    Args:
        ctx: Per-request SSE emission state.
        event_type: Frame classification (payload or error).
        payload: Snapshot payload mapping for payload frames.
        error: Error mapping for terminal error frames.
        sequence: Monotonic snapshot sequence.
        cursor: Resume cursor for reconnecting clients.
    """
    frame = StreamEvent(
        sequence=sequence,
        request_id=ctx.request_id,
        trace_id=ctx.trace_id,
        route=ctx.route,
        event_type=event_type,  # type: ignore[arg-type]
        timestamp=_utc_now(),
        payload=payload,
        error=error,
        cursor=cursor,
    )
    body = f"id: {sequence}\nevent: {event_type}\ndata: {frame.model_dump_json()}\n\n"
    await ctx.send(
        {"type": "http.response.body", "body": body.encode("utf-8"), "more_body": True}
    )


def _snapshot_request(symbols: tuple[str, ...]) -> ObserveMarketDataRequest:
    """Build one internal snapshot request.

    Args:
        symbols: Bounded symbol filter.

    Returns:
        Operation-discriminated SNAPSHOT request.
    """
    return ObserveMarketDataRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="SNAPSHOT",
        symbols=symbols,
    )


def _snapshot_of(
    result: ObserveMarketDataSuccess | InterfaceFailure,
) -> MarketTickSnapshot | None:
    """Extract the snapshot from a gateway result.

    Args:
        result: Gateway observation result.

    Returns:
        The projected snapshot, or None when the result carries none.
    """
    if not isinstance(result, ObserveMarketDataSuccess):
        return None
    return result.snapshot


async def _resolve_gateway[CapT](
    registry: ServiceRegistry,
    capability: CapabilityKey[CapT],
    unavailable_detail: str,
    route: str,
    operation: str,
    request_id: str,
    trace_id: str | None,
    send: Send,
) -> CapT | None:
    """Resolve one gateway capability or serve the unavailable failure.

    Args:
        registry: Live composition service registry.
        capability: Capability key of the required gateway.
        unavailable_detail: Failure detail naming the capability.
        route: Served route path.
        operation: Canonical operation name.
        request_id: Mirrored or generated request identifier.
        trace_id: Optional mirrored trace identifier.
        send: ASGI send callable.

    Returns:
        Active gateway, or None after serving the failure envelope.
    """
    gateway = registry.resolve(capability)
    if gateway is not None:
        return gateway
    await _send_json(
        send,
        HTTPStatus.SERVICE_UNAVAILABLE,
        _error_response(
            request_id,
            route,
            operation,
            HTTPStatus.SERVICE_UNAVAILABLE,
            "CAPABILITY_UNAVAILABLE",
            unavailable_detail,
            trace_id,
        ),
    )
    return None


async def _symbols_or_error(
    scope: Scope,
    route: str,
    operation: str,
    request_id: str,
    trace_id: str | None,
    send: Send,
) -> tuple[str, ...] | None:
    """Parse the bounded symbol filter or serve a validation failure.

    Args:
        scope: ASGI connection scope.
        route: Served route path.
        operation: Canonical operation name.
        request_id: Mirrored or generated request identifier.
        trace_id: Optional mirrored trace identifier.
        send: ASGI send callable.

    Returns:
        Symbol filter tuple, or None after serving the failure envelope.
    """
    symbols = _parse_symbols(scope)
    if len(symbols) <= _MAX_SYMBOLS:
        return symbols
    await _send_json(
        send,
        HTTPStatus.BAD_REQUEST,
        _error_response(
            request_id,
            route,
            operation,
            HTTPStatus.BAD_REQUEST,
            "VALIDATION_ERROR",
            f"The symbols filter exceeds {_MAX_SYMBOLS} entries.",
            trace_id,
        ),
    )
    return None


async def _serve_snapshot(
    registry: ServiceRegistry,
    scope: Scope,
    _receive: Receive,
    send: Send,
) -> None:
    """Serve one canonical JSON snapshot request.

    Args:
        registry: Live composition service registry.
        scope: ASGI connection scope.
        _receive: Unused for GET snapshot requests.
        send: ASGI send callable.
    """
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")
    operation = "api.market.ticks"
    symbols = await _symbols_or_error(
        scope, _SNAPSHOT_ROUTE, operation, request_id, trace_id, send
    )
    if symbols is None:
        return
    gateway = await _resolve_gateway(
        registry,
        OBSERVE_MARKET_DATA_CAPABILITY,
        "The market observation capability has no active provider.",
        _SNAPSHOT_ROUTE,
        operation,
        request_id,
        trace_id,
        send,
    )
    if gateway is None:
        return
    result = await gateway.observe_market_data(_snapshot_request(symbols))
    snapshot = _snapshot_of(result)
    if snapshot is None:
        await _send_error(
            send,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "INTERNAL_ERROR",
            "The observation gateway returned no snapshot.",
            _SNAPSHOT_ROUTE,
            operation,
            trace_id,
        )
        return
    envelope = ApiResponse(
        status="success",
        message=HTTPStatus.OK.phrase,
        data=_snapshot_payload(snapshot),
        metadata=_metadata(
            request_id,
            _SNAPSHOT_ROUTE,
            operation,
            "read",
            snapshot.stale,
            snapshot.stale_reason,
            trace_id,
        ),
    )
    await _send_json(send, HTTPStatus.OK, envelope)


async def _pump_events(
    ctx: _SseContext,
    gateway: ObserveMarketDataCapability,
    iterator: AsyncIterator[Any],
    disconnect: asyncio.Future[None],
    request: ObserveMarketDataRequest,
) -> None:
    """Emit one frame per provider event until disconnect or stream end.

    Args:
        ctx: Per-request SSE emission state.
        gateway: Active observation gateway.
        iterator: Gateway subscription async iterator.
        disconnect: Future completing on client disconnect.
        request: Reused internal snapshot request.
    """
    while not disconnect.done():
        next_event = asyncio.ensure_future(anext(iterator))
        done, _pending = await asyncio.wait(
            {next_event, disconnect},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if disconnect in done:
            next_event.cancel()
            with contextlib.suppress(BaseException):
                await next_event
            return
        try:
            await next_event
        except StopAsyncIteration:
            return
        update = await gateway.observe_market_data(request)
        snapshot = _snapshot_of(update)
        if snapshot is None:
            await _emit_terminal_failure(ctx, update)
            return
        await _emit_frame(
            ctx,
            "payload",
            _snapshot_payload(snapshot),
            None,
            snapshot.sequence,
            str(snapshot.sequence),
        )


async def _emit_terminal_failure(
    ctx: _SseContext,
    result: ObserveMarketDataSuccess | InterfaceFailure,
) -> None:
    """Emit one terminal SSE error frame for a failed snapshot refresh.

    Args:
        ctx: Per-request SSE emission state.
        result: Failed gateway observation result.
    """
    if isinstance(result, ObserveMarketDataSuccess):
        return
    await _emit_frame(
        ctx,
        "error",
        None,
        {"code": result.code, "detail": result.problem.detail},
        0,
        None,
    )


async def _serve_stream(
    registry: ServiceRegistry,
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """Serve one SSE observation stream request.

    Args:
        registry: Live composition service registry.
        scope: ASGI connection scope.
        receive: ASGI receive callable.
        send: ASGI send callable.
    """
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")
    route = str(scope.get("path", _STREAM_ROUTE))
    operation = "api.market.ticks_stream"
    symbols = await _symbols_or_error(
        scope, route, operation, request_id, trace_id, send
    )
    if symbols is None:
        return
    gateway = await _resolve_gateway(
        registry,
        OBSERVE_MARKET_DATA_CAPABILITY,
        "The market observation capability has no active provider.",
        route,
        operation,
        request_id,
        trace_id,
        send,
    )
    if gateway is None:
        return
    resume_header = _header(scope, "last-event-id")
    resume_event_id = (
        resume_header
        if resume_header is not None and _UUID7_PATTERN.match(resume_header)
        else None
    )
    subscription = ObserveMarketDataEventSubscription(
        symbols=symbols,
        resume_event_id=resume_event_id,
        replay_limit=0,
    )
    await send(
        {
            "type": "http.response.start",
            "status": HTTPStatus.OK,
            "headers": [
                (b"content-type", b"text/event-stream"),
                (b"cache-control", b"no-cache"),
            ],
        }
    )
    iterator = gateway.subscribe_observe_market_data_events(subscription)
    # Request-scoped racing task, released in the finally block below;
    # feature-owned background work uses context.spawn() instead.
    disconnect = asyncio.ensure_future(_wait_disconnect(receive))
    ctx = _SseContext(send=send, request_id=request_id, trace_id=trace_id, route=route)
    try:
        request = _snapshot_request(symbols)
        initial = _snapshot_of(await gateway.observe_market_data(request))
        if initial is not None:
            await _emit_frame(
                ctx,
                "payload",
                _snapshot_payload(initial),
                None,
                initial.sequence,
                str(initial.sequence),
            )
        await _pump_events(ctx, gateway, iterator, disconnect, request)
    finally:
        disconnect.cancel()
        await asyncio.gather(disconnect, return_exceptions=True)
        close = getattr(iterator, "aclose", None)
        if close is not None:
            await close()
        # The client may already be gone after a disconnect; the
        # subscription release above is the required cleanup.
        with contextlib.suppress(Exception):
            await send({"type": "http.response.body", "body": b"", "more_body": False})


async def _serve_catalogue(
    registry: ServiceRegistry,
    scope: Scope,
    _receive: Receive,
    send: Send,
) -> None:
    """Serve one market catalogue browse request.

    Args:
        registry: Live composition service registry.
        scope: ASGI connection scope.
        _receive: Unused for GET catalogue requests.
        send: ASGI send callable.
    """
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")
    route = str(scope.get("path", _CATALOGUE_ROUTES[0]))
    query = parse_qs(scope.get("query_string", b"").decode("latin-1"))
    raw_limit = query.get("limit", [""])[0]
    try:
        page_size = int(raw_limit) if raw_limit else 100
    except ValueError:
        page_size = -1
    if not 1 <= page_size <= _MAX_CATALOGUE_PAGE_SIZE:
        await _send_json(
            send,
            HTTPStatus.BAD_REQUEST,
            _error_response(
                request_id,
                route,
                _CATALOGUE_OPERATION,
                HTTPStatus.BAD_REQUEST,
                "VALIDATION_ERROR",
                "limit must be an integer between 1 and 500.",
                trace_id,
            ),
        )
        return
    page_cursor = query.get("cursor", [None])[0]
    gateway = await _resolve_gateway(
        registry,
        OBSERVE_MARKET_CATALOGUE_CAPABILITY,
        "The market catalogue capability has no active provider.",
        route,
        _CATALOGUE_OPERATION,
        request_id,
        trace_id,
        send,
    )
    if gateway is None:
        return
    request = ObserveMarketCatalogueRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation="LIST",
        page_size=page_size,
        page_cursor=page_cursor,
    )
    result = await gateway.observe_market_catalogue(request)
    if not isinstance(result, ObserveMarketCatalogueSuccess):
        failure = result
        await _send_json(
            send,
            HTTPStatus.SERVICE_UNAVAILABLE,
            _error_response(
                request_id,
                route,
                _CATALOGUE_OPERATION,
                HTTPStatus.SERVICE_UNAVAILABLE,
                failure.code,
                failure.problem.detail,
                trace_id,
            ),
        )
        return
    data: dict[str, Any] = {
        "source_id": _PROVIDER_CATALOGUE_SOURCE_ID,
        "rows": [entry.model_dump(mode="json") for entry in result.entries],
        "limit": page_size,
        "next_cursor": result.next_cursor,
        "revision": result.revision,
        "generated_at": result.generated_at,
        "request_id": result.request_id,
    }
    envelope = ApiResponse(
        status="success",
        message=HTTPStatus.OK.phrase,
        data=data,
        metadata=_metadata(
            request_id,
            route,
            _CATALOGUE_OPERATION,
            "read",
            False,
            None,
            trace_id,
        ),
    )
    await _send_json(send, HTTPStatus.OK, envelope)


async def _lifespan(receive: Receive, send: Send) -> None:
    """Answer the ASGI lifespan protocol without owning feature state.

    Args:
        receive: ASGI receive callable.
        send: ASGI send callable.
    """
    while True:
        message = await receive()
        if message.get("type") == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message.get("type") == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return


async def _dispatch(
    registry: ServiceRegistry,
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """Route one HTTP request to its owning boundary handler.

    Args:
        registry: Live composition service registry.
        scope: ASGI connection scope.
        receive: ASGI receive callable.
        send: ASGI send callable.
    """
    path = str(scope.get("path", ""))
    method = str(scope.get("method", "GET")).upper()
    if method != "GET":
        await _send_error(
            send,
            HTTPStatus.METHOD_NOT_ALLOWED,
            "NOT_IMPLEMENTED",
            "Only GET is served by the boundary in this foundation.",
            path,
            "api.boundary",
            None,
        )
    elif path == _SNAPSHOT_ROUTE:
        await _serve_snapshot(registry, scope, receive, send)
    elif path in _CATALOGUE_ROUTES:
        await _serve_catalogue(registry, scope, receive, send)
    elif path in _STREAM_ROUTES:
        await _serve_stream(registry, scope, receive, send)
    else:
        await _send_error(
            send,
            HTTPStatus.NOT_FOUND,
            "NOT_FOUND",
            "The requested boundary route is not registered.",
            path,
            "api.boundary",
            None,
        )


def create_api_asgi_app(registry: ServiceRegistry) -> AsgiApp:
    """Build the raw-ASGI boundary application over a live registry.

    The application is inert until a server runs it; capabilities are
    resolved per request so feature removal, replacement, and absence
    behave exactly like the in-process semantics.

    Args:
        registry: Live composition service registry.

    Returns:
        ASGI application callable.
    """

    async def _app(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            await _lifespan(receive, send)
        elif scope["type"] == "http":
            await _dispatch(registry, scope, receive, send)

    return _app
