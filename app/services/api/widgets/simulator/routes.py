"""Authenticated canonical backtest HTTP boundaries.

A canonical run takes far longer than the API endpoint deadline, so the run
surface is a job: submission returns immediately with an identity, and progress
is observed by polling or by consuming the ordered event stream.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.kernel.identity import generate_id
from app.services.api import build_stream_event
from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    require_permission,
    run_idempotent_write_async,
)
from app.services.api.widgets.simulator.schemas import (
    SimulatorRunRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)

type AuthContext = Any
type _StrategySource = Callable[[], tuple[object, ...]]
type _RunSource = Callable[..., object]

router = APIRouter(prefix="/api/v1/simulator", tags=["simulator"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200
_STREAM_ROUTE = "/api/v1/simulator/runs/{run_id}/stream"


def _simulator_strategy_source() -> _StrategySource:
    """Fail closed until canonical composition injects the strategy catalogue.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="SIMULATOR_RUNTIME_UNAVAILABLE",
    )


def _simulator_run_source() -> _RunSource:
    """Fail closed until canonical composition injects backtest execution.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="SIMULATOR_RUNTIME_UNAVAILABLE",
    )


def _require_idempotency(value: str | None) -> str:
    """Require a bounded non-empty HTTP idempotency key.

    Returns:
        Validated idempotency key.

    Raises:
        HTTPException: If the key is absent, blank, or oversized.
    """
    if value is None or not value.strip() or len(value) > _MAX_IDEMPOTENCY_KEY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    return value


def _require_run(source: _RunSource, run_id: str, auth: AuthContext) -> object:
    """Return one owned run snapshot or fail closed.

    Returns:
        Bounded run projection.

    Raises:
        HTTPException: If the run is unknown or owned by another principal.
    """
    snapshot = source("get", run_id, principal_id=auth.principal_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SIMULATOR_RUN_NOT_FOUND",
        )
    return snapshot


@router.get("/strategies", response_model=None)
def _list_strategies(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_StrategySource, Depends(_simulator_strategy_source)],
) -> object:
    """Return every registered backtest strategy and its parameters.

    Returns:
        Simulation-owned strategy catalogue.
    """
    require_permission(auth, "simulation:read")
    return {"strategies": source()}


@router.post("/runs", response_model=None, status_code=status.HTTP_202_ACCEPTED)
async def _start_run(
    request: SimulatorRunRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RunSource, Depends(_simulator_run_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Start one canonical backtest run and return its accepted identity.

    Returns:
        Initial run projection.

    Raises:
        HTTPException: If authorization, validation, or composition fails.
        RuntimeError: If the Simulator reports an unexpected runtime failure.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/simulator/runs",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: asyncio.to_thread(
                source, "submit", request, principal_id=auth.principal_id
            ),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except RuntimeError as error:
        if str(error) != "SIMULATOR_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get("/runs", response_model=None)
def _list_runs(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RunSource, Depends(_simulator_run_source)],
) -> object:
    """Return the caller's retained backtest runs, newest first.

    Returns:
        Bounded run projections owned by the caller.
    """
    require_permission(auth, "simulation:read")
    return {"runs": source("list", principal_id=auth.principal_id)}


@router.get("/runs/{run_id}", response_model=None)
def _get_run(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RunSource, Depends(_simulator_run_source)],
) -> object:
    """Return one owned backtest run including its terminal report.

    Returns:
        Bounded run projection.
    """
    require_permission(auth, "simulation:read")
    return _require_run(source, run_id, auth)


@router.delete("/runs/{run_id}", response_model=None)
def _cancel_run(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RunSource, Depends(_simulator_run_source)],
) -> object:
    """Request cooperative cancellation of one owned backtest run.

    Returns:
        Bounded run projection after the cancellation request.

    Raises:
        HTTPException: If the run is unknown or owned by another principal.
    """
    require_human_permission(auth, "simulation:run")
    snapshot = source("cancel", run_id, principal_id=auth.principal_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SIMULATOR_RUN_NOT_FOUND",
        )
    return snapshot


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


async def _events(
    request: Request, frames: object, *, run_id: str, request_id: str
) -> AsyncIterator[bytes]:
    """Yield ordered run frames without blocking the event loop.

    The registry exposes a blocking iterator because a run executes on its own
    thread; each advance is therefore awaited off the loop.

    Yields:
        Encoded SSE frames until the run is terminal or the client disconnects.
    """
    iterator = iter(cast("Any", frames))
    sentinel = object()
    sequence = 0
    route = _STREAM_ROUTE.replace("{run_id}", run_id)
    while not await request.is_disconnected():
        item = await asyncio.to_thread(next, iterator, sentinel)
        if item is sentinel:
            return
        payload = dict(cast("Any", item))
        kind = str(payload.pop("kind", "progress"))
        event_type = "heartbeat" if kind == "heartbeat" else "payload"
        yield _frame(
            build_stream_event(
                sequence=sequence,
                request_id=request_id,
                route=route,
                event_type=event_type,
                payload=payload,
                cursor=str(payload.get("sequence", sequence)),
            )
        )
        sequence += 1
        if kind == "terminal":
            return


@router.get("/runs/{run_id}/stream", response_class=StreamingResponse)
async def _stream_run(
    run_id: str,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RunSource, Depends(_simulator_run_source)],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    """Stream ordered progress for one owned backtest run.

    Returns:
        Authenticated server-sent-event response.

    Raises:
        HTTPException: If the run is unknown or owned by another principal.
    """
    require_permission(auth, "simulation:read")
    _require_run(source, run_id, auth)
    try:
        after = max(0, int(last_event_id)) if last_event_id else 0
    except ValueError:
        after = 0
    frames = source("stream", run_id, principal_id=auth.principal_id, after=after)
    if frames is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SIMULATOR_RUN_NOT_FOUND",
        )
    return StreamingResponse(
        _events(request, frames, run_id=run_id, request_id=generate_id("req")),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


__all__ = ("router",)
