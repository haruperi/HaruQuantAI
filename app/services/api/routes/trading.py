"""Authenticated Trading session and governed mutation HTTP boundaries."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from app.services.api.contracts import (  # noqa: TC001 - FastAPI runtime annotation.
    TradingMutationRequest,
)
from app.services.api.identity import require_auth_context, require_human_permission

type AuthContext = Any
type _SessionSource = Callable[[str, str, str, AuthContext], object | None]
type _MutationSource = Callable[[str, object, AuthContext], Awaitable[object]]

router = APIRouter(prefix="/api/v1/trading", tags=["trading"])


def _trading_session_source() -> _SessionSource:
    """Fail closed until composition injects aggregate Trading session reads.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_SESSION_UNAVAILABLE",
    )


def _trading_mutation_source() -> _MutationSource:
    """Fail closed until composition injects governed Trading execution.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_MUTATIONS_UNAVAILABLE",
    )


def _governed_preflight(
    body: TradingMutationRequest,
    request: Request,
    idempotency_key: str | None,
) -> None:
    """Enforce boundary policy before delegating a Trading mutation.

    Raises:
        HTTPException: If production, configuration, or idempotency policy fails.
    """
    settings = request.app.state.api_settings
    if body.route == "live":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="PRODUCTION_EXECUTION_EXCLUDED",
        )
    if settings.execution_route != "paper" or settings.runtime_profile != "paper":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PAPER_EXECUTION_NOT_CONFIGURED",
        )
    if idempotency_key is None or idempotency_key != body.idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )


@router.get("/session", response_model=None)
def _get_session(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_SessionSource, Depends(_trading_session_source)],
    authority_id: Annotated[str, Query(min_length=1, max_length=200)],
    route: Annotated[Literal["sim", "paper"], Query()] = "paper",
) -> object:
    """Return one exact-scope aggregate Trading session projection.

    Returns:
        Trading-owned aggregate projection.

    Raises:
        HTTPException: If authorization fails or state is absent.
    """
    require_human_permission(auth, "trading:read")
    result = source(route, auth.tenant_or_environment, authority_id, auth)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TRADING_SESSION_NOT_FOUND",
        )
    return result


@router.post("/orders", response_model=None)
async def _submit_order(
    body: TradingMutationRequest,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_MutationSource, Depends(_trading_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Submit one governed non-production Trading order.

    Returns:
        Trading-owned mutation receipt.

    Raises:
        HTTPException: If boundary governance or composition fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _governed_preflight(body, request, idempotency_key)
    if body.action != "submit_order":
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    try:
        return await source("submit_order", body, auth)
    except RuntimeError as error:
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.delete("/orders/{order_id}", response_model=None)
async def _cancel_order(
    order_id: str,
    body: TradingMutationRequest,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_MutationSource, Depends(_trading_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Cancel one governed non-production Trading order.

    Returns:
        Trading-owned mutation receipt.

    Raises:
        HTTPException: If boundary governance or composition fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _governed_preflight(body, request, idempotency_key)
    if body.action != "cancel_order" or body.target_broker_order_id != order_id:
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    try:
        return await source("cancel_order", body, auth)
    except RuntimeError as error:
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/positions/{position_id}/close", response_model=None)
async def _close_position(
    position_id: str,
    body: TradingMutationRequest,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_MutationSource, Depends(_trading_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Close one governed non-production Trading position.

    Returns:
        Trading-owned mutation receipt.

    Raises:
        HTTPException: If boundary governance or composition fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _governed_preflight(body, request, idempotency_key)
    if body.action != "close_position" or body.target_broker_position_id != position_id:
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    try:
        return await source("close_position", body, auth)
    except RuntimeError as error:
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


__all__ = ("router",)
