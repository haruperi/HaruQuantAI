"""Unit tests for FR 6: Deals and Account Transactions."""

from __future__ import annotations

from app.services.brokers.operations._deals_info import (
    get_deals,
    list_account_transactions,
    list_deal_history,
)


def test_get_deals_and_history() -> None:
    """Verify deal retrieval and deal history filtering."""
    deals = get_deals()
    assert len(deals) >= 2

    single = get_deals(deal_id=801)
    assert len(single) == 1
    assert single[0]["deal_id"] == 801

    eur_deals = list_deal_history(symbol="EURUSD")
    assert all(d["symbol"] == "EURUSD" for d in eur_deals)


def test_list_account_transactions() -> None:
    """Verify account financial transaction logs."""
    txs = list_account_transactions()
    assert len(txs) >= 2
    types = [t["type"] for t in txs]
    assert "DEPOSIT" in types
