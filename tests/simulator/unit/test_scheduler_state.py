"""Unit evidence for serializable scheduler state."""

from datetime import UTC, datetime

from app.kernel.serialization import canonical_json
from app.services.simulator import (
    create_simulation_scheduler,
    restore_simulation_scheduler,
    schedule_simulation_event,
    serialize_simulation_scheduler,
)


def test_fr_sim_204_state_round_trip_contains_no_runtime_objects() -> None:
    """FR-SIM-204: pending identity round-trips without callbacks/futures."""
    now = datetime(2026, 8, 15, tzinfo=UTC)
    handlers = {"ok": lambda payload: payload}
    scheduler = create_simulation_scheduler(now, handlers)
    schedule_simulation_event(
        scheduler,
        scheduled_at=now,
        priority="tick_arrival",
        canonical_symbol="EURUSD",
        source_sequence=7,
        handler_id="ok",
        payload={"safe": True},
    )
    state = serialize_simulation_scheduler(scheduler)
    canonical_json(state)
    restored = restore_simulation_scheduler(state, handlers)
    assert serialize_simulation_scheduler(restored)["events"] == state["events"]
