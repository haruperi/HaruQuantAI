"""Tick stream capability specification v1."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol, runtime_checkable

CAPABILITY_ID = "data.tick_stream.v1"
_MIN_BUFFER_SIZE = 1
_MAX_BUFFER_SIZE = 4096


@dataclass(frozen=True, slots=True)
class TickStreamRequestV1:
    """Request to start a real-time tick stream for a financial instrument.

    Attributes:
        symbol: Ticker symbol to stream.
        buffer_size: Internal queue buffer capacity (1 to 4096).
    """

    symbol: str
    buffer_size: int = 256

    def __post_init__(self) -> None:
        """Validate request invariants.

        Raises:
            ValueError: If symbol is blank or buffer_size is out of range.
        """
        if not self.symbol or not self.symbol.strip():
            msg = "symbol must be a non-blank string"
            raise ValueError(msg)
        if not _MIN_BUFFER_SIZE <= self.buffer_size <= _MAX_BUFFER_SIZE:
            msg = (
                f"buffer_size must be between {_MIN_BUFFER_SIZE} and {_MAX_BUFFER_SIZE}"
            )
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class TickStreamEventV1:
    """Single immutable tick event emitted by an active stream.

    Attributes:
        sequence: Monotonically increasing 1-based sequence index.
        symbol: Ticker symbol.
        payload: Immutable tick attribute mapping.
    """

    sequence: int
    symbol: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        """Validate event invariants and ensure immutable payload.

        Raises:
            ValueError: If sequence < 1 or symbol is blank.
        """
        if self.sequence < 1:
            msg = "sequence must be >= 1"
            raise ValueError(msg)
        if not self.symbol or not self.symbol.strip():
            msg = "symbol must be a non-blank string"
            raise ValueError(msg)
        if not isinstance(self.payload, MappingProxyType):
            object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@runtime_checkable
class TickStreamCapabilityV1(Protocol):
    """Protocol for providers supplying real-time tick event streams."""

    @property
    def active(self) -> bool:
        """Return True if the tick stream is actively running."""
        ...

    @property
    def generation_id(self) -> str | None:
        """Return identifier of the active stream generation, or None if inactive."""
        ...

    async def start(self, request: TickStreamRequestV1) -> None:
        """Start streaming ticks for the requested symbol.

        Args:
            request: Validated tick stream parameters.
        """
        ...

    def events(self) -> AsyncIterator[TickStreamEventV1]:
        """Asynchronously iterate over incoming tick stream events.

        Returns:
            Async iterator yielding TickStreamEventV1 instances.
        """
        ...

    async def stop(self) -> None:
        """Stop the active tick stream and release internal buffers."""
        ...


__all__ = (
    "CAPABILITY_ID",
    "TickStreamCapabilityV1",
    "TickStreamEventV1",
    "TickStreamRequestV1",
)
