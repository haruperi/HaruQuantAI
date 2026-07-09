"""Platform-independent position lifecycle action primitives.

This module implements ``position_open``/``position_close``/``position_modify``
position lifecycle controls, supporting Close-By-Ticket and Close-By-Symbol
semantics under netting and hedging account modes, plus ``reduce_exposure``
for approved partial-close/volume-reduction commands (TRD-FR-026, TRD-FR-027).

``reduce_exposure`` packages a pre-approved risk decision; it never computes
sizing or exposure thresholds itself, which remains exclusively in the risk
module.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from app.services.trading.actions._common import (
    TradingActionDependencies,
    dispatch_or_package,
    package_request,
)
from app.services.trading.actions.orders import buy, sell
from app.services.trading.actions.validation import OrderSide, OrderValidationContext
from app.services.trading.contracts import (
    JsonObject,
    MutationCapability,
    PromotionStage,
    QuoteSnapshot,
    TradingAction,
    TradingResponseEnvelope,
    TradingRoute,
)
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger


class NettingMode(StrEnum):
    """Account position-netting mode."""

    NETTING = "netting"
    HEDGING = "hedging"


class PositionCloseMode(StrEnum):
    """Resolved close addressing mode."""

    BY_TICKET = "by_ticket"
    BY_SYMBOL = "by_symbol"


class ReduceExposureScope(StrEnum):
    """Approved scope for an exposure reduction command."""

    POSITION = "position"
    SYMBOL = "symbol"
    ACCOUNT = "account"


def position_open(
    *,
    symbol: str,
    side: OrderSide,
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
    """Open a position via a validated market order intent (TRD-FR-026).

    Args:
        symbol: Instrument symbol.
        side: Trade direction.
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
    logger.info("Opening position for {} side {}.", symbol, side.value)
    action_fn = buy if side is OrderSide.BUY else sell
    return action_fn(
        symbol=symbol,
        volume=volume,
        sl=sl,
        tp=tp,
        deviation_points=deviation_points,
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


def position_close(
    *,
    netting_mode: NettingMode,
    ticket: str | None = None,
    symbol: str | None = None,
    volume: Decimal | None = None,
    deviation_points: int | None = None,
    comment: str | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Package a position close by ticket or by symbol (TRD-FR-026).

    Hedging accounts may hold multiple positions per symbol, so a ``ticket``
    is required in ``hedging`` mode. Netting accounts hold at most one
    position per symbol, so ``symbol`` alone is sufficient.

    Args:
        netting_mode: Account netting or hedging mode.
        ticket: Position ticket for Close-By-Ticket addressing.
        symbol: Instrument symbol for Close-By-Symbol addressing.
        volume: Optional partial-close volume. Omit for a full close.
        deviation_points: Maximum acceptable slippage in points.
        comment: Optional close comment.
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
        TradingMappedError: If neither ticket nor symbol is supplied, or a
            hedging-mode close omits the required ticket.
    """
    logger.info("Packaging position_close for netting_mode {}.", netting_mode.value)
    if ticket is None and symbol is None:
        raise TradingMappedError(
            "Either ticket or symbol must be supplied for position_close.",
            code="INVALID_INPUT",
        )
    if netting_mode is NettingMode.HEDGING and ticket is None:
        raise TradingMappedError(
            "Hedging-mode position_close requires an explicit ticket.",
            code="INVALID_INPUT",
        )
    close_mode = (
        PositionCloseMode.BY_TICKET
        if ticket is not None
        else PositionCloseMode.BY_SYMBOL
    )
    payload: JsonObject = {
        "close_mode": close_mode.value,
        "netting_mode": netting_mode.value,
        "ticket": ticket,
        "symbol": symbol,
        "volume": str(volume) if volume is not None else None,
        "deviation_points": deviation_points,
        "comment": comment,
    }
    request = package_request(
        action=TradingAction.CLOSE_POSITION,
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


def position_modify(
    *,
    position_id: str,
    sl: Decimal | None = None,
    tp: Decimal | None = None,
    expected_state_version: int | None = None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    symbol: str | None = None,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Package a position SL/TP mutation (TRD-FR-026).

    Args:
        position_id: Local or broker position identifier.
        sl: Optional new stop-loss price.
        tp: Optional new take-profit price.
        expected_state_version: Optional expected position state version.
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
        TradingMappedError: If ``position_id`` is blank.
    """
    logger.info("Packaging position_modify for position {}.", position_id)
    if not position_id.strip():
        raise TradingMappedError(
            "position_id must be non-empty for position_modify.",
            code="INVALID_INPUT",
        )
    payload: JsonObject = {
        "position_id": position_id,
        "sl": str(sl) if sl is not None else None,
        "tp": str(tp) if tp is not None else None,
        "expected_state_version": expected_state_version,
    }
    request = package_request(
        action=TradingAction.MODIFY_POSITION,
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


def reduce_exposure(
    *,
    scope: ReduceExposureScope,
    target: str,
    volume: Decimal,
    risk_decision_id: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Package a partial-close/volume-reduction command (TRD-FR-027).

    Packages a pre-approved risk decision's exposure reduction. This
    function does not compute sizing or execution thresholds; ``volume``
    must already reflect the approved risk decision.

    Args:
        scope: Approved reduction scope (position, symbol, or account).
        target: Scope target identifier (position ID, symbol, or account ID).
        volume: Pre-approved reduction volume.
        risk_decision_id: Identifier of the validated risk decision
            authorizing this reduction.
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
        TradingMappedError: If ``target`` or ``risk_decision_id`` is blank,
            or ``volume`` is not positive.
    """
    logger.info(
        "Packaging reduce_exposure for scope {} target {}.", scope.value, target
    )
    if not target.strip():
        raise TradingMappedError(
            "target must be non-empty for reduce_exposure.",
            code="INVALID_INPUT",
        )
    if not risk_decision_id.strip():
        raise TradingMappedError(
            "risk_decision_id must be non-empty for reduce_exposure.",
            code="INVALID_INPUT",
        )
    if volume <= 0:
        raise TradingMappedError(
            "volume must be positive for reduce_exposure.",
            code="INVALID_INPUT",
        )
    payload: JsonObject = {
        "scope": scope.value,
        "target": target,
        "volume": str(volume),
        "risk_decision_id": risk_decision_id,
    }
    symbol = target if scope is ReduceExposureScope.SYMBOL else None
    request = package_request(
        action=TradingAction.REDUCE_EXPOSURE,
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
