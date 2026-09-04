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
import json
import re
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal
from urllib.parse import parse_qs
from uuid import uuid4, uuid7

from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_CATALOGUE_CAPABILITY,
    OBSERVE_MARKET_DATA_CAPABILITY,
    OPERATE_TRADING_CAPABILITY,
    OPERATE_WATCHLISTS_CAPABILITY,
)
from app.contracts.interfaces.errors import InterfaceFailure
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
    OperateTradingRequest,
    OperateWatchlistsRequest,
    OperateWatchlistsSuccess,
    StreamEvent,
)
from app.services.interfaces.serve_api_events import (
    _data_reference_db,
    _db_hydration,
    _markets_db,
    _trading_db,
)
from app.services.interfaces.serve_api_events._auth_db import (
    get_session_identity,
    login_user,
    logout_session,
    register_user,
)
from app.services.interfaces.serve_api_events._data_reference_db import (
    BarsUnavailableError,
    ReferenceNotFoundError,
)
from app.services.interfaces.serve_api_events._settings_db import (
    get_credentials_status,
    get_settings_manifest,
    get_system_settings,
    update_credential_slot,
    update_system_settings,
)

if TYPE_CHECKING:
    from collections.abc import MutableMapping
    from typing import Any

    from app.contracts.common.models import JsonObject, JsonValue
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
_WATCHLIST_ID_PATTERN = re.compile(
    r"^(?:[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}|id-[0-9a-fA-F_\-]+|[a-zA-Z0-9_\-\.]{1,128})$"
)

_SNAPSHOT_ROUTE = "/api/v1/market/ticks"
_STREAM_ROUTE = "/api/v1/market/ticks/stream"
_ALIAS_STREAM_ROUTE = "/api/v1/data/snapshot-stream"
_STREAM_ROUTES = frozenset({_STREAM_ROUTE, _ALIAS_STREAM_ROUTE})
_CATALOGUE_ROUTES = ("/api/v1/market/catalogue", "/api/v1/data/markets")
_CATALOGUE_OPERATION = "api.market.catalogue"
_WATCHLISTS_ROUTE = "/api/v1/watchlists"
_WATCHLIST_OPERATION = "api.watchlists"
_SETTINGS_ROUTE = "/api/v1/settings"
_SETTINGS_MANIFEST_ROUTE = "/api/v1/settings/manifest"
_SETTINGS_CREDENTIALS_ROUTE = "/api/v1/settings/credentials"
_SETTINGS_CREDENTIAL_PREFIX = "/api/v1/settings/credentials/"
_TRADING_PREFIX = "/api/v1/trading"
_AUTH_PREFIX = "/api/v1/auth"
_DATA_PREFIX = "/api/v1/data"
_DATA_CAPABILITIES_ROUTE = "/api/v1/data/capabilities"
_DATA_SERIES_ROUTE = "/api/v1/data/series"
_DATA_INSTRUMENTS_ROUTE = "/api/v1/data/instruments"
_DATA_BROKERS_ROUTE = "/api/v1/data/brokers"
_DATA_SYMBOLS_ROUTE = "/api/v1/data/symbols"
_DATA_BARS_ROUTE = "/api/v1/data/bars"
_DATA_QUOTES_ROUTE = "/api/v1/data/quotes"
_DATA_REFERENCE_SYNC_ROUTE = "/api/v1/data/reference/sync"
_DATA_SERIES_ID_PATTERN = re.compile(r"^/api/v1/data/series/(\d+)$")
_DATA_INSTRUMENT_ID_PATTERN = re.compile(r"^/api/v1/data/instruments/([^/]+)$")
_BAR_TIMEFRAMES = frozenset({"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"})
_DEFAULT_BAR_COUNT = 500
_MAX_BAR_COUNT = 1_000_000
_AUTH_REGISTER_ROUTE = "/api/v1/auth/register"
_AUTH_LOGIN_ROUTE = "/api/v1/auth/login"
_AUTH_LOGOUT_ROUTE = "/api/v1/auth/logout"
_AUTH_ME_ROUTE = "/api/v1/auth/me"
_MAX_BODY_BYTES = 65_536
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


_COOKIE_PAIR_LEN: Final = 2
_SESSION_COOKIE_NAME: Final = "hq_session"
_CSRF_COOKIE_NAME: Final = "hq_csrf"
_AUTH_TTL_SECONDS: Final = 7 * 86400


def _get_cookie(scope: Scope, name: str) -> str | None:
    """Read a cookie value from the request scope headers.

    Args:
        scope: ASGI connection scope.
        name: Name of the cookie.

    Returns:
        Cookie string value if found, None otherwise.
    """
    cookie_header = _header(scope, "cookie")
    if not cookie_header:
        return None
    for item in cookie_header.split(";"):
        parts = item.strip().split("=", maxsplit=1)
        if len(parts) == _COOKIE_PAIR_LEN and parts[0].strip() == name:
            return parts[1].strip()
    return None


def _get_request_identity(scope: Scope) -> tuple[str, str]:
    """Return (account_id, username) from active session or fallback default.

    Args:
        scope: ASGI connection scope.

    Returns:
        Tuple of principal identifier and username.
    """
    token = _get_cookie(scope, _SESSION_COOKIE_NAME)
    if token:
        ident = get_session_identity(token)
        if ident:
            return (
                str(ident.get("user_id") or "usr_haruquantai"),
                str(ident.get("username") or "haruquantai"),
            )
    return ("usr_haruquantai", "haruquantai")


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


async def _send_json(
    send: Send,
    status: HTTPStatus,
    envelope: ApiResponse,
    extra_headers: Sequence[tuple[bytes, bytes]] | None = None,
) -> None:
    """Emit one complete JSON response.

    Args:
        send: ASGI send callable.
        status: HTTP status code.
        envelope: Response envelope to serialize.
        extra_headers: Optional additional response headers (e.g. cookies).
    """
    body = envelope.model_dump_json().encode("utf-8")
    headers: list[tuple[bytes, bytes]] = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("ascii")),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": headers,
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
    rows: list[dict[str, Any]] = [
        entry.model_dump(mode="json") for entry in result.entries
    ]
    if not rows:
        market_query = query.get("query", [None])[0]
        db_data = _markets_db.list_market_directory(
            query=market_query,
            cursor=page_cursor,
            limit=page_size,
            request_id=request_id,
        )
        rows = db_data["rows"]
    data: dict[str, Any] = {
        "source_id": _PROVIDER_CATALOGUE_SOURCE_ID,
        "rows": rows,
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


async def _read_json_body(receive: Receive) -> dict[str, Any] | None:
    """Read one bounded JSON request body.

    Args:
        receive: ASGI receive callable.

    Returns:
        The parsed body mapping, {} for an empty body, or None when
        malformed.
    """
    body = bytearray()
    while True:
        message = await receive()
        if message.get("type") == "http.disconnect":
            return None
        chunk = message.get("body", b"")
        if chunk:
            body.extend(chunk)
        if not message.get("more_body", False):
            break
    if not body:
        return {}
    if len(body) > _MAX_BODY_BYTES:
        return None
    try:
        parsed = json.loads(body.decode("utf-8"))
    except UnicodeDecodeError, ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _watchlist_request(operation: str, **fields: object) -> OperateWatchlistsRequest:
    """Build one watchlist gateway request.

    Args:
        operation: Gateway operation discriminator.
        fields: Optional operation fields.

    Returns:
        Operation-discriminated gateway request.

    Raises:
        ValueError: If the composed request violates its contract.
    """
    return OperateWatchlistsRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,  # type: ignore[arg-type]
        **fields,  # type: ignore[arg-type]
    )


async def _serve_watchlist_result(
    result: object,
    send: Send,
    request_id: str,
    route: str,
    trace_id: str | None,
    deleted_id: str | None = None,
) -> None:
    """Serve one watchlist gateway result or failure envelope.

    Args:
        result: Gateway operation result.
        send: ASGI send callable.
        request_id: Mirrored or generated request identifier.
        route: Served route path.
        trace_id: Optional mirrored trace identifier.
        deleted_id: Watchlist id from the route for deletion results.
    """
    if not isinstance(result, OperateWatchlistsSuccess):
        failure = result
        status = HTTPStatus(failure.problem.status)  # type: ignore[attr-defined]
        await _send_json(
            send,
            status,
            _error_response(
                request_id,
                route,
                _WATCHLIST_OPERATION,
                status,
                failure.code,  # type: ignore[attr-defined]
                failure.problem.detail,  # type: ignore[attr-defined]
                trace_id,
            ),
        )
        return
    data: dict[str, JsonValue] | list[dict[str, JsonValue]]
    if result.deleted:
        resolved_id = (
            deleted_id
            if deleted_id is not None
            else (result.watchlist.watchlist_id if result.watchlist is not None else "")
        )
        data = {"watchlist_id": resolved_id, "deleted": True}
    elif result.watchlist is not None:
        data = result.watchlist.model_dump(mode="json")
    else:
        data = [entry.model_dump(mode="json") for entry in result.watchlists]
    await _send_json(
        send,
        HTTPStatus.OK,
        ApiResponse(
            status="success",
            message=HTTPStatus.OK.phrase,
            data=data,
            metadata=_metadata(
                request_id, route, _WATCHLIST_OPERATION, "read", False, None, trace_id
            ),
        ),
    )


async def _serve_watchlists_collection(
    registry: ServiceRegistry,
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """Serve the watchlists collection: GET list and POST create.

    Args:
        registry: Live composition service registry.
        scope: ASGI connection scope.
        receive: ASGI receive callable.
        send: ASGI send callable.
    """
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")
    method = str(scope.get("method", "GET")).upper()
    gateway = await _resolve_gateway(
        registry,
        OPERATE_WATCHLISTS_CAPABILITY,
        "The watchlist capability has no active provider.",
        _WATCHLISTS_ROUTE,
        _WATCHLIST_OPERATION,
        request_id,
        trace_id,
        send,
    )
    if gateway is None:
        return

    if method == "GET":
        request = _watchlist_request("LIST")
    else:
        body = await _read_json_body(receive)
        name = body.get("name") if body is not None else None
        if not isinstance(name, str) or not name.strip():
            await _send_error(
                send,
                HTTPStatus.BAD_REQUEST,
                "VALIDATION_ERROR",
                "The request body must carry a non-empty name.",
                _WATCHLISTS_ROUTE,
                _WATCHLIST_OPERATION,
                trace_id,
            )
            return
        try:
            request = _watchlist_request("CREATE", name=name.strip())
        except ValueError:
            await _send_error(
                send,
                HTTPStatus.BAD_REQUEST,
                "VALIDATION_ERROR",
                "The create request violates the watchlist contract.",
                _WATCHLISTS_ROUTE,
                _WATCHLIST_OPERATION,
                trace_id,
            )
            return
    result = await gateway.operate_watchlists(request)
    await _serve_watchlist_result(result, send, request_id, _WATCHLISTS_ROUTE, trace_id)


async def _serve_watchlists_item(
    registry: ServiceRegistry,
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """Serve one watchlist item: PATCH update and DELETE.

    Args:
        registry: Live composition service registry.
        scope: ASGI connection scope.
        receive: ASGI receive callable.
        send: ASGI send callable.
    """
    path = str(scope.get("path", ""))
    watchlist_id = path[len(_WATCHLISTS_ROUTE) + 1 :]
    route = f"{_WATCHLISTS_ROUTE}/{watchlist_id}"
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")
    method = str(scope.get("method", "")).upper()
    if not _WATCHLIST_ID_PATTERN.match(watchlist_id):
        await _send_error(
            send,
            HTTPStatus.BAD_REQUEST,
            "VALIDATION_ERROR",
            "The watchlist id is not a valid identifier.",
            route,
            _WATCHLIST_OPERATION,
            trace_id,
        )
        return
    gateway = await _resolve_gateway(
        registry,
        OPERATE_WATCHLISTS_CAPABILITY,
        "The watchlist capability has no active provider.",
        route,
        _WATCHLIST_OPERATION,
        request_id,
        trace_id,
        send,
    )
    if gateway is None:
        return

    if method == "DELETE":
        request = _watchlist_request("DELETE", watchlist_id=watchlist_id)
    else:
        body = await _read_json_body(receive)
        if body is None:
            await _send_error(
                send,
                HTTPStatus.BAD_REQUEST,
                "VALIDATION_ERROR",
                "The request body must be a JSON object.",
                route,
                _WATCHLIST_OPERATION,
                trace_id,
            )
            return
        fields: dict[str, object] = {"watchlist_id": watchlist_id}
        if "name" in body:
            fields["name"] = body["name"]
        if isinstance(body.get("symbols"), list):
            fields["symbols"] = tuple(
                symbol for symbol in body["symbols"] if isinstance(symbol, str)
            )
        if "is_default" in body:
            fields["is_default"] = body["is_default"]
        if "sort_order" in body:
            fields["sort_order"] = body["sort_order"]
        try:
            request = _watchlist_request("UPDATE", **fields)
        except ValueError:
            await _send_error(
                send,
                HTTPStatus.BAD_REQUEST,
                "VALIDATION_ERROR",
                "The update request violates the watchlist contract.",
                route,
                _WATCHLIST_OPERATION,
                trace_id,
            )
            return
    result = await gateway.operate_watchlists(request)
    await _serve_watchlist_result(
        result, send, request_id, route, trace_id, deleted_id=watchlist_id
    )


def _query_params(scope: Scope) -> dict[str, str]:
    """Flatten one query string into a last-value-wins mapping.

    Args:
        scope: ASGI connection scope.

    Returns:
        Mapping of parameter name to its final value.
    """
    parsed = parse_qs(scope.get("query_string", b"").decode("latin-1"))
    return {name: values[-1] for name, values in parsed.items() if values}


async def _serve_data_json(
    send: Send,
    path: str,
    operation: str,
    payload: JsonObject | list[JsonObject],
    request_id: str,
    trace_id: str | None,
    side_effect: Literal["read", "write"] = "read",
) -> None:
    """Serve one success envelope for a Data reference read or write."""
    await _send_json(
        send,
        HTTPStatus.OK,
        ApiResponse(
            status="success",
            message=HTTPStatus.OK.phrase,
            data=payload,
            metadata=_metadata(
                request_id,
                path,
                operation,
                side_effect,
                False,
                None,
                trace_id,
            ),
        ),
    )


async def _serve_bars(
    scope: Scope,
    send: Send,
    request_id: str,
    trace_id: str | None,
) -> None:
    """Serve one bounded bar history from the persisted reference store.

    A symbol/timeframe pair with no stored history answers with an honest
    503 ``UPSTREAM_UNAVAILABLE``; the boundary never substitutes generated
    bars for a provider history a chart would render as real.
    """
    params = _query_params(scope)
    symbol = params.get("symbol", "").strip()
    if not symbol:
        await _send_error(
            send,
            HTTPStatus.UNPROCESSABLE_CONTENT,
            "VALIDATION_FAILED",
            "The symbol query parameter is required.",
            _DATA_BARS_ROUTE,
            "api.data.bars",
            trace_id,
        )
        return
    timeframe = params.get("timeframe", "H1").strip() or "H1"
    if timeframe not in _BAR_TIMEFRAMES:
        await _send_error(
            send,
            HTTPStatus.UNPROCESSABLE_CONTENT,
            "VALIDATION_FAILED",
            "The requested timeframe is not a canonical Data timeframe.",
            _DATA_BARS_ROUTE,
            "api.data.bars",
            trace_id,
        )
        return
    start = params.get("start") or None
    end = params.get("end") or None
    if start is not None and end is not None and end <= start:
        await _send_error(
            send,
            HTTPStatus.UNPROCESSABLE_CONTENT,
            "BAR_WINDOW_INVALID",
            "The requested bar window end must not precede its start.",
            _DATA_BARS_ROUTE,
            "api.data.bars",
            trace_id,
        )
        return
    try:
        limit = int(params.get("limit", _DEFAULT_BAR_COUNT))
    except ValueError:
        limit = _DEFAULT_BAR_COUNT
    limit = max(1, min(limit, _MAX_BAR_COUNT))
    try:
        payload = _data_reference_db.get_bars(
            symbol,
            timeframe,
            limit=limit,
            start=start,
            end=end,
            request_id=request_id,
        )
    except BarsUnavailableError as error:
        await _send_error(
            send,
            HTTPStatus.SERVICE_UNAVAILABLE,
            "UPSTREAM_UNAVAILABLE",
            str(error),
            _DATA_BARS_ROUTE,
            "api.data.bars",
            trace_id,
        )
        return
    await _serve_data_json(
        send, _DATA_BARS_ROUTE, "api.data.bars", payload, request_id, trace_id
    )


async def _serve_data_series_item(
    receive: Receive,
    send: Send,
    series_id: int,
    request_id: str,
    trace_id: str | None,
) -> None:
    """Serve one governed series edit against the reference catalogue."""
    body = await _read_json_body(receive)
    if body is None:
        await _send_error(
            send,
            HTTPStatus.BAD_REQUEST,
            "VALIDATION_FAILED",
            "The request body must be a JSON object.",
            _DATA_SERIES_ROUTE,
            "api.data.series.update",
            trace_id,
        )
        return
    try:
        payload = _data_reference_db.update_market_series(series_id, body)
    except ValueError:
        await _send_error(
            send,
            HTTPStatus.UNPROCESSABLE_CONTENT,
            "VALIDATION_FAILED",
            "Series symbol and instrument are required.",
            _DATA_SERIES_ROUTE,
            "api.data.series.update",
            trace_id,
        )
        return
    except ReferenceNotFoundError:
        await _send_error(
            send,
            HTTPStatus.NOT_FOUND,
            "SERIES_NOT_FOUND",
            f"No series {series_id} exists in the reference catalogue.",
            _DATA_SERIES_ROUTE,
            "api.data.series.update",
            trace_id,
        )
        return
    route = f"{_DATA_SERIES_ROUTE}/{series_id}"
    await _serve_data_json(
        send,
        route,
        "api.data.series.update",
        payload,
        request_id,
        trace_id,
        side_effect="write",
    )


async def _serve_data_instrument_item(
    receive: Receive,
    send: Send,
    instrument: str,
    method: str,
    request_id: str,
    trace_id: str | None,
) -> None:
    """Serve one instrument specification read or governed edit."""
    route = f"{_DATA_INSTRUMENTS_ROUTE}/{instrument}"
    if method == "GET":
        try:
            payload = _data_reference_db.get_instrument_spec(instrument)
        except ReferenceNotFoundError:
            await _send_error(
                send,
                HTTPStatus.NOT_FOUND,
                "INSTRUMENT_NOT_FOUND",
                f"No instrument {instrument} exists in the reference catalogue.",
                route,
                "api.data.instrument",
                trace_id,
            )
            return
        await _serve_data_json(
            send, route, "api.data.instrument", payload, request_id, trace_id
        )
        return
    body = await _read_json_body(receive)
    if body is None:
        await _send_error(
            send,
            HTTPStatus.BAD_REQUEST,
            "VALIDATION_FAILED",
            "The request body must be a JSON object.",
            route,
            "api.data.instrument.update",
            trace_id,
        )
        return
    try:
        payload = _data_reference_db.update_instrument_spec(instrument, body)
    except ReferenceNotFoundError:
        await _send_error(
            send,
            HTTPStatus.NOT_FOUND,
            "INSTRUMENT_NOT_FOUND",
            f"No instrument {instrument} exists in the reference catalogue.",
            route,
            "api.data.instrument.update",
            trace_id,
        )
        return
    await _serve_data_json(
        send,
        route,
        "api.data.instrument.update",
        payload,
        request_id,
        trace_id,
        side_effect="write",
    )


async def _serve_data_capability_routes(
    registry: ServiceRegistry,
    scope: Scope,
    receive: Receive,
    send: Send,
    path: str,
    method: str,
) -> bool:
    """Delegate capability-gated catalogue and stream aliases.

    Args:
        registry: Live composition service registry.
        scope: ASGI connection scope.
        receive: ASGI receive callable.
        send: ASGI send callable.
        path: Request path.
        method: Uppercase request method.

    Returns:
        True when the route was handled.
    """
    if path in _CATALOGUE_ROUTES and method == "GET":
        await _serve_catalogue(registry, scope, receive, send)
        return True
    if path == _ALIAS_STREAM_ROUTE and method == "GET":
        await _serve_stream(registry, scope, receive, send)
        return True
    return False


async def _serve_data_catalogue_read(
    path: str,
    params: dict[str, str],
    send: Send,
    request_id: str,
    trace_id: str | None,
) -> bool:
    """Serve the static capability surface and reference catalogue reads.

    Args:
        path: Request path.
        params: Flattened query parameters.
        send: ASGI send callable.
        request_id: Mirrored or generated request identifier.
        trace_id: Optional mirrored trace identifier.

    Returns:
        True when the route was handled.
    """
    payload: JsonObject | list[JsonObject]
    if path == _DATA_CAPABILITIES_ROUTE:
        payload = _data_reference_db.list_capabilities()
        operation = "api.data.capabilities"
    elif path == _DATA_SERIES_ROUTE:
        payload = _data_reference_db.list_market_series(
            limit=int(params.get("limit", "50"))
        )
        operation = "api.data.series"
    elif path == _DATA_INSTRUMENTS_ROUTE:
        payload = _data_reference_db.list_instruments(
            limit=int(params.get("limit", "50"))
        )
        operation = "api.data.instruments"
    elif path == _DATA_BROKERS_ROUTE:
        payload = _data_reference_db.list_brokers(limit=int(params.get("limit", "50")))
        operation = "api.data.brokers"
    else:
        return False
    await _serve_data_json(send, path, operation, payload, request_id, trace_id)
    return True


async def _serve_data_discovery_read(
    path: str,
    params: dict[str, str],
    send: Send,
    request_id: str,
    trace_id: str | None,
) -> bool:
    """Serve symbol discovery and explicit-symbol quote reads.

    Args:
        path: Request path.
        params: Flattened query parameters.
        send: ASGI send callable.
        request_id: Mirrored or generated request identifier.
        trace_id: Optional mirrored trace identifier.

    Returns:
        True when the route was handled.
    """
    if path == _DATA_SYMBOLS_ROUTE:
        payload = _data_reference_db.list_symbols(
            source_id=params.get("source_id", "mt5"),
            query=params.get("query"),
            cursor=params.get("cursor"),
            limit=int(params.get("limit", "50")),
            request_id=request_id,
        )
        await _serve_data_json(
            send, path, "api.data.symbols", payload, request_id, trace_id
        )
        return True
    if path == _DATA_QUOTES_ROUTE:
        symbols = [
            symbol.strip()
            for symbol in params.get("symbols", "").split(",")
            if symbol.strip()
        ]
        payload = _data_reference_db.list_quotes(
            symbols,
            source_id=params.get("source_id", "mt5"),
            request_id=request_id,
        )
        await _serve_data_json(
            send, path, "api.data.quotes", payload, request_id, trace_id
        )
        return True
    return False


async def _serve_data_write_routes(
    receive: Receive,
    send: Send,
    path: str,
    method: str,
    request_id: str,
    trace_id: str | None,
) -> bool:
    """Serve the governed reference writes and item reads/edits.

    Args:
        receive: ASGI receive callable.
        send: ASGI send callable.
        path: Request path.
        method: Uppercase request method.
        request_id: Mirrored or generated request identifier.
        trace_id: Optional mirrored trace identifier.

    Returns:
        True when the route was handled.
    """
    if path == _DATA_REFERENCE_SYNC_ROUTE and method == "POST":
        payload = _data_reference_db.sync_reference()
        await _serve_data_json(
            send,
            path,
            "api.data.reference.sync",
            payload,
            request_id,
            trace_id,
            side_effect="write",
        )
        return True
    series_match = _DATA_SERIES_ID_PATTERN.match(path)
    if series_match is not None and method == "PATCH":
        await _serve_data_series_item(
            receive, send, int(series_match.group(1)), request_id, trace_id
        )
        return True
    instrument_match = _DATA_INSTRUMENT_ID_PATTERN.match(path)
    if instrument_match is not None and method in ("GET", "PATCH"):
        await _serve_data_instrument_item(
            receive,
            send,
            instrument_match.group(1),
            method,
            request_id,
            trace_id,
        )
        return True
    return False


async def _serve_data(
    registry: ServiceRegistry,
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """Serve the Data reference boundary: discovery, catalogue, and bars.

    ``/api/v1/data/markets`` and the ``snapshot-stream`` alias keep their
    capability-gated catalogue/stream handlers; every other ``/data`` route
    reads the hydrated reference store.
    """
    path = str(scope.get("path", ""))
    method = str(scope.get("method", "GET")).upper()
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")
    params = _query_params(scope)

    if await _serve_data_capability_routes(
        registry, scope, receive, send, path, method
    ):
        return
    if path == _DATA_BARS_ROUTE and method == "GET":
        await _serve_bars(scope, send, request_id, trace_id)
        return
    if await _serve_data_catalogue_read(path, params, send, request_id, trace_id):
        return
    if await _serve_data_discovery_read(path, params, send, request_id, trace_id):
        return
    if await _serve_data_write_routes(
        receive, send, path, method, request_id, trace_id
    ):
        return
    await _send_error(
        send,
        HTTPStatus.NOT_FOUND,
        "NOT_FOUND",
        "The requested boundary route is not registered.",
        path,
        "api.data",
        trace_id,
    )


async def _serve_settings(
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """Serve system and user settings backed by data/database/haruquantai.db."""
    path = str(scope.get("path", ""))
    method = str(scope.get("method", "GET")).upper()
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")

    if path == _SETTINGS_ROUTE:
        if method == "GET":
            data = get_system_settings()
            await _send_json(
                send,
                HTTPStatus.OK,
                ApiResponse(
                    status="success",
                    message=HTTPStatus.OK.phrase,
                    data=data,
                    metadata=_metadata(
                        request_id,
                        path,
                        "api.settings.read",
                        "read",
                        False,
                        None,
                        trace_id,
                    ),
                ),
            )
            return
        if method == "PUT":
            body = await _read_json_body(receive)
            settings_delta = body.get("settings", {}) if isinstance(body, dict) else {}
            data = update_system_settings(settings_delta)
            await _send_json(
                send,
                HTTPStatus.OK,
                ApiResponse(
                    status="success",
                    message=HTTPStatus.OK.phrase,
                    data=data,
                    metadata=_metadata(
                        request_id,
                        path,
                        "api.settings.update",
                        "write",
                        False,
                        None,
                        trace_id,
                    ),
                ),
            )
            return
    elif path == _SETTINGS_MANIFEST_ROUTE and method == "GET":
        manifest_data = get_settings_manifest()
        await _send_json(
            send,
            HTTPStatus.OK,
            ApiResponse(
                status="success",
                message=HTTPStatus.OK.phrase,
                data=manifest_data,
                metadata=_metadata(
                    request_id,
                    path,
                    "api.settings.manifest",
                    "read",
                    False,
                    None,
                    trace_id,
                ),
            ),
        )
        return
    elif path == _SETTINGS_CREDENTIALS_ROUTE and method == "GET":
        credentials_data = get_credentials_status()
        await _send_json(
            send,
            HTTPStatus.OK,
            ApiResponse(
                status="success",
                message=HTTPStatus.OK.phrase,
                data=credentials_data,
                metadata=_metadata(
                    request_id,
                    path,
                    "api.settings.credentials.read",
                    "read",
                    False,
                    None,
                    trace_id,
                ),
            ),
        )
        return
    elif path.startswith(_SETTINGS_CREDENTIAL_PREFIX) and method == "PUT":
        slot = path[len(_SETTINGS_CREDENTIAL_PREFIX) :].strip()
        body = await _read_json_body(receive)
        material = body.get("material", {}) if isinstance(body, dict) else {}
        updated_slot = update_credential_slot(slot, material)
        await _send_json(
            send,
            HTTPStatus.OK,
            ApiResponse(
                status="success",
                message=HTTPStatus.OK.phrase,
                data=updated_slot,
                metadata=_metadata(
                    request_id,
                    path,
                    "api.settings.credentials.update",
                    "write",
                    False,
                    None,
                    trace_id,
                ),
            ),
        )
        return

    await _send_error(
        send,
        HTTPStatus.METHOD_NOT_ALLOWED,
        "METHOD_NOT_ALLOWED",
        f"Method {method} is not supported on {path}.",
        path,
        "api.settings",
        trace_id,
    )


_TRADING_SUBPATH_ACTION_PARTS: Final = 2


async def _serve_trading_sessions(
    path: str,
    method: str,
    principal_id: str,
    query_string: bytes,
    request_id: str,
    trace_id: str | None,
    send: Send,
) -> None:
    """Serve trading execution sessions listing and creation."""
    if method == "GET":
        query = parse_qs(query_string.decode("latin-1"))
        mode_filter = query.get("mode", [None])[0]
        sessions = _trading_db.list_execution_sessions(
            principal_id=principal_id, mode=mode_filter
        )
        envelope = ApiResponse(
            status="success",
            message=HTTPStatus.OK.phrase,
            data=sessions,
            metadata=_metadata(
                request_id,
                path,
                "api.trading.execution_sessions",
                "read",
                False,
                None,
                trace_id,
            ),
        )
        await _send_json(send, HTTPStatus.OK, envelope)
        return
    session = _trading_db.get_active_or_default_session(principal_id=principal_id)
    envelope = ApiResponse(
        status="success",
        message=HTTPStatus.CREATED.phrase,
        data=session or {},
        metadata=_metadata(
            request_id,
            path,
            "api.trading.execution_sessions.create",
            "write",
            False,
            None,
            trace_id,
        ),
    )
    await _send_json(send, HTTPStatus.CREATED, envelope)


async def _serve_trading_session_actions(
    path: str,
    method: str,
    principal_id: str,
    request_id: str,
    trace_id: str | None,
    send: Send,
) -> bool:
    """Serve session action triggers: default, start, stop.

    Returns:
        True if the request matched and was handled, False otherwise.
    """
    subpath = path[len("/api/v1/trading/execution-sessions/") :].strip("/")
    parts = subpath.split("/")
    if len(parts) != _TRADING_SUBPATH_ACTION_PARTS or method != "POST":
        return False

    session_id, action = parts[0], parts[1]
    res: dict[str, Any]
    try:
        if action == "default":
            res = _trading_db.set_default_session(session_id, principal_id=principal_id)
        elif action == "start":
            res = _trading_db.start_session(session_id)
        elif action == "stop":
            res = _trading_db.stop_session(session_id)
        else:
            return False
    except LookupError:
        await _send_error(
            send,
            HTTPStatus.NOT_FOUND,
            "SESSION_NOT_FOUND",
            "Session not found",
            path,
            f"api.trading.execution_sessions.{action}",
            trace_id,
        )
        return True

    envelope = ApiResponse(
        status="success",
        message=HTTPStatus.OK.phrase,
        data=res,
        metadata=_metadata(
            request_id,
            path,
            f"api.trading.execution_sessions.{action}",
            "write",
            False,
            None,
            trace_id,
        ),
    )
    await _send_json(send, HTTPStatus.OK, envelope)
    return True


async def _serve_trading_account_profile(
    path: str,
    principal_id: str,
    username: str,
    request_id: str,
    trace_id: str | None,
    send: Send,
) -> None:
    """Serve trading account profile."""
    profile = _trading_db.get_account_profile(
        principal_id=principal_id, username=username
    )
    envelope = ApiResponse(
        status="success",
        message=HTTPStatus.OK.phrase,
        data=profile,
        metadata=_metadata(
            request_id,
            path,
            "api.trading.account_profile",
            "read",
            False,
            None,
            trace_id,
        ),
    )
    await _send_json(send, HTTPStatus.OK, envelope)


async def _serve_trading_constraints(
    path: str,
    request_id: str,
    trace_id: str | None,
    send: Send,
) -> None:
    """Serve instrument trading constraints."""
    prefix = "/api/v1/trading/instruments/"
    suffix = "/constraints"
    symbol = path[len(prefix) : -len(suffix)].strip()
    constraints = _trading_db.get_instrument_constraints(symbol)
    envelope = ApiResponse(
        status="success",
        message=HTTPStatus.OK.phrase,
        data=constraints,
        metadata=_metadata(
            request_id,
            path,
            "api.trading.instrument_constraints",
            "read",
            False,
            None,
            trace_id,
        ),
    )
    await _send_json(send, HTTPStatus.OK, envelope)


async def _serve_trading(
    registry: ServiceRegistry,
    scope: Scope,
    _receive: Receive,
    send: Send,
) -> None:
    """Serve trading operations, execution sessions, and account profile."""
    path = str(scope.get("path", ""))
    method = str(scope.get("method", "GET")).upper()
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")
    principal_id, username = _get_request_identity(scope)

    gateway = await _resolve_gateway(
        registry,
        OPERATE_TRADING_CAPABILITY,
        "The trading operations capability has no active provider.",
        path,
        "api.trading",
        request_id,
        trace_id,
        send,
    )
    if gateway is None:
        return

    if path == "/api/v1/trading/execution-sessions":
        qs = bytes(scope.get("query_string", b""))
        await _serve_trading_sessions(
            path, method, principal_id, qs, request_id, trace_id, send
        )
        return

    if path.startswith("/api/v1/trading/execution-sessions/"):
        handled = await _serve_trading_session_actions(
            path, method, principal_id, request_id, trace_id, send
        )
        if handled:
            return

    if path == "/api/v1/trading/account-profile":
        await _serve_trading_account_profile(
            path, principal_id, username, request_id, trace_id, send
        )
        return

    if path.startswith("/api/v1/trading/instruments/") and path.endswith(
        "/constraints"
    ):
        await _serve_trading_constraints(path, request_id, trace_id, send)
        return

    operation: Literal[
        "MANAGE_SESSION",
        "READINESS",
        "PREVIEW_ACTION",
        "EMERGENCY",
        "MARKET_DATA",
        "OPERATOR_ANALYTICS",
    ] = "READINESS"
    if "session" in path:
        operation = "MANAGE_SESSION"
    elif "order" in path or "position" in path:
        operation = "PREVIEW_ACTION"

    request = OperateTradingRequest(
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        operation=operation,
    )
    result = await gateway.operate_trading(request)
    if isinstance(result, InterfaceFailure):
        await _send_error(
            send,
            HTTPStatus.SERVICE_UNAVAILABLE
            if result.code == "CAPABILITY_UNAVAILABLE"
            else HTTPStatus.BAD_REQUEST,
            result.code,
            result.problem.detail,
            path,
            "api.trading",
            trace_id,
        )
        return

    await _send_json(
        send,
        HTTPStatus.OK,
        ApiResponse(
            status="success",
            message=HTTPStatus.OK.phrase,
            data=result.model_dump(mode="json"),
            metadata=_metadata(
                request_id,
                path,
                "api.trading",
                "read" if method == "GET" else "write",
                False,
                None,
                trace_id,
            ),
        ),
    )


def _build_auth_cookies(
    session_token: str, csrf_token: str
) -> list[tuple[bytes, bytes]]:
    """Build Set-Cookie headers for session and CSRF credentials.

    Args:
        session_token: Opaque session token.
        csrf_token: Opaque CSRF token.

    Returns:
        List of Set-Cookie header tuples.
    """
    return [
        (
            b"set-cookie",
            (
                f"hq_session={session_token}; Path=/; "
                f"HttpOnly; SameSite=Lax; Max-Age={_AUTH_TTL_SECONDS}"
            ).encode("latin-1"),
        ),
        (
            b"set-cookie",
            (
                f"hq_csrf={csrf_token}; Path=/; "
                f"SameSite=Lax; Max-Age={_AUTH_TTL_SECONDS}"
            ).encode("latin-1"),
        ),
    ]


def _build_logout_cookies() -> list[tuple[bytes, bytes]]:
    """Build Set-Cookie headers to clear session and CSRF credentials.

    Returns:
        List of clearing Set-Cookie header tuples.
    """
    return [
        (
            b"set-cookie",
            b"hq_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0",
        ),
        (
            b"set-cookie",
            b"hq_csrf=; Path=/; SameSite=Lax; Max-Age=0",
        ),
    ]


async def _serve_auth_register(
    receive: Receive,
    send: Send,
    path: str,
    method: str,
    request_id: str,
    trace_id: str | None,
) -> None:
    """Serve user registration."""
    if method != "POST":
        await _send_error(
            send,
            HTTPStatus.METHOD_NOT_ALLOWED,
            "METHOD_NOT_ALLOWED",
            "Register route requires POST",
            path,
            "api.auth.register",
            trace_id,
        )
        return
    body = await _read_json_body(receive)
    username = str(body.get("username", "")).strip() if isinstance(body, dict) else ""
    password = str(body.get("password", "")) if isinstance(body, dict) else ""
    if not username or not password:
        await _send_error(
            send,
            HTTPStatus.BAD_REQUEST,
            "VALIDATION_ERROR",
            "Username and password are required",
            path,
            "api.auth.register",
            trace_id,
        )
        return
    try:
        user_data, session_token, csrf_token = register_user(username, password)
    except ValueError as err:
        await _send_error(
            send,
            HTTPStatus.BAD_REQUEST,
            "REGISTRATION_FAILED",
            str(err),
            path,
            "api.auth.register",
            trace_id,
        )
        return
    cookies = _build_auth_cookies(session_token, csrf_token)
    await _send_json(
        send,
        HTTPStatus.CREATED,
        ApiResponse(
            status="success",
            message=HTTPStatus.CREATED.phrase,
            data=user_data,
            metadata=_metadata(
                request_id,
                path,
                "api.auth.register",
                "write",
                False,
                None,
                trace_id,
            ),
        ),
        extra_headers=cookies,
    )


async def _serve_auth_login(
    receive: Receive,
    send: Send,
    path: str,
    method: str,
    request_id: str,
    trace_id: str | None,
) -> None:
    """Serve user login."""
    if method != "POST":
        await _send_error(
            send,
            HTTPStatus.METHOD_NOT_ALLOWED,
            "METHOD_NOT_ALLOWED",
            "Login route requires POST",
            path,
            "api.auth.login",
            trace_id,
        )
        return
    body = await _read_json_body(receive)
    username = str(body.get("username", "")).strip() if isinstance(body, dict) else ""
    password = str(body.get("password", "")) if isinstance(body, dict) else ""
    if not username or not password:
        await _send_error(
            send,
            HTTPStatus.BAD_REQUEST,
            "VALIDATION_ERROR",
            "Username and password are required",
            path,
            "api.auth.login",
            trace_id,
        )
        return
    try:
        user_data, session_token, csrf_token = login_user(username, password)
    except ValueError as err:
        await _send_error(
            send,
            HTTPStatus.UNAUTHORIZED,
            "AUTHENTICATION_REQUIRED",
            str(err),
            path,
            "api.auth.login",
            trace_id,
        )
        return
    cookies = _build_auth_cookies(session_token, csrf_token)
    await _send_json(
        send,
        HTTPStatus.OK,
        ApiResponse(
            status="success",
            message=HTTPStatus.OK.phrase,
            data=user_data,
            metadata=_metadata(
                request_id,
                path,
                "api.auth.login",
                "write",
                False,
                None,
                trace_id,
            ),
        ),
        extra_headers=cookies,
    )


async def _serve_auth_me(
    scope: Scope,
    send: Send,
    path: str,
    method: str,
    request_id: str,
    trace_id: str | None,
) -> None:
    """Serve current identity recovery."""
    if method != "GET":
        await _send_error(
            send,
            HTTPStatus.METHOD_NOT_ALLOWED,
            "METHOD_NOT_ALLOWED",
            "Identity route requires GET",
            path,
            "api.auth.me",
            trace_id,
        )
        return
    session_token = _get_cookie(scope, _SESSION_COOKIE_NAME)
    identity = get_session_identity(session_token)
    if identity is None:
        await _send_error(
            send,
            HTTPStatus.UNAUTHORIZED,
            "AUTHENTICATION_REQUIRED",
            "Authentication required",
            path,
            "api.auth.me",
            trace_id,
        )
        return
    await _send_json(
        send,
        HTTPStatus.OK,
        ApiResponse(
            status="success",
            message=HTTPStatus.OK.phrase,
            data=identity,
            metadata=_metadata(
                request_id,
                path,
                "api.auth.me",
                "read",
                False,
                None,
                trace_id,
            ),
        ),
    )


async def _serve_auth_logout(
    scope: Scope,
    send: Send,
    path: str,
    method: str,
    request_id: str,
    trace_id: str | None,
) -> None:
    """Serve user logout."""
    if method != "POST":
        await _send_error(
            send,
            HTTPStatus.METHOD_NOT_ALLOWED,
            "METHOD_NOT_ALLOWED",
            "Logout route requires POST",
            path,
            "api.auth.logout",
            trace_id,
        )
        return
    session_token = _get_cookie(scope, _SESSION_COOKIE_NAME)
    logout_session(session_token)
    cookies = _build_logout_cookies()
    await _send_json(
        send,
        HTTPStatus.OK,
        ApiResponse(
            status="success",
            message=HTTPStatus.OK.phrase,
            data=None,
            metadata=_metadata(
                request_id,
                path,
                "api.auth.logout",
                "write",
                False,
                None,
                trace_id,
            ),
        ),
        extra_headers=cookies,
    )


async def _serve_auth(
    scope: Scope,
    receive: Receive,
    send: Send,
) -> None:
    """Route authentication requests to their focused handlers."""
    path = str(scope.get("path", ""))
    method = str(scope.get("method", "GET")).upper()
    request_id = _header(scope, "x-request-id") or f"req-{uuid4()}"
    trace_id = _header(scope, "x-trace-id")

    if path == _AUTH_REGISTER_ROUTE:
        await _serve_auth_register(receive, send, path, method, request_id, trace_id)
    elif path == _AUTH_LOGIN_ROUTE:
        await _serve_auth_login(receive, send, path, method, request_id, trace_id)
    elif path == _AUTH_ME_ROUTE:
        await _serve_auth_me(scope, send, path, method, request_id, trace_id)
    elif path == _AUTH_LOGOUT_ROUTE:
        await _serve_auth_logout(scope, send, path, method, request_id, trace_id)
    else:
        await _send_error(
            send,
            HTTPStatus.NOT_FOUND,
            "NOT_FOUND",
            "The requested auth route is not registered.",
            path,
            "api.auth",
            trace_id,
        )


async def _lifespan(receive: Receive, send: Send) -> None:
    """Answer the ASGI lifespan protocol without owning feature state.

    Args:
        receive: ASGI receive callable.
        send: ASGI send callable.
    """
    while True:
        message = await receive()
        if message.get("type") == "lifespan.startup":
            _db_hydration.ensure_database_hydrated()
            await send({"type": "lifespan.startup.complete"})
        elif message.get("type") == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return


async def _serve_watchlists_routing(
    registry: ServiceRegistry,
    scope: Scope,
    receive: Receive,
    send: Send,
    path: str,
    method: str,
) -> bool:
    """Route watchlist collection and item requests.

    Args:
        registry: Live composition service registry.
        scope: ASGI connection scope.
        receive: ASGI receive callable.
        send: ASGI send callable.
        path: Request path.
        method: Uppercase request method.

    Returns:
        True when the request was handled.
    """
    if path == _WATCHLISTS_ROUTE and method in ("GET", "POST"):
        await _serve_watchlists_collection(registry, scope, receive, send)
        return True
    if path.startswith(_WATCHLISTS_ROUTE + "/") and method in ("PATCH", "DELETE"):
        await _serve_watchlists_item(registry, scope, receive, send)
        return True
    return False


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
    if path.startswith(_AUTH_PREFIX):
        await _serve_auth(scope, receive, send)
        return
    if path.startswith(_SETTINGS_ROUTE):
        await _serve_settings(scope, receive, send)
        return
    if path.startswith(_TRADING_PREFIX):
        await _serve_trading(registry, scope, receive, send)
        return
    if await _serve_watchlists_routing(registry, scope, receive, send, path, method):
        return
    if path.startswith(_DATA_PREFIX):
        await _serve_data(registry, scope, receive, send)
        return
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
