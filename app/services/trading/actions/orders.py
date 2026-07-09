"""Platform-independent order action primitives.

This module implements ``buy``/``sell`` market order intents, pending-order
intents (``buy_limit``/``sell_limit``/``buy_stop``/``sell_stop``), pending
order mutation (``order_modify``/``order_delete``), and OCO/bracket group
submission (``submit_oco_group``). Every action runs local schema validation
(``actions/validation.py``) first, matching step 1 of the canonical 16-step
execution path (TRD-FR-025):

1. Local schema validation (``actions/validation.py``) -- implemented here.
2-16. Compliance, promotion, session, kill-switch, approval, risk, turbulence,
   readiness, clock-drift, idempotency, concurrency, reconciliation, audit,
   adapter-permission, and dispatch steps -- evaluated by the injected
   :class:`~app.services.trading.actions._common.LiveGatePipeline` seam,
   wired by the future ``gates/pipeline.py`` unit for ``route="live"``.

Until that pipeline is injected, every action fails closed to a
``packaged_only`` response.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.trading.actions._common import (
    TradingActionDependencies,
    dispatch_or_package,
    package_request,
)
from app.services.trading.actions.validation import (
    OrderIntent,
    OrderSide,
    OrderType,
    OrderValidationContext,
    validate_order_request,
)
from app.services.trading.contracts import (
    JsonObject,
    JsonValue,
    MutationCapability,
    PromotionStage,
    QuoteSnapshot,
    TimeInForce,
    TradingAction,
    TradingResponseEnvelope,
    TradingRoute,
)
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger

MIN_OCO_GROUP_SIZE = 2


def _validate_and_package(
    intent: OrderIntent,
    *,
    context: OrderValidationContext,
    deps: TradingActionDependencies,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    action: TradingAction,
    magic_number: int | None,
    comment: str | None,
    quote_snapshot: QuoteSnapshot | None,
    oco_group_id: str | None = None,
    linked_order_ids: tuple[str, ...] = (),
) -> TradingResponseEnvelope:
    """Validate an order intent and package it into a request envelope.

    Args:
        intent: Local order parameter intent.
        context: Evidence bundle required to validate the intent.
        deps: Shared trading action dependencies.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        action: Trading action to package.
        magic_number: Optional strategy magic number.
        comment: Optional order comment.
        quote_snapshot: Quote evidence, mandatory for live mutations.
        oco_group_id: Optional One-Cancels-Other group identifier.
        linked_order_ids: Optional sibling order identifiers.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Validating and packaging {} for {}.", action.value, intent.symbol)
    result = validate_order_request(intent, context=context)
    payload: JsonObject = {
        "intent": result.normalized_intent,
        "validation_audit": result.audit,
        "magic_number": magic_number,
        "comment": comment,
    }
    request = package_request(
        action=action,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        symbol=intent.symbol,
        payload=payload,
        quote_snapshot=quote_snapshot,
        oco_group_id=oco_group_id,
        linked_order_ids=linked_order_ids,
    )
    return dispatch_or_package(request=request, deps=deps)


def buy(
    *,
    symbol: str,
    volume: Decimal,
    sl: Decimal | None = None,
    tp: Decimal | None = None,
    deviation_points: int | None = None,
    magic_number: int | None = None,
    comment: str | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    context: OrderValidationContext,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Formulate a buy market order intent (TRD-FR-021).

    Args:
        symbol: Instrument symbol.
        volume: Requested order volume.
        sl: Optional stop-loss price.
        tp: Optional take-profit price.
        deviation_points: Maximum acceptable slippage in points.
        magic_number: Optional strategy magic number.
        comment: Optional order comment.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        context: Evidence bundle required to validate the intent.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Formulating buy market order for {}.", symbol)
    intent = OrderIntent(
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        volume=volume,
        sl=sl,
        tp=tp,
        max_slippage_points=deviation_points,
    )
    return _validate_and_package(
        intent,
        context=context,
        deps=deps,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        action=TradingAction.SUBMIT_ORDER,
        magic_number=magic_number,
        comment=comment,
        quote_snapshot=quote_snapshot,
    )


def sell(
    *,
    symbol: str,
    volume: Decimal,
    sl: Decimal | None = None,
    tp: Decimal | None = None,
    deviation_points: int | None = None,
    magic_number: int | None = None,
    comment: str | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    context: OrderValidationContext,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Formulate a sell market order intent (TRD-FR-021).

    Args:
        symbol: Instrument symbol.
        volume: Requested order volume.
        sl: Optional stop-loss price.
        tp: Optional take-profit price.
        deviation_points: Maximum acceptable slippage in points.
        magic_number: Optional strategy magic number.
        comment: Optional order comment.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        context: Evidence bundle required to validate the intent.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Formulating sell market order for {}.", symbol)
    intent = OrderIntent(
        symbol=symbol,
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        volume=volume,
        sl=sl,
        tp=tp,
        max_slippage_points=deviation_points,
    )
    return _validate_and_package(
        intent,
        context=context,
        deps=deps,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        action=TradingAction.SUBMIT_ORDER,
        magic_number=magic_number,
        comment=comment,
        quote_snapshot=quote_snapshot,
    )


def _pending_order(
    *,
    symbol: str,
    side: OrderSide,
    order_type: OrderType,
    volume: Decimal,
    price: Decimal,
    stop_limit_price: Decimal | None,
    sl: Decimal | None,
    tp: Decimal | None,
    tif: TimeInForce,
    expiration: str | None,
    magic_number: int | None,
    comment: str | None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    context: OrderValidationContext,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None,
) -> TradingResponseEnvelope:
    """Formulate a pending order intent (TRD-FR-022).

    Args:
        symbol: Instrument symbol.
        side: Trade direction.
        order_type: Pending order type classification.
        volume: Requested order volume.
        price: Pending order trigger price.
        stop_limit_price: Stop-limit resting price, if applicable.
        sl: Optional stop-loss price.
        tp: Optional take-profit price.
        tif: Requested time-in-force.
        expiration: Expiration timestamp, required when ``tif`` is ``GTD``.
        magic_number: Optional strategy magic number.
        comment: Optional order comment.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        context: Evidence bundle required to validate the intent.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Formulating pending {} order for {}.", order_type.value, symbol)
    intent = OrderIntent(
        symbol=symbol,
        side=side,
        order_type=order_type,
        volume=volume,
        price=price,
        stop_limit_price=stop_limit_price,
        sl=sl,
        tp=tp,
        tif=tif,
        expiration=expiration,
    )
    return _validate_and_package(
        intent,
        context=context,
        deps=deps,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        action=TradingAction.SUBMIT_ORDER,
        magic_number=magic_number,
        comment=comment,
        quote_snapshot=quote_snapshot,
    )


def buy_limit(
    *,
    symbol: str,
    volume: Decimal,
    price: Decimal,
    sl: Decimal | None = None,
    tp: Decimal | None = None,
    tif: TimeInForce = TimeInForce.GTC,
    expiration: str | None = None,
    magic_number: int | None = None,
    comment: str | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    context: OrderValidationContext,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Formulate a buy-limit pending order intent (TRD-FR-022).

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Formulating buy_limit for {}.", symbol)
    return _pending_order(
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        volume=volume,
        price=price,
        stop_limit_price=None,
        sl=sl,
        tp=tp,
        tif=tif,
        expiration=expiration,
        magic_number=magic_number,
        comment=comment,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        context=context,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )


def sell_limit(
    *,
    symbol: str,
    volume: Decimal,
    price: Decimal,
    sl: Decimal | None = None,
    tp: Decimal | None = None,
    tif: TimeInForce = TimeInForce.GTC,
    expiration: str | None = None,
    magic_number: int | None = None,
    comment: str | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    context: OrderValidationContext,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Formulate a sell-limit pending order intent (TRD-FR-022).

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Formulating sell_limit for {}.", symbol)
    return _pending_order(
        symbol=symbol,
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        volume=volume,
        price=price,
        stop_limit_price=None,
        sl=sl,
        tp=tp,
        tif=tif,
        expiration=expiration,
        magic_number=magic_number,
        comment=comment,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        context=context,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )


def buy_stop(
    *,
    symbol: str,
    volume: Decimal,
    price: Decimal,
    stop_limit_price: Decimal | None = None,
    sl: Decimal | None = None,
    tp: Decimal | None = None,
    tif: TimeInForce = TimeInForce.GTC,
    expiration: str | None = None,
    magic_number: int | None = None,
    comment: str | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    context: OrderValidationContext,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Formulate a buy-stop pending order intent (TRD-FR-022).

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Formulating buy_stop for {}.", symbol)
    order_type = (
        OrderType.STOP_LIMIT if stop_limit_price is not None else OrderType.STOP
    )
    return _pending_order(
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=order_type,
        volume=volume,
        price=price,
        stop_limit_price=stop_limit_price,
        sl=sl,
        tp=tp,
        tif=tif,
        expiration=expiration,
        magic_number=magic_number,
        comment=comment,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        context=context,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )


def sell_stop(
    *,
    symbol: str,
    volume: Decimal,
    price: Decimal,
    stop_limit_price: Decimal | None = None,
    sl: Decimal | None = None,
    tp: Decimal | None = None,
    tif: TimeInForce = TimeInForce.GTC,
    expiration: str | None = None,
    magic_number: int | None = None,
    comment: str | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    context: OrderValidationContext,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Formulate a sell-stop pending order intent (TRD-FR-022).

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Formulating sell_stop for {}.", symbol)
    order_type = (
        OrderType.STOP_LIMIT if stop_limit_price is not None else OrderType.STOP
    )
    return _pending_order(
        symbol=symbol,
        side=OrderSide.SELL,
        order_type=order_type,
        volume=volume,
        price=price,
        stop_limit_price=stop_limit_price,
        sl=sl,
        tp=tp,
        tif=tif,
        expiration=expiration,
        magic_number=magic_number,
        comment=comment,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        context=context,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )


def order_modify(
    *,
    ticket: str,
    price: Decimal | None = None,
    sl: Decimal | None = None,
    tp: Decimal | None = None,
    expected_state_version: int | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    symbol: str | None,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Package a pending order mutation while preserving order identity.

    Preserves the order ticket, an optional expected state version for
    version-gated amendments (TRD-FR-129, resolved by the future
    ``execution/state_machine.py`` unit), and idempotency/side-effect
    classification (TRD-FR-023).

    Args:
        ticket: Local or broker order identifier.
        price: Optional new trigger price.
        sl: Optional new stop-loss price.
        tp: Optional new take-profit price.
        expected_state_version: Optional expected order state version.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        symbol: Optional target symbol.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.

    Raises:
        TradingMappedError: If ``ticket`` is blank.
    """
    logger.info("Packaging order_modify for ticket {}.", ticket)
    if not ticket.strip():
        raise TradingMappedError(
            "ticket must be non-empty for order_modify.",
            code="INVALID_INPUT",
        )
    payload: JsonObject = {
        "ticket": ticket,
        "price": str(price) if price is not None else None,
        "sl": str(sl) if sl is not None else None,
        "tp": str(tp) if tp is not None else None,
        "expected_state_version": expected_state_version,
    }
    request = package_request(
        action=TradingAction.MODIFY_ORDER,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        symbol=symbol,
        payload=payload,
        quote_snapshot=quote_snapshot,
    )
    return dispatch_or_package(request=request, deps=deps)


def order_delete(
    *,
    ticket: str,
    expected_state_version: int | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    symbol: str | None,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Package a pending order cancellation (TRD-FR-023).

    Args:
        ticket: Local or broker order identifier.
        expected_state_version: Optional expected order state version.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        symbol: Optional target symbol.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.

    Raises:
        TradingMappedError: If ``ticket`` is blank.
    """
    logger.info("Packaging order_delete for ticket {}.", ticket)
    if not ticket.strip():
        raise TradingMappedError(
            "ticket must be non-empty for order_delete.",
            code="INVALID_INPUT",
        )
    payload: JsonObject = {
        "ticket": ticket,
        "expected_state_version": expected_state_version,
    }
    request = package_request(
        action=TradingAction.CANCEL_ORDER,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        symbol=symbol,
        payload=payload,
        quote_snapshot=quote_snapshot,
    )
    return dispatch_or_package(request=request, deps=deps)


def submit_oco_group(
    orders: tuple[OrderIntent, ...],
    *,
    contexts: tuple[OrderValidationContext, ...],
    oco_group_id: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Submit an OCO/bracket order group with consistent group parameters.

    Validates group parameter consistency (matching symbols, at least two
    distinct legs) and every leg's local order parameters before dispatch
    (TRD-FR-024, TRD-FR-009).

    Args:
        orders: Order intents belonging to the same OCO/bracket group.
        contexts: Evidence bundle for each order intent, positionally paired.
        oco_group_id: Shared One-Cancels-Other group identifier.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.

    Raises:
        TradingMappedError: If the group has fewer than two legs, a blank
            group ID, or a symbol/context count mismatch.
    """
    logger.info("Submitting OCO group {} with {} legs.", oco_group_id, len(orders))
    if not oco_group_id.strip():
        raise TradingMappedError(
            "oco_group_id must be non-empty for submit_oco_group.",
            code="INVALID_INPUT",
        )
    if len(orders) < MIN_OCO_GROUP_SIZE:
        raise TradingMappedError(
            "An OCO/bracket group requires at least two order legs.",
            code="INVALID_INPUT",
            details={"leg_count": len(orders)},
        )
    if len(orders) != len(contexts):
        raise TradingMappedError(
            "Each OCO/bracket order leg requires a matching validation context.",
            code="INVALID_INPUT",
            details={"orders": len(orders), "contexts": len(contexts)},
        )
    symbol = orders[0].symbol
    if any(order.symbol != symbol for order in orders):
        raise TradingMappedError(
            "OCO/bracket group legs must share the same symbol.",
            code="INVALID_INPUT",
            details={"symbol": symbol},
        )

    normalized_legs: list[JsonValue] = []
    combined_audit: JsonObject = {}
    for index, (order, context) in enumerate(zip(orders, contexts, strict=True)):
        result = validate_order_request(order, context=context)
        normalized_legs.append(result.normalized_intent)
        combined_audit[f"leg_{index}"] = result.audit

    linked_order_ids = tuple(
        f"{oco_group_id}-leg-{index}" for index in range(len(orders))
    )
    payload: JsonObject = {"legs": normalized_legs, "validation_audit": combined_audit}
    request = package_request(
        action=TradingAction.SUBMIT_ORDER,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        symbol=symbol,
        payload=payload,
        quote_snapshot=quote_snapshot,
        oco_group_id=oco_group_id,
        linked_order_ids=linked_order_ids,
    )
    return dispatch_or_package(request=request, deps=deps)
