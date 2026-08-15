"""Authority event ordering tests for FR-TRD-108."""

# ruff: noqa: INP001

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.trading import (
    create_execution_position_store,
    create_position_authority_event,
    reconcile_position_authority_event,
)
from app.services.trading.contracts import TradingError


def event(sequence: int, identity: str | None = None) -> object:
    """Build one complete route-neutral authority event."""
    return create_position_authority_event(
        event_id=identity or f"event-{sequence}",
        route="sim",
        account_id="account-1",
        authority_id="simulator",
        deal_id=f"deal-{sequence}",
        position_id="position-1",
        symbol="EURUSD",
        side="LONG",
        state="OPEN",
        quantity=Decimal(1),
        source_sequence=sequence,
        available_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        reason="ORDER",
    )


def test_duplicate_late_and_gap_events_fail_closed_deterministically() -> None:
    """Only the next sequence changes projection and durable watermark."""
    store = create_execution_position_store()
    assert (
        reconcile_position_authority_event(store, event(10))["disposition"] == "APPLIED"
    )
    assert (
        reconcile_position_authority_event(store, event(10))["disposition"]
        == "DUPLICATE"
    )
    assert reconcile_position_authority_event(store, event(9))["disposition"] == "LATE"
    with pytest.raises(TradingError, match="RECONCILIATION_REQUIRED"):
        reconcile_position_authority_event(store, event(12))
    with pytest.raises(TradingError, match="RECONCILIATION_REQUIRED"):
        reconcile_position_authority_event(store, event(10, "conflict"))
