"""Bounded per-connection stream delivery, resume, and cleanup lifecycle."""

from __future__ import annotations

import asyncio
from collections import Counter, deque
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.composition.logging import get_logger
from app.services.api.contracts import StreamEvent
from app.services.api.contracts.models import StreamEventType

logger = get_logger(__name__)


class StreamLimitError(RuntimeError):
    """Configured actor or process connection limit was exceeded."""


class StreamGapError(RuntimeError):
    """Requested resume sequence is outside the retained window."""


@dataclass(slots=True)
class _Connection:
    """Private resources for one active client connection."""

    actor_id: str
    queue: asyncio.Queue[StreamEvent | None]
    closed: bool = False


@dataclass(slots=True)
class StreamConnectionManager:
    """Own bounded non-authoritative stream delivery state."""

    max_connections_per_actor: int
    max_connections_process: int
    resume_window: int
    queue_size: int = 64
    _connections: dict[str, _Connection] = field(default_factory=dict, init=False)
    _actor_counts: Counter[str] = field(default_factory=Counter, init=False)
    _history: deque[StreamEvent] = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        """Validate configured lifecycle bounds.

        Raises:
            ValueError: If any configured bound is invalid.
        """
        if (
            min(
                self.max_connections_per_actor,
                self.max_connections_process,
                self.resume_window,
                self.queue_size,
            )
            <= 0
        ):
            raise ValueError("stream lifecycle limits must be positive")
        if self.max_connections_per_actor > self.max_connections_process:
            raise ValueError("actor stream limit cannot exceed process limit")
        self._history = deque(maxlen=self.resume_window)

    async def open(
        self,
        *,
        connection_id: str,
        actor_id: str,
        resume_after: int | None = None,
    ) -> None:
        """Authenticate quota evidence and allocate one connection.

        Args:
            connection_id: Unique connection identity.
            actor_id: Authenticated principal identity.
            resume_after: Last sequence observed by the client, if any.

        Raises:
            StreamLimitError: If connection identity or quota is invalid.
            StreamGapError: If requested history is no longer retained.
        """
        logger.info("Opening one API stream connection")
        if not connection_id or not actor_id:
            raise StreamLimitError("stream identity is required")
        async with self._lock:
            if connection_id in self._connections:
                raise StreamLimitError("stream connection already exists")
            if len(self._connections) >= self.max_connections_process:
                raise StreamLimitError("process stream limit exceeded")
            if self._actor_counts[actor_id] >= self.max_connections_per_actor:
                raise StreamLimitError("actor stream limit exceeded")
            replay = self._resume_events(resume_after)
            queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue(
                maxsize=self.queue_size
            )
            for event in replay:
                queue.put_nowait(event)
            self._connections[connection_id] = _Connection(actor_id, queue)
            self._actor_counts[actor_id] += 1

    def _resume_events(self, resume_after: int | None) -> tuple[StreamEvent, ...]:
        """Resolve retained replay events after a sequence.

        Returns:
            Ordered retained events.

        Raises:
            StreamGapError: If the requested sequence predates retained history.
        """
        if resume_after is None or not self._history:
            return ()
        first = self._history[0].sequence
        last = self._history[-1].sequence
        if resume_after < first - 1 or resume_after > last:
            raise StreamGapError("stream resume requires authoritative refresh")
        return tuple(event for event in self._history if event.sequence > resume_after)

    async def publish(self, event: StreamEvent) -> None:
        """Publish one ordered event to active bounded queues.

        Args:
            event: Validated immutable stream envelope.

        Raises:
            StreamGapError: If publication sequence is not strictly increasing.
        """
        logger.info("Publishing one API stream event")
        async with self._lock:
            if self._history and event.sequence <= self._history[-1].sequence:
                raise StreamGapError("stream publication sequence is not increasing")
            self._history.append(event)
            overflowed: list[str] = []
            for connection_id, connection in self._connections.items():
                if connection.closed:
                    continue
                try:
                    connection.queue.put_nowait(event)
                except asyncio.QueueFull:
                    overflowed.append(connection_id)
            for connection_id in overflowed:
                connection = self._connections[connection_id]
                while not connection.queue.empty():
                    connection.queue.get_nowait()
                terminal = StreamEvent.model_validate(
                    {
                        **event.model_dump(),
                        "event_type": "error",
                        "payload": None,
                        "error": "STREAM_BACKPRESSURE_LIMIT",
                    }
                )
                connection.queue.put_nowait(terminal)
                connection.closed = True

    async def events(self, connection_id: str) -> AsyncIterator[StreamEvent]:
        """Yield events until terminal cleanup or caller disconnect.

        Args:
            connection_id: Previously opened connection identity.

        Yields:
            Ordered stream events.

        Raises:
            StreamLimitError: If the connection is unknown.
        """
        connection = self._connections.get(connection_id)
        if connection is None:
            raise StreamLimitError("stream connection is not active")
        try:
            while True:
                event = await connection.queue.get()
                if event is None:
                    break
                yield event
                if event.event_type == StreamEventType.ERROR:
                    break
        finally:
            await self.close(connection_id)

    async def close(self, connection_id: str) -> None:
        """Idempotently release all resources for one connection.

        Args:
            connection_id: Connection to close.
        """
        logger.info("Closing one API stream connection")
        async with self._lock:
            self._close_locked(connection_id)

    def _close_locked(self, connection_id: str) -> None:
        """Release one connection while the lifecycle lock is held."""
        connection = self._connections.pop(connection_id, None)
        if connection is None:
            return
        connection.closed = True
        self._actor_counts[connection.actor_id] -= 1
        if self._actor_counts[connection.actor_id] <= 0:
            del self._actor_counts[connection.actor_id]
        while not connection.queue.empty():
            connection.queue.get_nowait()
        connection.queue.put_nowait(None)

    @property
    def connection_count(self) -> int:
        """Return current process-local active connection count."""
        return len(self._connections)


def create_stream_connection_manager(
    *,
    max_connections_per_actor: int,
    max_connections_process: int,
    resume_window: int,
    queue_size: int = 64,
) -> StreamConnectionManager:
    """Create one explicitly owned stream lifecycle manager.

    Returns:
        Validated manager with no active connections.
    """
    return StreamConnectionManager(
        max_connections_per_actor=max_connections_per_actor,
        max_connections_process=max_connections_process,
        resume_window=resume_window,
        queue_size=queue_size,
    )


__all__ = (
    "StreamConnectionManager",
    "StreamGapError",
    "StreamLimitError",
    "create_stream_connection_manager",
)
