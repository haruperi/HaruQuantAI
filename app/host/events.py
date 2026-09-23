"""Channel pub/sub event hub with an SSE endpoint.

The hub mirrors the SQX shell's project/channel update model (ledger
SQX144-EV-000009) adapted to a web satellite: subscribers stream over
server-sent events at ``GET /api/v1/events?channels=a,b``, and host or
future domain code publishes to named channels via :meth:`EventBus.publish`
or ``POST /api/v1/events/publish``.

Delivery semantics are deliberately simple and bounded: each subscriber owns
a fixed-size queue; when it is full, further events are dropped **for that
subscriber only** (a slow consumer never blocks or starves others), and the
publish return value reports how many subscribers actually received the
event. Channel names are strictly validated (lowercase, dot/dash/underscore
separated) so routes, logs, and future persistence can rely on them as safe
identifiers.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from app.host.envelope import (
    ValidationIssue,
    error_payload,
    success_payload,
)
from app.host.http import (
    MalformedRequestError,
    envelope_response,
    read_json_body,
    request_id_of,
)

CHANNEL_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
DEFAULT_QUEUE_SIZE = 100
SETTINGS_CHANNEL = "settings.changed"


class ChannelError(Exception):
    """Raised when a channel name is malformed."""


def validate_channel(channel: str) -> str:
    """Return ``channel`` when well-formed; raise ``ChannelError`` otherwise.

    Valid names start with a lowercase letter and continue with lowercase
    letters, digits, dots, dashes, or underscores (max 64 characters) —
    for example ``settings.changed`` or ``builder.progress``.

    Raises:
        ChannelError: If the name does not match the pattern.
    """
    if not CHANNEL_PATTERN.fullmatch(channel):
        raise ChannelError(
            f"Channel names must match {CHANNEL_PATTERN.pattern}: {channel!r}"
        )
    return channel


class Subscriber:
    """One SSE consumer bound to a set of channels.

    Attributes:
        channels: The exact channel names this subscriber receives.
        queue: Bounded queue of ``{"channel", "data"}`` events drained by
            the SSE stream generator.
    """

    def __init__(self, channels: tuple[str, ...], queue_size: int) -> None:
        """Bind a subscriber to ``channels`` with a bounded queue."""
        self.channels = channels
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=queue_size)

    def matches(self, channel: str) -> bool:
        """Return whether this subscriber listens to ``channel``."""
        return channel in self.channels


class EventBus:
    """In-process publish/subscribe hub with strictly validated channels.

    Subscriptions are in-memory only: they die with the process, and there
    is no replay — subscribers see only events published while attached.
    """

    def __init__(self, *, queue_size: int = DEFAULT_QUEUE_SIZE) -> None:
        """Create a hub.

        Args:
            queue_size: Per-subscriber queue capacity; a full queue drops
                events for that subscriber instead of blocking publishers.
        """
        self._subscribers: list[Subscriber] = []
        self._queue_size = queue_size

    def subscribe(self, channels: list[str] | tuple[str, ...]) -> Subscriber:
        """Register a subscriber for the given validated channels.

        Args:
            channels: Channel names to receive; every entry must be valid.

        Returns:
            The registered :class:`Subscriber` (drain its ``queue``).

        Raises:
            ChannelError: If any name is malformed.
        """
        validated = tuple(validate_channel(channel) for channel in channels)
        subscriber = Subscriber(validated, self._queue_size)
        self._subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: Subscriber) -> None:
        """Remove a subscriber; safe to call twice.

        Callers should invoke this in a ``finally`` block so disconnected
        streams never leak queue capacity.
        """
        if subscriber in self._subscribers:
            self._subscribers.remove(subscriber)

    def publish(self, channel: str, data: Any) -> int:
        """Push an event to matching subscribers; return the delivery count.

        A full subscriber queue drops the event for that subscriber only —
        publication itself never blocks or raises.

        Args:
            channel: Target channel name (validated).
            data: Any JSON-serializable event payload.

        Returns:
            The number of subscribers that actually received the event.

        Raises:
            ChannelError: If ``channel`` is malformed.
        """
        validate_channel(channel)
        event = {"channel": channel, "data": data}
        delivered = 0
        for subscriber in self._subscribers:
            if not subscriber.matches(channel):
                continue
            try:
                subscriber.queue.put_nowait(event)
            except asyncio.QueueFull:
                continue
            delivered += 1
        return delivered

    def subscriber_count(self) -> int:
        """Return the number of live subscribers."""
        return len(self._subscribers)


async def subscribe_events(request: Request) -> Response:
    """Stream ``GET /api/v1/events?channels=a,b`` as server-sent events.

    The response is an unbounded ``text/event-stream``: each published event
    on a requested channel arrives as one ``data: {json}`` frame. The
    subscriber is removed when the client disconnects (the stream generator
    is cancelled), so abandoned streams never leak queue capacity.

    Returns a ``400 BAD_REQUEST`` envelope when ``channels`` is missing or
    contains an invalid name.
    """
    raw_channels = request.query_params.get("channels", "")
    channels = [channel for channel in raw_channels.split(",") if channel]
    if not channels:
        request_id = request_id_of(request)
        return envelope_response(
            request_id,
            error_payload(
                request_id, "BAD_REQUEST", "The channels parameter is required"
            ),
            status_code=400,
        )
    try:
        bus: EventBus = request.app.state.services.events
        subscriber = bus.subscribe(channels)
    except ChannelError as err:
        request_id = request_id_of(request)
        issue = ValidationIssue(path="channels", code="invalid", message=str(err))
        return envelope_response(
            request_id,
            error_payload(request_id, "BAD_REQUEST", "Invalid channel name", [issue]),
            status_code=400,
        )

    async def stream() -> AsyncIterator[bytes]:
        try:
            while True:
                event = await subscriber.queue.get()
                payload = json.dumps(event, separators=(",", ":"))
                yield f"data: {payload}\n\n".encode()
        finally:
            bus.unsubscribe(subscriber)

    return StreamingResponse(stream(), media_type="text/event-stream")


async def publish_event(request: Request) -> Response:
    """Handle ``POST /api/v1/events/publish`` {channel, data}.

    A host-internal convenience command (also used by tests and, later,
    mounted domains) to push events without holding a reference to the bus.
    Returns the delivery count; invalid channel names yield ``400``.
    """
    body = await read_json_body(request)
    channel = body.get("channel")
    if not isinstance(channel, str):
        raise MalformedRequestError("Body must carry a string 'channel'")
    request_id = request_id_of(request)
    try:
        bus: EventBus = request.app.state.services.events
        delivered = bus.publish(channel, body.get("data"))
    except ChannelError as err:
        issue = ValidationIssue(path="channel", code="invalid", message=str(err))
        return envelope_response(
            request_id,
            error_payload(request_id, "BAD_REQUEST", "Invalid channel name", [issue]),
            status_code=400,
        )
    return envelope_response(
        request_id, success_payload(request_id, {"delivered": delivered})
    )
