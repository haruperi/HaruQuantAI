"""Tick stream capability v1 contract."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class TickStreamRequestV1:
    """Request model for starting a tick stream."""

    symbol: str
    buffer_size: int = 256


@dataclass(frozen=True, slots=True)
class TickStreamEventV1:
    """Individual tick stream event."""

    sequence: int = 0
    symbol: str = ""
    bid: float = 0.0
    ask: float = 0.0
    timestamp: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)


class TickStreamCapabilityV1(Protocol):
    """Protocol for a real-time tick streaming capability."""

    @property
    def generation_id(self) -> str:
        """Return the unique generation ID for this stream instance."""
        ...

    async def start(self, request: TickStreamRequestV1) -> None:
        """Start streaming ticks."""
        ...

    async def stop(self) -> None:
        """Stop streaming ticks."""
        ...

    def events(self) -> AsyncIterator[TickStreamEventV1]:
        """Iterate over real-time tick events."""
        ...
