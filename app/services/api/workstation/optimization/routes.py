"""Authenticated Optimization HTTP boundaries.

Backend v1 exposes the eleven Optimization operations that are clean thin
delegations through the function-only public API: four governed runs
(parameter sweep, walk-forward, walk-forward matrix, robustness), six
read-only analyses (compare, stability, overfit, rank, robustness score,
evidence handoff), and one durable result read. Each route validates the
API DTO, enforces the approved permission, and delegates exactly once to the
composed Optimization source dispatcher.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    run_idempotent_write,
    run_idempotent_write_async,
)
from app.services.api.workstation.optimization.schemas import (
    OptimizationCompareRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationHandoffRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationOverfitRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationParameterSweepRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationRankRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationRobustnessRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationRobustnessScoreRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationStabilityRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationWalkForwardMatrixRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    OptimizationWalkForwardRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.utils import generate_id

type AuthContext = Any
type _OptimizationSource = Callable[..., Any]

router = APIRouter(prefix="/api/v1/optimization", tags=["optimization"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200
_UNAVAILABLE = "OPTIMIZATION_RUNTIME_UNAVAILABLE"
_RESULTS_UNAVAILABLE = "OPTIMIZATION_RESULTS_UNAVAILABLE"


def _optimization_source() -> _OptimizationSource:
    """Fail closed until canonical composition injects Optimization operations.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=_UNAVAILABLE,
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


def _translate(error: RuntimeError) -> NoReturn:
    """Translate a deterministic Optimization runtime sentinel to HTTP 503.

    Args:
        error: RuntimeError raised by the composed source dispatcher.

    Raises:
        HTTPException: For the two known unavailability sentinels.
        RuntimeError: Re-raised for any unexpected runtime failure.
    """
    if str(error) in {_UNAVAILABLE, _RESULTS_UNAVAILABLE}:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    raise error


@router.post("/parameter-sweep", response_model=None)
async def _run_parameter_sweep(
    request: OptimizationParameterSweepRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute one governed authenticated Optimization parameter sweep.

    Returns:
        Optimization-owned result envelope.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:run")
    key = _require_idempotency(idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/optimization/parameter-sweep",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("parameter-sweep", request.payload),
        )
    except RuntimeError as error:
        _translate(error)


@router.post("/walk-forward", response_model=None)
async def _run_walk_forward(
    request: OptimizationWalkForwardRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute one governed authenticated Optimization walk-forward run.

    Returns:
        Optimization-owned result envelope.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:run")
    key = _require_idempotency(idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/optimization/walk-forward",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("walk-forward", request.payload),
        )
    except RuntimeError as error:
        _translate(error)


@router.post("/walk-forward-matrix", response_model=None)
async def _run_walk_forward_matrix(
    request: OptimizationWalkForwardMatrixRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute one governed bounded Optimization walk-forward matrix.

    Returns:
        Optimization-owned ordered result envelope.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:run")
    key = _require_idempotency(idempotency_key)
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/optimization/walk-forward-matrix",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(
                "walk-forward-matrix", tuple(request.requests), request.max_requests
            ),
        )
    except RuntimeError as error:
        _translate(error)


@router.post("/robustness", response_model=None)
def _run_robustness(
    request: OptimizationRobustnessRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute one governed authenticated Optimization robustness analysis.

    Returns:
        Optimization-owned robustness result envelope.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:run")
    key = _require_idempotency(idempotency_key)
    try:
        return run_idempotent_write(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/optimization/robustness",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(
                "robustness", request.payload, request.max_simulations
            ),
        )
    except RuntimeError as error:
        _translate(error)


@router.get("/results/{search_id}", response_model=None)
def _get_result(
    search_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
    reproducibility_hash: Annotated[
        str, Query(min_length=64, max_length=64, alias="reproducibility_hash")
    ],
) -> object:
    """Return one persisted Optimization result by search identity.

    Args:
        search_id: Canonical search identifier of the persisted result.
        auth: Authenticated caller principal.
        source: Composed Optimization source dispatcher.
        reproducibility_hash: Canonical evidence hash of the persisted result.

    Returns:
        Optimization-owned canonical result envelope.

    Raises:
        HTTPException: If authorization or composition fails, or the result
            is absent.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:read")
    try:
        result = source("read", search_id, reproducibility_hash)
    except RuntimeError as error:
        _translate(error)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OPTIMIZATION_RESULT_NOT_FOUND",
        )
    return result


@router.post("/compare", response_model=None)
def _compare(
    request: OptimizationCompareRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
) -> object:
    """Compare compatible Optimization results without recomputing evidence.

    Returns:
        Optimization-owned comparison envelope.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:read")
    try:
        return source("compare", tuple(request.results))
    except RuntimeError as error:
        _translate(error)


@router.post("/stability", response_model=None)
def _stability(
    request: OptimizationStabilityRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
) -> object:
    """Calculate exact-match parameter stability over supplied candidates.

    Returns:
        Optimization-owned stability evidence envelope.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:read")
    try:
        return source("stability", tuple(request.ranked_candidates))
    except RuntimeError as error:
        _translate(error)


@router.post("/overfit", response_model=None)
def _overfit(
    request: OptimizationOverfitRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
) -> object:
    """Detect parameter evidence whose degradation exceeds a threshold.

    Returns:
        Optimization-owned overfit evidence envelope.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:read")
    try:
        return source(
            "overfit",
            request.in_sample,
            request.out_of_sample,
            request.threshold,
        )
    except RuntimeError as error:
        _translate(error)


@router.post("/rank", response_model=None)
def _rank(
    request: OptimizationRankRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
) -> object:
    """Rank supplied candidate parameter sets deterministically.

    Returns:
        Optimization-owned ordered candidate-score envelope.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:read")
    try:
        return source("rank", tuple(request.candidates))
    except RuntimeError as error:
        _translate(error)


@router.post("/robustness-score", response_model=None)
def _robustness_score(
    request: OptimizationRobustnessScoreRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
) -> object:
    """Calculate a percentage over supplied applicable Boolean checks.

    Returns:
        Optimization-owned robustness-score envelope.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:read")
    try:
        return source("robustness-score", tuple(request.checks))
    except RuntimeError as error:
        _translate(error)


@router.post("/handoff", response_model=None)
def _handoff(
    request: OptimizationHandoffRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_OptimizationSource, Depends(_optimization_source)],
) -> object:
    """Build the canonical versioned advisory Optimization handoff evidence.

    Returns:
        Optimization-owned advisory handoff envelope.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If Optimization reports an unexpected runtime failure.
    """
    require_human_permission(auth, "optimization:read")
    try:
        return source("handoff", request.payload)
    except RuntimeError as error:
        _translate(error)


__all__ = ("router",)
