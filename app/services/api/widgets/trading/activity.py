"""Authenticated session-scoped redacted application-log streaming."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.services.api import build_stream_event
from app.services.api.identity import require_auth_context, require_permission
from app.services.trading import get_execution_session
from app.utils import generate_id, load_settings

type AuthContext = Any

router = APIRouter(prefix="/api/v1/trading", tags=["trading"])
_POLL_SECONDS = 0.5
_HEARTBEAT_POLLS = 10
_MAX_INITIAL_BYTES = 131_072
_MAX_LINE_LENGTH = 2_000


def _frame(event: object) -> bytes:
    """Serialize one stream event as an SSE frame.

    Returns:
        Encoded SSE frame.
    """
    payload = event.model_dump(mode="json")  # type: ignore[attr-defined]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return (
        f"id: {payload['sequence']}\nevent: {payload['event_type']}\n"
        f"data: {encoded}\n\n"
    ).encode()


def _active_log_path() -> Path | None:
    """Resolve the configured active application log without creating it.

    Returns:
        Absolute configured log path, or ``None`` when file logging is disabled.
    """
    logging_settings = load_settings().logging
    if logging_settings.file_path is not None:
        return Path(logging_settings.file_path).resolve()
    if logging_settings.log_directory is not None:
        return (Path(logging_settings.log_directory) / "app.log").resolve()
    return None


async def _events(
    request: Request, *, session_id: str, request_id: str
) -> AsyncIterator[bytes]:
    """Yield bounded redacted log lines that carry one session identifier."""
    sequence = 0
    position: int | None = None
    idle_polls = 0
    while not await request.is_disconnected():
        path = _active_log_path()
        emitted = False
        if path is not None and path.is_file():
            size = path.stat().st_size
            if position is None or position > size:
                position = max(0, size - _MAX_INITIAL_BYTES)
            with path.open(encoding="utf-8", errors="replace") as handle:
                handle.seek(position)
                for raw_line in handle:
                    line = raw_line.strip().replace("\x00", "")[:_MAX_LINE_LENGTH]
                    if session_id not in line:
                        continue
                    yield _frame(
                        build_stream_event(
                            sequence=sequence,
                            request_id=request_id,
                            route=f"/api/v1/trading/execution-sessions/{session_id}/activity",
                            event_type="payload",
                            payload={"line": line},
                            cursor=str(sequence),
                        )
                    )
                    sequence += 1
                    emitted = True
                position = handle.tell()
        idle_polls = 0 if emitted else idle_polls + 1
        if idle_polls >= _HEARTBEAT_POLLS:
            yield _frame(
                build_stream_event(
                    sequence=sequence,
                    request_id=request_id,
                    route=f"/api/v1/trading/execution-sessions/{session_id}/activity",
                    event_type="heartbeat",
                    payload={"session_id": session_id},
                    cursor=str(sequence),
                )
            )
            sequence += 1
            idle_polls = 0
        await asyncio.sleep(_POLL_SECONDS)


@router.get(
    "/execution-sessions/{session_id}/activity",
    response_class=StreamingResponse,
)
async def _stream_session_activity(
    session_id: str,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> StreamingResponse:
    """Stream redacted file-backed logs for one owned Trading session.

    Returns:
        Authenticated server-sent-event response.

    Raises:
        HTTPException: If the session is absent or outside the caller's scope.
    """
    require_permission(auth, "trading:read")
    session = get_execution_session(session_id)
    if (
        session is None
        or getattr(session, "principal_id", None) != auth.principal_id
        or getattr(session, "environment_id", None) != auth.tenant_or_environment
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="EXECUTION_SESSION_NOT_FOUND",
        )
    request_id = generate_id("req")
    return StreamingResponse(
        _events(request, session_id=session_id, request_id=request_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


__all__ = ("router",)
