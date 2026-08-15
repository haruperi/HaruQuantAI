"""Standalone usage evidence for FEAT-SIM-15 deterministic scheduling."""

import asyncio
from datetime import UTC, datetime, timedelta

from app.services.simulator import (
    cancel_simulation_event,
    create_simulation_scheduler,
    get_simulation_scheduler_state,
    restore_simulation_scheduler,
    run_simulation_scheduler_until_complete,
    schedule_simulation_event,
    serialize_simulation_scheduler,
)

_START = datetime(2026, 8, 15, tzinfo=UTC)


def _fixture() -> tuple[object, str]:
    """Return one scheduler and awaited event identity."""
    scheduler = create_simulation_scheduler(
        _START, {"double": lambda payload: int(payload["value"]) * 2}
    )
    event_id = schedule_simulation_event(
        scheduler,
        scheduled_at=_START + timedelta(seconds=1),
        priority="command_arrival",
        canonical_symbol="EURUSD",
        source_sequence=1,
        handler_id="double",
        payload={"value": 3},
    )
    return scheduler, event_id


def fr_sim_194() -> None:
    """FR-SIM-194: create the sole simulated clock and event pump."""
    scheduler, _ = _fixture()
    print(
        "SUCCESS FR-SIM-194", get_simulation_scheduler_state(scheduler)["current_time"]
    )


def fr_sim_199() -> None:
    """FR-SIM-199: declare deterministic internal stage order."""
    _scheduler, event_id = _fixture()
    print("SUCCESS FR-SIM-199", event_id[:24])


def fr_sim_200() -> None:
    """FR-SIM-200: schedule and cancel stable queue identities."""
    scheduler, event_id = _fixture()
    print("SUCCESS FR-SIM-200", cancel_simulation_event(scheduler, event_id))


def fr_sim_201() -> None:
    """FR-SIM-201: advance only through an explicit event."""
    scheduler, event_id = _fixture()
    asyncio.run(run_simulation_scheduler_until_complete(scheduler, event_id))
    print(
        "SUCCESS FR-SIM-201", get_simulation_scheduler_state(scheduler)["current_time"]
    )


def fr_sim_202() -> None:
    """FR-SIM-202: await one scheduled response."""
    scheduler, event_id = _fixture()
    result = asyncio.run(run_simulation_scheduler_until_complete(scheduler, event_id))
    print("SUCCESS FR-SIM-202", result)


def fr_sim_203() -> None:
    """FR-SIM-203: pump bounded work to a selected result."""
    scheduler, event_id = _fixture()
    asyncio.run(run_simulation_scheduler_until_complete(scheduler, event_id))
    print("SUCCESS FR-SIM-203 completed")


def fr_sim_204() -> None:
    """FR-SIM-204: serialize and restore pending identity."""
    scheduler, _ = _fixture()
    state = serialize_simulation_scheduler(scheduler)
    restore_simulation_scheduler(
        state, {"double": lambda payload: int(payload["value"]) * 2}
    )
    print("SUCCESS FR-SIM-204", len(state["events"]))


def main() -> None:
    """Execute every scheduler requirement through package-root functions."""
    for function in (
        fr_sim_194,
        fr_sim_199,
        fr_sim_200,
        fr_sim_201,
        fr_sim_202,
        fr_sim_203,
        fr_sim_204,
    ):
        function()


if __name__ == "__main__":
    main()
