"""Integration evidence for stable scheduler total order."""

import asyncio
import json
import random
import subprocess
import sys
from datetime import UTC, datetime

from app.services.simulator import (
    create_simulation_scheduler,
    pump_simulation_scheduler_once,
    schedule_simulation_event,
)


def _run(seed: int) -> list[str]:
    """Run one shuffled admission set and return execution order."""
    observed: list[str] = []
    handlers = {"record": lambda payload: observed.append(str(payload["name"]))}
    scheduler = create_simulation_scheduler(datetime(2026, 8, 15, tzinfo=UTC), handlers)
    rows = [
        ("tick_arrival", "GBPUSD", 2, "third"),
        ("command_arrival", "EURUSD", 1, "first"),
        ("tick_arrival", "EURUSD", 1, "second"),
    ]
    random.Random(seed).shuffle(rows)
    event_ids = [
        schedule_simulation_event(
            scheduler,
            scheduled_at=datetime(2026, 8, 15, tzinfo=UTC),
            priority=priority,
            canonical_symbol=symbol,
            source_sequence=sequence,
            handler_id="record",
            payload={"name": name},
        )
        for priority, symbol, sequence, name in rows
    ]

    async def _drain() -> None:
        for _event_id in event_ids:
            await pump_simulation_scheduler_once(scheduler)

    asyncio.run(_drain())
    return observed


def test_scheduler_total_order_is_cross_process_stable() -> None:
    """Standing regression: shuffled cold runs produce identical total order."""
    assert _run(1) == _run(2) == ["first", "second", "third"]
    script = """
import json
from datetime import UTC, datetime
from app.services.simulator.scheduler.contracts import _ScheduledEvent
rows = [
    _ScheduledEvent("third", datetime(2026, 8, 15, tzinfo=UTC), "tick_arrival", "GBPUSD", 2, 2, "record"),
    _ScheduledEvent("first", datetime(2026, 8, 15, tzinfo=UTC), "command_arrival", "EURUSD", 1, 1, "record"),
    _ScheduledEvent("second", datetime(2026, 8, 15, tzinfo=UTC), "tick_arrival", "EURUSD", 1, 0, "record"),
]
print(json.dumps([event.event_id for event in sorted(rows, key=lambda event: event.key)]))
"""
    outputs = [
        subprocess.run(  # noqa: S603 - fixed interpreter and local test program.
            [sys.executable, "-c", script],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        for _index in range(2)
    ]
    assert outputs == [json.dumps(["first", "second", "third"])] * 2
