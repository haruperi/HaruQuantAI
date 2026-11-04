"""Mutable SQX-style tick event independent of broker wire records.

Description:
    Owns donor TickEvent lifecycle, session boundaries and bar boundary flags.
    Maintains source timestamp units (milliseconds) without implicit coercion.
Purpose:
    FEAT-DATA-TICK-EVENT: Donor event value and state semantics.
Key Capabilities:
    - FR-DATA-TICK-EVENT-state: Event set, copy and timestamp handling.
Python API Usage:
    TickEvent().set(0, 1, 2, 1.0, 1.1, 0.0, 0)
CLI Usage:
    uv run pytest tests/core/data/test_events.py --no-cov
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TickEvent:
    """Mutable recovered SQX tick/event record; `time` is epoch milliseconds."""

    is_set: bool = False
    symbol_hash: int = 0
    connection_hash: int = 0
    time: int = -1
    ask: float = 0.0
    bid: float = 0.0
    volume: float = 0.0
    session_start_time: int = 0
    session_end_time: int = 0
    bar_open: bool = False
    bar_close: bool = False

    def set(
        self,
        time: int,
        connection_hash: int,
        symbol_hash: int,
        bid: float,
        ask: float,
        volume: float,
        session_start_time: int,
        session_end_time: int = 0,
        bar_open: bool = False,
        bar_close: bool = False,
    ) -> None:
        """Match donor's explicit setter without implicitly changing `is_set`."""
        self.time = time
        self.symbol_hash = symbol_hash
        self.connection_hash = connection_hash
        self.bid = bid
        self.ask = ask
        self.volume = volume
        self.session_start_time = session_start_time
        self.session_end_time = session_end_time
        self.bar_open = bar_open
        self.bar_close = bar_close

    def set_from_event(self, event: TickEvent) -> None:
        """Match donor `set(TickEvent)` overload, retaining `is_set` state."""
        self.set(
            event.time,
            event.connection_hash,
            event.symbol_hash,
            event.bid,
            event.ask,
            event.volume,
            event.session_start_time,
            event.session_end_time,
            event.bar_open,
            event.bar_close,
        )

    def copy_values(self, event: TickEvent) -> None:
        """Match donor `copyValues`, including its non-copy of `barOpen`.

        The recovered Java method assigns `barClose` twice and does not copy
        `isSet` or `barOpen`. Retain that observable behavior explicitly.
        """
        self.time = event.time
        self.symbol_hash = event.symbol_hash
        self.connection_hash = event.connection_hash
        self.bid = event.bid
        self.ask = event.ask
        self.volume = event.volume
        self.session_start_time = event.session_start_time
        self.session_end_time = event.session_end_time
        self.bar_close = event.bar_close

    def __str__(self) -> str:
        """Represent `ask,bid` in donor field order."""
        return f"{self.ask},{self.bid}"
