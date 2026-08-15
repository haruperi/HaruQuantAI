"""Paired-route position reconciliation tests for FR-TRD-107."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.trading import (
    create_execution_position_store,
    create_position_authority_event,
    get_execution_position_snapshot,
    reconcile_position_authority_event,
)


def authority_event(
    route: str, sequence: int, deal_id: str, quantity: str, reason: str = "ORDER"
) -> object:
    """Build equivalent Simulation or live authority evidence."""
    return create_position_authority_event(
        event_id=f"{route}-event-{sequence}",
        route=route,
        account_id="account-1",
        authority_id=f"{route}-authority",
        deal_id=deal_id,
        position_id="position-1",
        symbol="EURUSD",
        side="SHORT" if reason in {"REVERSAL", "LIQUIDATION"} else "LONG",
        state="FLAT" if quantity == "0" else "OPEN",
        quantity=Decimal(quantity),
        source_sequence=sequence,
        available_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        reason=reason,
    )


def test_simulation_and_live_apply_identical_many_to_one_transitions() -> None:
    """Route changes authority identity, never projection semantics."""
    snapshots = []
    for route in ("sim", "live"):
        store = create_execution_position_store()
        for sequence, deal_id, quantity, reason in (
            (0, "deal-open", "2", "ORDER"),
            (1, "deal-modify", "2", "MODIFICATION"),
            (2, "deal-reduce", "1", "ORDER"),
            (3, "deal-protect", "0", "PROTECTION"),
            (4, "deal-reversal", "1", "REVERSAL"),
            (5, "deal-liquidate", "0", "LIQUIDATION"),
        ):
            result = reconcile_position_authority_event(
                store, authority_event(route, sequence, deal_id, quantity, reason)
            )
            assert result["disposition"] == "APPLIED"
        snapshots.append(get_execution_position_snapshot(store))
    assert snapshots[0] == snapshots[1]
