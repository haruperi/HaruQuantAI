"""Process-Local Publish/Subscribe Event Bus and Replay Buffer.

Description:
    This module provides in-process, non-blocking publish/subscribe event
    distribution, bounded subscriber queues, and an in-memory ring buffer for
    historical event replay. It exists to decouple state-changing host services
    from real-time event consumers (UI WebSocket streams, SSE endpoints, testing
    probes) without permitting slow or stalling consumers to block event-loop
    execution. Externally, it participates in three major workflows: (1)
    `Startup.mark()` in `app.host.bootstrap` publishes `boot.progress` lifecycle
    events; (2) `SettingsStore.patch()` in `app.host.settings` publishes
    `settings.changed` updates; and (3) The transport layer (`app.host.transport`)
    subscribes to channels for SSE and WebSocket connections, replaying missed
    events to reconnecting clients via `replay()`. Internally, `validate_channel()`
    enforces topic namespace syntax; `Subscriber` encapsulates a bounded queue with
    overflow detection; and `EventBus` manages monotonic sequence numbers, circular
    history, and non-blocking subscriber fan-out.

Purpose:
    FEAT-HOST-EVENTS: In-Process Pub/Sub Event Bus and Replay Buffer.
    Provides namespaced topic filtering, non-blocking fan-out delivery, circular
    replay buffering, and overflow-guarded subscriber queues.

Key Capabilities:
    - FR-HOST-EVENTS-TOPIC-VALIDATION: Namespaced Channel Validation
      Associated: `validate_channel()`
      Logging: Enforces syntax and length limits on channel strings with
      ChannelError validation.
    - FR-HOST-EVENTS-SUBSCRIPTION-MANAGEMENT: Bounded Subscription Lifecycle
      Associated: `EventBus.subscribe()`, `EventBus.unsubscribe()`
      Logging: Emits debug log when subscribers are admitted or released,
      enforcing max subscriber limits.
    - FR-HOST-EVENTS-NONBLOCKING-PUBLISH: Event Fan-Out & Sequencing
      Associated: `EventBus.publish()`
      Logging: Emits debug log on event publication with sequence number and
      delivered count, and emits warning log on subscriber queue overflow.
    - FR-HOST-EVENTS-RING-REPLAY: Circular Historical Event Replay
      Associated: `EventBus.replay()`
      Logging: Emits debug log with event count upon historical event replay
      request.

Python API Usage:
    ```python
    from app.host.events import EventBus

    # 1. Instantiate process event bus
    bus = EventBus(queue_size=256)

    # 2. Subscribe to topics
    subscriber = bus.subscribe(["boot.progress", "settings.changed"])

    # 3. Publish an event
    delivered = bus.publish("settings.changed", {"theme": "dark"})

    # 4. Replay missed events after reconnect
    missed = bus.replay(after=10)

    # 5. Clean up subscription
    bus.unsubscribe(subscriber)
    ```

CLI Usage:
    The event bus is verified via host lifecycle and event delivery test
    suites:
    ```bash
    # Run in-process event bus tests
    uv run pytest tests/host/test_events.py

    # Test full lifecycle and event delivery integration
    uv run pytest tests/host/test_lifecycle.py
    ```
"""

import asyncio
import json
import re
from collections import deque
from dataclasses import dataclass
from typing import Any

from app.host.logging import get_logger

logger = get_logger(__name__)
MAX_TOPICS = 16
MAX_SUBSCRIBERS = 256
MAX_EVENT_BYTES = 262144
SETTINGS_CHANNEL = "settings.changed"


class ChannelError(ValueError):
    """An event topic or subscriber limit is invalid."""


def validate_channel(channel: str) -> str:
    """Validate a bounded namespaced event-topic string.

    Args:
        channel: Lowercase topic starting with a letter, followed by letters, digits,
            dots, or underscores.

    Returns:
        The unchanged topic when it matches the 100-character limit.

    Raises:
        ChannelError: The topic syntax or length is invalid.
    """
    if not re.fullmatch(r"[a-z][a-z0-9_.]{0,99}", channel):
        raise ChannelError("Invalid channel")
    return channel


@dataclass(eq=False)
class Subscriber:
    """Track one subscription and its bounded delivery queue.

    channels determines delivery eligibility. queue contains independent event
    objects. overflow remains set after any dropped delivery so the transport can
    request a fresh snapshot and release this subscription.
    """

    channels: tuple[str, ...]
    queue: asyncio.Queue[dict[str, Any]]
    overflow: bool = False


class EventBus:
    """Own event sequence, bounded history, and active client queues.

    Call methods on the same event loop; no cross-thread synchronization is provided.
    Successful serialization advances the sequence even if no subscriber receives
    an event. Returned payload copies do not share state with retained history.
    """

    def __init__(self, *, queue_size: int = 256) -> None:
        """Allocate an empty replay ring and subscription collection.

        Args:
            queue_size: Positive capacity used for both history and each subscriber
                queue.

        Raises:
            ValueError: queue_size is less than one.
        """
        if queue_size < 1:
            raise ValueError("Queue capacity must be positive")
        self.capacity = queue_size
        self.sequence = 0
        self._history: deque[str] = deque(maxlen=queue_size)
        self._subscribers: list[Subscriber] = []

    def subscribe(self, channels: list[str] | tuple[str, ...]) -> Subscriber:
        """Register a finite queue for explicitly requested topics.

        Args:
            channels: Nonempty collection of validated topic names, at most MAX_TOPICS.

        Returns:
            Subscriber to pass to unsubscribe when its transport closes.

        Raises:
            ChannelError: Topic syntax or topic/subscriber capacity is invalid.
        """
        if (
            not channels
            or len(channels) > MAX_TOPICS
            or len(self._subscribers) >= MAX_SUBSCRIBERS
        ):
            raise ChannelError("Subscription limit exceeded")
        subscriber = Subscriber(
            tuple(validate_channel(c) for c in channels), asyncio.Queue(self.capacity)
        )
        self._subscribers.append(subscriber)
        logger.info("Event subscriber admitted")
        return subscriber

    def unsubscribe(self, subscriber: Subscriber) -> None:
        """Release a subscription without touching other consumers.

        Args:
            subscriber: Previously admitted subscriber; an already-removed instance is
                harmless.
        """
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
        logger.info("Event subscriber released")

    def publish(self, channel: str, data: Any) -> int:
        """Snapshot a payload and enqueue independent copies without waiting.

        Successful serialization increments sequence and retains history. Full queues
        set overflow and skip delivery; publishing is not rolled back for slow
        consumers.

        Args:
            channel: Validated topic name.
            data: JSON-serializable payload; NaN and infinities are rejected.

        Returns:
            Number of matching subscriber queues that accepted the event.

        Raises:
            ChannelError: Topic is invalid or serialized event exceeds MAX_EVENT_BYTES.
            ValueError: JSON encoding rejects a value.
            TypeError: Payload contains values unsupported by JSON.
        """
        validate_channel(channel)
        encoded = json.dumps(
            {"sequence": self.sequence + 1, "channel": channel, "data": data},
            allow_nan=False,
        )
        if len(encoded.encode()) > MAX_EVENT_BYTES:
            raise ChannelError("Event exceeds limit")
        self.sequence += 1
        self._history.append(encoded)
        delivered = 0
        for subscriber in self._subscribers:
            if channel not in subscriber.channels:
                continue
            try:
                subscriber.queue.put_nowait(json.loads(encoded))
                delivered += 1
            except asyncio.QueueFull:
                subscriber.overflow = True
                logger.warning("Event subscriber overflow; snapshot required")
        logger.info(
            "Event published: channel=%s, seq=%d, delivered=%d",
            channel,
            self.sequence,
            delivered,
        )
        return delivered

    def replay(self, after: int = 0) -> list[dict[str, Any]]:
        """Copy retained events newer than a caller-supplied sequence.

        Args:
            after: Exclusive sequence lower bound; zero requests all retained history.

        Returns:
            Independent decoded event dictionaries in publication order; older evicted
            events are unavailable.
        """
        replayed = [
            json.loads(item)
            for item in self._history
            if json.loads(item)["sequence"] > after
        ]
        logger.info(
            "Event replay requested: after=%d, returned=%d",
            after,
            len(replayed),
        )
        return replayed

    def subscriber_count(self) -> int:
        """Count currently admitted subscriptions.

        Returns:
            Active subscription count, including any awaiting overflow cleanup.
        """
        return len(self._subscribers)
