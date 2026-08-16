"""Integration evidence for lifecycle recovery at durable boundaries."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.simulator.execution.lifecycle import build_lifecycle_deal
from app.services.simulator.recovery import (
    build_replay_identity,
    create_recovery_checkpoint,
    restore_simulation_session,
)


def test_lifecycle_mapping_survives_verified_checkpoint_restore() -> None:
    """Referential deal material is unchanged after checkpoint verification."""
    occurred_at = datetime(2026, 8, 17, tzinfo=UTC)
    deal = build_lifecycle_deal(
        order_id="order-1",
        account_id="account-1",
        position_id="position-1",
        side="BUY",
        quantity=Decimal(1),
        price=Decimal("1.1"),
        entry="DEAL_ENTRY_IN",
        reason="EXPERT",
        occurred_at=occurred_at,
        economic_at=occurred_at,
        available_at=occurred_at,
        source_sequence=1,
        fee_evidence={"commission": Decimal(0)},
        authority_snapshot={
            "position": {
                "position_id": "position-1",
                "symbol": "EURUSD",
                "side": "LONG",
                "state": "OPEN",
                "quantity": Decimal(1),
                "source_sequence": 1,
            },
            "account": {"equity": Decimal(1000)},
        },
        ledger_reference="ledger-1",
    )
    identity = build_replay_identity(
        run_id="run-1",
        scenario_id="scenario-1",
        scenario_version="v1",
        scenario_hash="a" * 64,
        data_ref="data-1",
        data_hash="b" * 64,
        execution_profile_id="execution-1",
        execution_profile_hash="c" * 64,
        rules_version="v1",
        seed=1,
    )
    checkpoint = create_recovery_checkpoint(
        session_id="session-1",
        sequence=0,
        previous_hash=None,
        replay_identity=identity,
        state_payload={"deals": (dict(deal),), "event_boundary": "deal_applied"},
        created_at=occurred_at,
    )
    restored = restore_simulation_session(
        (checkpoint,), expected_replay_id=identity.replay_id
    )
    assert restored["state_payload"]["deals"][0] == deal  # type: ignore[index]
