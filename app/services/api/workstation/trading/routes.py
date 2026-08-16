"""Authenticated Trading session and governed mutation HTTP boundaries."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    run_idempotent_write_async,
)
from app.services.api.workstation.trading.schemas import (  # noqa: TC001
    CancelAllPreflightRequest,
    CancelOrderPreflightRequest,
    OrderPreflightRequest,
    TradingMutationRequest,
)
from app.utils import generate_id

type AuthContext = Any
type _SessionSource = Callable[[str, str, str, AuthContext], object | None]
type _MutationSource = Callable[[str, object, AuthContext], Awaitable[object]]
type _PreflightSource = Callable[[object, AuthContext], Awaitable[object]]

router = APIRouter(prefix="/api/v1/trading", tags=["trading"])

# A request whose declared runtime contradicts the deployment is a caller
# error, not an outage: it is refused deterministically rather than reported
# as an unavailable dependency.
_RUNTIME_POLICY_REFUSALS = frozenset(
    {
        "TRADING_RUNTIME_PROFILE_MISMATCH",
        "TRADING_EXECUTION_ROUTE_MISMATCH",
        "TRADING_LIVE_MUTATIONS_DISABLED",
    }
)


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


def _trading_preflight_source() -> _PreflightSource:
    """Fail closed until composition injects the real Risk preflight review.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_PREFLIGHT_UNAVAILABLE",
    )


def _trading_cancel_order_preflight_source() -> _PreflightSource:
    """Fail closed until composition injects the real single-cancel Risk review.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_CANCEL_ORDER_PREFLIGHT_UNAVAILABLE",
    )


def _trading_cancel_all_preflight_source() -> _PreflightSource:
    """Fail closed until composition injects the real bulk-cancel Risk review.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="TRADING_CANCEL_ALL_PREFLIGHT_UNAVAILABLE",
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
    # Demo and live share one execution path and differ only by the
    # credentials in the composed BrokerConnectionConfig (docs/PROJECT.md
    # 2.1.9). The boundary therefore does not ban a route; it requires the
    # request to name the route this deployment is actually configured for, so
    # a demo deployment can never relay a live order even if asked.
    if body.route != settings.execution_route:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="EXECUTION_ROUTE_NOT_CONFIGURED",
        )
    if body.route == "live" and not settings.allow_live_mutations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="LIVE_MUTATIONS_DISABLED",
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
    route: Annotated[Literal["sim", "demo", "live"], Query()] = "demo",
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
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("submit_order", body, auth),
        )
    except RuntimeError as error:
        if str(error) in _RUNTIME_POLICY_REFUSALS:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/orders/preflight", response_model=None)
async def _preflight_order(
    body: OrderPreflightRequest,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PreflightSource, Depends(_trading_preflight_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Review one candidate human-initiated order through Risk's real gate.

    Produces the ``risk_decision_id``/``action_policy_verdict_id``/
    ``approval_token_ref`` a subsequent ``POST /orders`` needs — it never
    submits an order itself.

    Returns:
        The real Risk decision/verdict pair.

    Raises:
        HTTPException: If boundary governance, live routing, or evidence
            availability fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    settings = request.app.state.api_settings
    if body.route != settings.execution_route:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="EXECUTION_ROUTE_NOT_CONFIGURED",
        )
    if idempotency_key is None or idempotency_key != body.idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders/preflight",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(body, auth),
        )
    except RuntimeError as error:
        if str(error) == "MANUAL_ORDER_LIVE_NOT_CONFIGURED":
            raise HTTPException(status_code=403, detail=str(error)) from error
        if str(error) == "ACCOUNT_SNAPSHOT_UNAVAILABLE":
            raise HTTPException(status_code=503, detail=str(error)) from error
        if str(error) != "TRADING_PREFLIGHT_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/orders/cancel-all/preflight", response_model=None)
async def _preflight_cancel_all_orders(
    body: CancelAllPreflightRequest,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_PreflightSource, Depends(_trading_cancel_all_preflight_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Authorize one candidate bulk cancel-all-orders action through Risk.

    Produces the ``risk_decision_id``/``action_policy_verdict_id``/
    ``approval_token_ref`` a subsequent ``POST /orders/cancel-all`` needs — it
    never cancels an order itself.

    Returns:
        The real Risk decision/verdict pair.

    Raises:
        HTTPException: If boundary governance, live routing, or evidence
            availability fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    settings = request.app.state.api_settings
    if body.route != settings.execution_route:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="EXECUTION_ROUTE_NOT_CONFIGURED",
        )
    if idempotency_key is None or idempotency_key != body.idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders/cancel-all/preflight",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(body, auth),
        )
    except RuntimeError as error:
        if str(error) == "MANUAL_ORDER_LIVE_NOT_CONFIGURED":
            raise HTTPException(status_code=403, detail=str(error)) from error
        if str(error) == "ACCOUNT_SNAPSHOT_UNAVAILABLE":
            raise HTTPException(status_code=503, detail=str(error)) from error
        if str(error) != "TRADING_CANCEL_ALL_PREFLIGHT_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/orders/cancel-all", response_model=None)
async def _cancel_all_orders(
    body: TradingMutationRequest,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_MutationSource, Depends(_trading_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Cancel every eligible governed non-production Trading order.

    Returns:
        Trading-owned bulk mutation receipt (ordered child results and any
        skipped orders).

    Raises:
        HTTPException: If boundary governance or composition fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    _governed_preflight(body, request, idempotency_key)
    if body.action != "cancel_all_orders":
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders/cancel-all",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("cancel_all_orders", body, auth),
        )
    except RuntimeError as error:
        if str(error) in _RUNTIME_POLICY_REFUSALS:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/orders/{order_id}/preflight", response_model=None)
async def _preflight_cancel_order(
    order_id: str,
    body: CancelOrderPreflightRequest,
    request: Request,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[
        _PreflightSource, Depends(_trading_cancel_order_preflight_source)
    ],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Authorize one candidate single-order cancellation through Risk.

    Produces the ``risk_decision_id``/``action_policy_verdict_id``/
    ``approval_token_ref`` a subsequent ``DELETE /orders/{order_id}`` needs —
    it never cancels an order itself.

    Returns:
        The real Risk decision/verdict pair.

    Raises:
        HTTPException: If boundary governance, live routing, evidence
            availability, or a mismatched order id fails.
        RuntimeError: If Trading reports an unexpected runtime failure.
    """
    require_human_permission(auth, "trading:write")
    if body.target_broker_order_id != order_id:
        raise HTTPException(status_code=422, detail="TRADING_ACTION_MISMATCH")
    settings = request.app.state.api_settings
    if body.route != settings.execution_route:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="EXECUTION_ROUTE_NOT_CONFIGURED",
        )
    if idempotency_key is None or idempotency_key != body.idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    try:
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/orders/{order_id}/preflight",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(body, auth),
        )
    except RuntimeError as error:
        if str(error) == "MANUAL_ORDER_LIVE_NOT_CONFIGURED":
            raise HTTPException(status_code=403, detail=str(error)) from error
        if str(error) == "ACCOUNT_SNAPSHOT_UNAVAILABLE":
            raise HTTPException(status_code=503, detail=str(error)) from error
        if str(error) != "TRADING_CANCEL_ORDER_PREFLIGHT_UNAVAILABLE":
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
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="DELETE",
            route="/api/v1/trading/orders/{order_id}",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("cancel_order", body, auth),
        )
    except RuntimeError as error:
        if str(error) in _RUNTIME_POLICY_REFUSALS:
            raise HTTPException(status_code=422, detail=str(error)) from error
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
        return await run_idempotent_write_async(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/trading/positions/{position_id}/close",
            key=str(idempotency_key),
            request_material=body.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("close_position", body, auth),
        )
    except RuntimeError as error:
        if str(error) in _RUNTIME_POLICY_REFUSALS:
            raise HTTPException(status_code=422, detail=str(error)) from error
        if str(error) != "TRADING_MUTATIONS_UNAVAILABLE":
            raise
        raise HTTPException(status_code=503, detail=str(error)) from error


__all__ = ("router",)
