"""Structured trading report and execution-quality event construction.

This module constructs structured trading reports containing positions, order
records, execution latencies, cost entries, and reconciliation discrepancies
(TRD-FR-132). It also emits standardized, redacted execution-quality events —
realized slippage versus the mandatory quote snapshot, implementation
shortfall, fill latency, partial-fill counts, and transaction cost facts —
under the versioned contract schema (TRD-XM-004). Trading performs no metric
aggregation of its own; analytics consumes these contracts.
"""

from __future__ import annotations

from decimal import Decimal

from app.services.trading.contracts import (
    OrderState,
    PositionState,
    QuoteSnapshot,
    TradingContract,
)
from app.services.trading.execution.coordinator import (
    CostAdjustmentEvent,
    TransactionCostFacts,
)
from app.services.trading.execution.state_machine import LifecycleKind
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger
from pydantic import Field, model_validator

_VALID_SIDES = frozenset({"buy", "sell"})
_BPS_DENOMINATOR = Decimal(10_000)


class ExecutionLatencyEntry(TradingContract):
    """Latency breakdown for one order's execution lifecycle.

    Attributes:
        order_id: Local order identifier.
        dispatch_to_ack_ms: Latency from dispatch to broker acknowledgement.
        ack_to_fill_ms: Latency from acknowledgement to final fill report.
        total_ms: Total dispatch-to-fill latency.
    """

    order_id: str
    dispatch_to_ack_ms: Decimal = Field(ge=0)
    ack_to_fill_ms: Decimal = Field(ge=0)
    total_ms: Decimal = Field(ge=0)

    @model_validator(mode="after")
    def validate_latency_entry(self) -> ExecutionLatencyEntry:
        """Validate the latency entry identifier and component consistency.

        Returns:
            ExecutionLatencyEntry: Validated latency entry.

        Raises:
            ValueError: If ``order_id`` is blank.
        """
        logger.debug("Validating execution latency entry for {}.", self.order_id)
        if not self.order_id.strip():
            raise ValueError("order_id must be non-empty.")
        return self


class ReconciliationDiscrepancyEntry(TradingContract):
    """One detected local-versus-broker reconciliation discrepancy.

    Attributes:
        entity_id: Local order or position identifier.
        kind: Whether the discrepancy concerns an order or a position.
        discrepancy_type: Stable discrepancy classification (e.g.
            ``state_mismatch``, ``volume_mismatch``, ``missing_locally``,
            ``missing_at_broker``).
        local_value: Redacted local projection value.
        broker_value: Redacted broker-reported value.
        detected_at: UTC timestamp supplied by an injected Clock.
    """

    entity_id: str
    kind: LifecycleKind
    discrepancy_type: str
    local_value: str
    broker_value: str
    detected_at: str

    @model_validator(mode="after")
    def validate_discrepancy_entry(self) -> ReconciliationDiscrepancyEntry:
        """Validate discrepancy entry identifiers.

        Returns:
            ReconciliationDiscrepancyEntry: Validated discrepancy entry.

        Raises:
            ValueError: If ``entity_id`` or ``discrepancy_type`` is blank.
        """
        logger.debug("Validating reconciliation discrepancy for {}.", self.entity_id)
        if not self.entity_id.strip():
            raise ValueError("entity_id must be non-empty.")
        if not self.discrepancy_type.strip():
            raise ValueError("discrepancy_type must be non-empty.")
        return self


class TradingReport(TradingContract):
    """Structured trading report (TRD-FR-132).

    Attributes:
        report_id: Unique report identifier.
        generated_at: UTC timestamp supplied by an injected Clock.
        tenant_id: Tenant or session namespace this report covers.
        positions: Position state projections included in this report.
        orders: Order state projections included in this report.
        execution_latencies: Per-order execution latency breakdowns.
        cost_entries: Transaction cost capture/adjustment events.
        reconciliation_discrepancies: Detected reconciliation discrepancies.
    """

    report_id: str
    generated_at: str
    tenant_id: str
    positions: tuple[PositionState, ...] = Field(default_factory=tuple)
    orders: tuple[OrderState, ...] = Field(default_factory=tuple)
    execution_latencies: tuple[ExecutionLatencyEntry, ...] = Field(
        default_factory=tuple
    )
    cost_entries: tuple[CostAdjustmentEvent, ...] = Field(default_factory=tuple)
    reconciliation_discrepancies: tuple[ReconciliationDiscrepancyEntry, ...] = Field(
        default_factory=tuple
    )

    @model_validator(mode="after")
    def validate_report(self) -> TradingReport:
        """Validate trading report identifiers.

        Returns:
            TradingReport: Validated trading report.

        Raises:
            ValueError: If ``report_id`` or ``tenant_id`` is blank.
        """
        logger.info("Validating trading report {}.", self.report_id)
        if not self.report_id.strip():
            raise ValueError("report_id must be non-empty.")
        if not self.tenant_id.strip():
            raise ValueError("tenant_id must be non-empty.")
        return self


def build_trading_report(
    *,
    report_id: str,
    generated_at: str,
    tenant_id: str,
    positions: tuple[PositionState, ...] = (),
    orders: tuple[OrderState, ...] = (),
    execution_latencies: tuple[ExecutionLatencyEntry, ...] = (),
    cost_entries: tuple[CostAdjustmentEvent, ...] = (),
    reconciliation_discrepancies: tuple[ReconciliationDiscrepancyEntry, ...] = (),
) -> TradingReport:
    """Construct a structured trading report (TRD-FR-132).

    Args:
        report_id: Unique report identifier.
        generated_at: UTC timestamp supplied by an injected Clock.
        tenant_id: Tenant or session namespace this report covers.
        positions: Position state projections to include.
        orders: Order state projections to include.
        execution_latencies: Per-order execution latency breakdowns.
        cost_entries: Transaction cost capture/adjustment events.
        reconciliation_discrepancies: Detected reconciliation discrepancies.

    Returns:
        TradingReport: The constructed, validated trading report.
    """
    logger.info("Building trading report {} for tenant {}.", report_id, tenant_id)
    report = TradingReport(
        report_id=report_id,
        generated_at=generated_at,
        tenant_id=tenant_id,
        positions=positions,
        orders=orders,
        execution_latencies=execution_latencies,
        cost_entries=cost_entries,
        reconciliation_discrepancies=reconciliation_discrepancies,
    )
    logger.debug(
        "Built trading report {} with {} order(s), {} position(s).",
        report_id,
        len(orders),
        len(positions),
    )
    return report


class ExecutionQualityEvent(TradingContract):
    """Standardized execution-quality event (TRD-XM-004).

    Attributes:
        order_id: Local order identifier the event concerns.
        symbol: Executed symbol.
        realized_slippage_bps: Realized slippage versus the reference quote,
            in basis points, direction-adjusted so a positive value is
            always adverse to the requester.
        implementation_shortfall: Direction-adjusted difference between the
            executed price and the pre-trade decision price.
        fill_latency_ms: Dispatch-to-fill latency.
        partial_fill_count: Number of partial fills observed for this order.
        cost_facts: Captured transaction cost facts.
        owner: ``internal`` or ``external`` order attribution.
        is_external: Whether this event is excluded from strategy
            performance attribution.
    """

    order_id: str
    symbol: str
    realized_slippage_bps: Decimal
    implementation_shortfall: Decimal
    fill_latency_ms: Decimal = Field(ge=0)
    partial_fill_count: int = Field(ge=0)
    cost_facts: TransactionCostFacts
    owner: str = "internal"
    is_external: bool = False

    @model_validator(mode="after")
    def validate_event(self) -> ExecutionQualityEvent:
        """Validate execution-quality event identifiers and owner tag.

        Returns:
            ExecutionQualityEvent: Validated execution-quality event.

        Raises:
            ValueError: If identifiers are blank or ``owner`` is unrecognized.
        """
        logger.debug("Validating execution quality event for {}.", self.order_id)
        if not self.order_id.strip() or not self.symbol.strip():
            raise ValueError("order_id and symbol must be non-empty.")
        if self.owner not in {"internal", "external"}:
            raise ValueError("owner must be either internal or external.")
        return self


def compute_realized_slippage_bps(
    *,
    quote_snapshot: QuoteSnapshot,
    executed_price: Decimal,
    side: str,
) -> Decimal:
    """Compute realized slippage versus the mandatory quote snapshot.

    A positive result is always adverse to the requester: for a buy, paying
    more than the quoted ask; for a sell, receiving less than the quoted bid.

    Args:
        quote_snapshot: Mandatory quote evidence captured at request time.
        executed_price: Final executed price.
        side: Order side, either ``buy`` or ``sell``.

    Returns:
        Decimal: Realized slippage in basis points.

    Raises:
        TradingMappedError: If ``side`` is not ``buy`` or ``sell``.
    """
    logger.info(
        "Computing realized slippage for {} side {}.", quote_snapshot.symbol, side
    )
    if side not in _VALID_SIDES:
        raise TradingMappedError(
            "side must be either buy or sell.",
            code="INVALID_INPUT",
        )
    if side == "buy":
        reference_price = quote_snapshot.ask
        slippage = executed_price - reference_price
    else:
        reference_price = quote_snapshot.bid
        slippage = reference_price - executed_price
    slippage_bps = (slippage / reference_price) * _BPS_DENOMINATOR
    logger.debug(
        "Realized slippage for {}: {} bps.", quote_snapshot.symbol, slippage_bps
    )
    return slippage_bps


def compute_implementation_shortfall(
    *,
    executed_price: Decimal,
    decision_price: Decimal,
    side: str,
) -> Decimal:
    """Compute direction-adjusted implementation shortfall.

    A positive result is always adverse to the requester relative to the
    price observed at the pre-trade decision point.

    Args:
        executed_price: Final executed price.
        decision_price: Reference price observed at the trading decision.
        side: Order side, either ``buy`` or ``sell``.

    Returns:
        Decimal: Direction-adjusted implementation shortfall.

    Raises:
        TradingMappedError: If ``side`` is not ``buy`` or ``sell``.
    """
    logger.info("Computing implementation shortfall for side {}.", side)
    if side not in _VALID_SIDES:
        raise TradingMappedError(
            "side must be either buy or sell.",
            code="INVALID_INPUT",
        )
    if side == "buy":
        shortfall = executed_price - decision_price
    else:
        shortfall = decision_price - executed_price
    logger.debug("Implementation shortfall: {}.", shortfall)
    return shortfall


def build_execution_quality_event(
    *,
    order_id: str,
    symbol: str,
    quote_snapshot: QuoteSnapshot,
    executed_price: Decimal,
    decision_price: Decimal,
    side: str,
    fill_latency_ms: Decimal,
    partial_fill_count: int,
    cost_facts: TransactionCostFacts,
    owner: str = "internal",
) -> ExecutionQualityEvent:
    """Build a standardized execution-quality event (TRD-XM-004).

    Events attributed to ``owner="external"`` carry ``is_external=True`` so
    analytics excludes them from strategy performance attribution
    (TRD-FR-161/162).

    Args:
        order_id: Local order identifier.
        symbol: Executed symbol.
        quote_snapshot: Mandatory quote evidence captured at request time.
        executed_price: Final executed price.
        decision_price: Reference price observed at the trading decision.
        side: Order side, either ``buy`` or ``sell``.
        fill_latency_ms: Dispatch-to-fill latency.
        partial_fill_count: Number of partial fills observed for this order.
        cost_facts: Captured transaction cost facts.
        owner: ``internal`` or ``external`` order attribution.

    Returns:
        ExecutionQualityEvent: The constructed, validated event.
    """
    logger.info("Building execution quality event for order {}.", order_id)
    event = ExecutionQualityEvent(
        order_id=order_id,
        symbol=symbol,
        realized_slippage_bps=compute_realized_slippage_bps(
            quote_snapshot=quote_snapshot, executed_price=executed_price, side=side
        ),
        implementation_shortfall=compute_implementation_shortfall(
            executed_price=executed_price, decision_price=decision_price, side=side
        ),
        fill_latency_ms=fill_latency_ms,
        partial_fill_count=partial_fill_count,
        cost_facts=cost_facts,
        owner=owner,
        is_external=owner == "external",
    )
    logger.debug("Built execution quality event for order {}.", order_id)
    return event
