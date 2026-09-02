"""Unit tests for MetaTrader 5 FR 6: Deals and Transactions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.brokers.metatrader._deals_info import (
    get_deals,
    list_account_transactions,
    list_deal_history,
)
from app.services.brokers.metatrader.client import MetaTraderClient


def test_deals_and_transactions_success() -> None:
    """Verify deals and transactions retrieval via client instance."""
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

    mock_mt5 = MagicMock()
    mock_mt5.history_deals_get.return_value = (mock_deal,)

    client = MetaTraderClient(mt5_module=mock_mt5)

    deals = get_deals(client=client)
    assert len(deals) == 1
    assert deals[0]["ticket"] == 801

    history = list_deal_history(client=client)
    assert len(history) == 1

    txs = list_account_transactions(client=client)
    assert len(txs) == 1
    assert txs[0]["amount"] == 150.0


def test_deals_failure_raises_error() -> None:
    """Verify deals query failure raises RuntimeError."""
    mock_mt5 = MagicMock()
    mock_mt5.history_deals_get.return_value = None
    mock_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MetaTraderClient(mt5_module=mock_mt5)

    with pytest.raises(
        RuntimeError, match=r"Failed to retrieve deals from MetaTrader 5"
    ):
        get_deals(client=client)
