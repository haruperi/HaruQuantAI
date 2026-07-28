"""Workflow integration for event persistence and state recovery."""

# ruff: noqa: INP001
from app.services.trading import TradingEvent, apply_execution_event
from tests.trading.conftest import NOW, MemoryStore


def test_recovery_preserves_unresolved_attempt() -> None:
    """A persisted send attempt reconstructs its unresolved retry lock."""
    store = MemoryStore()
    event = TradingEvent(
        event_id="attempt-001",
        event_type="send_attempted",
        aggregate_version=0,
        route="sim",
        tenant_id="account-001",
        authority_id="simulation",
        occurred_at=NOW,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        payload={"client_order_id": "client-001"},
    )
    projection = apply_execution_event(event, store)
    assert projection.status == "success"
    assert projection.data is not None
    assert projection.data.unresolved_attempt_ids == ("attempt-001",)
    assert (
        store.load_projection(("sim", "account-001", "simulation")) == projection.data
    )
