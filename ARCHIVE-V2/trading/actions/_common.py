"""Shared packaging helpers for trading action primitives.

This module contains the injected-dependency bag and request/response
packaging helpers shared by ``actions/orders.py``, ``actions/positions.py``,
``actions/controls.py``, and ``actions/emergency.py``. It performs no broker
calls; the :class:`LiveGatePipeline` protocol is a documented injection seam
for the canonical 16-step live gate pipeline implemented by the future
``gates/pipeline.py`` unit (TRD-FR-025). Until a pipeline is injected for
``route="live"``, every action fails closed to a ``packaged_only`` response,
matching the package's default-deny mutation posture (TRD-FR-055).
"""
# ruff: noqa: ARG002

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.services.trading.contracts import (
    JsonObject,
    MutationCapability,
    PromotionStage,
    QuoteSnapshot,
    RetrySafety,
    SideEffectMode,
    TradingAction,
    TradingMetadata,
    TradingRequestEnvelope,
    TradingResponseEnvelope,
    TradingRoute,
    TradingStatus,
)
from app.services.trading.execution import ExecutionCoordinator
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.trading.state.ports import (
        RNG,
        Clock,
        EventJournal,
        IdempotencyStore,
        TradeStore,
    )


@runtime_checkable
class LiveGatePipeline(Protocol):
    """Injection seam for the future canonical 16-step live gate pipeline."""

    def evaluate(self, request: TradingRequestEnvelope) -> TradingResponseEnvelope:
        """Evaluate the live gate pipeline for a packaged request.

        Args:
            request: Packaged trading request envelope.

        Returns:
            TradingResponseEnvelope: Gate pipeline outcome envelope.
        """
        logger.debug("LiveGatePipeline.evaluate protocol placeholder invoked.")
        raise NotImplementedError


class TradingActionDependencies:
    """Injected dependencies shared by trading action primitives.

    Args:
        clock: Injected clock for deterministic time reads.
        rng: Injected pseudo-random generator for deterministic jitter.
        tenant_id: Tenant or session namespace for store operations.
        gate_pipeline: Optional live gate pipeline seam for ``route="live"``.
        idempotency_store: Optional injected idempotency store port.
        event_journal: Optional injected append-only event journal port.
        trade_store: Optional injected trade projection store port.
    """

    def __init__(
        self,
        *,
        clock: Clock,
        rng: RNG,
        tenant_id: str,
        gate_pipeline: LiveGatePipeline | None = None,
        idempotency_store: IdempotencyStore | None = None,
        event_journal: EventJournal | None = None,
        trade_store: TradeStore | None = None,
    ) -> None:
        """Initialize the shared trading action dependency bag.

        Args:
            clock: Injected clock for deterministic time reads.
            rng: Injected pseudo-random generator for deterministic jitter.
            tenant_id: Tenant or session namespace for store operations.
            gate_pipeline: Optional live gate pipeline seam for ``route="live"``.
            idempotency_store: Optional injected idempotency store port.
            event_journal: Optional injected append-only event journal port.
            trade_store: Optional injected trade projection store port.

        Raises:
            ValueError: If ``tenant_id`` is blank.
        """
        logger.info(
            "Initializing trading action dependencies for tenant {}.", tenant_id
        )
        if not tenant_id.strip():
            raise ValueError("tenant_id must be non-empty.")
        self.clock = clock
        self.rng = rng
        self.tenant_id = tenant_id
        self.gate_pipeline = gate_pipeline
        self.idempotency_store = idempotency_store
        self.event_journal = event_journal
        self.trade_store = trade_store


def package_request(
    *,
    action: TradingAction,
    route: TradingRoute,
    promotion_stage: PromotionStage,
    mutation_capability: MutationCapability,
    request_id: str,
    correlation_id: str,
    symbol: str | None,
    payload: JsonObject,
    quote_snapshot: QuoteSnapshot | None = None,
    oco_group_id: str | None = None,
    linked_order_ids: tuple[str, ...] = (),
) -> TradingRequestEnvelope:
    """Build a canonical trading request envelope for a packaged action.

    Args:
        action: Trading action being packaged.
        route: Runtime route.
        promotion_stage: Active promotion stage.
        mutation_capability: Active mutation capability.
        request_id: Unique request identifier.
        correlation_id: Correlation identifier.
        symbol: Optional target symbol.
        payload: JSON-safe action payload.
        quote_snapshot: Quote evidence, mandatory for live mutations.
        oco_group_id: Optional One-Cancels-Other group identifier.
        linked_order_ids: Optional sibling order identifiers.

    Returns:
        TradingRequestEnvelope: Validated request envelope.
    """
    logger.info("Packaging trading request {} for action {}.", request_id, action.value)
    return TradingRequestEnvelope(
        route=route,
        action=action,
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


def dispatch_or_package(
    *,
    request: TradingRequestEnvelope,
    deps: TradingActionDependencies,
    message: str = "Trading request packaged; live gate pipeline not yet engaged.",
) -> TradingResponseEnvelope:
    """Evaluate the injected live gate pipeline or return a packaged response.

    Args:
        request: Packaged trading request envelope.
        deps: Shared trading action dependencies.
        message: Public response message for the packaged-only path.

    Returns:
        TradingResponseEnvelope: Gate pipeline outcome, or a fail-closed
        ``packaged_only`` response when no live gate pipeline is injected.
    """
    coordinator = ExecutionCoordinator()
    dispatch_payload = coordinator.build_broker_dispatch_payload(request)
    if request.route is TradingRoute.LIVE and deps.gate_pipeline is not None:
        logger.info(
            "Delegating live request {} to the injected gate pipeline.",
            request.request_id,
        )
        return deps.gate_pipeline.evaluate(request)

    logger.info(
        "Packaging request {} as packaged_only for route {}.",
        request.request_id,
        request.route.value,
    )
    return TradingResponseEnvelope(
        status=TradingStatus.ACCEPTED,
        message=message,
        data={"dispatch_payload": dispatch_payload},
        metadata=TradingMetadata(writes=True),
        route=request.route,
        action=request.action,
        side_effect_mode=SideEffectMode.PACKAGED_ONLY,
        retry_safety=RetrySafety.DO_NOT_RETRY,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
    )
