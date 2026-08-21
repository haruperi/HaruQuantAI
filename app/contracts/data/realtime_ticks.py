"""Realtime market tick streaming capability contract."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey


@dataclass(frozen=True, slots=True)
class Tick:
    """Realtime price tick update.

    Attributes:
        symbol: Financial instrument symbol.
        timestamp: Tick timestamp in UTC.
        bid: Current bid price.
        ask: Current ask price.
        last: Last traded price (if available).
        volume: Tick volume.
    """

    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    last: float | None = None
    volume: float = 0.0


@runtime_checkable
class RealtimeTicks(Protocol):
    """Protocol for streaming realtime market ticks."""

    async def stream_ticks(self, symbol: str) -> AsyncIterator[Tick]:
        """Stream realtime tick updates for a given symbol.

        Args:
            symbol: Target financial instrument symbol.

        Returns:
            Asynchronous iterator yielding real-time ticks.
        """
        ...


REALTIME_TICKS = CapabilityKey[RealtimeTicks](
    name="data.realtime-ticks",
    major=1,
)
