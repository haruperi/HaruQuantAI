"""Persistence and state tracking for Real-time Market Events."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contracts.common.models import UtcTimestamp
    from app.contracts.data.models import (
        MarketEvent,
        MarketFeedState,
    )
    from app.services.data.realtime_market_events.config import (
        RealtimeMarketEventsConfig,
    )


class RealtimeEventPersistence:
    """In-memory event buffer and feed state persistence store."""

    def __init__(self, config: RealtimeMarketEventsConfig) -> None:
        self._config = config
        self._feeds: dict[str, MarketFeedState] = {}
        self._provider_to_feed: dict[str, str] = {}
        self._event_buffers: dict[str, deque[MarketEvent]] = defaultdict(
            lambda: deque(maxlen=self._config.buffer_capacity)
        )
        self._feed_sequences: dict[str, int] = {}
        self._feed_disconnects: dict[str, UtcTimestamp] = {}

    def set_feed(self, feed_id: str, state: MarketFeedState) -> None:
        """Store or update a market feed state."""
        self._feeds[feed_id] = state

    def get_feed(self, feed_id: str) -> MarketFeedState | None:
        """Retrieve a market feed state by feed ID."""
        return self._feeds.get(feed_id)

    def bind_provider(self, provider_id: str, feed_id: str) -> None:
        """Associate a provider ID with a feed ID."""
        self._provider_to_feed[provider_id] = feed_id

    def get_feed_id_for_provider(self, provider_id: str) -> str | None:
        """Return the feed ID bound to a provider ID, if any."""
        return self._provider_to_feed.get(provider_id)

    def append_event(self, feed_id: str, event: MarketEvent) -> None:
        """Append an event to the ring buffer for a feed."""
        self._event_buffers[feed_id].append(event)

    def get_events(self, feed_id: str) -> list[MarketEvent]:
        """Return all buffered events for a feed."""
        return list(self._event_buffers[feed_id])

    def get_last_sequence(self, feed_id: str) -> int | None:
        """Get the last seen sequence number for a feed."""
        return self._feed_sequences.get(feed_id)

    def set_last_sequence(self, feed_id: str, seq: int) -> None:
        """Record the last seen sequence number for a feed."""
        self._feed_sequences[feed_id] = seq

    def record_disconnect(self, feed_id: str, disconnect_at: UtcTimestamp) -> None:
        """Record the timestamp when a feed disconnected."""
        self._feed_disconnects[feed_id] = disconnect_at

    def pop_disconnect(self, feed_id: str) -> UtcTimestamp | None:
        """Pop and return the disconnect timestamp for a feed, if recorded."""
        return self._feed_disconnects.pop(feed_id, None)

    def clear(self) -> None:
        """Reset all in-memory buffers and states."""
        self._feeds.clear()
        self._provider_to_feed.clear()
        self._event_buffers.clear()
        self._feed_sequences.clear()
        self._feed_disconnects.clear()
