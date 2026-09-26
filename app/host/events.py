"""Process-local, bounded event delivery for boot and settings updates.

Producers publish JSON snapshots on the owning event loop. Subscribers receive
independent copies through finite asyncio queues; slow consumers are marked for
resynchronization rather than blocking publishers. History is an in-memory ring,
not a durable log. Transport code owns subscription cleanup and reconnect policy.
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
        logger.debug("Event subscriber admitted")
        return subscriber

    def unsubscribe(self, subscriber: Subscriber) -> None:
        """Release a subscription without touching other consumers.

        Args:
            subscriber: Previously admitted subscriber; an already-removed instance is
                harmless.
        """
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)
        logger.debug("Event subscriber released")

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
        return delivered

    def replay(self, after: int = 0) -> list[dict[str, Any]]:
        """Copy retained events newer than a caller-supplied sequence.

        Args:
            after: Exclusive sequence lower bound; zero requests all retained history.

        Returns:
            Independent decoded event dictionaries in publication order; older evicted
            events are unavailable.
        """
        return [
            json.loads(item)
            for item in self._history
            if json.loads(item)["sequence"] > after
        ]

    def subscriber_count(self) -> int:
        """Count currently admitted subscriptions.

        Returns:
            Active subscription count, including any awaiting overflow cleanup.
        """
        return len(self._subscribers)
