"""Scheduler-bound realism stream resume evidence."""

from datetime import UTC, datetime

from app.services.simulator import (
    bind_realism_stream_to_scheduler,
    create_realism_stream,
    create_simulation_scheduler,
    restore_realism_stream,
    restore_simulation_scheduler,
    sample_realism_stream,
    serialize_simulation_scheduler,
)


def test_rng_counter_resume_preserves_next_draw_and_scheduler_order() -> None:
    """FR-SIM-176/242: scheduler checkpoint preserves exact stream counters."""
    stream = create_realism_stream({"seed": 5, "symbol": "EURUSD"}, "latency")
    scheduler = create_simulation_scheduler(
        datetime(2025, 1, 1, tzinfo=UTC), {"noop": lambda payload: payload}
    )
    bind_realism_stream_to_scheduler(scheduler, "latency", stream)
    sample_realism_stream(stream)
    state = serialize_simulation_scheduler(scheduler)
    restored_scheduler = restore_simulation_scheduler(
        state, {"noop": lambda payload: payload}
    )
    restored_state = serialize_simulation_scheduler(restored_scheduler)
    assert restored_state == state
    streams = restored_state["realism_streams"]
    restored_stream = restore_realism_stream(streams["latency"])  # type: ignore[index]
    assert sample_realism_stream(restored_stream) == sample_realism_stream(stream)
