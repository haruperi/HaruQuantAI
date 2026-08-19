"""Authenticated live what-if Simulation session boundaries.

These five operations expose the Simulator's bounded live-session capability:
open a session over a prepared run, advance it in bounded tick increments, read
its state, fork an advisory what-if branch, and close it.

Two boundary facts are deliberate and visible in the responses:

* Practice sessions persist their immutable request, replay cursor, state
  digest, and manual intent journal. Private engine objects are never stored.
* Every projection carries an advisory marker and a branch journals under its
  own run identity. A what-if answer is evidence for a human, never an official
  `SimulationResult`.

The gateway simulates nothing itself: determinism, lineage, and capacity are
all Simulator rules, reached through one composed dispatcher.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    run_idempotent_write,
)
from app.services.api.widgets.simulation.schemas import (
    SimulationBranchRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    SimulationRunRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.utils import generate_id

type AuthContext = Any
type _LiveSource = Callable[..., object]

router = APIRouter(prefix="/api/v1/simulation/live-sessions", tags=["simulation"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200
_MAX_STEP_TICKS = 10_000

_UNAVAILABLE = frozenset(
    {
        "SIMULATION_LIVE_RUNTIME_UNAVAILABLE",
    }
)


def _live_source() -> _LiveSource:
    """Fail closed until composition injects the live-session runtime.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="SIMULATION_LIVE_RUNTIME_UNAVAILABLE",
    )


def _require_idempotency(value: str | None) -> str:
    """Require a bounded non-empty HTTP idempotency key.

    Args:
        value: Caller-supplied idempotency key header value.

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


def _delegate(source: _LiveSource, operation: str, *args: object) -> object:
    """Delegate once and translate the unavailable sentinel into HTTP 503.

    Args:
        source: Composed live-session dispatcher.
        operation: Canonical live-session operation name.
        *args: Operation-specific positional inputs.

    Returns:
        Simulator-owned session projection envelope.

    Raises:
        HTTPException: If no Simulator live bundle is composed.
        RuntimeError: If the Simulator reports an unexpected runtime failure.
    """
    try:
        return source(operation, *args)
    except RuntimeError as error:
        if str(error) not in _UNAVAILABLE:
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("", response_model=None)
def _create_session(
    request: SimulationRunRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_LiveSource, Depends(_live_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Open one bounded live what-if session over a prepared run.

    Returns:
        Simulator-owned session projection positioned before the first tick.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route="/api/v1/simulation/live-sessions",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _delegate(source, "create", request, generate_id("req")),
    )


@router.get("/{session_id}", response_model=None)
def _read_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_LiveSource, Depends(_live_source)],
) -> object:
    """Read one live session projection.

    Returns:
        Simulator-owned session projection.

    Raises:
        HTTPException: If authorization or composition fails.
    """
    require_human_permission(auth, "simulation:read")
    return _delegate(source, "read", session_id)


@router.post("/{session_id}/restore", response_model=None)
def _restore_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_LiveSource, Depends(_live_source)],
) -> object:
    """Reconstruct and verify one durable session after process restart.

    Returns:
        Verified exposure-blocked session projection.

    Raises:
        HTTPException: If authorization, composition, or integrity fails.
    """
    require_human_permission(auth, "simulation:run")
    return _delegate(source, "restore", session_id, generate_id("req"))


@router.post("/{session_id}/rearm", response_model=None)
def _rearm_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_LiveSource, Depends(_live_source)],
    approved: Annotated[bool, Query()] = False,
) -> object:
    """Explicitly rearm one verified reconstructed practice session.

    Returns:
        Running durable session projection.

    Raises:
        HTTPException: If authorization, composition, or approval fails.
    """
    require_human_permission(auth, "simulation:run")
    return _delegate(source, "rearm", session_id, approved, generate_id("req"))


@router.post("/{session_id}/step", response_model=None)
def _step_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_LiveSource, Depends(_live_source)],
    ticks: Annotated[int, Query(ge=1, le=_MAX_STEP_TICKS)] = 1,
) -> object:
    """Advance one live session by a bounded number of ticks.

    Stepping is not idempotency-keyed: advancing is the caller's explicit
    intent and the cursor is the authority on how far a session has moved, so
    a repeated step legitimately advances again.

    Returns:
        Simulator-owned session projection after advancing.

    Raises:
        HTTPException: If authorization or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    return _delegate(source, "step", session_id, ticks)


@router.post("/{session_id}/branch", response_model=None)
def _branch_session(
    session_id: str,
    request: SimulationBranchRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_LiveSource, Depends(_live_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Fork one live session into an independent advisory what-if branch.

    Returns:
        Simulator-owned projection of the new branch.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route="/api/v1/simulation/live-sessions/{session_id}/branch",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _delegate(
            source, "branch", session_id, request.overrides, generate_id("req")
        ),
    )


@router.delete("/{session_id}", response_model=None)
def _close_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_LiveSource, Depends(_live_source)],
) -> object:
    """Close one live session and release its engine.

    Returns:
        Simulator-owned final session projection.

    Raises:
        HTTPException: If authorization or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    return _delegate(source, "close", session_id)


__all__ = ("router",)
