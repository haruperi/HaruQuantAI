"""Workflow integration for budget and monitoring delivery failures."""

# ruff: noqa: INP001

import pytest
from app.services.trading.contracts import TradingError
from app.services.trading.monitoring import (
    BudgetGate,
    OperationalEvent,
    emit_runtime_event,
)
from tests.trading.conftest import (
    NOW,
    monitoring_allocation,
    monitoring_request,
    monitoring_verdict,
)


def test_budget_and_event_delivery_failures_emit_incidents() -> None:
    """Budget mismatch blocks and event-delivery failure attempts an incident."""
    item = monitoring_request()
    with pytest.raises(TradingError, match="BUDGET_BLOCKED"):
        BudgetGate.validate(
            item,
            monitoring_allocation(),
            type(monitoring_verdict(item)).model_validate(
                {
                    **monitoring_verdict(item).model_dump(mode="python"),
                    "allowed": False,
                    "reasons": ("blocked",),
                }
            ),
            now=NOW,
        )
    delivered = []
    event = OperationalEvent(
        event_id="event-001",
        event_type="COST_OBSERVED",
        severity="warning",
        occurred_at=NOW,
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        facts={"cost": "1.25"},
        source_refs={"receipt": "receipt-001"},
    )

    def sink(value):
        """Retain delivery attempts and fail every publication."""
        delivered.append(value)
        raise RuntimeError("sink unavailable")

    with pytest.raises(TradingError, match="SERVICE_UNAVAILABLE"):
        emit_runtime_event(event, sink)
    assert [value.event_type for value in delivered] == [
        "COST_OBSERVED",
        "EVENT_DELIVERY_FAILED",
    ]
