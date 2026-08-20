"""Deterministic fake tick stream provider adapter and factory."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator, Mapping
from contextlib import suppress
from typing import TYPE_CHECKING

from app.capabilities.data.tick_stream.v1 import (
    TickStreamCapabilityV1,
    TickStreamEventV1,
    TickStreamRequestV1,
)

if TYPE_CHECKING:
    from app.kernel.effects import EffectScope
    from app.kernel.identifiers import CapabilityId


class _FakeTickStreamAdapter:
    """Deterministic fake provider conforming to TickStreamCapabilityV1."""

    def __init__(self) -> None:
        """Initialize fake tick stream adapter."""
        self._active = False
        self._generation_id: str | None = None
        self._queue: asyncio.Queue[TickStreamEventV1 | None] = asyncio.Queue(maxsize=3)

    @property
    def active(self) -> bool:
        """Return whether provider is currently active.

        Returns:
            True if active, False otherwise.
        """
        return self._active

    @property
    def generation_id(self) -> str | None:
        """Return current provider generation identifier.

        Returns:
            Current generation ID string or None.
        """
        return self._generation_id

    async def start(self, request: TickStreamRequestV1) -> None:
        """Start streaming ticks for the requested symbol.

        Args:
            request: Tick stream request configuration.
        """
        if self._active:
            await self.stop()

        self._generation_id = str(uuid.uuid4())
        self._active = True
        self._queue = asyncio.Queue(maxsize=request.buffer_size)

        bids = ("1.1000", "1.1001", "1.1002")
        for i, bid in enumerate(bids, start=1):
            event = TickStreamEventV1(
                sequence=i,
                symbol=request.symbol,
                payload={"bid": bid},
            )
            await self._queue.put(event)

    async def events(self) -> AsyncIterator[TickStreamEventV1]:
        """Yield stream of incoming tick events.

        Yields:
            TickStreamEventV1 instances from queue.
        """
        while self._active or not self._queue.empty():
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.1)
                if event is None:
                    break
                yield event
            except TimeoutError, asyncio.CancelledError:
                break

    async def stop(self) -> None:
        """Stop streaming ticks and clear pending queue items."""
        if not self._active:
            return
        self._active = False
        self._generation_id = None
        while not self._queue.empty():
            with suppress(asyncio.QueueEmpty):
                self._queue.get_nowait()

    def sync_close(self) -> None:
        """Synchronously release local resources."""
        self._active = False


_EXPECTED_BUFFER_SIZE = 3


def create_provider(
    *,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object],
    scope: EffectScope,
) -> TickStreamCapabilityV1:
    """Create scoped deterministic fake tick stream provider instance.

    Args:
        dependencies: Must be empty.
        config: Must contain symbol="EURUSD" and buffer_size=3.
        scope: EffectScope managing provider lifecycle.

    Returns:
        TickStreamCapabilityV1 instance.

    Raises:
        ValueError: If config or dependencies do not match required configuration.
    """
    if (
        dependencies
        or config.get("symbol") != "EURUSD"
        or config.get("buffer_size") != _EXPECTED_BUFFER_SIZE
        or bool(set(config.keys()) - {"symbol", "buffer_size"})
    ):
        msg = "fake tick stream config must be symbol EURUSD and buffer_size 3"
        raise ValueError(msg)

    adapter = _FakeTickStreamAdapter()
    scope.callback(adapter.sync_close)
    return adapter


__all__ = ("create_provider",)
