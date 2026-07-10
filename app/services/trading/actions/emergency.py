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


# Most-severe first. A flatten reports the worst thing that happened to any of
# its children: an operator must never read "packaged_only" off a flatten whose
# close leg actually reached the broker, nor "accepted" off one that was blocked.
_SIDE_EFFECT_SEVERITY: tuple[SideEffectMode, ...] = (
    SideEffectMode.UNKNOWN_OUTCOME,
    SideEffectMode.BROKER_MUTATION_ATTEMPTED,
    SideEffectMode.BROKER_MUTATION_REJECTED,
    SideEffectMode.BROKER_MUTATION_CONFIRMED,
    SideEffectMode.PACKAGED_ONLY,
    SideEffectMode.NONE,
)

_STATUS_SEVERITY: tuple[TradingStatus, ...] = (
    TradingStatus.ERROR,
    TradingStatus.BLOCKED,
    TradingStatus.REJECTED,
    TradingStatus.SUCCESS,
    TradingStatus.ACCEPTED,
)

_RETRY_SEVERITY: tuple[RetrySafety, ...] = (
    RetrySafety.RETRY_AFTER_RECONCILIATION,
    RetrySafety.DO_NOT_RETRY,
    RetrySafety.RETRY_AFTER_DELAY,
    RetrySafety.SAFE_TO_RETRY,
)


def _combine_side_effects(
    children: tuple[TradingResponseEnvelope, ...],
) -> SideEffectMode:
    """Resolve the combined side effect of a flatten's child actions.

    Args:
        children: Child action response envelopes.

    Returns:
        SideEffectMode: The most severe side effect observed.
    """
    modes = {child.side_effect_mode for child in children}
    for candidate in _SIDE_EFFECT_SEVERITY:
        if candidate in modes:
            return candidate
    return SideEffectMode.NONE


def _combine_statuses(children: tuple[TradingResponseEnvelope, ...]) -> TradingStatus:
    """Resolve the combined status of a flatten's child actions.

    Args:
        children: Child action response envelopes.

    Returns:
        TradingStatus: The most severe status observed.
    """
    statuses = {child.status for child in children}
    for candidate in _STATUS_SEVERITY:
        if candidate in statuses:
            return candidate
    return TradingStatus.ACCEPTED


def _combine_retry_safety(
    children: tuple[TradingResponseEnvelope, ...],
) -> RetrySafety:
    """Resolve the combined retry safety of a flatten's child actions.

    Args:
        children: Child action response envelopes.

    Returns:
        RetrySafety: The most conservative retry classification observed.
    """
    safeties = {child.retry_safety for child in children}
    for candidate in _RETRY_SEVERITY:
        if candidate in safeties:
            return candidate
    return RetrySafety.DO_NOT_RETRY


def _flatten_message(
    *, scope: EmergencyScope, side_effect_mode: SideEffectMode
) -> str:
    """Describe what a flatten actually did, not what it intended to do.

    Args:
        scope: Emergency action scope classification.
        side_effect_mode: Combined side effect of the child actions.

    Returns:
        str: Human-readable, redacted outcome message.
    """
    if side_effect_mode is SideEffectMode.PACKAGED_ONLY:
        return f"Flatten packaged for scope {scope.value}."
    if side_effect_mode is SideEffectMode.NONE:
        return f"Flatten blocked for scope {scope.value}."
    if side_effect_mode is SideEffectMode.UNKNOWN_OUTCOME:
        return f"Flatten outcome unknown for scope {scope.value}; reconcile."
    return f"Flatten dispatched for scope {scope.value}."


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
    children = (cancel_result, close_result)
    side_effect_mode = _combine_side_effects(children)
    status = _combine_statuses(children)
    return TradingResponseEnvelope(
        status=status,
        message=_flatten_message(scope=scope, side_effect_mode=side_effect_mode),
        data={
            "cancel_result": cancel_result.model_dump(mode="json"),
            "close_result": close_result.model_dump(mode="json"),
        },
        metadata=TradingMetadata(
            reads=True,
            writes=True,
            trades=any(child.metadata.trades for child in children),
        ),
        route=route,
        action=TradingAction.CLOSE_ALL_POSITIONS,
        side_effect_mode=side_effect_mode,
        retry_safety=_combine_retry_safety(children),
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
