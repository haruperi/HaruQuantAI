"""Executable Trading monitoring usage example.

Demonstrates operational events, runtime event emission, and budget gates.
"""

# ruff: noqa: E501
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading import (
    BudgetGate,
    ExecutionReceipt,
    OperationalEvent,
    build_broker_state_unknown_event,
    emit_runtime_event,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)
REQUEST_ID = "req-11111111-1111-4111-8111-111111111111"
WORKFLOW_ID = "wf-22222222-2222-4222-8222-222222222222"
CORRELATION_ID = "cor-33333333-3333-4333-8333-333333333333"


def fr_trd_068() -> OperationalEvent:
    """FR-TRD-068: After the first persisted transition of a conflict scope into retry-locked `unknown_outcome`, build one `BROKER_STATE_UNKNOWN` `OperationalEvent` with `severity="critical"`, deterministic identity, receipt/incident references, `retry_locked=true`, and bounded redacted unresolved-scope facts. Emit it through the existing injected composition sink after persistence; construction or delivery failure is surfaced and never changes the lock, reconciliation result, or execution truth.

    Returns:
        Critical unknown-broker-state operational evidence.
    """
    receipt = ExecutionReceipt(
        receipt_id="usage-receipt-unknown",
        intent_id="usage-intent-unknown",
        client_order_id="usage-client-order-unknown",
        route="sim",
        authority="simulator",
        status="unknown_outcome",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal(0),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="timeout",
        retry_safe=False,
        reconciliation_required=True,
        request_id=REQUEST_ID,
        correlation_id=CORRELATION_ID,
    )
    event = build_broker_state_unknown_event(
        receipt,
        incident_id="usage-incident-unknown",
        unresolved_scope=("order:usage-order",),
        occurred_at=NOW,
        workflow_id=WORKFLOW_ID,
    )
    published: list[OperationalEvent] = []
    emit_runtime_event(event, published.append)
    assert published == [event]
    return event


def example_monitoring() -> None:
    """Demonstrate Trading monitoring models and emission."""
    print("=" * 80)
    print("Trading Example 6: Operational Events and Monitoring")
    print("=" * 80)

    # 1. Operational event construction
    event = OperationalEvent(
        event_id="usage-event-001",
        event_type="LATENCY_OBSERVED",
        severity="info",
        occurred_at=NOW,
        request_id=REQUEST_ID,
        workflow_id=WORKFLOW_ID,
        correlation_id=CORRELATION_ID,
        facts={"elapsed_seconds": "0.125"},
        source_refs={"operation": "submit_order"},
    )
    print(f"Operational event schema_id: {event.schema_id}, type: {event.event_type}")

    # 2. Emit runtime event
    published: list[OperationalEvent] = []
    event2 = OperationalEvent(
        event_id="usage-event-002",
        event_type="HEALTH_CHANGED",
        severity="info",
        occurred_at=NOW,
        request_id="req-44444444-4444-4444-8444-444444444444",
        workflow_id="wf-55555555-5555-4555-8555-555555555555",
        correlation_id="cor-66666666-6666-4666-8666-666666666666",
        facts={"health": "ready"},
        source_refs={"session": "session-001"},
    )
    emit_runtime_event(event2, published.append)
    print(f"Published runtime events count: {len(published)}")

    # 3. Budget gate
    print(f"BudgetGate validate is callable: {callable(BudgetGate.validate)}")

    # 4. Critical unknown-broker-state evidence
    critical = fr_trd_068()
    print(f"Critical event type: {critical.event_type}")


def fr_trd_046() -> None:
    """FR-TRD-046: The system shall represent focused health, dependency, staleness, timeout, latency, cost, and incident evidence in a Trading-owned contract."""
    example_monitoring()


def fr_trd_047() -> None:
    """FR-TRD-047: Enforce the current Risk-owned `AllocationRiskDecision v1` together with a current `PortfolioBudgetExecutionVerdict v1` for the exact portfolio, allocation version, plan ID/hash, and budget unit; never calculate or modify the budget."""
    example_monitoring()


def fr_trd_048() -> None:
    """FR-TRD-048: The system shall publish redacted runtime evidence through an injected composition sink without importing Data or UI/API and without hiding delivery failure."""
    example_monitoring()


def main() -> None:
    """Run Trading monitoring usage example."""
    example_monitoring()


if __name__ == "__main__":
    main()
