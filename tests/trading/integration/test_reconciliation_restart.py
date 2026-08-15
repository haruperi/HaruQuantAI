"""Durable-watermark restart tests for FR-TRD-110."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.trading import (
    create_execution_position_store,
    create_position_authority_event,
    get_execution_position_snapshot,
    reconcile_position_authority_event,
    restore_execution_position_store,
    serialize_execution_position_store,
)


def test_restart_replays_no_applied_authority_event() -> None:
    """Projection and watermark restore together and suppress duplicate apply."""
    event = create_position_authority_event(
        event_id="event-1",
        route="sim",
        account_id="account-1",
        authority_id="simulator",
        deal_id="deal-1",
        position_id="position-1",
        symbol="EURUSD",
        side="LONG",
        state="OPEN",
        quantity=Decimal(1),
        source_sequence=7,
        available_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        reason="ORDER",
    )
    store = create_execution_position_store()
    assert reconcile_position_authority_event(store, event)["disposition"] == "APPLIED"
    before = get_execution_position_snapshot(store)
    restored = restore_execution_position_store(
        serialize_execution_position_store(store)
    )
    assert (
        reconcile_position_authority_event(restored, event)["disposition"]
        == "DUPLICATE"
    )
    assert get_execution_position_snapshot(restored) == before
