"""Unit tests for FR 5: Historical Orders and Audit Listings."""

from __future__ import annotations

from app.services.brokers.operations._history_order_info import (
    get_history_order,
    list_order_history,
)


def test_list_order_history_and_lookup() -> None:
    """Verify historical order queries and individual ticket retrieval."""
    history = list_order_history()
    assert len(history) >= 2

    eur_history = list_order_history(symbol="EURUSD")
    assert all(o["symbol"] == "EURUSD" for o in eur_history)

    h_order = get_history_order(501)
    assert h_order is not None
    assert h_order["symbol"] == "EURUSD"
    assert h_order["state"] == "FILLED"

    assert get_history_order(999999) is None
