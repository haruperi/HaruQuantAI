"""Unit evidence for deterministic scheduler queue ordering."""

from datetime import UTC, datetime

import pytest
from app.services.simulator.scheduler.contracts import EVENT_PRIORITIES, _ScheduledEvent
from app.services.simulator.scheduler.queue import _EventQueue

_NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _event(priority: str, sequence: int, symbol: str = "EURUSD") -> _ScheduledEvent:
    """Build one event fixture."""
    return _ScheduledEvent(
        f"event-{priority}-{sequence}", _NOW, priority, symbol, sequence, sequence, "ok"
    )


@pytest.mark.parametrize(
    ("earlier", "later"),
    [
        (left, right)
        for index, left in enumerate(EVENT_PRIORITIES)
        for right in EVENT_PRIORITIES[index + 1 :]
    ],
)
def test_fr_sim_199_200_every_priority_pair_is_ordered(
    earlier: str, later: str
) -> None:
    """FR-SIM-199/200: every stage pair follows declared priority."""
    queue = _EventQueue()
    queue.push(_event(later, 1))
    queue.push(_event(earlier, 0))
    assert queue.pop().priority == earlier


def test_same_time_orders_symbol_source_then_scheduler_sequence() -> None:
    """FR-SIM-200: remaining key fields produce one exact order."""
    queue = _EventQueue()
    queue.push(_event("tick_arrival", 2, "GBPUSD"))
    queue.push(_event("tick_arrival", 1, "EURUSD"))
    assert [queue.pop().canonical_symbol, queue.pop().canonical_symbol] == [
        "EURUSD",
        "GBPUSD",
    ]


def test_duplicate_identity_and_empty_queue_fail_closed() -> None:
    """FR-SIM-200/203: duplicate and empty operations fail."""
    queue = _EventQueue()
    event = _event("tick_arrival", 0)
    queue.push(event)
    with pytest.raises(ValueError, match="duplicate"):
        queue.push(event)
    queue.pop()
    with pytest.raises(ValueError, match="empty"):
        queue.pop()
