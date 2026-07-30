"""Workflow integration for budget and monitoring delivery failures."""

from app.services.trading import (
    create_operational_event,
    emit_runtime_event,
    validate_budget_authority,
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
    budget_result = validate_budget_authority(
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
    assert budget_result.status == "error"
    assert budget_result.error is not None
    assert budget_result.error.code == "BUDGET_BLOCKED"
    delivered = []
    event = create_operational_event(
        event_id="event-001",
        event_type="COST_OBSERVED",
        severity="warning",
        occurred_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        facts={"cost": "1.25"},
        source_refs={"receipt": "receipt-001"},
    )

    def sink(value):
        """Retain delivery attempts and fail every publication."""
        delivered.append(value)
        raise RuntimeError("sink unavailable")

    event_result = emit_runtime_event(event, sink)
    assert event_result.status == "error"
    assert event_result.error is not None
    assert event_result.error.code == "SERVICE_UNAVAILABLE"
    assert [value.event_type for value in delivered] == [
        "COST_OBSERVED",
        "EVENT_DELIVERY_FAILED",
    ]
