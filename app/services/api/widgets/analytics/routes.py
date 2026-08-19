"""Analytics Workbench HTTP boundaries (FEAT-API-28).

Reads require ``simulation:read``; annotation and archive writes require
``simulation:run`` and an idempotency key. Unknown or foreign-owned runs
return 404, never 403. Every metric and comparison is delegated to
Analytics; the gateway computes nothing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    require_permission,
    run_idempotent_write,
)
from app.services.api.widgets.analytics.schemas import (
    AnalyticsAnnotationRequest,  # noqa: TC001 - FastAPI resolves annotations.
    AnalyticsArchiveRequest,  # noqa: TC001
    AnalyticsCompareRequest,  # noqa: TC001
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

type AuthContext = Any
type _AnalyticsSource = Any

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics-workbench"])

_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _analytics_workbench_source() -> _AnalyticsSource:
    """Fail closed until canonical composition injects the source.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="ANALYTICS_WORKBENCH_RUNTIME_UNAVAILABLE",
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


def _dispatch(
    source: _AnalyticsSource, operation: str, *args: object, **kwargs: object
) -> object:
    """Dispatch one operation, normalizing domain failures to HTTP codes.

    Returns:
        Operation result.

    Raises:
        HTTPException: On unknown resources, invalid input, or uncomposed
            authorities.
    """
    try:
        return source(operation, *args, **kwargs)
    except KeyError as error:
        detail = error.args[0] if error.args else "ANALYTICS_RUN_NOT_FOUND"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(detail)
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
        ) from error


def _read_permission(auth: AuthContext) -> None:
    """Authorize one Analytics Workbench read."""
    require_permission(auth, "simulation:read")


@router.get("/runs", response_model=None)
def _list_runs(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> object:
    """List the caller's catalogue runs, newest first.

    Returns:
        Bounded catalogue page owned by the caller.
    """
    _read_permission(auth)
    return {
        "runs": _dispatch(
            source,
            "list_runs",
            principal_id=auth.principal_id,
            limit=page_size,
            offset=(page - 1) * page_size,
        )
    }


@router.get("/runs/{run_id}", response_model=None)
def _get_run(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
) -> object:
    """Read one owned catalogue run.

    Returns:
        Catalogue row projection.

    Raises:
        HTTPException: If the run is unknown or foreign-owned.
    """
    _read_permission(auth)
    return _dispatch(source, "get_run", run_id, principal_id=auth.principal_id)


@router.get("/runs/{run_id}/simulation-result", response_model=None)
def _get_simulation_result(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
) -> object:
    """Read the canonical Simulation result content owned by one run.

    Returns:
        Canonical ``SimulationResult.v1`` owner evidence.

    Raises:
        HTTPException: If the run or its result evidence is missing.
    """
    _read_permission(auth)
    return _dispatch(
        source, "simulation_result", run_id, principal_id=auth.principal_id
    )


@router.get("/runs/{run_id}/report", response_model=None)
def _get_report(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
) -> object:
    """Read the attached immutable Analytics report artifact.

    Returns:
        Serialized Analytics report.

    Raises:
        HTTPException: If the run or report evidence is missing.
    """
    _read_permission(auth)
    return _dispatch(source, "report", run_id, principal_id=auth.principal_id)


@router.get("/runs/{run_id}/workbench", response_model=None)
def _get_workbench(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
) -> object:
    """Read the Analytics-delegated workbench projection for one run.

    Returns:
        Workbench payload.

    Raises:
        HTTPException: If the run or its evidence is missing.
    """
    _read_permission(auth)
    return _dispatch(source, "workbench", run_id, principal_id=auth.principal_id)


@router.get("/runs/{run_id}/trades", response_model=None)
def _get_trades(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=500)] = 50,
    side: Annotated[str, Query(pattern="^(all|buy|sell)$")] = "all",
) -> object:
    """Paginate the canonical Simulation trade ledger.

    Returns:
        One bounded trade page with explicit total count.

    Raises:
        HTTPException: If the run or its result evidence is missing.
    """
    _read_permission(auth)
    return _dispatch(
        source,
        "trades",
        run_id,
        principal_id=auth.principal_id,
        page=page,
        page_size=page_size,
        side=side,
    )


@router.get("/runs/{run_id}/trades/{ticket}", response_model=None)
def _get_trade(
    run_id: str,
    ticket: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
) -> object:
    """Read one trade from the canonical Simulation result.

    Returns:
        Exact trade record.

    Raises:
        HTTPException: If the run or trade is missing.
    """
    _read_permission(auth)
    return _dispatch(source, "trade", run_id, ticket, principal_id=auth.principal_id)


@router.get("/runs/{run_id}/periods", response_model=None)
def _get_periods(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
    dimension: Annotated[
        str,
        Query(pattern="^(year|quarter|month|week|day|day_of_week|hour)$"),
    ] = "month",
    context: Annotated[str, Query(pattern="^(all|long|short)$")] = "all",
) -> object:
    """Read the workbench period-table section with exact query dimensions.

    Returns:
        Owner period-table projection.

    Raises:
        HTTPException: If the run or its evidence is missing.
    """
    _read_permission(auth)
    section = _dispatch(
        source,
        "periods",
        run_id,
        principal_id=auth.principal_id,
        dimension=dimension,
        context=context,
    )
    return {
        "run_id": run_id,
        "dimension": dimension,
        "context": context,
        "section": getattr(section, "data", section),
    }


@router.get("/runs/{run_id}/artifacts", response_model=None)
def _get_artifacts(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
) -> object:
    """List the immutable artifact references recorded for one run.

    Returns:
        Artifact reference rows.

    Raises:
        HTTPException: If the run is unknown or foreign-owned.
    """
    _read_permission(auth)
    row = cast(
        "Mapping[str, object]",
        _dispatch(source, "get_run", run_id, principal_id=auth.principal_id),
    )
    return {
        "run_id": run_id,
        "artifacts": tuple(
            {"kind": kind, "ref": row.get(column)}
            for kind, column in (
                ("result", "result_ref"),
                ("report", "report_ref"),
                ("manifest", "artifact_manifest_ref"),
            )
            if row.get(column)
        ),
    }


@router.get("/runs/{run_id}/replay-anchors", response_model=None)
def _get_replay_anchors(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
) -> object:
    """List replay anchors for one run's immutable journal.

    Returns:
        Replay anchor rows derived from the owner trade ledger.

    Raises:
        HTTPException: If the run or its result evidence is missing.
    """
    _read_permission(auth)
    trades = cast(
        "Mapping[str, object]",
        _dispatch(
            source,
            "trades",
            run_id,
            principal_id=auth.principal_id,
            page=1,
            page_size=500,
        ),
    )
    return {
        "run_id": run_id,
        "anchors": tuple(
            {"ticket": str(trade.get("ticket")), "exit_time": trade.get("exit_time")}
            for trade in cast("Sequence[Mapping[str, object]]", trades["trades"])
        ),
    }


@router.post("/compare", response_model=None)
def _compare_runs(
    request: AnalyticsCompareRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
) -> object:
    """Delegate one multi-run comparison to Analytics.

    Returns:
        Owner comparison evidence.

    Raises:
        HTTPException: If any run is unknown or lacks report evidence.
    """
    _read_permission(auth)
    return _dispatch(
        source,
        "compare",
        request.model_dump(),
        principal_id=auth.principal_id,
    )


@router.post("/runs/{run_id}/annotations", response_model=None)
def _annotate_run(
    run_id: str,
    request: AnalyticsAnnotationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Apply metadata-only annotations to one owned run.

    Returns:
        Annotation result.

    Raises:
        HTTPException: If the run is unknown or foreign-owned.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/analytics/runs/{run_id}/annotations",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _dispatch(
            source,
            "annotate",
            run_id,
            request.model_dump(),
            principal_id=auth.principal_id,
        ),
    )


@router.post("/runs/{run_id}/archive", response_model=None)
def _archive_run(
    run_id: str,
    request: AnalyticsArchiveRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AnalyticsSource, Depends(_analytics_workbench_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Change one run's archive state; evidence is never deleted.

    Returns:
        Archive result.

    Raises:
        HTTPException: If the run is unknown or foreign-owned.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route=f"/api/v1/analytics/runs/{run_id}/archive",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _dispatch(
            source,
            "archive",
            run_id,
            principal_id=auth.principal_id,
        ),
    )


__all__ = ("router",)
