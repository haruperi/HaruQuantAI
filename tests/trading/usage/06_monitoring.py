"""Executable Trading monitoring usage example.

Demonstrates operational events, runtime event emission, and budget gates.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading.monitoring import (
    BudgetGate,
    OperationalEvent,
    emit_runtime_event,
)

NOW = datetime(2026, 7, 19, tzinfo=UTC)


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
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
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
        request_id="usage-request-002",
        workflow_id="usage-workflow-002",
        correlation_id="usage-correlation-002",
        facts={"health": "ready"},
        source_refs={"session": "session-001"},
    )
    emit_runtime_event(event2, published.append)
    print(f"Published runtime events count: {len(published)}")

    # 3. Budget gate
    print(f"BudgetGate validate is callable: {callable(BudgetGate.validate)}")


def main() -> None:
    """Run Trading monitoring usage example."""
    example_monitoring()


if __name__ == "__main__":
    main()
