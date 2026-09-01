# mypy: ignore-errors
"""Bounded local TCP receiver for MetaTrader snapshot frames."""

from __future__ import annotations

import asyncio
import hmac
import logging
import secrets
from collections.abc import AsyncIterator, Mapping
from contextlib import suppress
from datetime import UTC, datetime
from typing import cast

from app.services.brokers.metatrader.snapshot_protocol import (
    build_set_symbols_frame,
    parse_snapshot_frame,
)

logger = logging.getLogger(__name__)

_MAX_PORT = 65_535
_MAX_INTERVAL_SECONDS = 3_600
_MAX_FRAME_BYTES = 1_048_576
_QUEUE_SIZE = 8
_HELLO_TIMEOUT_SECONDS = 3.0
_IDLE_TIMEOUT_SECONDS = 5.0
_SYMBOL_ACK_TIMEOUT_SECONDS = 5.0
_BOOK_FIRST_READ_TIMEOUT_SECONDS = 5.0
_SYMBOL_RELEASE_GRACE_SECONDS = 30.0
_MAX_DEMANDED_SYMBOLS = 200


class _SnapshotGateway:
    """Own the listener and one active MT5 producer connection."""

    def __init__(self) -> None:
        """Initialize stopped bounded gateway state."""
        self.server: asyncio.Server | None = None
        self.producer: asyncio.StreamWriter | None = None
        self.subscribers: set[asyncio.Queue[Mapping[str, object] | None]] = set()
        self.book_subscribers: set[asyncio.Queue[Mapping[str, object] | None]] = set()
        self.last_sequence: int | None = None
        self.last_book_sequence: int | None = None
        self.last_received_at: datetime | None = None
        self.source_id: str | None = None
        self.auth_token: str | None = None
        self.expected_source_id: str | None = None
        self.expected_interval_seconds: int | None = None
        self.expected_symbols: tuple[str, ...] = ()
        self.symbol_consumers: dict[str, tuple[str, ...]] = {}
        self.desired_symbols: tuple[str, ...] = ()
        self.applied_symbols: tuple[str, ...] = ()
        self.desired_revision = 0
        self.applied_revision = 0
        self.runtime_authoritative = False
        self.symbol_condition = asyncio.Condition()
        self.release_tasks: dict[str, asyncio.Task[None]] = {}
        self.log_snapshots = False

    async def start(
        self,
        *,
        host: str,
        port: int,
        auth_token: str,
        source_id: str,
        interval_seconds: int,
        symbols: tuple[str, ...],
        log_snapshots: bool = False,
    ) -> None:
        """Start the configured local listener once.

        Args:
            host: Loopback listener host.
            port: Bounded listener port.
            auth_token: In-memory producer authentication token.
            source_id: Expected producer identity.
            interval_seconds: Expected snapshot interval.
            symbols: Initial exact provider-symbol set.
            log_snapshots: Whether to log bounded snapshot counts.

        Raises:
            ValueError: If configured host or port is invalid.
            OSError: If the listener cannot bind.
        """
        if self.server is not None:
            return
        host = host.strip()
        if not host:
            raise ValueError("MT5 snapshot host must not be empty")
        if not 1 <= port <= _MAX_PORT:
            raise ValueError("MT5 snapshot port is outside bounds")
        if (
            not auth_token
            or not source_id
            or not 1 <= interval_seconds <= _MAX_INTERVAL_SECONDS
        ):
            raise ValueError("MT5 snapshot identity configuration is invalid")
        if not symbols or len(symbols) != len(set(symbols)):
            raise ValueError("MT5 snapshot symbol configuration is invalid")
        self.auth_token = auth_token
        self.expected_source_id = source_id
        self.expected_interval_seconds = interval_seconds
        self.expected_symbols = symbols
        self.desired_symbols = symbols
        self.log_snapshots = log_snapshots
        self.server = await asyncio.start_server(
            self.handle_producer,
            host,
            port,
            limit=_MAX_FRAME_BYTES,
        )
        logger.info("MT5 snapshot gateway listening on %s:%s", host, port)

    async def stop(self) -> None:
        """Stop the listener, producer, and subscribers cleanly."""
        if self.producer is not None:
            self.producer.close()
            with suppress(ConnectionError):
                await self.producer.wait_closed()
            self.producer = None
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        for queue in tuple(self.subscribers):
            with suppress(asyncio.QueueFull):
                queue.put_nowait(None)
        self.subscribers.clear()
        for queue in tuple(self.book_subscribers):
            with suppress(asyncio.QueueFull):
                queue.put_nowait(None)
        self.book_subscribers.clear()
        for task in self.release_tasks.values():
            task.cancel()
        if self.release_tasks:
            await asyncio.gather(*self.release_tasks.values(), return_exceptions=True)
        self.release_tasks.clear()
        self.symbol_consumers.clear()
        self.desired_symbols = ()
        self.applied_symbols = ()
        self.desired_revision = 0
        self.applied_revision = 0
        self.runtime_authoritative = False
        self.last_sequence = None
        self.last_book_sequence = None
        self.last_received_at = None
        self.source_id = None
        self.auth_token = None
        self.expected_source_id = None
        self.expected_interval_seconds = None
        self.expected_symbols = ()
        self.log_snapshots = False

    async def stream(self) -> AsyncIterator[Mapping[str, object]]:
        """Yield validated snapshots to one bounded subscriber.

        Yields:
            Immutable snapshot mappings.
        """
        queue: asyncio.Queue[Mapping[str, object] | None] = asyncio.Queue(_QUEUE_SIZE)
        self.subscribers.add(queue)
        try:
            while True:
                snapshot = await queue.get()
                if snapshot is None:
                    return
                yield snapshot
        finally:
            self.subscribers.discard(queue)

    async def stream_books(self) -> AsyncIterator[Mapping[str, object]]:
        """Yield validated Depth-of-Market reads to one bounded subscriber.

        The first read is bounded. A producer that never publishes a book frame
        — a stale EA, a paused revision, or a broker outage — must fail the
        subscriber explicitly instead of holding it open forever.

        Yields:
            Immutable book mappings.

        Raises:
            TimeoutError: If no book frame arrives before the first-read bound.
        """
        queue: asyncio.Queue[Mapping[str, object] | None] = asyncio.Queue(_QUEUE_SIZE)
        self.book_subscribers.add(queue)
        try:
            book = await asyncio.wait_for(
                queue.get(),
                timeout=_BOOK_FIRST_READ_TIMEOUT_SECONDS,
            )
            while book is not None:
                yield book
                book = await queue.get()
        finally:
            self.book_subscribers.discard(queue)

    async def handle_producer(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Validate one producer connection and publish complete frames.

        Args:
            reader: Connected producer byte stream.
            writer: Connected producer response stream.
        """
        if self.producer is not None:
            writer.close()
            await writer.wait_closed()
            return
        self.producer = writer
        # Sequence identity is scoped to one EA connection; an EA restart begins
        # again at zero and must not be mistaken for an eternal duplicate.
        self.last_sequence = None
        self.last_book_sequence = None
        logger.info("MT5 snapshot producer connection opened")
        try:
            hello = await self._read_hello(reader)
            self.source_id = cast("str", hello["source_id"])
            await self._publish_desired_symbols()
            await self._read_frames(reader, hello)
        except (
            ConnectionError,
            TypeError,
            ValueError,
            asyncio.LimitOverrunError,
            TimeoutError,
        ):
            logger.exception("MT5 snapshot producer stopped after invalid input")
        finally:
            writer.close()
            with suppress(ConnectionError):
                await writer.wait_closed()
            if self.producer is writer:
                self.producer = None
                self.source_id = None
                self.applied_symbols = ()
                self.applied_revision = 0
            logger.info("MT5 snapshot producer disconnected")

    async def _read_hello(
        self,
        reader: asyncio.StreamReader,
    ) -> Mapping[str, object]:
        """Authenticate the tested EA's mandatory first frame.

        Args:
            reader: Connected producer byte stream.

        Returns:
            Validated hello message.

        Raises:
            ValueError: If framing or authentication fails.
        """
        frame = await asyncio.wait_for(
            reader.readline(),
            timeout=_HELLO_TIMEOUT_SECONDS,
        )
        if not frame or len(frame) > _MAX_FRAME_BYTES or not frame.endswith(b"\n"):
            raise ValueError("MT5 hello frame is missing or exceeds bounds")
        hello = parse_snapshot_frame(frame.rstrip(b"\r\n"))
        if hello["type"] != "hello":
            raise ValueError("MT5 producer must send hello first")
        expected = self.auth_token
        if expected is None:
            raise ValueError("MT5 snapshot gateway is not configured")
        supplied = cast("str", hello["token"])
        if not hmac.compare_digest(supplied, expected):
            raise ValueError("MT5 producer authentication failed")
        if (
            hello["source_id"] != self.expected_source_id
            or hello["interval_seconds"] != self.expected_interval_seconds
        ):
            raise ValueError("MT5 producer declaration does not match settings")
        return hello

    async def _read_frames(
        self,
        reader: asyncio.StreamReader,
        hello: Mapping[str, object],
    ) -> None:
        """Read and publish frames until the producer disconnects.

        Args:
            reader: Connected producer byte stream.
            hello: Authenticated producer identity and symbol declaration.

        Raises:
            TypeError: If a decoded field has an invalid type.
            ValueError: If framing, content, or ordering is invalid.
        """
        while frame := await asyncio.wait_for(
            reader.readline(),
            timeout=_IDLE_TIMEOUT_SECONDS,
        ):
            if len(frame) > _MAX_FRAME_BYTES or not frame.endswith(b"\n"):
                raise ValueError("MT5 snapshot frame exceeds bounds")
            snapshot = parse_snapshot_frame(frame.rstrip(b"\r\n"))
            if snapshot["type"] == "symbols_applied":
                await self._accept_symbols_applied(snapshot)
                continue
            if snapshot["type"] == "heartbeat":
                self._accept_heartbeat(snapshot)
                continue
            if snapshot["type"] == "book":
                await self._publish_book(snapshot, hello)
                continue
            if snapshot["type"] != "snapshot":
                raise ValueError("unsupported producer frame")
            await self._publish_snapshot(snapshot, hello)

    async def _publish_snapshot(
        self,
        snapshot: Mapping[str, object],
        hello: Mapping[str, object],
    ) -> None:
        """Validate ordering and fan out one acknowledged snapshot.

        Args:
            snapshot: Validated snapshot protocol frame.
            hello: Authenticated producer declaration.

        Raises:
            ValueError: If revision, symbols, or ordering are invalid.
        """
        if snapshot["revision"] != self.applied_revision:
            raise ValueError("snapshot revision is not acknowledged")
        declared_symbols = set(self.applied_symbols)
        frame_symbols = {
            str(item["symbol"])
            for key in ("quotes", "errors")
            for item in cast("tuple[Mapping[str, object], ...]", snapshot[key])
        }
        if not frame_symbols.issubset(declared_symbols):
            raise ValueError("snapshot contains an undeclared symbol")
        sequence = cast("int", snapshot["sequence"])
        if self.last_sequence is not None and sequence <= self.last_sequence:
            logger.warning("Ignoring duplicate or out-of-order MT5 snapshot")
            return
        gap = (
            0
            if self.last_sequence is None
            else max(0, sequence - self.last_sequence - 1)
        )
        if gap:
            logger.warning("MT5 snapshot sequence gap detected: %s", gap)
        self.last_sequence = sequence
        self.last_received_at = datetime.now(UTC)
        if self.log_snapshots:
            logger.info(
                "Received MT5 snapshot sequence %s with %s quotes and %s errors",
                sequence,
                len(cast("tuple[object, ...]", snapshot["quotes"])),
                len(cast("tuple[object, ...]", snapshot["errors"])),
            )
        published = {
            **snapshot,
            "gap": gap,
            "received_at": self.last_received_at,
            "source_id": hello["source_id"],
            "interval_seconds": hello["interval_seconds"],
            "symbols": self.applied_symbols,
        }
        for queue in tuple(self.subscribers):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(published)

    async def _publish_book(
        self,
        book: Mapping[str, object],
        hello: Mapping[str, object],
    ) -> None:
        """Validate ordering and fan out one acknowledged Depth-of-Market read.

        Args:
            book: Raw decoded ``book`` frame payload.
            hello: Most recent decoded ``hello`` handshake payload.

        Raises:
            ValueError: If revision, symbols, or ordering are invalid.
        """
        if book["revision"] != self.applied_revision:
            raise ValueError("book revision is not acknowledged")
        declared_symbols = set(self.applied_symbols)
        frame_symbols = {
            str(item["symbol"])
            for key in ("books", "errors")
            for item in cast("tuple[Mapping[str, object], ...]", book[key])
        }
        if not frame_symbols.issubset(declared_symbols):
            raise ValueError("book contains an undeclared symbol")
        sequence = cast("int", book["sequence"])
        if self.last_book_sequence is not None and sequence <= self.last_book_sequence:
            logger.warning("Ignoring duplicate or out-of-order MT5 book")
            return
        gap = (
            0
            if self.last_book_sequence is None
            else max(0, sequence - self.last_book_sequence - 1)
        )
        if gap:
            logger.warning("MT5 book sequence gap detected: %s", gap)
        self.last_book_sequence = sequence
        published = {
            **book,
            "gap": gap,
            "received_at": datetime.now(UTC),
            "source_id": hello["source_id"],
            "interval_seconds": hello["interval_seconds"],
            "symbols": self.applied_symbols,
        }
        for queue in tuple(self.book_subscribers):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(published)

    async def acquire_symbols(self, symbols: tuple[str, ...]) -> str:
        """Register one consumer and wait for the EA to apply its symbols.

        Args:
            symbols: Exact unique provider symbols demanded by the consumer.

        Returns:
            Opaque consumer identifier.

        Raises:
            ValueError: If demand is invalid, excessive, or rejected.
            TimeoutError: If the EA does not acknowledge in time.
        """
        normalized = tuple(sorted(set(symbols)))
        if not normalized or len(normalized) != len(symbols):
            raise ValueError("MT5 symbol demand must be non-empty and unique")
        consumer_id = secrets.token_urlsafe(18)
        self.symbol_consumers[consumer_id] = normalized
        self.runtime_authoritative = True
        prospective = {
            symbol for values in self.symbol_consumers.values() for symbol in values
        }
        if len(prospective) > _MAX_DEMANDED_SYMBOLS:
            # Grace-period consumers are already detached. Evict them before
            # rejecting a legitimate replacement subscription at the bound.
            cancelled: list[asyncio.Task[None]] = []
            for released_id, task in tuple(self.release_tasks.items()):
                task.cancel()
                cancelled.append(task)
                self.release_tasks.pop(released_id, None)
                self.symbol_consumers.pop(released_id, None)
            if cancelled:
                await asyncio.gather(*cancelled, return_exceptions=True)
        try:
            revision = await self._reconcile_symbols()
            async with self.symbol_condition:
                await asyncio.wait_for(
                    self.symbol_condition.wait_for(
                        lambda: self.applied_revision >= revision
                    ),
                    timeout=_SYMBOL_ACK_TIMEOUT_SECONDS,
                )
            self._require_applied(normalized)
        except BaseException:
            self.symbol_consumers.pop(consumer_id, None)
            await self._reconcile_symbols()
            raise
        return consumer_id

    def _require_applied(self, symbols: tuple[str, ...]) -> None:
        """Require the acknowledged set to cover one consumer demand.

        Args:
            symbols: Exact symbols that must be acknowledged.

        Raises:
            ValueError: If the EA rejected any demanded symbol.
        """
        if not set(symbols).issubset(self.applied_symbols):
            raise ValueError("MT5 rejected one or more demanded symbols")

    async def release_symbols(self, consumer_id: str) -> None:
        """Release one consumer after a bounded anti-churn grace period.

        Args:
            consumer_id: Opaque identifier returned by ``acquire_symbols``.
        """
        if consumer_id not in self.symbol_consumers:
            return
        previous = self.release_tasks.pop(consumer_id, None)
        if previous is not None:
            previous.cancel()

        active_consumers = set(self.symbol_consumers) - set(self.release_tasks)
        active_consumers.discard(consumer_id)
        if not active_consumers:
            pending = tuple(self.release_tasks.values())
            for task in pending:
                task.cancel()
            self.release_tasks.clear()
            self.symbol_consumers.clear()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            await self._reconcile_symbols()
            return

        async def delayed_release() -> None:
            await asyncio.sleep(_SYMBOL_RELEASE_GRACE_SECONDS)
            self.symbol_consumers.pop(consumer_id, None)
            self.release_tasks.pop(consumer_id, None)
            await self._reconcile_symbols()

        self.release_tasks[consumer_id] = asyncio.create_task(delayed_release())

    async def _reconcile_symbols(self) -> int:
        """Publish the deterministic bounded union when it changes.

        Returns:
            Current desired revision.

        Raises:
            ValueError: If the union exceeds its configured bound.
        """
        desired = tuple(
            sorted(
                {
                    symbol
                    for values in self.symbol_consumers.values()
                    for symbol in values
                }
            )
        )
        if len(desired) > _MAX_DEMANDED_SYMBOLS:
            raise ValueError("MT5 symbol demand exceeds the configured bound")
        if not self.runtime_authoritative:
            desired = self.expected_symbols
        if desired == self.desired_symbols and self.desired_revision:
            return self.desired_revision
        self.desired_symbols = desired
        return await self._publish_desired_symbols()

    async def _publish_desired_symbols(self) -> int:
        """Send the current complete desired set to an authenticated EA.

        Returns:
            Newly assigned desired revision.
        """
        self.desired_revision += 1
        revision = self.desired_revision
        if self.producer is not None and self.source_id is not None:
            self.producer.write(build_set_symbols_frame(revision, self.desired_symbols))
            await self.producer.drain()
        return revision

    async def _accept_symbols_applied(self, message: Mapping[str, object]) -> None:
        """Accept only the acknowledgment for the current desired revision.

        Args:
            message: Validated symbols-applied protocol frame.

        Raises:
            ValueError: If acknowledgment ordering or coverage is invalid.
        """
        revision = cast("int", message["revision"])
        if revision < self.desired_revision:
            return
        if revision != self.desired_revision:
            raise ValueError("MT5 acknowledgment revision is ahead of demand")
        applied = cast("tuple[str, ...]", message["symbols"])
        rejected = {
            str(item["symbol"])
            for item in cast("tuple[Mapping[str, object], ...]", message["errors"])
        }
        if set(applied) | rejected != set(self.desired_symbols):
            raise ValueError("MT5 acknowledgment does not cover desired symbols")
        self.applied_symbols = applied
        self.applied_revision = revision
        async with self.symbol_condition:
            self.symbol_condition.notify_all()

    def _accept_heartbeat(self, message: Mapping[str, object]) -> None:
        """Accept an idle heartbeat only for the acknowledged paused revision.

        Args:
            message: Validated protocol heartbeat.

        Raises:
            ValueError: If the EA is not paused at the acknowledged revision.
        """
        if self.applied_symbols or message["revision"] != self.applied_revision:
            raise ValueError("heartbeat does not match the acknowledged paused state")

    def status(self) -> Mapping[str, object]:
        """Return bounded non-secret listener health evidence.

        Returns:
            Detached gateway status mapping.
        """
        return {
            "listening": self.server is not None,
            "connected": self.producer is not None,
            "last_sequence": self.last_sequence,
            "last_book_sequence": self.last_book_sequence,
            "last_received_at": self.last_received_at,
            "source_id": self.source_id,
            "subscribers": len(self.subscribers),
            "book_subscribers": len(self.book_subscribers),
            "desired_revision": self.desired_revision,
            "applied_revision": self.applied_revision,
            "desired_symbol_count": len(self.desired_symbols),
            "applied_symbol_count": len(self.applied_symbols),
            "demand_consumers": len(self.symbol_consumers),
            "paused": self.producer is not None and not self.applied_symbols,
        }


_GATEWAY = _SnapshotGateway()


async def start_metatrader_snapshot_gateway(
    *,
    host: str,
    port: int,
    auth_token: str,
    source_id: str,
    interval_seconds: int,
    symbols: tuple[str, ...],
    log_snapshots: bool = False,
) -> None:
    """Start the configured local MT5 snapshot listener once.

    Args:
        host: Local listener interface.
        port: Local listener port.
        auth_token: In-memory shared authentication token.
        source_id: Exact expected EA source identity.
        interval_seconds: Exact expected snapshot interval.
        symbols: Exact expected ordered symbol declaration.
        log_snapshots: Whether to log bounded sequence metadata.
    """
    await _GATEWAY.start(
        host=host,
        port=port,
        auth_token=auth_token,
        source_id=source_id,
        interval_seconds=interval_seconds,
        symbols=symbols,
        log_snapshots=log_snapshots,
    )


async def stop_metatrader_snapshot_gateway() -> None:
    """Stop the listener and release all network resources."""
    await _GATEWAY.stop()


async def stream_metatrader_snapshots() -> AsyncIterator[Mapping[str, object]]:
    """Yield validated snapshots from the active MT5 producer.

    Yields:
        Immutable snapshot mappings.
    """
    async for snapshot in _GATEWAY.stream():
        yield snapshot


async def stream_metatrader_book_snapshots() -> AsyncIterator[Mapping[str, object]]:
    """Yield validated Depth-of-Market reads from the active MT5 producer.

    Yields:
        Immutable book mappings.

    Raises:
        TimeoutError: If no book frame arrives before the first-read bound.
    """
    async for book in _GATEWAY.stream_books():
        yield book


async def acquire_metatrader_snapshot_symbols(symbols: tuple[str, ...]) -> str:
    """Acquire a bounded MT5 symbol demand.

    Args:
        symbols: Exact unique provider symbols demanded by the consumer.

    Returns:
        Opaque consumer identifier.
    """
    return await _GATEWAY.acquire_symbols(symbols)


async def release_metatrader_snapshot_symbols(consumer_id: str) -> None:
    """Release one previously acquired MT5 symbol demand idempotently.

    Args:
        consumer_id: Opaque identifier returned by symbol acquisition.
    """
    await _GATEWAY.release_symbols(consumer_id)


def get_metatrader_snapshot_gateway_status() -> Mapping[str, object]:
    """Return bounded non-secret listener health evidence.

    Returns:
        Detached gateway status mapping.
    """
    return _GATEWAY.status()


__all__ = [
    "acquire_metatrader_snapshot_symbols",
    "get_metatrader_snapshot_gateway_status",
    "release_metatrader_snapshot_symbols",
    "start_metatrader_snapshot_gateway",
    "stop_metatrader_snapshot_gateway",
    "stream_metatrader_book_snapshots",
    "stream_metatrader_snapshots",
]
