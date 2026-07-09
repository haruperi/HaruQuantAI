"""Platform-independent emergency safety action primitives.

This module implements first-class emergency actions: ``cancel_all_orders``,
``close_all_positions``, ``flatten_account``, ``flatten_strategy``, and
``flatten_symbol`` (TRD-FR-035). Every emergency action snapshots broker
state before packaging its per-child cancel/close commands, tolerates
partial scope coverage, and returns per-child details so callers can verify
exactly which tickets were addressed (TRD-FR-036).

Actual broker dispatch of each child command is delegated to the same
:class:`~app.services.trading.actions._common.LiveGatePipeline` seam used by
``actions/orders.py``; scope reconciliation locking on unknown broker
outcomes is a future responsibility of ``reconciliation/service.py`` once
that dispatch path is wired.
"""

from __future__ import annotations

from enum import StrEnum

from app.services.trading.actions._common import (
    TradingActionDependencies,
    dispatch_or_package,
    package_request,
)
from app.services.trading.contracts import (
    JsonObject,
    MutationCapability,
    PromotionStage,
    QuoteSnapshot,
    RetrySafety,
    SideEffectMode,
    TradingAction,
    TradingMetadata,
    TradingResponseEnvelope,
    TradingRoute,
    TradingStatus,
)
from app.services.trading.info._common import broker_call, iter_or_empty, safe_attr
from app.utils.logger import logger


class EmergencyScope(StrEnum):
    """Emergency action scope classification."""

    ACCOUNT = "account"
    STRATEGY = "strategy"
    SYMBOL = "symbol"


def _matches_scope(
    raw_record: object, *, scope: EmergencyScope, target: str | None
) -> bool:
    """Return whether a raw broker record falls within the requested scope.

    Args:
        raw_record: Raw broker position or order record.
        scope: Emergency action scope classification.
        target: Scope target (strategy magic number or symbol), if any.

    Returns:
        bool: True when the record matches the requested scope.
    """
    logger.debug("Matching broker record against scope {}.", scope.value)
    if scope is EmergencyScope.ACCOUNT or target is None:
        return True
    if scope is EmergencyScope.SYMBOL:
        return safe_attr(raw_record, "symbol", "", str) == target
    if scope is EmergencyScope.STRATEGY:
        return str(safe_attr(raw_record, "magic", 0, int)) == target
    return False


def _snapshot_orders(
    *, scope: EmergencyScope, target: str | None
) -> tuple[JsonObject, ...]:
    """Snapshot working pending orders within the requested scope.

    Args:
        scope: Emergency action scope classification.
        target: Scope target (strategy magic number or symbol), if any.

    Returns:
        tuple[JsonObject, ...]: JSON-safe order snapshot entries.
    """
    logger.info("Snapshotting orders for scope {} target {}.", scope.value, target)
    raw_orders = iter_or_empty(broker_call("get_order_info"))
    return tuple(
        {
            "ticket": safe_attr(item, "ticket", "", str),
            "symbol": safe_attr(item, "symbol", "", str),
            "volume_current": safe_attr(item, "volume_current", 0.0, float),
        }
        for item in raw_orders
        if _matches_scope(item, scope=scope, target=target)
    )


def _snapshot_positions(
    *, scope: EmergencyScope, target: str | None
) -> tuple[JsonObject, ...]:
    """Snapshot open positions within the requested scope.

    Args:
        scope: Emergency action scope classification.
        target: Scope target (strategy magic number or symbol), if any.

    Returns:
        tuple[JsonObject, ...]: JSON-safe position snapshot entries.
    """
    logger.info("Snapshotting positions for scope {} target {}.", scope.value, target)
    raw_positions = iter_or_empty(broker_call("get_position_info"))
    return tuple(
        {
            "ticket": safe_attr(item, "ticket", "", str),
            "symbol": safe_attr(item, "symbol", "", str),
            "volume": safe_attr(item, "volume", 0.0, float),
        }
        for item in raw_positions
        if _matches_scope(item, scope=scope, target=target)
    )


def _child_actions(
    snapshot: tuple[JsonObject, ...], *, child_action: str
) -> tuple[JsonObject, ...]:
    """Build per-child emergency action entries pending dispatch.

    Args:
        snapshot: Pre-action broker snapshot entries.
        child_action: Child action label (``cancel_order``/``close_position``).

    Returns:
        tuple[JsonObject, ...]: Per-child action entries.
    """
    logger.debug(
        "Building {} child actions for {} entries.", child_action, len(snapshot)
    )
    return tuple(
        {
            "child_action": child_action,
            "ticket": entry["ticket"],
            "outcome": "packaged_only",
        }
        for entry in snapshot
    )


def cancel_all_orders(
    *,
    scope: EmergencyScope,
    target: str | None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Cancel all working pending orders within a scope (TRD-FR-035).

    Snapshots the pre-action order state, tolerates partial scope coverage,
    and returns per-child cancellation entries (TRD-FR-036).

    Args:
        scope: Emergency action scope classification.
        target: Scope target (strategy magic number or symbol), if any.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Cancelling all orders for scope {} target {}.", scope.value, target)
    pre_snapshot = _snapshot_orders(scope=scope, target=target)
    payload: JsonObject = {
        "scope": scope.value,
        "target": target,
        "pre_snapshot": list(pre_snapshot),
        "child_actions": list(
            _child_actions(pre_snapshot, child_action="cancel_order")
        ),
    }
    request = package_request(
        action=TradingAction.CANCEL_ALL_ORDERS,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        symbol=target if scope is EmergencyScope.SYMBOL else None,
        payload=payload,
        quote_snapshot=quote_snapshot,
    )
    return dispatch_or_package(request=request, deps=deps)


def close_all_positions(
    *,
    scope: EmergencyScope,
    target: str | None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Close all open positions within a scope (TRD-FR-035).

    Snapshots the pre-action position state, tolerates partial scope
    coverage, and returns per-child close entries (TRD-FR-036).

    Args:
        scope: Emergency action scope classification.
        target: Scope target (strategy magic number or symbol), if any.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Packaged or gate-evaluated response.
    """
    logger.info("Closing all positions for scope {} target {}.", scope.value, target)
    pre_snapshot = _snapshot_positions(scope=scope, target=target)
    payload: JsonObject = {
        "scope": scope.value,
        "target": target,
        "pre_snapshot": list(pre_snapshot),
        "child_actions": list(
            _child_actions(pre_snapshot, child_action="close_position")
        ),
    }
    request = package_request(
        action=TradingAction.CLOSE_ALL_POSITIONS,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        symbol=target if scope is EmergencyScope.SYMBOL else None,
        payload=payload,
        quote_snapshot=quote_snapshot,
    )
    return dispatch_or_package(request=request, deps=deps)


def _flatten(
    *,
    scope: EmergencyScope,
    target: str | None,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None,
) -> TradingResponseEnvelope:
    """Combine cancel-all and close-all into one flatten response.

    Args:
        scope: Emergency action scope classification.
        target: Scope target (strategy magic number or symbol), if any.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.
        quote_snapshot: Quote evidence, mandatory for live mutations.

    Returns:
        TradingResponseEnvelope: Combined flatten response.
    """
    logger.info("Flattening scope {} target {}.", scope.value, target)
    cancel_result = cancel_all_orders(
        scope=scope,
        target=target,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )
    close_result = close_all_positions(
        scope=scope,
        target=target,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )
    return TradingResponseEnvelope(
        status=TradingStatus.ACCEPTED,
        message=f"Flatten packaged for scope {scope.value}.",
        data={
            "cancel_result": cancel_result.model_dump(mode="json"),
            "close_result": close_result.model_dump(mode="json"),
        },
        metadata=TradingMetadata(reads=True, writes=True),
        route=route,
        action=TradingAction.CLOSE_ALL_POSITIONS,
        side_effect_mode=SideEffectMode.PACKAGED_ONLY,
        retry_safety=RetrySafety.DO_NOT_RETRY,
        request_id=request_id,
        correlation_id=correlation_id,
    )


def flatten_account(
    *,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Cancel all orders and close all positions for the account (TRD-FR-035).

    Returns:
        TradingResponseEnvelope: Combined flatten response.
    """
    logger.info("Flattening entire account.")
    return _flatten(
        scope=EmergencyScope.ACCOUNT,
        target=None,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )


def flatten_strategy(
    *,
    strategy_id: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Cancel all orders and close all positions for a strategy (TRD-FR-035).

    ``strategy_id`` is matched against the broker magic number.

    Returns:
        TradingResponseEnvelope: Combined flatten response.
    """
    logger.info("Flattening strategy {}.", strategy_id)
    return _flatten(
        scope=EmergencyScope.STRATEGY,
        target=strategy_id,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )


def flatten_symbol(
    *,
    symbol: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    quote_snapshot: QuoteSnapshot | None = None,
) -> TradingResponseEnvelope:
    """Cancel all orders and close all positions for a symbol (TRD-FR-035).

    Returns:
        TradingResponseEnvelope: Combined flatten response.
    """
    logger.info("Flattening symbol {}.", symbol)
    return _flatten(
        scope=EmergencyScope.SYMBOL,
        target=symbol,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
        quote_snapshot=quote_snapshot,
    )
