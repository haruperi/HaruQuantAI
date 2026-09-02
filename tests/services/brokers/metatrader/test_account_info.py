"""Unit tests for MetaTrader 5 FR 2: Account Properties and Balances."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.brokers.metatrader._account_info import (
    get_account_info,
    get_account_snapshot,
    get_balances,
    get_permissions,
)
from app.services.brokers.metatrader.client import MetaTraderClient


def test_account_properties_success() -> None:
    """Verify querying live account properties and balances via client instance."""
    mock_mt5 = MagicMock()
    mock_acc = MagicMock()
    mock_acc._asdict.return_value = {
        "login": 61563411,
        "name": "Rufaro Haruperi",
        "currency": "USD",
        "balance": 53375.40,
        "equity": 53375.40,
        "margin": 0.0,
        "margin_free": 53375.40,
        "margin_level": 0.0,
        "profit": 0.0,
        "trade_allowed": True,
        "trade_expert": True,
    }
    mock_mt5.account_info.return_value = mock_acc
    mock_mt5.terminal_info.return_value = MagicMock(connected=True)

    client = MetaTraderClient(mt5_module=mock_mt5)
    client.state["connected"] = True

    acc = get_account_info(client=client)
    assert acc["login"] == 61563411
    assert acc["balance"] == 53375.40

    balances = get_balances(client=client)
    assert balances["balance"] == 53375.40
    assert balances["currency"] == "USD"

    perms = get_permissions(client=client)
    assert "account:read" in perms
    assert "orders:create" in perms
    assert "algo_trading:allowed" in perms

    snap = get_account_snapshot(client=client)
    assert snap["login"] == 61563411
    assert snap["connected"] is True
    assert "timestamp" in snap


def test_account_info_failure_raises_error() -> None:
    """Verify account_info query failure strictly raises RuntimeError."""
    mock_mt5 = MagicMock()
    mock_mt5.account_info.return_value = None
    mock_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MetaTraderClient(mt5_module=mock_mt5)

    with pytest.raises(
        RuntimeError,
        match=r"Failed to retrieve MetaTrader 5 account info: \[-10004\] No IPC connection",
    ):
        get_account_info(client=client)
