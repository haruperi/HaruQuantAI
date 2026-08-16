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


def bind_realism_stream(scheduler: object, concern: str, stream: object) -> None:
    """Bind one deterministic realism stream into scheduler checkpoint state."""
    if not isinstance(scheduler, _DeterministicScheduler):
        raise TypeError("invalid scheduler handle")
    scheduler.bind_realism_stream(concern, stream)


def schedule_calibrated_realism_event(
    scheduler: object,
    *,
    sampled: Mapping[str, object],
    scheduled_at: datetime,
    canonical_symbol: str,
    source_sequence: int,
    handler_id: str,
) -> str:
    """Schedule one admitted calibrated sample with its causal evidence.

    Args:
        scheduler: Opaque deterministic scheduler handle.
        sampled: Output from ``sample_calibrated_realism``.
        scheduled_at: Aware UTC delivery instant.
        canonical_symbol: Canonical instrument identity.
        source_sequence: Stable source-local sequence.
        handler_id: Registered scheduler handler.

    Returns:
        Stable scheduler event identity.

    Raises:
        TypeError: If the scheduler or sampled evidence is invalid.
        ValueError: If the sample lacks calibrated journal evidence.
    """
    if not isinstance(scheduler, _DeterministicScheduler):
        raise TypeError("invalid scheduler handle")
    required = {
        "artifact_checksum",
        "canonical",
        "component",
        "journal_event_type",
        "stream_draw",
        "value",
    }
    if not required.issubset(sampled) or sampled["canonical"] is not True:
        raise ValueError("scheduler realism sample is not canonically admitted")
    if sampled["journal_event_type"] != "calibrated_realism_sample":
        raise ValueError("scheduler realism journal evidence is invalid")
    component = str(sampled["component"])
    priority = (
        "response_delivery"
        if component in {"latency", "requote"}
        else "match_evaluation"
    )
    return scheduler.schedule(
        scheduled_at=scheduled_at,
        priority=priority,
        canonical_symbol=canonical_symbol,
        source_sequence=source_sequence,
        handler_id=handler_id,
        payload=dict(sampled),
    )


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
    "bind_realism_stream",
    "cancel_event",
    "create_scheduler",
    "get_scheduler_state",
    "pump_scheduler_once",
    "restore_scheduler",
    "run_scheduler_until_complete",
    "schedule_calibrated_realism_event",
    "schedule_event",
    "serialize_scheduler",
    "shutdown_scheduler",
]
