"""Workflow integration for uncertain authority outcomes."""

from typing import Any

from app.services.trading import (
    build_broker_state_unknown_event,
    emit_runtime_event,
    resolve_unknown_outcome,
)

from tests.trading.conftest import (
    AuthorityStore,
    authority_projection,
    authority_receipt,
    authority_snapshot,
)


def test_unknown_outcome_blocks_retry() -> None:
    """An unresolved authority comparison retains the retry lock."""
    store = AuthorityStore(
        authority_projection(orders={"order-internal": {"state": "pending"}})
    )
    result = resolve_unknown_outcome(
        authority_receipt(), store, lambda route: authority_snapshot()
    )
    assert result.status == "success"
    assert result.data is not None
    assert result.data.transition == "retry_locked"
    assert not result.data.retry_allowed


def test_unknown_outcome_emits_critical_operational_event() -> None:
    """Persist retry lock before publishing one critical operational event."""
    request_id = "req-11111111-1111-4111-8111-111111111111"
    workflow_id = "wf-22222222-2222-4222-8222-222222222222"
    correlation_id = "cor-33333333-3333-4333-8333-333333333333"
    receipt_values = authority_receipt().model_dump(mode="python")
    receipt_values.update(
        request_id=request_id,
        correlation_id=correlation_id,
    )
    receipt = authority_receipt().model_validate(receipt_values)
    store = AuthorityStore(
        authority_projection(orders={"order-internal": {"state": "pending"}})
    )
    store.events[0] = store.events[0].model_copy(
        update={
            "request_id": request_id,
            "workflow_id": workflow_id,
            "correlation_id": correlation_id,
        }
    )
    published: list[Any] = []

    resolution = resolve_unknown_outcome(
        receipt,
        store,
        lambda route: authority_snapshot(),
    )
    assert resolution.data is not None
    resolution_data = resolution.data
    event_response = build_broker_state_unknown_event(
        receipt,
        incident_id=resolution_data.incident_reference,
        unresolved_scope=resolution_data.remaining_unresolved_scope,
        occurred_at=authority_snapshot().observed_at,
        workflow_id=workflow_id,
    )

    def sink(value: Any) -> None:
        """Assert durable transition evidence exists before publication."""
        assert store.events[-1].event_type == "reconciliation_transitioned"
        published.append(value)

    assert event_response.data is not None
    event = event_response.data
    assert emit_runtime_event(event, sink).status == "success"

    assert resolution_data.transition == "retry_locked"
    assert published == [event]
    assert event.event_type == "BROKER_STATE_UNKNOWN"
