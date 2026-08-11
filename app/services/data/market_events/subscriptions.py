"""Shared Data-owned market stream subscription lifecycle."""

from __future__ import annotations

import asyncio
import hashlib
from collections import OrderedDict, deque
from collections.abc import AsyncGenerator, AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast

from app.services.data.contracts import DataError
from app.services.data.market_events.contracts import (
    MarketStreamEvent,
    MarketStreamRequest,
)
from app.services.data.market_events.mt5_bars import iter_mt5_closed_bars
from app.services.data.market_events.mt5_ticks import iter_mt5_ticks
from app.services.data.time_sessions.timeframes import _get_timeframe_spec_raw
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

_STREAM_QUEUE_SIZE = 256
_STREAM_RESUME_WINDOW = 256
_STREAM_HEARTBEAT_SECONDS = 15.0
# Retained inactive hubs preserve short reconnect windows without allowing symbols and
# timeframe combinations to grow process memory without bound.
_STREAM_HUB_LIMIT = 128

type _StreamKey = tuple[str, str, str, str]


def build_market_stream_request(**values: object) -> MarketStreamRequest:
    """Build one validated Data market-stream request.

    Args:
        values: The ``values`` argument.

    Returns:
        Immutable request accepted by :func:`stream_market_data`.
    """
    request = MarketStreamRequest.model_validate(values)
    _get_timeframe_spec_raw(request.timeframe)
    return request


def _feed_id(key: _StreamKey) -> str:
    """Return one stable non-secret feed identifier.

    Args:
        key: The ``key`` argument.

    Returns:
        Stable feed identifier for the source/symbol/mode/timeframe tuple.
    """
    digest = hashlib.sha256(":".join(key).encode("utf-8")).hexdigest()[:20]
    return f"feed-{digest}"


@dataclass(slots=True)
class _StreamHub:
    """One shared provider poller and bounded fan-out stream."""

    request: MarketStreamRequest
    subscribers: dict[str, asyncio.Queue[MarketStreamEvent | None]] = field(
        default_factory=dict
    )
    history: deque[MarketStreamEvent] = field(
        default_factory=lambda: deque(maxlen=_STREAM_RESUME_WINDOW)
    )
    task: asyncio.Task[None] | None = None
    next_sequence: int = 0
    terminal_subscribers: set[str] = field(default_factory=set)

    @property
    def key(self) -> _StreamKey:
        """Return the stable provider stream identity.

        Returns:
            The result produced by the operation.
        """
        return (
            self.request.source_id,
            self.request.symbol,
            self.request.mode,
            self.request.timeframe,
        )

    def _event(
        self,
        event_type: str,
        *,
        payload: object | None = None,
        error: str | None = None,
        terminal: bool = False,
    ) -> MarketStreamEvent:
        """Build and advance one ordered Data stream event.

        Args:
            event_type: The ``event_type`` argument.
            payload: The ``payload`` argument.
            error: The ``error`` argument.
            terminal: The ``terminal`` argument.

        Returns:
            Validated canonical event.
        """
        sequence = self.next_sequence
        self.next_sequence += 1
        return MarketStreamEvent(
            feed_id=_feed_id(self.key),
            sequence=sequence,
            event_type=cast("Any", event_type),
            mode=self.request.mode,
            source_id=self.request.source_id,
            symbol=self.request.symbol,
            timeframe=self.request.timeframe,
            occurred_at=datetime.now(UTC),
            payload=payload,
            cursor=str(sequence),
            error=error,
            terminal=terminal,
            request_id=self.request.request_id,
        )

    async def _publish(self, event: MarketStreamEvent) -> None:
        """Publish one event without silently dropping a slow subscriber.

        Args:
            event: The ``event`` argument.
        """
        self.history.append(event)
        for subscriber_id, queue in tuple(self.subscribers.items()):
            if subscriber_id in self.terminal_subscribers:
                continue
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                while not queue.empty():
                    queue.get_nowait()
                terminal = event.model_copy(
                    update={
                        "event_type": "gap",
                        "payload": None,
                        "error": "DATA_DROPPED",
                        "terminal": True,
                    }
                )
                queue.put_nowait(terminal)
                self.terminal_subscribers.add(subscriber_id)

    def _producer(self) -> AsyncGenerator[object]:
        """Create the exact MT5 producer selected by the request.

        Returns:
            The result produced by the operation.
        """
        if self.request.mode == "ticks":
            return iter_mt5_ticks(
                symbol=self.request.symbol,
                request_id=self.request.request_id,
            )
        return iter_mt5_closed_bars(
            symbol=self.request.symbol,
            timeframe=self.request.timeframe,
            request_id=self.request.request_id,
        )

    async def run(self) -> None:
        """Pump one provider iterator into ordered shared Data events.

        Raises:
            Exception: If the operation cannot be completed safely.
        """
        logger.info("Starting shared Data market stream %s", _feed_id(self.key))
        producer = self._producer()
        pending: asyncio.Future[object] | None = None
        try:
            pending = asyncio.ensure_future(anext(producer))
            while True:
                done, _ = await asyncio.wait(
                    {pending},
                    timeout=_STREAM_HEARTBEAT_SECONDS,
                )
                if not done:
                    await self._publish(self._event("heartbeat"))
                    continue
                try:
                    payload = pending.result()
                except StopAsyncIteration:
                    break
                await self._publish(
                    self._event(self.request.mode[:-1], payload=payload)
                )
                pending = asyncio.ensure_future(anext(producer))
        except asyncio.CancelledError:
            raise
        except DataError as error:
            event_type = "gap" if error.code == "DATA_DROPPED" else "error"
            await self._publish(
                self._event(
                    event_type,
                    error=error.code,
                    terminal=True,
                )
            )
        except Exception:
            logger.exception("Data market stream failed")
            await self._publish(
                self._event(
                    "error",
                    error="SOURCE_UNAVAILABLE",
                    terminal=True,
                )
            )
        finally:
            if pending is not None and not pending.done():
                pending.cancel()
                await asyncio.gather(pending, return_exceptions=True)
            await producer.aclose()
            self.task = None
            logger.info("Stopped shared Data market stream %s", _feed_id(self.key))

    async def subscribe(
        self,
        subscriber_id: str,
        resume_after: int | None,
    ) -> asyncio.Queue[MarketStreamEvent | None]:
        """Register one bounded consumer and replay retained events.

        Args:
            subscriber_id: The ``subscriber_id`` argument.
            resume_after: The ``resume_after`` argument.

        Returns:
            Consumer queue.

        Raises:
            DataError: If the requested sequence is outside retained history.
        """
        queue: asyncio.Queue[MarketStreamEvent | None] = asyncio.Queue(
            maxsize=_STREAM_QUEUE_SIZE
        )
        if resume_after is not None and self.history:
            first = self.history[0].sequence
            last = self.history[-1].sequence
            if resume_after < first - 1 or resume_after > last:
                raise DataError(
                    "STATE_RECOVERY_FAILED",
                    safe_details={"operation": "market_stream_resume"},
                    request_id=self.request.request_id,
                )
            for event in self.history:
                if event.sequence > resume_after:
                    queue.put_nowait(event)
        self.subscribers[subscriber_id] = queue
        if self.task is None:
            self.task = asyncio.create_task(self.run())
        return queue

    async def unsubscribe(self, subscriber_id: str) -> None:
        """Release one subscriber and stop provider polling when none remain.

        Args:
            subscriber_id: The ``subscriber_id`` argument.
        """
        self.subscribers.pop(subscriber_id, None)
        self.terminal_subscribers.discard(subscriber_id)
        if not self.subscribers and self.task is not None:
            task = self.task
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


_HUBS: OrderedDict[_StreamKey, _StreamHub] = OrderedDict()


def _admit_hub(key: _StreamKey, request: MarketStreamRequest) -> _StreamHub:
    """Return an existing hub or admit one within the process memory bound.

    Args:
        key: The ``key`` argument.
        request: The ``request`` argument.

    Returns:
        Retained or newly admitted shared hub.

    Raises:
        DataError: If every retained hub is active at the configured bound.
    """
    existing = _HUBS.get(key)
    if existing is not None:
        _HUBS.move_to_end(key)
        return existing
    for retained_key, retained in tuple(_HUBS.items()):
        if len(_HUBS) < _STREAM_HUB_LIMIT:
            break
        if not retained.subscribers and retained.task is None:
            del _HUBS[retained_key]
    if len(_HUBS) >= _STREAM_HUB_LIMIT:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={"operation": "market_stream_hub_admission"},
            request_id=request.request_id,
        )
    hub = _StreamHub(request=request)
    _HUBS[key] = hub
    return hub


async def stream_market_data(
    request: object,
) -> AsyncIterator[MarketStreamEvent]:
    """Yield one Data-owned canonical MT5 market stream.

    Args:
        request: Value returned by :func:`build_market_stream_request`.

    Yields:
        Ordered ticks, closed bars, heartbeats, or explicit terminal errors.

    Raises:
        DataError: If the request type or resume cursor is invalid.
    """
    if not isinstance(request, MarketStreamRequest):
        raise DataError(
            "INVALID_INPUT",
            safe_details={"contract": "MarketStreamRequest"},
        )
    key: _StreamKey = (
        request.source_id,
        request.symbol,
        request.mode,
        request.timeframe,
    )
    hub = _admit_hub(key, request)
    subscriber_id = generate_id("evt")
    queue = await hub.subscribe(subscriber_id, request.resume_after)
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
            if event.terminal:
                break
    finally:
        await hub.unsubscribe(subscriber_id)


__all__ = ["build_market_stream_request", "stream_market_data"]
