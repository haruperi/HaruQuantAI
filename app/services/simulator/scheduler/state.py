"""Serializable deterministic scheduler state codec."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from app.services.simulator.realism.random_streams import restore, serialize
from app.services.simulator.scheduler.pump import _DeterministicScheduler, _Handler


def _serialize_scheduler(scheduler: _DeterministicScheduler) -> dict[str, object]:
    """Return JSON-safe scheduler identity without live runtime objects."""
    return {
        "current_time": scheduler.clock.current.isoformat(),
        "next_sequence": scheduler.next_sequence,
        "shutdown": scheduler.shutdown,
        "events": tuple(
            {
                "event_id": event.event_id,
                "scheduled_at": event.scheduled_at.isoformat(),
                "priority": event.priority,
                "canonical_symbol": event.canonical_symbol,
                "source_sequence": event.source_sequence,
                "scheduler_sequence": event.scheduler_sequence,
                "handler_id": event.handler_id,
                "payload": dict(event.payload),
                "status": event.status,
            }
            for event in sorted(scheduler.events.values(), key=lambda item: item.key)
        ),
        "results": dict(scheduler.results),
        "realism_streams": {
            concern: serialize(stream)
            for concern, stream in sorted(scheduler.realism_streams.items())
        },
    }


def _restore_scheduler(
    state: Mapping[str, object], handlers: Mapping[str, _Handler]
) -> _DeterministicScheduler:
    """Restore pending deterministic identities with injected handlers."""
    scheduler = _DeterministicScheduler(
        datetime.fromisoformat(str(state["current_time"])), handlers
    )
    rows = state.get("events")
    if not isinstance(rows, (tuple, list)):
        raise TypeError("scheduler state events are invalid")
    for row in rows:
        if not isinstance(row, Mapping):
            raise TypeError("scheduler state event is invalid")
        if row.get("status") == "pending":
            payload = row.get("payload")
            if not isinstance(payload, Mapping):
                raise TypeError("scheduler state event payload is invalid")
            scheduler.schedule(
                event_id=str(row["event_id"]),
                scheduled_at=datetime.fromisoformat(str(row["scheduled_at"])),
                priority=str(row["priority"]),
                canonical_symbol=str(row["canonical_symbol"]),
                source_sequence=int(str(row["source_sequence"])),
                handler_id=str(row["handler_id"]),
                payload=dict(payload),
            )
            scheduler.next_sequence = max(
                scheduler.next_sequence, int(str(row["scheduler_sequence"])) + 1
            )
    scheduler.next_sequence = max(
        scheduler.next_sequence, int(str(state["next_sequence"]))
    )
    scheduler.shutdown = bool(state.get("shutdown", False))
    streams = state.get("realism_streams", {})
    if not isinstance(streams, Mapping):
        raise TypeError("scheduler realism stream state is invalid")
    for concern, stream_state in streams.items():
        if not isinstance(stream_state, Mapping):
            raise TypeError("scheduler realism stream entry is invalid")
        scheduler.bind_realism_stream(str(concern), restore(stream_state))
    return scheduler


__all__ = ["_restore_scheduler", "_serialize_scheduler"]
