"""Single-owner deterministic scheduler event pump."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import replace
from datetime import datetime
from typing import cast

from app.kernel.serialization import canonical_digest
from app.services.simulator.realism.random_streams import serialize
from app.services.simulator.scheduler.clock import _SimulatedClock
from app.services.simulator.scheduler.contracts import _ScheduledEvent
from app.services.simulator.scheduler.queue import _EventQueue

type _Handler = Callable[[Mapping[str, object]], object | Awaitable[object]]


class _DeterministicScheduler:
    """Own the queue, simulated clock, results, and handler registry."""

    def __init__(self, start_at: datetime, handlers: Mapping[str, _Handler]) -> None:
        """Initialize one scheduler from explicit deterministic dependencies."""
        self.clock = _SimulatedClock(start_at)
        self.queue = _EventQueue()
        self.handlers = dict(handlers)
        self.events: dict[str, _ScheduledEvent] = {}
        self.results: dict[str, object] = {}
        self.failures: dict[str, BaseException] = {}
        self.source_identities: set[tuple[datetime, str, str, int]] = set()
        self.next_sequence = 0
        self.shutdown = False
        self.realism_streams: dict[str, object] = {}

    def bind_realism_stream(self, concern: str, stream: object) -> None:
        """Bind one unique serializable concern stream to scheduler state."""
        state = serialize(stream)
        if concern != state["concern"] or concern in self.realism_streams:
            raise ValueError("scheduler realism concern binding is invalid")
        self.realism_streams[concern] = stream

    def schedule(
        self,
        *,
        scheduled_at: datetime,
        priority: str,
        canonical_symbol: str,
        source_sequence: int,
        handler_id: str,
        payload: Mapping[str, object],
        event_id: str | None = None,
    ) -> str:
        """Schedule one event and return its stable identity."""
        if self.shutdown:
            raise ValueError("scheduler is shut down")
        source_identity = (
            scheduled_at,
            priority,
            canonical_symbol,
            source_sequence,
        )
        if source_identity in self.source_identities:
            raise ValueError("duplicate scheduler source sequence")
        sequence = self.next_sequence
        self.next_sequence += 1
        identity = event_id or "scheduler-event-" + canonical_digest(
            {
                "scheduled_at": scheduled_at,
                "priority": priority,
                "canonical_symbol": canonical_symbol,
                "source_sequence": source_sequence,
                "scheduler_sequence": sequence,
                "handler_id": handler_id,
                "payload": payload,
            }
        )
        event = _ScheduledEvent(
            identity,
            scheduled_at,
            priority,
            canonical_symbol,
            source_sequence,
            sequence,
            handler_id,
            payload,
        )
        if handler_id not in self.handlers:
            raise ValueError("unknown scheduler handler identity")
        self.queue.push(event)
        self.source_identities.add(source_identity)
        self.events[identity] = event
        return identity

    def cancel(self, event_id: str) -> bool:
        """Mark one pending event cancelled without disturbing heap order."""
        event = self.events.get(event_id)
        if event is None or event.status != "pending":
            return False
        self.events[event_id] = replace(event, status="cancelled")
        return True

    async def pump_once(self) -> str:
        """Execute exactly one non-cancelled event."""
        if self.shutdown:
            raise ValueError("scheduler is shut down")
        while self.queue:
            queued = self.queue.pop()
            event = self.events[queued.event_id]
            if event.status == "cancelled":
                continue
            self.clock.advance_to(event.scheduled_at)
            try:
                value = self.handlers[event.handler_id](event.payload)
                if inspect.isawaitable(value):
                    value = await cast("Awaitable[object]", value)
                self.results[event.event_id] = value
                self.events[event.event_id] = replace(event, status="completed")
            except Exception as error:  # noqa: BLE001 - preserved for awaiting caller.
                self.failures[event.event_id] = error
                self.events[event.event_id] = replace(event, status="failed")
            return event.event_id
        raise ValueError("scheduler queue is empty")

    async def run_until_complete(self, event_id: str) -> object:
        """Pump deterministically until the selected event resolves."""
        if event_id not in self.events:
            raise ValueError("unknown scheduler event identity")
        while event_id not in self.results and event_id not in self.failures:
            await self.pump_once()
        if event_id in self.failures:
            raise self.failures[event_id]
        return self.results[event_id]


__all__ = ["_DeterministicScheduler", "_Handler"]
