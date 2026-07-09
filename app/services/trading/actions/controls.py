"""Platform-independent strategy and session control action primitives.

This module implements non-broker-mutating operational controls
(``pause_strategy``/``resume_strategy``), read-only broker/local
synchronization (``sync_positions``), graceful session shutdown
(``shutdown``), and idempotent, audited, journaled kill-switch triggers
(``trigger_global_kill_switch``/``trigger_strategy_kill_switch``/
``trigger_symbol_kill_switch``) (TRD-FR-028 through TRD-FR-034).

Kill-switch triggers reserve an idempotency key and append a journal event
before returning, so repeated triggers for the same scope are deduplicated
and every activation is forensically traceable. Clearing a kill switch is out
of scope for this module; it requires dual-control approval evidence and is
owned by the future ``gates/kill_switch.py`` unit.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, cast

from app.services.trading.contracts import (
    JsonObject,
    JsonValue,
    MutationCapability,
    PromotionStage,
    RetrySafety,
    SideEffectMode,
    TradingAction,
    TradingContract,
    TradingMetadata,
    TradingResponseEnvelope,
    TradingRoute,
    TradingStatus,
)
from app.services.trading.info._common import broker_call, iter_or_empty, safe_attr
from app.services.trading.security.error_mapping import TradingMappedError
from app.services.trading.security.redaction_boundary import redact_for_boundary
from app.services.trading.state.idempotency import (
    IdempotencyMaterial,
    compute_idempotency_key,
    compute_material_hash,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.actions._common import TradingActionDependencies
    from app.services.trading.state.ports import EventJournal, IdempotencyStore

DEFAULT_KILL_SWITCH_IDEMPOTENCY_TTL_SECONDS = 300
WILDCARD_SCOPE = "*"


class ShutdownResult(TradingContract):
    """Structured outcome of a graceful session shutdown request.

    Attributes:
        initiated_at: UTC timestamp shutdown was initiated, from the
            injected Clock.
        pending_request_count: In-flight request count observed at shutdown.
        flushed: Whether the injected flush callback ran successfully.
        reconciliation_triggered: Whether final reconciliation was requested.
    """

    initiated_at: str
    pending_request_count: int
    flushed: bool
    reconciliation_triggered: bool


def pause_strategy(
    *,
    strategy_id: str,
    reason: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
) -> TradingResponseEnvelope:
    """Pause a strategy's local operational state (TRD-FR-028).

    This is a non-broker-mutating control that adjusts local state and
    monitoring projections only.

    Args:
        strategy_id: Target strategy identifier.
        reason: Human-readable pause reason.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.

    Returns:
        TradingResponseEnvelope: Local, non-broker-mutating response.

    Raises:
        TradingMappedError: If ``strategy_id`` or ``reason`` is blank.
    """
    logger.info("Pausing strategy {}.", strategy_id)
    return _strategy_state_response(
        action=TradingAction.PAUSE_STRATEGY,
        strategy_id=strategy_id,
        reason=reason,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
    )


def resume_strategy(
    *,
    strategy_id: str,
    reason: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
) -> TradingResponseEnvelope:
    """Resume a previously paused strategy (TRD-FR-028).

    Args:
        strategy_id: Target strategy identifier.
        reason: Human-readable resume reason.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.

    Returns:
        TradingResponseEnvelope: Local, non-broker-mutating response.

    Raises:
        TradingMappedError: If ``strategy_id`` or ``reason`` is blank.
    """
    logger.info("Resuming strategy {}.", strategy_id)
    return _strategy_state_response(
        action=TradingAction.RESUME_STRATEGY,
        strategy_id=strategy_id,
        reason=reason,
        route=route,
        promotion_stage=promotion_stage,
        mutation_capability=mutation_capability,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
    )


def _strategy_state_response(
    *,
    action: TradingAction,
    strategy_id: str,
    reason: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
) -> TradingResponseEnvelope:
    """Build a local, non-broker-mutating strategy control response.

    Args:
        action: Strategy control action.
        strategy_id: Target strategy identifier.
        reason: Human-readable control reason.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.

    Returns:
        TradingResponseEnvelope: Local, non-broker-mutating response.

    Raises:
        TradingMappedError: If ``strategy_id`` or ``reason`` is blank.
    """
    if not strategy_id.strip():
        raise TradingMappedError("strategy_id must be non-empty.", code="INVALID_INPUT")
    if not reason.strip():
        raise TradingMappedError("reason must be non-empty.", code="INVALID_INPUT")
    logger.debug("Building local strategy control response for {}.", action.value)
    audit_ref = None
    if deps.event_journal is not None:
        audit_ref = deps.event_journal.append(
            event={
                "event_type": action.value,
                "strategy_id": strategy_id,
                "reason": reason,
            },
            recorded_at=deps.clock.now_utc(),
        )
    return TradingResponseEnvelope(
        status=TradingStatus.SUCCESS,
        message=f"Strategy {strategy_id} control {action.value} applied locally.",
        data={
            "strategy_id": strategy_id,
            "reason": reason,
            "promotion_stage": promotion_stage.value,
            "mutation_capability": mutation_capability.value,
        },
        metadata=TradingMetadata(writes=True),
        route=route,
        action=action,
        side_effect_mode=SideEffectMode.NONE,
        retry_safety=RetrySafety.DO_NOT_RETRY,
        request_id=request_id,
        correlation_id=correlation_id,
        audit_ref=audit_ref,
    )


def sync_positions(
    *,
    route: TradingRoute,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
) -> TradingResponseEnvelope:
    """Retrieve current broker state and synchronize local projections.

    Reads current broker positions and pending orders through the read-only
    broker resolver and, when an injected ``TradeStore`` is available,
    persists a minimal JSON-safe projection for each. Never submits new
    orders or broker mutations (TRD-FR-029).

    Args:
        route: Requested runtime route.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.

    Returns:
        TradingResponseEnvelope: Read-only synchronization summary.
    """
    logger.info("Synchronizing positions and orders for route {}.", route.value)
    raw_positions = iter_or_empty(broker_call("get_position_info"))
    raw_orders = iter_or_empty(broker_call("get_order_info"))

    position_states: list[JsonObject] = [
        _extract_position_projection(item) for item in raw_positions
    ]
    order_states: list[JsonObject] = [
        _extract_order_projection(item) for item in raw_orders
    ]

    if deps.trade_store is not None:
        for position_state in position_states:
            deps.trade_store.save_position_state(
                route=route,
                tenant_id=deps.tenant_id,
                position_state=position_state,
                expected_version=None,
            )
        for order_state in order_states:
            deps.trade_store.save_order_state(
                route=route,
                tenant_id=deps.tenant_id,
                order_state=order_state,
                expected_version=None,
            )
        logger.debug(
            "Persisted {} position(s) and {} order(s) via injected TradeStore.",
            len(position_states),
            len(order_states),
        )

    return TradingResponseEnvelope(
        status=TradingStatus.SUCCESS,
        message="Broker positions and orders synchronized read-only.",
        data={
            "positions": cast("JsonValue", position_states),
            "orders": cast("JsonValue", order_states),
        },
        metadata=TradingMetadata(reads=True, writes=deps.trade_store is not None),
        route=route,
        action=TradingAction.SYNC_POSITIONS,
        side_effect_mode=SideEffectMode.NONE,
        retry_safety=RetrySafety.SAFE_TO_RETRY,
        request_id=request_id,
        correlation_id=correlation_id,
    )


def _extract_position_projection(raw_position: object) -> JsonObject:
    """Extract a minimal JSON-safe position projection from broker data.

    Args:
        raw_position: Raw broker position record.

    Returns:
        JsonObject: JSON-safe position projection fields.
    """
    logger.debug("Extracting position projection from broker record.")
    return {
        "ticket": safe_attr(raw_position, "ticket", "", str),
        "symbol": safe_attr(raw_position, "symbol", "", str),
        "volume": safe_attr(raw_position, "volume", 0.0, float),
    }


def _extract_order_projection(raw_order: object) -> JsonObject:
    """Extract a minimal JSON-safe order projection from broker data.

    Args:
        raw_order: Raw broker order record.

    Returns:
        JsonObject: JSON-safe order projection fields.
    """
    logger.debug("Extracting order projection from broker record.")
    return {
        "ticket": safe_attr(raw_order, "ticket", "", str),
        "symbol": safe_attr(raw_order, "symbol", "", str),
        "volume_current": safe_attr(raw_order, "volume_current", 0.0, float),
    }


def shutdown(
    *,
    pending_request_count: int,
    deps: TradingActionDependencies,
    flush: object | None = None,
) -> ShutdownResult:
    """Stop admitting new requests and flush state ahead of final shutdown.

    Args:
        pending_request_count: In-flight request count observed at shutdown.
        deps: Shared trading action dependencies.
        flush: Optional zero-argument callable that flushes audit/state
            records before shutdown completes.

    Returns:
        ShutdownResult: Structured shutdown outcome.

    Raises:
        TradingMappedError: If ``pending_request_count`` is negative.
    """
    logger.info(
        "Initiating graceful shutdown with {} in-flight requests.",
        pending_request_count,
    )
    if pending_request_count < 0:
        raise TradingMappedError(
            "pending_request_count must not be negative.",
            code="INVALID_INPUT",
        )
    flushed = False
    if callable(flush):
        flush()
        flushed = True
        logger.debug("Shutdown flush callback completed.")
    if deps.event_journal is not None:
        deps.event_journal.append(
            event={
                "event_type": "shutdown_initiated",
                "pending_request_count": pending_request_count,
            },
            recorded_at=deps.clock.now_utc(),
        )
    return ShutdownResult(
        initiated_at=deps.clock.now_utc().isoformat(),
        pending_request_count=pending_request_count,
        flushed=flushed,
        reconciliation_triggered=True,
    )


def trigger_global_kill_switch(
    *,
    reason: str,
    actor: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    idempotency_store: IdempotencyStore,
    event_journal: EventJournal,
    idempotency_ttl_seconds: int = DEFAULT_KILL_SWITCH_IDEMPOTENCY_TTL_SECONDS,
) -> TradingResponseEnvelope:
    """Activate the global kill switch (TRD-FR-031, TRD-FR-034).

    Args:
        reason: Operator/system reason for the activation.
        actor: Identifier of the operator or system triggering the switch.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.
        idempotency_store: Injected idempotency store port.
        event_journal: Injected append-only event journal port.
        idempotency_ttl_seconds: In-progress lease TTL in seconds.

    Returns:
        TradingResponseEnvelope: Idempotent, audited, journaled activation.
    """
    logger.info("Triggering global kill switch, actor={}.", actor)
    return _trigger_kill_switch(
        action=TradingAction.TRIGGER_GLOBAL_KILL_SWITCH,
        scope_symbol=None,
        scope_strategy_id=None,
        reason=reason,
        actor=actor,
        route=route,
        promotion_stage=promotion_stage,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
        idempotency_store=idempotency_store,
        event_journal=event_journal,
        idempotency_ttl_seconds=idempotency_ttl_seconds,
    )


def trigger_strategy_kill_switch(
    *,
    strategy_id: str,
    reason: str,
    actor: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    idempotency_store: IdempotencyStore,
    event_journal: EventJournal,
    idempotency_ttl_seconds: int = DEFAULT_KILL_SWITCH_IDEMPOTENCY_TTL_SECONDS,
) -> TradingResponseEnvelope:
    """Activate a strategy-scoped kill switch (TRD-FR-032, TRD-FR-034).

    Args:
        strategy_id: Target strategy identifier.
        reason: Operator/system reason for the activation.
        actor: Identifier of the operator or system triggering the switch.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.
        idempotency_store: Injected idempotency store port.
        event_journal: Injected append-only event journal port.
        idempotency_ttl_seconds: In-progress lease TTL in seconds.

    Returns:
        TradingResponseEnvelope: Idempotent, audited, journaled activation.

    Raises:
        TradingMappedError: If ``strategy_id`` is blank.
    """
    logger.info("Triggering strategy kill switch for {}.", strategy_id)
    if not strategy_id.strip():
        raise TradingMappedError("strategy_id must be non-empty.", code="INVALID_INPUT")
    return _trigger_kill_switch(
        action=TradingAction.TRIGGER_STRATEGY_KILL_SWITCH,
        scope_symbol=None,
        scope_strategy_id=strategy_id,
        reason=reason,
        actor=actor,
        route=route,
        promotion_stage=promotion_stage,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
        idempotency_store=idempotency_store,
        event_journal=event_journal,
        idempotency_ttl_seconds=idempotency_ttl_seconds,
    )


def trigger_symbol_kill_switch(
    *,
    symbol: str,
    reason: str,
    actor: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    idempotency_store: IdempotencyStore,
    event_journal: EventJournal,
    idempotency_ttl_seconds: int = DEFAULT_KILL_SWITCH_IDEMPOTENCY_TTL_SECONDS,
) -> TradingResponseEnvelope:
    """Activate a symbol-scoped kill switch (TRD-FR-033, TRD-FR-034).

    Args:
        symbol: Target instrument symbol.
        reason: Operator/system reason for the activation.
        actor: Identifier of the operator or system triggering the switch.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.
        idempotency_store: Injected idempotency store port.
        event_journal: Injected append-only event journal port.
        idempotency_ttl_seconds: In-progress lease TTL in seconds.

    Returns:
        TradingResponseEnvelope: Idempotent, audited, journaled activation.

    Raises:
        TradingMappedError: If ``symbol`` is blank.
    """
    logger.info("Triggering symbol kill switch for {}.", symbol)
    if not symbol.strip():
        raise TradingMappedError("symbol must be non-empty.", code="INVALID_INPUT")
    return _trigger_kill_switch(
        action=TradingAction.TRIGGER_SYMBOL_KILL_SWITCH,
        scope_symbol=symbol,
        scope_strategy_id=None,
        reason=reason,
        actor=actor,
        route=route,
        promotion_stage=promotion_stage,
        request_id=request_id,
        correlation_id=correlation_id,
        deps=deps,
        idempotency_store=idempotency_store,
        event_journal=event_journal,
        idempotency_ttl_seconds=idempotency_ttl_seconds,
    )


def _trigger_kill_switch(
    *,
    action: TradingAction,
    scope_symbol: str | None,
    scope_strategy_id: str | None,
    reason: str,
    actor: str,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    request_id: str,
    correlation_id: str,
    deps: TradingActionDependencies,
    idempotency_store: IdempotencyStore,
    event_journal: EventJournal,
    idempotency_ttl_seconds: int,
) -> TradingResponseEnvelope:
    """Reserve idempotency, journal, and package a kill-switch activation.

    The idempotency material is scope-only (action, route, promotion stage,
    symbol, strategy) so repeated activations for the same scope dedupe
    regardless of ``request_id`` or ``reason`` text (TRD-FR-034).

    Args:
        action: Kill-switch trigger action.
        scope_symbol: Optional symbol scope.
        scope_strategy_id: Optional strategy scope.
        reason: Operator/system reason for the activation.
        actor: Identifier of the operator or system triggering the switch.
        route: Requested runtime route.
        promotion_stage: Active promotion stage.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        deps: Shared trading action dependencies.
        idempotency_store: Injected idempotency store port.
        event_journal: Injected append-only event journal port.
        idempotency_ttl_seconds: In-progress lease TTL in seconds.

    Returns:
        TradingResponseEnvelope: Idempotent, audited, journaled activation.

    Raises:
        TradingMappedError: If ``reason`` or ``actor`` is blank.
    """
    if not reason.strip():
        raise TradingMappedError("reason must be non-empty.", code="INVALID_INPUT")
    if not actor.strip():
        raise TradingMappedError("actor must be non-empty.", code="INVALID_INPUT")

    material = IdempotencyMaterial(
        account_id=WILDCARD_SCOPE,
        strategy_id=scope_strategy_id or WILDCARD_SCOPE,
        route=route,
        promotion_stage=promotion_stage.value,
        broker=WILDCARD_SCOPE,
        symbol=scope_symbol or WILDCARD_SCOPE,
        action=action,
    )
    key = compute_idempotency_key(material)
    material_hash = compute_material_hash(material.canonical_payload())
    now = deps.clock.now_utc()
    reservation = idempotency_store.reserve(
        route=route,
        tenant_id=deps.tenant_id,
        key=key,
        material_hash=material_hash,
        expires_at=now + timedelta(seconds=idempotency_ttl_seconds),
    )
    audit_ref = event_journal.append(
        event={
            "event_type": action.value,
            "reason": reason,
            "actor": actor,
            "scope_symbol": scope_symbol,
            "scope_strategy_id": scope_strategy_id,
            "idempotency_key": key,
        },
        recorded_at=now,
    )
    logger.info(
        "Kill switch {} activated by {}, journal ref {}.",
        action.value,
        actor,
        audit_ref,
    )
    redacted_reservation = redact_for_boundary(reservation).payload
    return TradingResponseEnvelope(
        status=TradingStatus.ACCEPTED,
        message=f"Kill switch {action.value} activated.",
        data={"reservation": redacted_reservation},
        metadata=TradingMetadata(writes=True),
        route=route,
        action=action,
        side_effect_mode=SideEffectMode.NONE,
        retry_safety=RetrySafety.DO_NOT_RETRY,
        request_id=request_id,
        correlation_id=correlation_id,
        audit_ref=audit_ref,
    )
