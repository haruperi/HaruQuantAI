"""Simulation Workbench HTTP boundaries (FEAT-API-27).

Authorization happens before any resource access; unknown or
foreign-owned resources return 404, never 403. Every create, retry,
finalize, and reproduce request requires an idempotency key.
"""

from __future__ import annotations

from inspect import isawaitable
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    require_permission,
    run_idempotent_write,
    run_idempotent_write_async,
)
from app.services.api.workstation.simulation_workbench.registry import (
    SimulationWorkbenchConflictError,
)
from app.services.api.workstation.simulation_workbench.schemas import (
    BatchCreateRequest,  # noqa: TC001
    LiveSessionBranchRequest,  # noqa: TC001 - FastAPI resolves annotations.
    LiveSessionCommandRequest,  # noqa: TC001
    LiveSessionCreateRequest,  # noqa: TC001
    SeekRequest,  # noqa: TC001
    StepRequest,  # noqa: TC001
    ViewportQuery,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

type AuthContext = Any
type _WorkbenchSource = Any

router = APIRouter(prefix="/api/v1/simulator", tags=["simulator-workbench"])

_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _simulation_workbench_source() -> _WorkbenchSource:
    """Fail closed until canonical composition injects the workbench source.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="SIMULATION_WORKBENCH_RUNTIME_UNAVAILABLE",
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


def _not_found(detail: str) -> HTTPException:
    """Build one uniform 404 for unknown or foreign resources.

    Returns:
        Constructed not-found exception ready to raise.
    """
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _dispatch(
    source: _WorkbenchSource, operation: str, *args: object, **kwargs: object
) -> object:
    """Dispatch one operation, normalizing domain failures to HTTP codes.

    Returns:
        Operation result.

    Raises:
        HTTPException: On unknown resources, invalid input, conflicts, or
            uncomposed authorities.
    """
    try:
        return source(operation, *args, **kwargs)
    except SimulationWorkbenchConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=error.code
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error


@router.post("/live-sessions", response_model=None, status_code=status.HTTP_201_CREATED)
def _create_live_session(
    request: LiveSessionCreateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Open one typed practice session over a completed owned run.

    Returns:
        Created live-session catalogue projection.

    Raises:
        HTTPException: If authorization, ownership, or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route="/api/v1/simulator/live-sessions",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _require(
            _dispatch(
                source,
                "create_session",
                request.run_id,
                principal_id=auth.principal_id,
                durable=request.durable,
            ),
            "SIMULATION_RUN_NOT_FOUND",
        ),
    )


def _require(value: object, detail: str) -> object:
    """Return the value or raise the uniform 404.

    Returns:
        The value when the resource exists.

    Raises:
        HTTPException: If the resource is unknown or foreign-owned.
    """
    if value is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return value


@router.get("/live-sessions", response_model=None)
def _list_live_sessions(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
) -> object:
    """List the caller's live sessions, newest first.

    Returns:
        Bounded session projections owned by the caller.
    """
    require_permission(auth, "simulation:read")
    return {
        "sessions": _dispatch(source, "list_sessions", principal_id=auth.principal_id)
    }


@router.get("/live-sessions/{session_id}", response_model=None)
def _get_live_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
) -> object:
    """Read one owned live session.

    Returns:
        Session projection.

    Raises:
        HTTPException: If the session is unknown or foreign-owned.
    """
    require_permission(auth, "simulation:read")
    return _require(
        _dispatch(source, "get_session", session_id, principal_id=auth.principal_id),
        "SIMULATION_SESSION_NOT_FOUND",
    )


@router.get("/live-sessions/{session_id}/viewport", response_model=None)
def _get_viewport(
    session_id: str,
    query: Annotated[ViewportQuery, Query()],
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
) -> object:
    """Return one backwards-only market viewport at or before the cursor.

    Returns:
        Bounded viewport rows and cursor truth.

    Raises:
        HTTPException: If the session is unknown, the viewport would expose
            future rows, or composition fails.
    """
    require_permission(auth, "simulation:read")
    _require(
        _dispatch(source, "get_session", session_id, principal_id=auth.principal_id),
        "SIMULATION_SESSION_NOT_FOUND",
    )
    return _dispatch(
        source,
        "viewport",
        session_id,
        principal_id=auth.principal_id,
        before=query.before,
        after=query.after,
    )


@router.post("/live-sessions/{session_id}/step", response_model=None)
def _step_live_session(
    session_id: str,
    request: StepRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
) -> object:
    """Advance one owned session by a bounded tick count.

    Returns:
        Refreshed typed session projection.

    Raises:
        HTTPException: If the session is unknown or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    return _require(
        _dispatch(
            source,
            "step",
            session_id,
            principal_id=auth.principal_id,
            ticks=request.ticks,
        ),
        "SIMULATION_SESSION_NOT_FOUND",
    )


@router.post("/live-sessions/{session_id}/seek", response_model=None)
def _seek_live_session(
    session_id: str,
    request: SeekRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
) -> object:
    """Move one owned session forward to an absolute cursor.

    Returns:
        Refreshed typed session projection.

    Raises:
        HTTPException: On rewind or bound violations, or unknown sessions.
    """
    require_human_permission(auth, "simulation:run")
    return _require(
        _dispatch(
            source,
            "seek",
            session_id,
            principal_id=auth.principal_id,
            target_cursor=request.target_cursor,
        ),
        "SIMULATION_SESSION_NOT_FOUND",
    )


@router.post("/live-sessions/{session_id}/commands", response_model=None)
async def _submit_command(
    session_id: str,
    request: LiveSessionCommandRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Submit one manual command and return receipt plus refreshed state.

    No fill is ever invented; the owner receipt is authoritative.

    Returns:
        Owner receipt and refreshed session projection.

    Raises:
        HTTPException: If the session is unknown or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)

    async def _execute() -> object:
        """Execute the manual command through the composed live authority.

        Returns:
            Owner receipt evidence and refreshed session projection.
        """
        pending = _require(
            _dispatch(
                source,
                "command",
                session_id,
                principal_id=auth.principal_id,
                command=request.model_dump(),
            ),
            "SIMULATION_SESSION_NOT_FOUND",
        )
        if isawaitable(pending):
            return _require(await pending, "SIMULATION_SESSION_NOT_FOUND")
        return pending

    return await run_idempotent_write_async(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/simulator/live-sessions/{session_id}/commands",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=_execute,
    )


@router.post("/live-sessions/{session_id}/branch", response_model=None)
def _branch_live_session(
    session_id: str,
    request: LiveSessionBranchRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Fork one owned session into an advisory what-if branch.

    Returns:
        Advisory branch projection.

    Raises:
        HTTPException: If the session is unknown or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/simulator/live-sessions/{session_id}/branch",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _require(
            _dispatch(
                source,
                "branch",
                session_id,
                principal_id=auth.principal_id,
                overrides=request.overrides,
            ),
            "SIMULATION_SESSION_NOT_FOUND",
        ),
    )


@router.post("/live-sessions/{session_id}/restore", response_model=None)
def _restore_live_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Reconstruct one durable session and leave it recovery-blocked.

    Returns:
        Recovery projection.

    Raises:
        HTTPException: If the session is unknown or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/simulator/live-sessions/{session_id}/restore",
        key=key,
        request_material={"session_id": session_id},
        request_id=generate_id("req"),
        operation=lambda: _require(
            _dispatch(source, "restore", session_id, principal_id=auth.principal_id),
            "SIMULATION_SESSION_NOT_FOUND",
        ),
    )


@router.post("/live-sessions/{session_id}/rearm", response_model=None)
def _rearm_live_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    approved: Annotated[bool, Query()],
) -> object:
    """Explicitly rearm one verified reconstructed session.

    Returns:
        Rearmed session projection.

    Raises:
        HTTPException: If the session is unknown or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    return _require(
        _dispatch(
            source,
            "rearm",
            session_id,
            principal_id=auth.principal_id,
            approved=approved,
        ),
        "SIMULATION_SESSION_NOT_FOUND",
    )


@router.post("/live-sessions/{session_id}/finalize", response_model=None)
def _finalize_live_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Seal one session's advisory journal; finalization stays advisory.

    Returns:
        Finalized session projection.

    Raises:
        HTTPException: If the session is unknown or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/simulator/live-sessions/{session_id}/finalize",
        key=key,
        request_material={"session_id": session_id},
        request_id=generate_id("req"),
        operation=lambda: _require(
            _dispatch(source, "finalize", session_id, principal_id=auth.principal_id),
            "SIMULATION_SESSION_NOT_FOUND",
        ),
    )


@router.post(
    "/live-sessions/{session_id}/reproduce", response_model=None, status_code=201
)
def _reproduce_live_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Reproduce one finalized session as a separate canonical job.

    Returns:
        New canonical job projection.

    Raises:
        HTTPException: If the session is unknown or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/simulator/live-sessions/{session_id}/reproduce",
        key=key,
        request_material={"session_id": session_id},
        request_id=generate_id("req"),
        operation=lambda: _require(
            _dispatch(source, "reproduce", session_id, principal_id=auth.principal_id),
            "SIMULATION_SESSION_NOT_FOUND",
        ),
    )


@router.delete("/live-sessions/{session_id}", response_model=None)
def _close_live_session(
    session_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
) -> object:
    """Close one owned live session and release its engine.

    Returns:
        Closed session projection.

    Raises:
        HTTPException: If the session is unknown or foreign-owned.
    """
    require_human_permission(auth, "simulation:run")
    return _require(
        _dispatch(source, "close_session", session_id, principal_id=auth.principal_id),
        "SIMULATION_SESSION_NOT_FOUND",
    )


@router.post("/batches", response_model=None, status_code=status.HTTP_202_ACCEPTED)
def _create_batch(
    request: BatchCreateRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute a bounded batch of canonical runs.

    Returns:
        Accepted batch projection.

    Raises:
        HTTPException: If authorization or composition fails.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route="/api/v1/simulator/batches",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _dispatch(
            source,
            "create_batch",
            request.model_dump(mode="json"),
            principal_id=auth.principal_id,
        ),
    )


@router.get("/batches/{batch_id}", response_model=None)
def _get_batch(
    batch_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
) -> object:
    """Read one owned batch with its ordered item rows.

    Returns:
        Batch projection with items.

    Raises:
        HTTPException: If the batch is unknown or foreign-owned.
    """
    require_permission(auth, "simulation:read")
    return _require(
        _dispatch(source, "get_batch", batch_id, principal_id=auth.principal_id),
        "SIMULATION_BATCH_NOT_FOUND",
    )


@router.get("/batches/{batch_id}/stream", response_model=None)
def _stream_batch(
    batch_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    after: Annotated[int, Query(ge=0)] = 0,
) -> object:
    """Stream ordered batch progress frames.

    Returns:
        Batch stream projection handle.

    Raises:
        HTTPException: If the batch is unknown or foreign-owned.
    """
    require_permission(auth, "simulation:read")
    return _require(
        _dispatch(
            source,
            "stream_batch",
            batch_id,
            principal_id=auth.principal_id,
            after=after,
        ),
        "SIMULATION_BATCH_NOT_FOUND",
    )


@router.post("/batches/{batch_id}/cancel", response_model=None)
def _cancel_batch(
    batch_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Cancel every non-terminal item of one owned batch exactly once.

    Returns:
        Cancellation result with cancelled item count.

    Raises:
        HTTPException: If the batch is unknown or foreign-owned.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/simulator/batches/{batch_id}/cancel",
        key=key,
        request_material={"batch_id": batch_id},
        request_id=generate_id("req"),
        operation=lambda: _require(
            _dispatch(source, "cancel_batch", batch_id, principal_id=auth.principal_id),
            "SIMULATION_BATCH_NOT_FOUND",
        ),
    )


@router.post("/batches/{batch_id}/retry-failed", response_model=None)
def _retry_failed(
    batch_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_WorkbenchSource, Depends(_simulation_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Retry only the failed items of one owned batch.

    Returns:
        Retry result with retried item count.

    Raises:
        HTTPException: If the batch is unknown or foreign-owned.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/simulator/batches/{batch_id}/retry-failed",
        key=key,
        request_material={"batch_id": batch_id},
        request_id=generate_id("req"),
        operation=lambda: _require(
            _dispatch(source, "retry_failed", batch_id, principal_id=auth.principal_id),
            "SIMULATION_BATCH_NOT_FOUND",
        ),
    )


__all__ = ("router",)
