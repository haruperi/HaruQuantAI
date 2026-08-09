"""Contracts for deterministic, no-lookahead replay packages.

Trading Cockpit Phase 0 reconciliation (`TC-IMP-DATA-08`, `FEAT-DATA-19`):
a replay package declares what bounded evidence to replay; `stream_replay_events`
(`service.py`) streams it in deterministic source order with an explicit
per-event availability timestamp and no future visibility relative to a
caller-supplied `as_of` boundary. `TC-IMP-SIM-01` (Simulator's
`SimulationClock`) does not exist yet, so this package never assumes a
wall-clock "now" — the required `as_of` argument is itself the fail-closed
consumer port (§8): a caller that supplies no boundary sees no events,
never an inferred one.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import field_validator, model_validator

from app.services.data.contracts._base import TracedOpenContract as _Contract
from app.utils import get_logger

logger = get_logger(__name__)


def _text(value: str) -> str:
    """Execute one private DATA operation."""
    if not value or value != value.strip():
        raise ValueError("value must be a non-empty trimmed string")
    return value


def _utc(value: datetime) -> datetime:
    """Execute one private DATA operation."""
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


class ReplayPackage(_Contract):
    """Bounded declaration of what evidence a replay session covers."""

    source_id: str
    symbols: tuple[str, ...]
    data_kind: Literal["bars", "ticks", "spreads"]
    timeframe: str | None = None
    start: datetime
    end: datetime
    request_id: str

    @field_validator("source_id", "request_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Validate one required package identifier.

        Returns:
            Non-empty trimmed identifier.
        """
        return _text(value)

    @field_validator("symbols")
    @classmethod
    def _validate_symbols(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate at least one non-empty trimmed symbol.

        Returns:
            Validated non-empty symbol tuple.

        Raises:
            ValueError: If no symbol is supplied.
        """
        if not value:
            raise ValueError("at least one symbol is required")
        return tuple(_text(symbol) for symbol in value)

    @field_validator("timeframe")
    @classmethod
    def _validate_timeframe(cls, value: str | None) -> str | None:
        """Validate an optional trimmed timeframe.

        Returns:
            Non-empty trimmed timeframe or ``None``.
        """
        return None if value is None else _text(value)

    @field_validator("start", "end")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate a required coverage boundary as aware UTC.

        Returns:
            Validated timestamp.
        """
        return _utc(value)

    @model_validator(mode="after")
    def _validate_package(self) -> ReplayPackage:
        """Validate coverage ordering and timeframe requirements.

        Returns:
            Validated package.

        Raises:
            ValueError: If the coverage window is inverted or a bars
                package omits a timeframe.
        """
        if self.start >= self.end:
            raise ValueError("start must precede end")
        if self.data_kind == "bars" and self.timeframe is None:
            raise ValueError("bars replay packages require a timeframe")
        return self


class ReplayEvent(_Contract):
    """One ordered, no-lookahead replay event."""

    sequence: int
    symbol: str
    available_at: datetime
    record: object

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str) -> str:
        """Validate the required event symbol.

        Returns:
            Non-empty trimmed symbol.
        """
        return _text(value)

    @field_validator("sequence")
    @classmethod
    def _validate_sequence(cls, value: int) -> int:
        """Validate one non-negative deterministic sequence.

        Returns:
            Validated sequence.

        Raises:
            ValueError: If the sequence is negative.
        """
        if value < 0:
            raise ValueError("sequence must be non-negative")
        return value

    @field_validator("available_at")
    @classmethod
    def _validate_available_at(cls, value: datetime) -> datetime:
        """Validate the event availability timestamp as aware UTC.

        Returns:
            Validated timestamp.
        """
        return _utc(value)


__all__ = ["ReplayEvent", "ReplayPackage"]
