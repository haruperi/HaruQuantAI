"""Authenticated Portfolio HTTP boundaries.

Backend v1 exposes the three Portfolio operations that are clean thin
delegations through the existing function-only public API: construction,
active-status reads, and allocation-history reads. Governed writes that
require non-HTTP-producible evidence (``activate_portfolio``,
``rollback_portfolio``, ``assess_portfolio_drift``,
``submit_portfolio_rebalance``, ``recompute_portfolio_measurement``) remain
pending until Portfolio exposes the intermediate evidence/review objects
through its public boundary; see FR-API-056 in the package README.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api.contracts import (
    PortfolioConstructRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.services.api.identity import require_auth_context, require_human_permission

type AuthContext = Any
type _PortfolioSource = Callable[..., object]

router = APIRouter(prefix="/api/v1/portfolio", tags=["portfolio"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _portfolio_source() -> _PortfolioSource:
    """Fail closed until canonical composition injects Portfolio operations.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="PORTFOLIO_RUNTIME_UNAVAILABLE",
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


@router.post("/construct", response_model=None)
def _construct(
    request: PortfolioConstructRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute one governed authenticated Portfolio construction.

    Returns:
        Portfolio-owned construction result envelope.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
        RuntimeError: If Portfolio reports an unexpected runtime failure.
    """
    require_human_permission(auth, "portfolio:write")
    _require_idempotency(idempotency_key)
    try:
        return source("construct", request, auth)
    except RuntimeError as error:
        if str(error) != "PORTFOLIO_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get("/{portfolio_id}/status", response_model=None)
def _get_status(
    portfolio_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
    scope_key: Annotated[str, Query(min_length=1, max_length=200, alias="scope_key")],
    scope_value: Annotated[
        str, Query(min_length=1, max_length=200, alias="scope_value")
    ],
) -> object:
    """Return the exact active allocation for one Portfolio scope.

    Returns:
        Portfolio-owned active allocation envelope.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If Portfolio reports an unexpected runtime failure.
    """
    require_human_permission(auth, "portfolio:read")
    try:
        return source("status", portfolio_id, {scope_key: scope_value}, auth)
    except RuntimeError as error:
        if str(error) != "PORTFOLIO_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get("/{portfolio_id}/history", response_model=None)
def _get_history(
    portfolio_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
) -> object:
    """Return immutable Portfolio allocation history in activation order.

    Returns:
        Portfolio-owned allocation history envelope.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If Portfolio reports an unexpected runtime failure.
    """
    require_human_permission(auth, "portfolio:read")
    try:
        return source("history", portfolio_id, auth)
    except RuntimeError as error:
        if str(error) != "PORTFOLIO_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


__all__ = ("router",)
