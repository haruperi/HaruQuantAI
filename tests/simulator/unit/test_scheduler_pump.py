"""Unit evidence for scheduler future resolution and failures."""

import asyncio
from datetime import UTC, datetime

import pytest
from app.services.simulator import (
    cancel_simulation_event,
    create_simulation_scheduler,
    pump_simulation_scheduler_once,
    run_simulation_scheduler_until_complete,
    schedule_simulation_event,
    shutdown_simulation_scheduler,
)

_NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _schedule(
    scheduler: object, handler_id: str = "ok", source_sequence: int = 0
) -> str:
    """Schedule one fixture event."""
    return schedule_simulation_event(
        scheduler,
        scheduled_at=_NOW,
        priority="command_arrival",
        canonical_symbol="EURUSD",
        source_sequence=source_sequence,
        handler_id=handler_id,
        payload={"value": 2},
    )


def test_fr_sim_202_203_awaited_mutation_resolves_without_sleep() -> None:
    """FR-SIM-202/203: awaited handler result resolves through pumping."""

    async def handler(payload: object) -> int:
        return int(payload["value"]) + 1  # type: ignore[index]

    scheduler = create_simulation_scheduler(_NOW, {"ok": handler})
    event_id = _schedule(scheduler)
    assert (
        asyncio.run(run_simulation_scheduler_until_complete(scheduler, event_id)) == 3
    )


def test_cancellation_failure_empty_queue_and_shutdown() -> None:
    """FR-SIM-203: bounded failure boundaries are deterministic."""

    def fail(_payload: object) -> None:
        raise RuntimeError("bounded failure")

    scheduler = create_simulation_scheduler(
        _NOW, {"ok": lambda payload: payload, "fail": fail}
    )
    cancelled = _schedule(scheduler)
    assert cancel_simulation_event(scheduler, cancelled) is True
    failed = _schedule(scheduler, "fail", 1)
    with pytest.raises(RuntimeError, match="bounded failure"):
        asyncio.run(run_simulation_scheduler_until_complete(scheduler, failed))
    with pytest.raises(ValueError, match="empty"):
        asyncio.run(pump_simulation_scheduler_once(scheduler))
    shutdown_simulation_scheduler(scheduler)
    with pytest.raises(ValueError, match="shut down"):
        _schedule(scheduler)


def test_duplicate_source_sequence_fails_closed() -> None:
    """FR-SIM-200: duplicate source identity is rejected."""
    scheduler = create_simulation_scheduler(_NOW, {"ok": lambda payload: payload})
    _schedule(scheduler)
    with pytest.raises(ValueError, match=r"duplicate.*source sequence"):
        _schedule(scheduler)
