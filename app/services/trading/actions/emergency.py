"""Explicit gated Trading bulk cancellation and closure workflows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, cast

from pydantic import ValidationError as PydanticValidationError

from app.services.risk.contracts import DecisionState
from app.services.trading.actions._shared import authority_id, require_action
from app.services.trading.actions.orders import cancel_order
from app.services.trading.actions.positions import close_position
from app.services.trading.contracts import (
    StandardTradingEnvelope,
    TradingError,
    TradingRequest,
)
from app.services.trading.contracts.errors import _redacted_envelope_data
from app.utils import logger

if TYPE_CHECKING:
    from app.services.trading.actions.dependencies import TradingDependencies
    from app.services.trading.contracts.models import JsonValue

_CANCELLABLE_STATES = frozenset({"PENDING", "ACCEPTED", "PARTIALLY_FILLED"})


def _validated_child(
    request: TradingRequest,
    updates: Mapping[str, object],
) -> TradingRequest:
    """Construct and fully validate one derived bulk child request.

    Args:
        request: Canonical parent bulk request.
        updates: Exact child-specific field replacements.

    Returns:
        Fully validated child request.

    Raises:
        TradingError: If the derived combination violates the request contract.
    """
    logger.debug("Validating derived Trading emergency child request")
    material = {**request.model_dump(mode="python"), **dict(updates)}
    try:
        return TradingRequest.model_validate(material)
    except PydanticValidationError as error:
        raise TradingError(
            "INVALID_REQUEST", "Derived emergency child request is invalid"
        ) from error


def _bind_child_authority(
    child: TradingRequest,
    deps: TradingDependencies,
) -> TradingRequest:
    """Bind one paper/live child to exact current Risk authorities.

    Args:
        child: Structurally valid derived child request.
        deps: Explicit action dependencies.

    Returns:
        Revalidated child carrying exact Risk decision/token and policy references.

    Raises:
        TradingError: If per-child Risk or action-policy authority is invalid.
    """
    logger.debug("Binding Trading emergency child to Risk authority")
    if child.route.value == "sim":
        return child
    now = deps.clock()
    decision = deps.child_risk_decision_source(child)
    policy = deps.action_policy_source(child)
    token = None if decision is None else decision.token
    if (
        decision is None
        or decision.state is not DecisionState.APPROVE
        or decision.intent_id is None
        or decision.approved_size != child.quantity
        or decision.expires_at <= now
        or token is None
        or token.decision_id != decision.decision_id
        or token.action != child.action
        or token.request_id != child.request_id
        or token.workflow_id != child.workflow_id
        or token.correlation_id != child.correlation_id
        or token.expires_at <= now
        or policy is None
        or not policy.allowed
        or policy.action != child.action
        or policy.decision_id != decision.decision_id
        or policy.request_id != child.request_id
        or policy.workflow_id != child.workflow_id
        or policy.correlation_id != child.correlation_id
        or policy.scope.get("account_id") != child.account_id
        or policy.expires_at <= now
    ):
        raise TradingError(
            "PERMISSION_DENIED", "Per-child emergency authority is invalid"
        )
    return _validated_child(
        child,
        {
            "intent_id": decision.intent_id,
            "risk_decision_id": decision.decision_id,
            "approval_token_ref": token.token_id,
            "action_policy_verdict_id": policy.verdict_id,
        },
    )


def _max_children(request: TradingRequest, deps: TradingDependencies) -> int:
    """Read the positive Risk-owned bulk side-effect ceiling.

    Args:
        request: Canonical bulk request.
        deps: Explicit action dependencies.

    Returns:
        Positive maximum child count.

    Raises:
        TradingError: If policy scope is absent or malformed.
    """
    logger.debug("Reading Risk-owned Trading bulk child limit")
    verdict = deps.action_policy_source(request)
    if verdict is None or not verdict.allowed or verdict.expires_at <= deps.clock():
        raise TradingError("PERMISSION_DENIED", "Bulk action policy is unavailable")
    try:
        value = int(verdict.scope.get("max_children", ""))
    except ValueError as error:
        raise TradingError(
            "PERMISSION_DENIED", "Bulk child limit is malformed"
        ) from error
    if value <= 0 or str(value) != verdict.scope.get("max_children"):
        raise TradingError("PERMISSION_DENIED", "Bulk child limit must be positive")
    return value


def _bulk_envelope(
    request: TradingRequest,
    results: list[dict[str, JsonValue]],
    skipped: list[dict[str, JsonValue]],
) -> StandardTradingEnvelope:
    """Package all child and skipped bulk outcomes.

    Args:
        request: Source bulk request.
        results: Ordered child outcomes.
        skipped: Ordered non-mutated authority facts.

    Returns:
        Complete or partial bulk result.
    """
    logger.debug("Packaging complete Trading bulk action evidence")
    partial = bool(skipped) or any(
        item.get("status") in {"error", "unknown_outcome"} for item in results
    )
    data = _redacted_envelope_data(
        {
            "results": cast("JsonValue", results),
            "skipped": cast("JsonValue", skipped),
        }
    )
    return StandardTradingEnvelope(
        status="partial" if partial else "success",
        message="Trading bulk action retained every child result",
        data=data,
        errors=(),
        warnings=({"code": "PARTIAL_COMPLETION"},) if partial else (),
        audit_metadata={
            "operation": request.action,
            "request_id": request.request_id,
            "correlation_id": request.correlation_id,
            "redaction_applied": True,
        },
    )


async def cancel_all_orders(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Cancel every eligible order through the normal cancellation path.

    Args:
        request: Canonical bulk-cancel request.
        deps: Explicit action dependencies.

    Returns:
        Every child result and every skipped order.

    Raises:
        TradingError: If policy or the child ceiling blocks execution.
    """
    logger.warning("Executing governed Trading mass cancellation")
    require_action(request, "cancel_all_orders")
    snapshot = deps.account_state_source(request)
    limit = _max_children(request, deps)
    projection = deps.store.load_projection(
        (request.route, request.account_id, authority_id(request))
    )
    if projection is None:
        raise TradingError(
            "RECONCILIATION_REQUIRED", "Bulk cancellation requires Trading state"
        )
    state_targets = {
        target
        for identity, facts in projection.orders.items()
        for target in (
            facts.get("broker_order_id", identity) if isinstance(facts, dict) else None,
        )
        if isinstance(target, str)
    }
    results: list[dict[str, JsonValue]] = []
    skipped: list[dict[str, JsonValue]] = []
    if len(snapshot.orders) > limit:
        raise TradingError("GATE_BLOCKED", "Bulk cancellation exceeds policy ceiling")
    for order in snapshot.orders:
        if order.order_id not in state_targets:
            results.append(
                {
                    "order_id": order.order_id,
                    "status": "error",
                    "code": "RECONCILIATION_REQUIRED",
                }
            )
            continue
        if order.state not in _CANCELLABLE_STATES:
            skipped.append({"order_id": order.order_id, "state": order.state})
            continue
        child = _validated_child(
            request,
            {
                "action": "cancel_order",
                "request_id": f"{request.request_id}:{order.order_id}",
                "causation_id": request.request_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
                "price": order.price
                if request.order_type == "LIMIT"
                else request.price,
                "order_id": order.order_id,
                "target_broker_order_id": order.order_id,
                "expected_version": projection.version,
                "idempotency_key": f"{request.idempotency_key}:{order.order_id}",
            },
        )
        try:
            child = _bind_child_authority(child, deps)
            outcome = await cancel_order(child, deps)
            results.append(
                {
                    "order_id": order.order_id,
                    "status": outcome.status,
                    "data": outcome.data,
                }
            )
        except TradingError as error:
            logger.warning("Bulk cancellation child failed: %s", error.code)
            results.append(
                {"order_id": order.order_id, "status": "error", "code": error.code}
            )
    return _bulk_envelope(request, results, skipped)


async def close_all_positions(
    request: TradingRequest, deps: TradingDependencies
) -> StandardTradingEnvelope:
    """Close every position through the normal position-close path.

    Args:
        request: Canonical bulk-close request.
        deps: Explicit action dependencies.

    Returns:
        Every child close result.

    Raises:
        TradingError: If policy or the child ceiling blocks execution.
    """
    logger.warning("Executing governed Trading mass position closure")
    require_action(request, "close_all_positions")
    snapshot = deps.account_state_source(request)
    limit = _max_children(request, deps)
    projection = deps.store.load_projection(
        (request.route, request.account_id, authority_id(request))
    )
    if projection is None:
        raise TradingError(
            "RECONCILIATION_REQUIRED", "Bulk closure requires Trading state"
        )
    state_targets = {
        target
        for identity, facts in projection.positions.items()
        for target in (
            facts.get("broker_position_id", identity)
            if isinstance(facts, dict)
            else None,
        )
        if isinstance(target, str)
    }
    if len(snapshot.positions) > limit:
        raise TradingError("GATE_BLOCKED", "Bulk closure exceeds policy ceiling")
    results: list[dict[str, JsonValue]] = []
    for position in snapshot.positions:
        if position.position_id not in state_targets:
            results.append(
                {
                    "position_id": position.position_id,
                    "status": "error",
                    "code": "RECONCILIATION_REQUIRED",
                }
            )
            continue
        side = "SELL" if position.side == "LONG" else "BUY"
        child = _validated_child(
            request,
            {
                "action": "close_position",
                "request_id": f"{request.request_id}:{position.position_id}",
                "causation_id": request.request_id,
                "symbol": position.symbol,
                "side": side,
                "quantity": position.quantity,
                "position_id": position.position_id,
                "target_broker_position_id": position.position_id,
                "expected_version": projection.version,
                "idempotency_key": f"{request.idempotency_key}:{position.position_id}",
            },
        )
        try:
            child = _bind_child_authority(child, deps)
            outcome = await close_position(child, deps)
            results.append(
                {
                    "position_id": position.position_id,
                    "status": outcome.status,
                    "data": outcome.data,
                }
            )
        except TradingError as error:
            logger.warning("Bulk closure child failed: %s", error.code)
            results.append(
                {
                    "position_id": position.position_id,
                    "status": "error",
                    "code": error.code,
                }
            )
    return _bulk_envelope(request, results, [])


__all__ = ["cancel_all_orders", "close_all_positions"]
