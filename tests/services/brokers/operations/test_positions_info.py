"""Unit tests for FR 7: Open Positions."""

from __future__ import annotations

from app.services.brokers.operations._positions_info import (
    get_position,
    get_positions,
)


def test_get_positions_and_lookup() -> None:
    """Verify open positions retrieval and filtering."""
    positions = get_positions()
    assert len(positions) >= 2

    eur_pos = get_positions(symbol="EURUSD")
    assert all(p["symbol"] == "EURUSD" for p in eur_pos)

    pos = get_position(901)
    assert pos is not None
    assert pos["symbol"] == "EURUSD"

    assert get_position(999999) is None
