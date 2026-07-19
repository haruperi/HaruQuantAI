"""Runnable usage examples for Trading monitoring requirements."""

from datetime import UTC, datetime

from app.services.trading.monitoring import (
    BudgetGate,
    OperationalEvent,
    emit_runtime_event,
)
from app.utils import logger

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def test_usage_events_operational_event() -> None:
    """Construct focused redacted Trading runtime evidence."""
    logger.debug("Running OperationalEvent usage example")
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
    assert event.schema_id == "trading.operational_event.v1"


def test_usage_events_emit_runtime_event() -> None:
    """Publish validated runtime evidence through an injected sink."""
    logger.debug("Running runtime-event publication usage example")
    published: list[OperationalEvent] = []
    event = OperationalEvent(
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
    emit_runtime_event(event, published.append)
    assert published == [event]


def test_usage_budgets_budget_gate() -> None:
    """Expose the documented budget-gate API without calculating policy."""
    logger.debug("Running BudgetGate usage API example")
    assert callable(BudgetGate.validate)
