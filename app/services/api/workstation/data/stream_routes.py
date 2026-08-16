"""Authenticated transport bridge for Data-owned market streams."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.api.identity import require_auth_context, require_permission
from app.services.api.workstation.event_delivery import (
    StreamLimitError,
    build_stream_event,
)
from app.services.data import (
    build_market_depth_stream_request,
    build_market_snapshot_stream_request,
    build_market_stream_request,
    stream_market_data,
    stream_market_depth,
    stream_market_snapshots,
)
from app.utils import generate_id

type AuthContext = Any

router = APIRouter(prefix="/api/v1/data", tags=["data"])
_MAX_SNAPSHOT_SYMBOLS = 200


def _resume_sequence(value: str | None) -> int | None:
    """Parse an optional SSE ``Last-Event-ID`` header.

    Returns:
        Non-negative sequence or ``None``.

    Raises:
        HTTPException: If the supplied cursor is malformed.
    """
    if value is None:
        return None
    try:
        sequence = int(value)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="STREAM_CURSOR_INVALID",
        ) from error
    if sequence < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="STREAM_CURSOR_INVALID",
        )
    return sequence


def _sse_frame(event: BaseModel) -> bytes:
    """Serialize one validated API event as an SSE frame.

    Returns:
        UTF-8 encoded SSE frame.
    """
    payload = event.model_dump(mode="json")
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return (
        f"id: {payload['sequence']}\nevent: {payload['event_type']}\ndata: {data}\n\n"
    ).encode()


@router.get("/stream", response_class=StreamingResponse)
async def _stream_market_data(
    request: Request,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    symbol: Annotated[str, Query(min_length=1, max_length=128)],
    mode: Literal["ticks"],
    timeframe: Annotated[str, Query(min_length=1, max_length=16)],
    source_id: Literal["mt5"] = "mt5",
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    """Bridge one Data-owned MT5 stream to authenticated SSE.

    Returns:
        Streaming response containing only normalized API event envelopes.

    Raises:
        HTTPException: If permission, request, resume, or quota validation fails.
    """
    require_permission(context, "data:read")
    resume_after = _resume_sequence(last_event_id)
    data_request = build_market_stream_request(
        source_id=source_id,
        symbol=symbol,
        mode=mode,
        timeframe=timeframe,
        request_id=generate_id("req"),
        resume_after=resume_after,
    )

    connection_id = generate_id("evt")
    manager = request.app.state.api_stream_connection_manager
    try:
        await manager.open(
            connection_id=connection_id,
            actor_id=str(context.principal_id),
        )
    except StreamLimitError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="STREAM_CONNECTION_LIMIT",
        ) from error

    async def frames() -> AsyncIterator[bytes]:
        """Yield Data events and release both domain and transport resources."""
        try:
            async for data_event in stream_market_data(data_request):
                values = data_event.model_dump(mode="json")
                data_type = values.pop("event_type")
                occurred_at = values.pop("occurred_at")
                terminal_error = values.pop("error")
                values.pop("terminal")
                values.pop("request_id")
                api_event = build_stream_event(
                    {
                        **values,
                        "sequence": data_event.sequence,
                        "event_type": (
                            "payload"
                            if data_type in {"tick", "bar"}
                            else "heartbeat"
                            if data_type == "heartbeat"
                            else "error"
                        ),
                        "timestamp": occurred_at,
                        "error": terminal_error,
                        "cursor": data_event.cursor,
                        "kind": data_type,
                    },
                    {
                        "request_id": str(context.request_id),
                        "trace_id": str(context.correlation_id),
                        "route": "/api/v1/data/stream",
                    },
                )
                yield _sse_frame(api_event)
                if data_event.terminal:
                    break
        finally:
            await manager.close(connection_id)

    return StreamingResponse(
        frames(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/snapshot-stream", response_class=StreamingResponse)
async def _stream_market_snapshots(
    request: Request,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    symbols: Annotated[str, Query(min_length=1, max_length=25_799)],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    """Bridge one atomic multi-symbol MT5 snapshot feed to authenticated SSE.

    Returns:
        Streaming response containing validated snapshot event envelopes.

    Raises:
        HTTPException: If permission, symbol bounds, cursor, or quota fails.
    """
    require_permission(context, "data:read")
    parsed_symbols = tuple(item.strip() for item in symbols.split(",") if item.strip())
    if not parsed_symbols or len(parsed_symbols) > _MAX_SNAPSHOT_SYMBOLS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="SNAPSHOT_SYMBOL_LIMIT",
        )
    data_request = build_market_snapshot_stream_request(
        symbols=parsed_symbols,
        request_id=generate_id("req"),
        resume_after=_resume_sequence(last_event_id),
    )
    connection_id = generate_id("evt")
    manager = request.app.state.api_stream_connection_manager
    try:
        await manager.open(
            connection_id=connection_id,
            actor_id=str(context.principal_id),
        )
    except StreamLimitError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="STREAM_CONNECTION_LIMIT",
        ) from error

    async def frames() -> AsyncIterator[bytes]:
        """Yield snapshot events and release connection quota."""
        try:
            async for data_event in stream_market_snapshots(data_request):
                typed_event = cast("Any", data_event)
                values = typed_event.model_dump(mode="json")
                api_event = build_stream_event(
                    {
                        "sequence": typed_event.sequence,
                        "event_type": "payload",
                        "timestamp": typed_event.occurred_at,
                        "quotes": values["quotes"],
                        "stale": typed_event.stale,
                        "gap": typed_event.gap,
                        "source_id": typed_event.source_id,
                        "cursor": str(typed_event.sequence),
                        "kind": "snapshot",
                    },
                    {
                        "request_id": str(context.request_id),
                        "trace_id": str(context.correlation_id),
                        "route": "/api/v1/data/snapshot-stream",
                    },
                )
                yield _sse_frame(api_event)
        finally:
            await manager.close(connection_id)

    return StreamingResponse(
        frames(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/depth-stream", response_class=StreamingResponse)
async def _stream_market_depth(
    request: Request,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    symbols: Annotated[str, Query(min_length=1, max_length=25_799)],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    """Bridge one atomic multi-symbol MT5 Depth-of-Market feed to authenticated SSE.

    Returns:
        Streaming response containing validated depth event envelopes.

    Raises:
        HTTPException: If permission, symbol bounds, cursor, or quota fails.
    """
    require_permission(context, "data:read")
    parsed_symbols = tuple(item.strip() for item in symbols.split(",") if item.strip())
    if not parsed_symbols or len(parsed_symbols) > _MAX_SNAPSHOT_SYMBOLS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="SNAPSHOT_SYMBOL_LIMIT",
        )
    data_request = build_market_depth_stream_request(
        symbols=parsed_symbols,
        request_id=generate_id("req"),
        resume_after=_resume_sequence(last_event_id),
    )
    connection_id = generate_id("evt")
    manager = request.app.state.api_stream_connection_manager
    try:
        await manager.open(
            connection_id=connection_id,
            actor_id=str(context.principal_id),
        )
    except StreamLimitError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="STREAM_CONNECTION_LIMIT",
        ) from error

    async def frames() -> AsyncIterator[bytes]:
        """Yield depth events and release connection quota."""
        try:
            async for data_event in stream_market_depth(data_request):
                typed_event = cast("Any", data_event)
                values = typed_event.model_dump(mode="json")
                api_event = build_stream_event(
                    {
                        "sequence": typed_event.sequence,
                        "event_type": "payload",
                        "timestamp": typed_event.occurred_at,
                        "books": values["books"],
                        "errors": values["errors"],
                        "stale": typed_event.stale,
                        "gap": typed_event.gap,
                        "source_id": typed_event.source_id,
                        "cursor": str(typed_event.sequence),
                        "kind": "depth",
                    },
                    {
                        "request_id": str(context.request_id),
                        "trace_id": str(context.correlation_id),
                        "route": "/api/v1/data/depth-stream",
                    },
                )
                yield _sse_frame(api_event)
        finally:
            await manager.close(connection_id)

    return StreamingResponse(
        frames(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


__all__ = ("router",)
