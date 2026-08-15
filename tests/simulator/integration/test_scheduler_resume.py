"""Integration evidence for scheduler serialization and resume."""

import asyncio
from datetime import UTC, datetime, timedelta

from app.services.simulator import (
    create_simulation_scheduler,
    restore_simulation_scheduler,
    run_simulation_scheduler_until_complete,
    schedule_simulation_event,
    serialize_simulation_scheduler,
)


def test_scheduler_resume_preserves_event_and_result_order() -> None:
    """Standing regression: restored pending work retains canonical order."""
    observed: list[int] = []
    handlers = {"record": lambda payload: observed.append(int(payload["value"]))}
    start = datetime(2026, 8, 15, tzinfo=UTC)
    scheduler = create_simulation_scheduler(start, handlers)
    event_ids = tuple(
        schedule_simulation_event(
            scheduler,
            scheduled_at=start + timedelta(seconds=value),
            priority="response_delivery",
            canonical_symbol="EURUSD",
            source_sequence=value,
            handler_id="record",
            payload={"value": value},
        )
        for value in (1, 2)
    )
    restored = restore_simulation_scheduler(
        serialize_simulation_scheduler(scheduler), handlers
    )
    asyncio.run(run_simulation_scheduler_until_complete(restored, event_ids[-1]))
    assert observed == [1, 2]
