"""Unit tests for structured trading report and execution-quality events."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.trading.contracts import QuoteSnapshot
from app.services.trading.execution import reporting as r
from app.services.trading.execution.coordinator import (
    CostAdjustmentEvent,
    TransactionCostFacts,
)
from app.services.trading.execution.state_machine import LifecycleKind
from app.services.trading.security.error_mapping import TradingMappedError


def _quote(**overrides: object) -> QuoteSnapshot:
    defaults: dict[str, object] = {
        "symbol": "EURUSD",
        "bid": Decimal("1.1000"),
        "ask": Decimal("1.1002"),
        "spread": Decimal("0.0002"),
        "timestamp": "2026-07-09T00:00:00Z",
        "source": "mt5",
        "freshness_age_ms": 10,
    }
    defaults.update(overrides)
    return QuoteSnapshot(**defaults)  # type: ignore[arg-type]


def test_execution_latency_entry_rejects_blank_order_id() -> None:
    """A blank order_id fails validation."""
    with pytest.raises(ValueError, match="order_id"):
        r.ExecutionLatencyEntry(
            order_id="  ",
            dispatch_to_ack_ms=Decimal(1),
            ack_to_fill_ms=Decimal(1),
            total_ms=Decimal(2),
        )


def test_reconciliation_discrepancy_entry_rejects_blank_fields() -> None:
    """Blank entity_id or discrepancy_type fails validation."""
    with pytest.raises(ValueError, match="entity_id"):
        r.ReconciliationDiscrepancyEntry(
            entity_id="  ",
            kind=LifecycleKind.ORDER,
            discrepancy_type="state_mismatch",
            local_value="a",
            broker_value="b",
            detected_at="2026-07-09T00:00:00Z",
        )
    with pytest.raises(ValueError, match="discrepancy_type"):
        r.ReconciliationDiscrepancyEntry(
            entity_id="ord-1",
            kind=LifecycleKind.ORDER,
            discrepancy_type="  ",
            local_value="a",
            broker_value="b",
            detected_at="2026-07-09T00:00:00Z",
        )


def test_build_trading_report_defaults_to_empty_collections() -> None:
    """A report with no data still validates with empty collections."""
    report = r.build_trading_report(
        report_id="rep-1", generated_at="2026-07-09T00:00:00Z", tenant_id="tenant-1"
    )
    assert report.positions == ()
    assert report.orders == ()
    assert report.execution_latencies == ()
    assert report.cost_entries == ()
    assert report.reconciliation_discrepancies == ()


def test_build_trading_report_rejects_blank_identifiers() -> None:
    """Blank report_id or tenant_id fails validation."""
    with pytest.raises(ValueError, match="report_id"):
        r.build_trading_report(
            report_id="  ", generated_at="2026-07-09T00:00:00Z", tenant_id="tenant-1"
        )
    with pytest.raises(ValueError, match="tenant_id"):
        r.build_trading_report(
            report_id="rep-1", generated_at="2026-07-09T00:00:00Z", tenant_id="  "
        )


def test_build_trading_report_includes_supplied_entries() -> None:
    """Supplied latency and cost entries are included in the report."""
    latency = r.ExecutionLatencyEntry(
        order_id="ord-1",
        dispatch_to_ack_ms=Decimal(10),
        ack_to_fill_ms=Decimal(20),
        total_ms=Decimal(30),
    )
    cost_event = CostAdjustmentEvent(
        order_id="ord-1",
        cost_facts=TransactionCostFacts(commission=Decimal("0.5")),
        recorded_at="2026-07-09T00:00:00Z",
    )
    discrepancy = r.ReconciliationDiscrepancyEntry(
        entity_id="ord-1",
        kind=LifecycleKind.ORDER,
        discrepancy_type="state_mismatch",
        local_value="Filled",
        broker_value="Cancelled",
        detected_at="2026-07-09T00:00:00Z",
    )
    report = r.build_trading_report(
        report_id="rep-1",
        generated_at="2026-07-09T00:00:00Z",
        tenant_id="tenant-1",
        execution_latencies=(latency,),
        cost_entries=(cost_event,),
        reconciliation_discrepancies=(discrepancy,),
    )
    assert report.execution_latencies == (latency,)
    assert report.cost_entries == (cost_event,)
    assert report.reconciliation_discrepancies == (discrepancy,)


def test_execution_quality_event_rejects_blank_identifiers() -> None:
    """Blank order_id or symbol fails validation."""
    with pytest.raises(ValueError, match="order_id"):
        r.ExecutionQualityEvent(
            order_id="  ",
            symbol="EURUSD",
            realized_slippage_bps=Decimal(0),
            implementation_shortfall=Decimal(0),
            fill_latency_ms=Decimal(10),
            partial_fill_count=0,
            cost_facts=TransactionCostFacts(),
        )


def test_execution_quality_event_rejects_unknown_owner() -> None:
    """An owner value outside internal/external fails validation."""
    with pytest.raises(ValueError, match="owner"):
        r.ExecutionQualityEvent(
            order_id="ord-1",
            symbol="EURUSD",
            realized_slippage_bps=Decimal(0),
            implementation_shortfall=Decimal(0),
            fill_latency_ms=Decimal(10),
            partial_fill_count=0,
            cost_facts=TransactionCostFacts(),
            owner="mystery",
        )


def test_compute_realized_slippage_bps_buy_adverse() -> None:
    """A buy executed above the quoted ask is adverse (positive slippage)."""
    quote = _quote()
    slippage = r.compute_realized_slippage_bps(
        quote_snapshot=quote, executed_price=Decimal("1.1005"), side="buy"
    )
    assert slippage > 0


def test_compute_realized_slippage_bps_sell_favorable() -> None:
    """A sell executed above the quoted bid is favorable (negative slippage)."""
    quote = _quote()
    slippage = r.compute_realized_slippage_bps(
        quote_snapshot=quote, executed_price=Decimal("1.1005"), side="sell"
    )
    assert slippage < 0


def test_compute_realized_slippage_bps_rejects_invalid_side() -> None:
    """An unrecognized side fails closed."""
    with pytest.raises(TradingMappedError):
        r.compute_realized_slippage_bps(
            quote_snapshot=_quote(), executed_price=Decimal("1.1"), side="hold"
        )


def test_compute_implementation_shortfall_buy_and_sell() -> None:
    """Shortfall is direction-adjusted for buy versus sell."""
    buy_shortfall = r.compute_implementation_shortfall(
        executed_price=Decimal("1.1005"), decision_price=Decimal("1.1000"), side="buy"
    )
    assert buy_shortfall == Decimal("0.0005")
    sell_shortfall = r.compute_implementation_shortfall(
        executed_price=Decimal("1.1005"), decision_price=Decimal("1.1000"), side="sell"
    )
    assert sell_shortfall == Decimal("-0.0005")


def test_compute_implementation_shortfall_rejects_invalid_side() -> None:
    """An unrecognized side fails closed."""
    with pytest.raises(TradingMappedError):
        r.compute_implementation_shortfall(
            executed_price=Decimal("1.1"), decision_price=Decimal("1.1"), side="hold"
        )


def test_build_execution_quality_event_internal_owner() -> None:
    """An internal-owned event is not flagged external."""
    event = r.build_execution_quality_event(
        order_id="ord-1",
        symbol="EURUSD",
        quote_snapshot=_quote(),
        executed_price=Decimal("1.1005"),
        decision_price=Decimal("1.1001"),
        side="buy",
        fill_latency_ms=Decimal(120),
        partial_fill_count=0,
        cost_facts=TransactionCostFacts(),
    )
    assert event.is_external is False
    assert event.owner == "internal"


def test_build_execution_quality_event_external_owner_flagged() -> None:
    """An external-owned event carries the external flag for analytics."""
    event = r.build_execution_quality_event(
        order_id="ord-1",
        symbol="EURUSD",
        quote_snapshot=_quote(),
        executed_price=Decimal("1.1005"),
        decision_price=Decimal("1.1001"),
        side="sell",
        fill_latency_ms=Decimal(80),
        partial_fill_count=1,
        cost_facts=TransactionCostFacts(),
        owner="external",
    )
    assert event.is_external is True
    assert event.owner == "external"
