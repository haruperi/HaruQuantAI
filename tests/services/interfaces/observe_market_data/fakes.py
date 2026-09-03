"""Shared fakes for observe-market-data gateway tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import uuid7

from app.contracts.common.events import DomainEvent
from app.contracts.data.models import (
    StreamMarketEventsRequest,
    StreamMarketEventsSubscription,
    StreamMarketEventsSuccess,
)

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def format_timestamp(moment: datetime) -> str:
    """Format a UTC datetime as a canonical wire timestamp."""
    return moment.astimezone(UTC).strftime(TIMESTAMP_FORMAT)


def make_event(
    sequence: int,
    symbol: str = "EURUSD",
    bid: str = "1.085",
    ask: str = "1.0852",
    occurred_at: datetime | None = None,
    payload: dict[str, Any] | None = None,
) -> DomainEvent:
    """Build one scripted provider domain event."""
    moment = occurred_at or datetime(2026, 9, 3, 12, 0, 0, tzinfo=UTC)
    return DomainEvent(
        event_id=str(uuid7()),
        sequence=sequence,
        event_type="market.tick",
        occurred_at=format_timestamp(moment),
        request_id=str(uuid7()),
        capability_snapshot_id=str(uuid7()),
        payload=payload
        if payload is not None
        else {"symbol": symbol, "bid": bid, "ask": ask},
    )


class FakeStreamProvider:
    """In-memory data.stream-market-events provider."""

    def __init__(self, events: tuple[DomainEvent, ...] = ()) -> None:
        """Store scripted events and record received subscriptions."""
        self.events = events
        self.subscriptions: list[StreamMarketEventsSubscription] = []

    async def stream_market_events(
        self,
        request: StreamMarketEventsRequest,
    ) -> StreamMarketEventsSuccess:
        """Not exercised by the gateway consumer path."""
        raise NotImplementedError("stream operations are not exercised")

    def subscribe_stream_market_events_events(
        self,
        request: StreamMarketEventsSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Record the subscription and yield the scripted events."""
        self.subscriptions.append(request)
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[DomainEvent]:
        """Yield the scripted events in order."""
        for event in self.events:
            yield event


class FailingStreamProvider(FakeStreamProvider):
    """Provider whose subscription fails mid-stream."""

    async def _iterate(self) -> AsyncIterator[DomainEvent]:
        """Yield one event, then fail."""
        for event in self.events:
            yield event
        message = "provider exploded"
        raise RuntimeError(message)


class QueuedStreamProvider(FakeStreamProvider):
    """Provider broadcasting fed events to every active subscriber."""

    def __init__(self) -> None:
        """Initialize the subscriber registry."""
        super().__init__()
        self._subscribers: list[asyncio.Queue[DomainEvent | None]] = []
        self.closed = False
        self.iterator_closed = False

    @property
    def subscriber_count(self) -> int:
        """Return the number of active subscriber queues."""
        return len(self._subscribers)

    def publish(self, event: DomainEvent) -> None:
        """Fan one event out to every active subscriber.

        Args:
            event: Domain event to broadcast.
        """
        for queue in self._subscribers:
            queue.put_nowait(event)

    def finish(self) -> None:
        """Terminate every active subscriber."""
        self.closed = True
        for queue in self._subscribers:
            queue.put_nowait(None)

    async def _iterate(self) -> AsyncIterator[DomainEvent]:
        """Yield broadcast events until a None terminator."""
        queue: asyncio.Queue[DomainEvent | None] = asyncio.Queue()
        self._subscribers.append(queue)
        try:
            while True:
                item = await queue.get()
                if item is None:
                    return
                yield item
        finally:
            self._subscribers.remove(queue)
            self.iterator_closed = True
