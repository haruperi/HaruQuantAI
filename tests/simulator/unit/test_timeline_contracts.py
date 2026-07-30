"""Unit tests for the canonical Simulation tick."""

from datetime import UTC, datetime, timedelta
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


@pytest.mark.parametrize(
    "update",
    [
        {"symbol": " "},
        {"timestamp": datetime(2025, 1, 1)},  # noqa: DTZ001 - invalid test input.
        {"bid": Decimal("NaN")},
        {"bid": Decimal(0)},
        {"sequence": -1},
        {"available_at": datetime(2024, 12, 31, tzinfo=UTC)},
        {"volume": Decimal(1), "volume_unit": None},
        {"source_bar_time": datetime(2025, 1, 1, tzinfo=UTC)},
        {
            "source_bar_time": datetime(2025, 1, 1, tzinfo=UTC),
            "tick_index_in_bar": -1,
            "bar_phase": 1,
        },
        {
            "source_bar_time": datetime(2025, 1, 1, tzinfo=UTC),
            "tick_index_in_bar": 0,
            "bar_phase": 16,
        },
    ],
)
def test_tick_rejects_invalid_contract_evidence(update: dict[str, object]) -> None:
    """Reject malformed text, time, numeric, availability, and bar evidence."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    values: dict[str, object] = {
        "symbol": "EURUSD",
        "timestamp": instant,
        "bid": Decimal("1.1"),
        "ask": Decimal("1.2"),
        "source_id": "fixture",
        "sequence": 0,
        "available_at": instant,
    }
    with pytest.raises(ValueError, match=r".+"):
        Tick(**(values | update))


def test_tick_serializes_decimal_evidence_exactly() -> None:
    """Serialize prices and optional volume as exact strings."""
    instant = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(seconds=1)
    tick = Tick(
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="fixture",
        sequence=1,
        available_at=instant,
        volume=Decimal(0),
        volume_unit="lot",
    )
    payload = tick.model_dump(mode="json")
    assert payload["bid"] == "1.10000"
    assert payload["volume"] == "0"
