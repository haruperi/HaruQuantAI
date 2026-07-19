"""Unit tests for the canonical Simulation tick."""
# ruff: noqa: INP001

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.simulator.timeline import Tick


def test_tick_rejects_negative_spread() -> None:
    """Reject an ask below its bid."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="ask"):
        Tick(
            symbol="EURUSD",
            timestamp=instant,
            bid=Decimal("1.2"),
            ask=Decimal("1.1"),
            source_id="fixture",
            sequence=0,
            available_at=instant,
        )


def test_tick_is_immutable() -> None:
    """Reject mutation of canonical tick state."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    tick = Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.1"),
        ask=Decimal("1.2"),
        source_id="fixture",
        sequence=0,
        available_at=instant,
    )
    with pytest.raises(ValueError, match="frozen"):
        tick.bid = Decimal(1)
