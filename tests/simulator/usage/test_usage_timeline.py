"""Runnable usage examples for the Simulation timeline."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.simulator.timeline import (
    Tick,
    build_tick_timeline,
    validate_intent_timing,
)
from tests.simulator.unit.test_timeline import _dataset


def test_usage_tick_contract() -> None:
    """Construct one canonical immutable tick."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    tick = Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="provider",
        sequence=0,
        available_at=instant,
    )
    assert tick.ask - tick.bid == Decimal("0.00002")


def test_usage_build_tick_timeline() -> None:
    """Build an immutable clock from a Data-owned tick dataset."""
    timeline = build_tick_timeline(_dataset())
    assert tuple(tick.sequence for tick in timeline) == (0, 1)


def test_usage_validate_intent_timing() -> None:
    """Validate evidence visible at execution time."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    validate_intent_timing(instant, instant)
