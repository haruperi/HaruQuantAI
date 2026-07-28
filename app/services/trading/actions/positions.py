"""Route-aware public position action verbs."""

# ruff: noqa: BLE001 - public boundaries normalize every failure.

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.services.trading.actions._shared import authority_id, require_action
from app.services.trading.actions.orders import _execute_request
from app.services.trading.contracts import (
    TradingError,
    TradingRequest,
)
from app.utils import get_logger

type StandardResponse[T] = Any

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.trading.actions.dependencies import TradingDependencies


def _current_position_quantity(
    request: TradingRequest, deps: TradingDependencies
) -> Decimal:
    """Return the exact addressed Data position quantity.

    Args:
        request: Canonical position request.
        deps: Explicit action dependencies.

    Returns:
        Current exact position quantity.

    Raises:
        TradingError: If the position identity is absent or mismatched.
    """
    logger.debug("Reading addressed Trading position quantity")
    target = request.target_broker_position_id
    if target is None:
        raise TradingError("INVALID_REQUEST", "Position target is required")
    projection = deps.store.load_projection(
        (request.route, request.account_id, authority_id(request))
    )
    if projection is None:
        raise TradingError(
            "RECONCILIATION_REQUIRED", "Trading position state is absent"
        )
    targets = {
        broker_target
        for identity, facts in projection.positions.items()
        for broker_target in (
            facts.get("broker_position_id", identity)
            if isinstance(facts, dict)
            else None,
        )
        if isinstance(broker_target, str)
    }
    if target not in targets:
        raise TradingError(
            "RECONCILIATION_REQUIRED", "Broker position target is not in Trading state"
        )
    snapshot = deps.account_state_source(request)
    for position in snapshot.positions:
        if position.position_id == target:
            if request.symbol is not None and position.symbol != request.symbol:
                raise TradingError("SCOPE_MISMATCH", "Position symbol mismatches")
            return position.quantity
    raise TradingError("RECONCILIATION_REQUIRED", "Position target is unavailable")


async def _close_position_value(
    request: TradingRequest, deps: TradingDependencies
) -> StandardResponse[object]:
    """Close an addressed position fully or partially.

    Args:
        request: Canonical close request.
        deps: Explicit action dependencies.

    Returns:
        Route-authority outcome.

    Raises:
        TradingError: If position identity or close quantity is invalid.
    """
    logger.info("Closing governed Trading position")
    require_action(request, "close_position")
    current = _current_position_quantity(request, deps)
    if request.quantity is None or request.quantity > current:
        raise TradingError("VALIDATION_FAILED", "Close quantity exceeds position")
    return await _execute_request(request, deps)


async def _modify_position_value(
    request: TradingRequest, deps: TradingDependencies
) -> StandardResponse[object]:
    """Modify only Risk-approved stop fields for one position.

    Args:
        request: Canonical modify-position request.
        deps: Explicit action dependencies.

    Returns:
        Route-authority outcome.

    Raises:
        TradingError: If mutable-field authority is missing or exceeded.
    """
    logger.info("Modifying governed Trading position")
    require_action(request, "modify_position")
    _current_position_quantity(request, deps)
    verdict = deps.action_policy_source(request)
    if verdict is None or not verdict.allowed or verdict.expires_at <= deps.clock():
        raise TradingError("PERMISSION_DENIED", "Action policy is unavailable")
    permitted = tuple(
        field.strip()
        for field in verdict.scope.get("mutable_fields", "").split(",")
        if field.strip()
    )
    supplied = {
        field
        for field, value in (
            ("stop_loss", request.stop_loss),
            ("take_profit", request.take_profit),
        )
        if value is not None
    }
    if not supplied or not supplied.issubset(set(permitted)):
        raise TradingError("SCOPE_MISMATCH", "Position mutation exceeds policy")
    return await _execute_request(request, deps)


async def _reduce_exposure_value(
    request: TradingRequest, deps: TradingDependencies
) -> StandardResponse[object]:
    """Execute exactly one Risk-approved exposure reduction.

    Args:
        request: Canonical reduce-only request.
        deps: Explicit action dependencies.

    Returns:
        Route-authority outcome.

    Raises:
        TradingError: If reduction would exceed current exposure.
    """
    logger.info("Reducing governed Trading exposure")
    require_action(request, "reduce_exposure")
    current = _current_position_quantity(request, deps)
    if request.quantity is None or request.quantity <= 0 or request.quantity > current:
        raise TradingError("VALIDATION_FAILED", "Reduction cannot increase exposure")
    return await _execute_request(request, deps)


async def close_position(
    request: TradingRequest, deps: TradingDependencies
) -> StandardResponse[object]:
    """Close a governed position and return a standard response.

    Returns:
        Standard response containing the raw receipt or an error.
    """
    try:
        return await _close_position_value(request, deps)
    except Exception as error:
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(error, {"request_id": request.request_id})


async def modify_position(
    request: TradingRequest, deps: TradingDependencies
) -> StandardResponse[object]:
    """Modify a governed position and return a standard response.

    Returns:
        Standard response containing the raw receipt or an error.
    """
    try:
        return await _modify_position_value(request, deps)
    except Exception as error:
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(error, {"request_id": request.request_id})


async def reduce_exposure(
    request: TradingRequest, deps: TradingDependencies
) -> StandardResponse[object]:
    """Reduce governed exposure and return a standard response.

    Returns:
        Standard response containing the raw receipt or an error.
    """
    try:
        return await _reduce_exposure_value(request, deps)
    except Exception as error:
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(error, {"request_id": request.request_id})


__all__ = ["close_position", "modify_position", "reduce_exposure"]
