"""Deterministic execution scheduler feature API."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from app.services.simulator.scheduler.pump import _DeterministicScheduler, _Handler
from app.services.simulator.scheduler.state import (
    _restore_scheduler,
    _serialize_scheduler,
)


def create_scheduler(start_at: datetime, handlers: Mapping[str, _Handler]) -> object:
    """Create one opaque deterministic scheduler."""
    return _DeterministicScheduler(start_at, handlers)


def schedule_event(scheduler: object, **fields: object) -> str:
    """Schedule one event on an opaque scheduler."""
    if not isinstance(scheduler, _DeterministicScheduler):
        raise TypeError("invalid scheduler handle")
    return scheduler.schedule(**fields)  # type: ignore[arg-type]


def cancel_event(scheduler: object, event_id: str) -> bool:
    """Cancel one pending scheduler event."""
    if not isinstance(scheduler, _DeterministicScheduler):
        raise TypeError("invalid scheduler handle")
    return scheduler.cancel(event_id)


def get_scheduler_state(scheduler: object) -> Mapping[str, object]:
    """Return bounded detached scheduler state."""
    if not isinstance(scheduler, _DeterministicScheduler):
        raise TypeError("invalid scheduler handle")
    return _serialize_scheduler(scheduler)


async def pump_scheduler_once(scheduler: object) -> str:
    """Pump one deterministic event."""
    if not isinstance(scheduler, _DeterministicScheduler):
        raise TypeError("invalid scheduler handle")
    return await scheduler.pump_once()


async def run_scheduler_until_complete(scheduler: object, event_id: str) -> object:
    """Pump until one selected event resolves."""
    if not isinstance(scheduler, _DeterministicScheduler):
        raise TypeError("invalid scheduler handle")
    return await scheduler.run_until_complete(event_id)


def serialize_scheduler(scheduler: object) -> Mapping[str, object]:
    """Serialize scheduler state without runtime objects."""
    return get_scheduler_state(scheduler)


def restore_scheduler(
    state: Mapping[str, object], handlers: Mapping[str, _Handler]
) -> object:
    """Restore an opaque scheduler using an explicit handler registry."""
    return _restore_scheduler(state, handlers)


def shutdown_scheduler(scheduler: object) -> None:
    """Stop admission and pumping for one scheduler."""
    if not isinstance(scheduler, _DeterministicScheduler):
        raise TypeError("invalid scheduler handle")
    scheduler.shutdown = True


__all__ = [
    "cancel_event",
    "create_scheduler",
    "get_scheduler_state",
    "pump_scheduler_once",
    "restore_scheduler",
    "run_scheduler_until_complete",
    "schedule_event",
    "serialize_scheduler",
    "shutdown_scheduler",
]
