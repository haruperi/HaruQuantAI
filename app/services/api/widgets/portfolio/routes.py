"""Authenticated Portfolio HTTP boundaries.

Backend v1 exposes the complete Portfolio surface: construction, active-status
and allocation-history reads, and the governed allocation lifecycle —
activation, rollback, drift assessment, rebalance submission, and measurement
recomputation.

Every governed write delegates exactly once to the composed Portfolio
dispatcher, which in turn reaches Portfolio only through its function-only
public boundary and its allow-listed opaque handle operations. The gateway
produces no evidence, computes no weight, and decides no approval: Risk remains
the sole approval authority and Portfolio the sole activation authority.

Production capital is not banned here. Demo and live differ only by the
credentials in the composed broker configuration, so the rebalance boundary
mirrors `trading/routes.py`: it requires the request to name the route the
operator has actually selected as the account mode. Whether the change is
allowed at all is Risk's decision, not the boundary's.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.kernel.identity import generate_id
from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    run_idempotent_write,
    run_idempotent_write_async,
)
from app.services.api.widgets.portfolio.schemas import (
    PortfolioActivationRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    PortfolioConstructRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    PortfolioDefinitionRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    PortfolioDriftRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    PortfolioMeasurementRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    PortfolioRebalanceRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    PortfolioRollbackRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.services.api.widgets.settings.account_mode import resolve_execution_route

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


@router.post("/{portfolio_id}/definitions", response_model=None)
def _register_definition(
    portfolio_id: str,
    request: PortfolioDefinitionRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Register one immutable Portfolio definition version.

    Returns:
        Portfolio-owned definition envelope.

    Raises:
        HTTPException: If identity, permission, idempotency, or composition fails.
    """
    require_human_permission(auth, "portfolio:write")
    _require_matching_portfolio(portfolio_id, request.portfolio_id)
    _require_idempotency(idempotency_key)
    return _delegate(source, "register_definition", request, auth)


@router.get("/{portfolio_id}/definitions/{portfolio_version}", response_model=None)
def _get_definition(
    portfolio_id: str,
    portfolio_version: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
) -> object:
    """Read one exact immutable Portfolio definition.

    Returns:
        Portfolio-owned definition envelope.
    """
    require_human_permission(auth, "portfolio:read")
    return _delegate(source, "definition", portfolio_id, portfolio_version, auth)


def _delegate(source: _PortfolioSource, operation: str, *args: object) -> object:
    """Delegate once and translate the unavailable sentinel into HTTP 503.

    Args:
        source: Composed Portfolio operation dispatcher.
        operation: Canonical Portfolio route operation name.
        *args: Operation-specific positional inputs.

    Returns:
        Portfolio-owned standard response envelope.

    Raises:
        HTTPException: If no Portfolio dependency bundle is composed or the
            active allocation required by the operation is unavailable.
        RuntimeError: If Portfolio reports an unexpected runtime failure.
    """
    try:
        return source(operation, *args)
    except RuntimeError as error:
        if str(error) not in {
            "PORTFOLIO_RUNTIME_UNAVAILABLE",
            "PORTFOLIO_ALLOCATION_UNAVAILABLE",
        }:
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


async def _delegate_async(
    source: _PortfolioSource, operation: str, *args: object
) -> object:
    """Await one Portfolio operation and translate unavailable sentinels.

    Returns:
        The Portfolio-owned operation result.

    Raises:
        HTTPException: If Portfolio reports a known unavailable condition.
        RuntimeError: If Portfolio reports an unexpected runtime failure.
    """
    try:
        result = source(operation, *args)
        if inspect.isawaitable(result):
            return await result
        return result
    except RuntimeError as error:
        if str(error) not in {
            "PORTFOLIO_RUNTIME_UNAVAILABLE",
            "PORTFOLIO_ALLOCATION_UNAVAILABLE",
        }:
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/{portfolio_id}/activate", response_model=None)
async def _activate(
    portfolio_id: str,
    request: PortfolioActivationRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Activate one fully reviewed Portfolio allocation version.

    Returns:
        Portfolio-owned active allocation envelope.

    Raises:
        HTTPException: If authentication, authorization, idempotency, the
            portfolio identity binding, or composition fails.
    """
    require_human_permission(auth, "portfolio:activate")
    key = _require_idempotency(idempotency_key)
    _require_matching_portfolio(portfolio_id, request.construction.portfolio_id)
    return await run_idempotent_write_async(
        principal_id=auth.principal_id,
        method="POST",
        route="/api/v1/portfolio/{portfolio_id}/activate",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _delegate_async(source, "activate", request, auth, key),
    )


@router.post("/{portfolio_id}/rollback", response_model=None)
async def _rollback(
    portfolio_id: str,
    request: PortfolioRollbackRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Create one governed forward rollback version of a Portfolio.

    Returns:
        Portfolio-owned active allocation envelope.

    Raises:
        HTTPException: If authentication, authorization, idempotency, the
            portfolio identity binding, or composition fails.
    """
    require_human_permission(auth, "portfolio:activate")
    key = _require_idempotency(idempotency_key)
    _require_matching_portfolio(portfolio_id, request.construction.portfolio_id)
    return await run_idempotent_write_async(
        principal_id=auth.principal_id,
        method="POST",
        route="/api/v1/portfolio/{portfolio_id}/rollback",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _delegate_async(source, "rollback", request, auth, key),
    )


@router.post("/{portfolio_id}/drift", response_model=None)
def _assess_drift(
    portfolio_id: str,
    request: PortfolioDriftRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
) -> object:
    """Assess allocation drift for one active Portfolio scope.

    Returns:
        Portfolio-owned drift observation envelope.

    Raises:
        HTTPException: If authorization or composition fails.
    """
    require_human_permission(auth, "portfolio:read")
    return _delegate(source, "drift", portfolio_id, request, auth)


def _require_configured_execution_route(route: str) -> None:
    """Require the named execution route to be the active one.

    Mirrors ``trading/routes.py::_require_configured_route``: the route follows
    the operator-selected ``ACCOUNT_MODE``, so a request can never elect an
    execution context the operator has not selected. No separate live
    enablement flag is consulted - Risk is the sole authority on whether an
    allocation change may proceed.

    Args:
        route: Execution route named by the request.

    Raises:
        HTTPException: If the named route is not the active route.
    """
    if route != resolve_execution_route(request_id=generate_id("req")):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="EXECUTION_ROUTE_NOT_CONFIGURED",
        )


@router.post("/rebalance", response_model=None)
async def _submit_rebalance(
    request: PortfolioRebalanceRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Submit one governed Portfolio rebalance on the configured route.

    Returns:
        Portfolio-owned rebalance submission envelope.

    Raises:
        HTTPException: If authentication, authorization, execution-route
            configuration, idempotency, or composition fails.
    """
    require_human_permission(auth, "portfolio:rebalance")
    _require_configured_execution_route(request.execution_route)
    key = _require_idempotency(idempotency_key)
    return await _await_result(
        run_idempotent_write(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/portfolio/rebalance",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: _delegate(source, "rebalance", request, auth),
        )
    )


@router.post("/measurement/recompute", response_model=None)
def _recompute_measurement(
    request: PortfolioMeasurementRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PortfolioSource, Depends(_portfolio_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Recompute one Portfolio measurement from immutable Trading evidence.

    Returns:
        Portfolio-owned measurement envelope.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
    """
    require_human_permission(auth, "portfolio:write")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route="/api/v1/portfolio/measurement/recompute",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _delegate(source, "recompute", request, auth),
    )


def _require_matching_portfolio(path_id: str, body_id: str) -> None:
    """Reject a governed write whose path and body disagree on identity.

    Args:
        path_id: Portfolio identity from the request path.
        body_id: Portfolio identity carried by the construction command.

    Raises:
        HTTPException: If the two identities differ.
    """
    if path_id != body_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="PORTFOLIO_IDENTITY_MISMATCH",
        )


async def _await_result(value: object) -> object:
    """Await a Portfolio operation result that is a coroutine.

    ``submit_portfolio_rebalance`` is the one asynchronous Portfolio public
    operation, and the opaque handle dispatcher returns its coroutine unchanged.

    Args:
        value: Direct result or awaitable returned by the dispatcher.

    Returns:
        Resolved Portfolio-owned response envelope.
    """
    if inspect.isawaitable(value):
        return await value
    return value


__all__ = ("router",)
