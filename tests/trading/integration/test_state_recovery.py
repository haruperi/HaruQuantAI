"""Workflow integration for event persistence and state recovery."""

# ruff: noqa: INP001

from app.services.trading.state import TradingEvent, apply_execution_event
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
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
        payload={"client_order_id": "client-001"},
    )
    projection = apply_execution_event(event, store)
    assert projection.unresolved_attempt_ids == ("attempt-001",)
    assert store.load_projection(("sim", "account-001", "simulation")) == projection
