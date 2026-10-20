# ruff: noqa: INP001
"""Host event models and bounded asynchronous publish/subscribe delivery.

Description:
    Defines host events and the in-memory EventBus used by HTTP streaming,
    telemetry and settings notifications. Retains bounded replay, subscriber
    queues and delivery on each subscriber's event loop. Transport owns its
    existing lazy global bus; this module creates no service instance.

Purpose:
    FEAT-HOST-TRANSPORT: Share host events independently of HTTP gateway routing.

Key Capabilities:
    - FR-HOST-TRANSPORT-EVENT-BUS: Publish/replay events, manage subscriptions and
      inspect retained history [EventBus.publish(), EventBus.subscribe(),
      EventBus.update_subscription(), EventBus.unsubscribe(), EventBus.get_snapshot(),
      EventBus.clear(), EventBus.current_cursor, EventBus.channels]. Logging: DEBUG
      publish, INFO subscription changes, WARNING bounded-queue/delivery failures;
      existing transport tests explicitly verify FR logs.

Python API Usage:
    from app.host.events import EventBus
    bus = EventBus()
    event = bus.publish("settings.changed", payload={"revision": 1})

CLI Usage:
    uv run python -m app.host.transport --test-bus
"""

from __future__ import annotations

import asyncio
import secrets
import threading
from collections import deque
from collections.abc import Sequence
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any, Final

from app.host.logging import get_logger
from pydantic import BaseModel, ConfigDict, Field

__all__ = ["EventBus", "HostEvent"]

logger = get_logger(__name__)
CORE_EVENT_CHANNELS: Final = ("jobs", "system", "logs", "databanks", "settings.changed")
FR_BUS: Final = "FR-HOST-TRANSPORT-EVENT-BUS"
type _Chans = Sequence[str] | set[str]
type _Pld = dict[str, Any]


def _now_utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def _info(fr_id: str, msg: str) -> None:
    logger.info("%s: %s", fr_id, msg, extra={"fr_id": fr_id})


def _warn(fr_id: str, msg: str) -> None:
    logger.warning("%s: %s", fr_id, msg, extra={"fr_id": fr_id})


class HostEvent(BaseModel):
    """Discrete, monotonically sequenced event broadcast on the host EventBus."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    cursor: int
    channel: str
    event_type: str = "update"
    timestamp: str = Field(default_factory=_now_utc_iso)
    payload: _Pld = Field(default_factory=dict)


class _EventSnapshot(BaseModel):
    channel: str
    newest_cursor: int
    events: list[HostEvent] = Field(default_factory=list)
    has_gap: bool = False


class EventBus:
    """In-memory multi-channel pub/sub event bus with monotonic cursors."""

    def __init__(self, ring_capacity: int = 1024, max_queue_size: int = 256) -> None:
        self.ring_capacity = max(1, ring_capacity)
        self.max_queue_size = max(1, max_queue_size)
        self._lock, self._cursor_seq = threading.RLock(), 0
        self._ring: deque[HostEvent] = deque(maxlen=self.ring_capacity)
        self._subscribers: dict[str, tuple[set[str], asyncio.Queue[HostEvent]]] = {}
        self._channels: set[str] = set(CORE_EVENT_CHANNELS)
        self._subscriber_loops: dict[str, asyncio.AbstractEventLoop] = {}
        self._pending_deliveries: dict[str, int] = {}

    @property
    def current_cursor(self) -> int:
        """Return the highest monotonic cursor sequence value."""
        with self._lock:
            return self._cursor_seq

    @property
    def channels(self) -> list[str]:
        """Return sorted list of known event channels."""
        with self._lock:
            return sorted(self._channels)

    def publish(
        self,
        channel: str,
        event_type: str = "update",
        payload: _Pld | None = None,
        timestamp: str | None = None,
    ) -> HostEvent:
        """Publish an event to matching subscribers and append to the ring buffer."""
        with self._lock:
            self._cursor_seq += 1
            c, ch, et = self._cursor_seq, channel, event_type
            self._channels.add(ch)
            ts, p = timestamp or _now_utc_iso(), dict(payload or {})
            ev = HostEvent(cursor=c, channel=ch, event_type=et, timestamp=ts, payload=p)
            self._ring.append(ev)
            for sid, (chans, q) in list(self._subscribers.items()):
                if "*" in chans or ch in chans:
                    self._schedule_delivery(sid, q, ev)
        logger.debug("%s: Published %s on %s", FR_BUS, c, ch, extra={"fr_id": FR_BUS})
        return ev

    def _schedule_delivery(
        self, sub_id: str, queue: asyncio.Queue[HostEvent], event: HostEvent
    ) -> None:
        pending = self._pending_deliveries.get(sub_id, 0)
        if queue.qsize() + pending >= queue.maxsize:
            _warn(FR_BUS, f"Dropped cursor={event.cursor} for slow {sub_id}")
            return
        if (loop := self._subscriber_loops.get(sub_id)) is None:
            queue.put_nowait(event)
            return
        if loop.is_closed():
            return
        self._pending_deliveries[sub_id] = pending + 1
        try:
            loop.call_soon_threadsafe(self._deliver_event, sub_id, queue, event)
        except RuntimeError:
            self._pending_deliveries[sub_id] -= 1
            _warn(FR_BUS, "Subscriber loop closed during delivery")

    def _deliver_event(
        self, sub_id: str, queue: asyncio.Queue[HostEvent], event: HostEvent
    ) -> None:
        with self._lock:
            if sub_id in self._subscribers:
                self._pending_deliveries[sub_id] -= 1
                queue.put_nowait(event)

    def subscribe(
        self,
        channels: _Chans | None = None,
        since_cursor: int | None = None,
        max_queue_size: int | None = None,
    ) -> tuple[str, asyncio.Queue[HostEvent], list[HostEvent], bool]:
        """Subscribe to channels with optional replay from ``since_cursor``."""
        chans = set(channels) if channels else {"*"}
        q: asyncio.Queue[HostEvent] = asyncio.Queue(
            maxsize=max_queue_size or self.max_queue_size
        )
        sub_id, gap = f"sub-{secrets.token_hex(8)}", False
        replay: list[HostEvent] = []
        with self._lock:
            self._channels.update(ch for ch in chans if ch != "*")
            if since_cursor is not None and since_cursor >= 0 and self._ring:
                gap = since_cursor < self._ring[0].cursor - 1
                replay = [
                    e
                    for e in self._ring
                    if e.cursor > since_cursor and ("*" in chans or e.channel in chans)
                ]
            self._subscribers[sub_id] = (chans, q)
            self._pending_deliveries[sub_id] = 0
            with suppress(RuntimeError):
                self._subscriber_loops[sub_id] = asyncio.get_running_loop()
        _info(FR_BUS, f"Subscribed {sub_id} replay={len(replay)} gap={gap}.")
        return sub_id, q, replay, gap

    def update_subscription(self, subscriber_id: str, channels: _Chans) -> bool:
        """Update the channel set for an active subscriber."""
        with self._lock:
            if (entry := self._subscribers.get(subscriber_id)) is None:
                return False
            chans = set(channels) if channels else {"*"}
            self._channels.update(ch for ch in chans if ch != "*")
            self._subscribers[subscriber_id] = (chans, entry[1])
        _info(FR_BUS, f"Updated subscriber '{subscriber_id}' channels={sorted(chans)}.")
        return True

    def unsubscribe(self, subscriber_id: str) -> None:
        """Remove a subscriber queue from the EventBus."""
        with self._lock:
            self._subscriber_loops.pop(subscriber_id, None)
            self._pending_deliveries.pop(subscriber_id, None)
            if self._subscribers.pop(subscriber_id, None) is not None:
                _info(FR_BUS, f"Unsubscribed '{subscriber_id}'.")

    def get_snapshot(
        self, channel: str = "*", since_cursor: int | None = None, limit: int = 100
    ) -> _EventSnapshot:
        """Return retained historical events for ``channel``."""
        cap = max(1, min(limit, self.ring_capacity))
        with self._lock:
            r0 = self._ring[0].cursor - 1 if self._ring else -1
            gap = bool(self._ring and since_cursor is not None and since_cursor < r0)
            evs = [
                e
                for e in self._ring
                if channel in ("*", e.channel)
                and (since_cursor is None or e.cursor > since_cursor)
            ]
            ret, nc = (evs[-cap:] if len(evs) > cap else evs), self._cursor_seq
            return _EventSnapshot(
                channel=channel, newest_cursor=nc, events=ret, has_gap=gap
            )

    def clear(self) -> None:
        """Clear all retained events and active subscribers."""
        with self._lock:
            self._ring.clear()
            self._subscribers.clear()
            self._subscriber_loops.clear()
            self._pending_deliveries.clear()
