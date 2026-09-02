"""Unit tests for MetaTrader 5 FR 6: Deals and Transactions."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._deals_info as deal_mod
import pytest
from app.services.brokers.metatrader._deals_info import (
    get_deals,
    list_account_transactions,
    list_deal_history,
)


def test_deals_and_transactions_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify deals and transactions retrieval."""
    mock_deal = MagicMock()
    mock_deal.ticket = 801
    mock_deal._asdict.return_value = {
        "ticket": 801,
        "order": 501,
        "symbol": "EURUSD",
        "type": 0,
        "profit": 150.0,
        "time": 1788375000.0,
    }

    monkeypatch.setattr(
        deal_mod.mt5, "history_deals_get", lambda *a, **kw: (mock_deal,)
    )

    deals = get_deals()
    assert len(deals) == 1
    assert deals[0]["ticket"] == 801

    history = list_deal_history()
    assert len(history) == 1

    txs = list_account_transactions()
    assert len(txs) == 1
    assert txs[0]["amount"] == 150.0


def test_deals_failure_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify deals query failure raises RuntimeError."""
    monkeypatch.setattr(deal_mod.mt5, "history_deals_get", lambda *a, **kw: None)
    monkeypatch.setattr(
        deal_mod.mt5, "last_error", lambda: (-10004, "No IPC connection")
    )

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve deals from MetaTrader 5"
    ):
        get_deals()
