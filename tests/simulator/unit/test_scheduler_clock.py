"""Unit evidence for the explicit simulated scheduler clock."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.simulator.scheduler.clock import _SimulatedClock


def test_fr_sim_194_201_clock_advances_only_to_explicit_events() -> None:
    """FR-SIM-194/201: clock has no ambient read and is monotonic."""
    start = datetime(2026, 8, 15, tzinfo=UTC)
    clock = _SimulatedClock(start)
    assert clock.advance_to(start + timedelta(seconds=1)) == start + timedelta(
        seconds=1
    )
    with pytest.raises(ValueError, match="backwards"):
        clock.advance_to(start)
