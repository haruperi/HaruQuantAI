"""Authenticated journal-playback sessions for completed Simulation runs."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable, Mapping
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.api.contracts import (
    SimulationSessionCreateRequest,  # noqa: TC001 - FastAPI resolves annotations.
)
from app.services.api.identity import (
    IdentityError,
    finalize_idempotency_key,
    require_auth_context,
    require_permission,
    reserve_idempotency_key,
)
from app.services.api.streams import StreamLimitError, build_stream_event
from app.utils import canonical_json, generate_id

type AuthContext = Any
type _SessionSource = Callable[..., object]

router = APIRouter(prefix="/api/v1/simulation/sessions", tags=["simulation"])
_ROUTE = "/api/v1/simulation/sessions"
_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _simulation_session_source() -> _SessionSource:
    """Fail closed until canonical composition injects playback operations.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="SIMULATION_PLAYBACK_UNAVAILABLE",
    )


def _resume_sequence(value: str | None) -> int | None:
    """Parse an optional SSE ``Last-Event-ID`` sequence.

    Returns:
        Non-negative sequence or ``None``.

    Raises:
        HTTPException: If the cursor is malformed.
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
    """Serialize one validated stream event as an SSE frame.

    Returns:
        UTF-8 encoded SSE frame.
    """
    payload = event.model_dump(mode="json")
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return (
        f"id: {payload['sequence']}\nevent: {payload['event_type']}\ndata: {data}\n\n"
    ).encode()


def _require_idempotency(value: str | None) -> str:
    """Return one bounded non-empty HTTP idempotency key.

    Raises:
        HTTPException: If the key is absent or invalid.
    """
    if value is None or not value.strip() or len(value) > _MAX_IDEMPOTENCY_KEY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    return value


def _runtime_status(code: str) -> int:
    """Map bounded Simulator playback codes to HTTP status values.

    Returns:
        Public HTTP status for the bounded code.
    """
    if code == "SIM_SESSION_NOT_FOUND":
        return status.HTTP_404_NOT_FOUND
    if code == "SIM_SESSION_EXPIRED":
        return status.HTTP_410_GONE
    if code in {"SIM_PLAYBACK_CURSOR_INVALID", "SIM_INVALID_CONFIG"}:
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_503_SERVICE_UNAVAILABLE


def _replayed_session(response_json: str | None) -> dict[str, object]:
    """Decode one terminal idempotency replay response.

    Returns:
        Previously persisted session projection.

    Raises:
        HTTPException: If stored replay material is malformed.
    """
    replayed = json.loads(str(response_json))
    if not isinstance(replayed, Mapping):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IDEMPOTENCY_RESPONSE_INVALID",
        )
    return {str(key): value for key, value in replayed.items()}


@router.post("", response_model=None)
def _create_session(
    body: SimulationSessionCreateRequest,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_SessionSource, Depends(_simulation_session_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Create one idempotent playback session for a completed run.

    Returns:
        Simulator-owned playback-session projection.

    Raises:
        HTTPException: If permission, idempotency, or Simulator validation fails.
        IdentityError: If durable idempotency evidence is unavailable.
    """
    require_permission(context, "simulation:read")
    key = _require_idempotency(idempotency_key)
    request_id = generate_id("req")
    try:
        decision = reserve_idempotency_key(
            principal_id=str(context.principal_id),
            method="POST",
            route=_ROUTE,
            key=key,
            request_material=body.model_dump(mode="json"),
            request_id=request_id,
        )
        if decision.state == "replay":
            return _replayed_session(decision.response_json)
        session = source("create", body.run_id, request_id=request_id)
        response_json = canonical_json(session)
        finalize_idempotency_key(
            principal_id=str(context.principal_id),
            method="POST",
            route=_ROUTE,
            key=key,
            response_json=response_json,
            status_code=status.HTTP_200_OK,
            request_id=request_id,
        )
        return session
    except IdentityError as error:
        code = str(error)
        status_code = (
            status.HTTP_409_CONFLICT
            if code.endswith(("CONFLICT", "KEY"))
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        raise HTTPException(status_code=status_code, detail=code) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=_runtime_status(str(error)), detail=str(error)
        ) from error


@router.get("/{session_id}/frames", response_class=StreamingResponse)
async def _stream_frames(
    session_id: str,
    request: Request,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_SessionSource, Depends(_simulation_session_source)],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    """Stream one completed run's validated journal frames.

    Returns:
        SSE response containing ordered ``StreamEvent`` envelopes.

    Raises:
        HTTPException: If authorization, cursor, or quota admission fails.
    """
    require_permission(context, "simulation:read")
    resume_after = _resume_sequence(last_event_id)
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
        """Translate owner journal events and release connection quota.

        Yields:
            UTF-8 encoded SSE frames.
        """
        try:
            iterator = cast(
                "AsyncIterator[object]",
                source("frames", session_id, resume_after=resume_after),
            )
            async for journal_event in iterator:
                values = cast("Any", journal_event).model_dump(mode="json")
                api_event = build_stream_event(
                    {
                        "sequence": values["sequence"],
                        "event_type": "payload",
                        "timestamp": values["occurred_at"],
                        "cursor": str(values["sequence"]),
                        "run_id": values["run_id"],
                        "kind": values["event_type"],
                        "journal_payload": values["payload"],
                        "previous_hash": values["previous_hash"],
                        "event_hash": values["event_hash"],
                    },
                    {
                        "request_id": str(context.request_id),
                        "trace_id": str(context.correlation_id),
                        "route": f"{_ROUTE}/{session_id}/frames",
                    },
                )
                yield _sse_frame(api_event)
        except RuntimeError as error:
            terminal = build_stream_event(
                {
                    "sequence": max(0, (resume_after or -1) + 1),
                    "event_type": "error",
                    "timestamp": cast("Any", context).issued_at,
                    "error": str(error),
                    "cursor": None,
                },
                {
                    "request_id": str(context.request_id),
                    "trace_id": str(context.correlation_id),
                    "route": f"{_ROUTE}/{session_id}/frames",
                },
            )
            yield _sse_frame(terminal)
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
