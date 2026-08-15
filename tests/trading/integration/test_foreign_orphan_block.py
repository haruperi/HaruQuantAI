"""Foreign/manual orphan blocking tests for FR-TRD-109."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.trading import (
    assign_trade_ownership,
    build_trade_ownership,
    create_execution_position_store,
    create_position_authority_event,
    create_trade_ownership_registry,
    parse_trade_ownership,
    reconcile_position_authority_event,
)


def foreign_event(sequence: int, position_id: str) -> object:
    """Build one complete foreign authority event."""
    return create_position_authority_event(
        event_id=f"event-{sequence}",
        route="live",
        account_id="account-1",
        authority_id="mt5",
        deal_id=f"deal-{sequence}",
        position_id=position_id,
        symbol="EURUSD",
        side="LONG",
        state="OPEN",
        quantity=Decimal(1),
        source_sequence=sequence,
        available_at=datetime(2024, 1, 2, 12, tzinfo=UTC),
        reason="ORDER",
        activity_origin="manual",
    )


def test_foreign_exposure_is_orphaned_until_ownership_is_proven() -> None:
    """Trading records authority truth but never assigns a foreign owner."""
    registry = create_trade_ownership_registry()
    blocked = reconcile_position_authority_event(
        create_execution_position_store(),
        foreign_event(0, "orphan-position"),
        ownership_registry=registry,
    )
    assert blocked["disposition"] == "ORPHAN_BLOCKED"

    ownership = parse_trade_ownership(
        build_trade_ownership(
            ownership_id="ownership-1",
            owner_type="player",
            owner_id="owner-1",
            account_id="account-1",
            position_id="owned-position",
            trade_plan_id="plan-1",
            strategy_version="strategy-1",
            session_id="session-1",
            source_sequence=0,
        )
    )
    assign_trade_ownership(registry, ownership)
    admitted = reconcile_position_authority_event(
        create_execution_position_store(),
        foreign_event(0, "owned-position"),
        ownership_registry=registry,
    )
    assert admitted["disposition"] == "APPLIED"
