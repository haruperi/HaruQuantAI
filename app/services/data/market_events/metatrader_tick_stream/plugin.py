"""MetaTrader 5 real-time tick stream provider adapter and factory."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator, Mapping
from contextlib import suppress
from typing import TYPE_CHECKING, cast

from app.capabilities.data.tick_stream.v1 import (
    TickStreamCapabilityV1,
    TickStreamEventV1,
    TickStreamRequestV1,
)
from app.services.brokers.metatrader.snapshot_gateway import (
    acquire_metatrader_snapshot_symbols,
    release_metatrader_snapshot_symbols,
    stream_metatrader_snapshots,
)
from app.utils.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope
    from app.kernel.identifiers import CapabilityId

_LOGGER = get_logger(__name__)


class _MetaTraderTickStreamAdapter:
    """Adapts MT5 snapshot gateway to TickStreamCapabilityV1."""

    def __init__(self, default_symbol: str, buffer_size: int = 256) -> None:
        """Initialize MetaTrader tick stream adapter.

        Args:
            default_symbol: Default market ticker symbol.
            buffer_size: Event queue buffer capacity.
        """
        self._default_symbol = default_symbol
        self._buffer_size = buffer_size
        self._active = False
        self._generation_id: str | None = None
        self._consumer_id: str | None = None
        self._queue: asyncio.Queue[TickStreamEventV1 | None] = asyncio.Queue(
            maxsize=buffer_size
        )
        self._stream_task: asyncio.Task[None] | None = None
        self._sequence = 0

    @property
    def active(self) -> bool:
        """Return whether provider is currently streaming.

        Returns:
            True if active, False otherwise.
        """
        return self._active

    @property
    def generation_id(self) -> str | None:
        """Return active provider generation identifier.

        Returns:
            Current generation ID string or None.
        """
        return self._generation_id

    async def start(self, request: TickStreamRequestV1) -> None:
        """Start MT5 background ingestion and queueing for requested symbol.

        Args:
            request: Tick stream request configuration.

        Raises:
            Exception: If MT5 symbol acquisition fails.
        """
        if self._active:
            await self.stop()

        self._sequence = 0
        self._generation_id = str(uuid.uuid4())
        self._active = True
        self._queue = asyncio.Queue(maxsize=request.buffer_size)

        try:
            self._consumer_id = await acquire_metatrader_snapshot_symbols(
                (request.symbol,)
            )
        except Exception:
            self._active = False
            self._generation_id = None
            _LOGGER.exception("Failed to acquire MT5 symbol demand")
            raise

        self._stream_task = asyncio.create_task(
            self._consume_snapshots(request.symbol),
            name=f"mt5_tick_stream_{self._generation_id}",
        )
        _LOGGER.info(
            "Started MT5 tick stream [generation=%s, symbol=%s]",
            self._generation_id,
            request.symbol,
        )

    async def _consume_snapshots(self, symbol: str) -> None:
        """Consume gateway snapshots and enqueue matching tick events.

        Args:
            symbol: Target symbol to filter and enqueue.
        """
        try:
            async for snapshot in stream_metatrader_snapshots():
                if not self._active:
                    break
                quotes = cast(
                    "tuple[Mapping[str, object], ...]",
                    snapshot.get("quotes", ()),
                )
                for quote in quotes:
                    if str(quote.get("symbol")) == symbol:
                        self._sequence += 1
                        event = TickStreamEventV1(
                            sequence=self._sequence,
                            symbol=symbol,
                            payload=quote,
                        )
                        if self._queue.full():
                            with suppress(asyncio.QueueEmpty):
                                self._queue.get_nowait()
                        await self._queue.put(event)
        except asyncio.CancelledError:
            pass
        except (OSError, ConnectionError, RuntimeError, ValueError) as err:
            _LOGGER.warning(
                "MT5 tick stream lost [gen=%s]: %s (LOST_DURING_OPERATION)",
                self._generation_id,
                err,
            )
        finally:
            with suppress(asyncio.QueueFull):
                self._queue.put_nowait(None)

    async def events(self) -> AsyncIterator[TickStreamEventV1]:
        """Yield incoming stream of tick events.

        Yields:
            TickStreamEventV1 instances from the buffer queue.
        """
        while self._active:
            try:
                event = await self._queue.get()
                if event is None:
                    break
                yield event
            except asyncio.CancelledError:
                break

    async def stop(self) -> None:
        """Stop streaming task and release registered MT5 symbol demand."""
        if not self._active:
            return

        self._active = False
        if self._stream_task is not None:
            self._stream_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._stream_task
            self._stream_task = None

        if self._consumer_id is not None:
            await release_metatrader_snapshot_symbols(self._consumer_id)
            self._consumer_id = None

        while not self._queue.empty():
            with suppress(asyncio.QueueEmpty):
                self._queue.get_nowait()

        _LOGGER.info(
            "Stopped MT5 tick stream [generation=%s, total_events=%s]",
            self._generation_id,
            self._sequence,
        )
        self._generation_id = None

    def sync_close(self) -> None:
        """Synchronously cancel streaming tasks."""
        self._active = False
        if self._stream_task is not None:
            self._stream_task.cancel()
            self._stream_task = None


def create_provider(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> TickStreamCapabilityV1:
    """Create scoped MT5 tick stream provider instance.

    Args:
        dependencies: Empty mapping.
        config: Must contain 'symbol' and optional 'buffer_size'.
        scope: EffectScope managing provider lifecycle.

    Returns:
        TickStreamCapabilityV1 instance.

    Raises:
        ValueError: If config or dependencies are invalid.
    """
    if dependencies:
        msg = "MT5 tick stream provider accepts no dependencies"
        raise ValueError(msg)

    if "symbol" not in config or not isinstance(config["symbol"], str):
        msg = "MT5 tick stream provider requires 'symbol' string in configuration"
        raise ValueError(msg)

    symbol = config["symbol"]
    raw_buffer_size = config.get("buffer_size", 256)
    buffer_size = (
        int(raw_buffer_size) if isinstance(raw_buffer_size, (int, str)) else 256
    )

    adapter = _MetaTraderTickStreamAdapter(symbol, buffer_size)
    scope.callback(adapter.sync_close)
    return adapter


__all__ = ("create_provider",)
