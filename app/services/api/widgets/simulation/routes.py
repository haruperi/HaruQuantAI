"""Authenticated asynchronous Simulation HTTP boundaries."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    run_idempotent_write_async,
)
from app.services.api.widgets.simulation.schemas import (
    PortfolioSimulationRunRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    SimulationRunRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.utils import generate_id

type AuthContext = Any
type _RunSource = Callable[
    [Literal["run", "portfolio-run"], object, AuthContext], Awaitable[object]
]
type _ResultSource = Callable[[str, AuthContext], object | None]

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _simulation_run_source() -> _RunSource:
    """Fail closed until canonical composition injects Simulation execution.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="SIMULATION_RUNTIME_UNAVAILABLE",
    )


def _simulation_result_source() -> _ResultSource:
    """Fail closed until canonical composition injects result retrieval.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="SIMULATION_RESULTS_UNAVAILABLE",
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


@router.post("/run", response_model=None)
async def _run_backtest(
    request: SimulationRunRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RunSource, Depends(_simulation_run_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute one authenticated canonical asynchronous backtest.

    Returns:
        Simulator-owned canonical result.

    Raises:
        HTTPException: If authentication, authorization, or composition fails.
        RuntimeError: If Simulator reports an unexpected runtime failure.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/simulation/run",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("run", request, auth),
        )
    except RuntimeError as error:
        if str(error) != "SIMULATION_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/portfolio-run", response_model=None)
async def _run_portfolio_backtest(
    request: PortfolioSimulationRunRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RunSource, Depends(_simulation_run_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute one authenticated canonical asynchronous portfolio backtest.

    Returns:
        Simulator-owned canonical portfolio result.

    Raises:
        HTTPException: If authentication, authorization, or composition fails.
        RuntimeError: If Simulator reports an unexpected runtime failure.
    """
    require_human_permission(auth, "simulation:run")
    key = _require_idempotency(idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/simulation/portfolio-run",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("portfolio-run", request, auth),
        )
    except RuntimeError as error:
        if str(error) != "SIMULATION_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get("/results/{run_id}", response_model=None)
def _get_result(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ResultSource, Depends(_simulation_result_source)],
) -> object:
    """Return one completed canonical Simulation result by run ID.

    Returns:
        Simulator-owned canonical result.

    Raises:
        HTTPException: If authorization fails or the result is absent.
    """
    require_human_permission(auth, "simulation:read")
    result = source(run_id, auth)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SIMULATION_RESULT_NOT_FOUND",
        )
    return result


__all__ = ("router",)
