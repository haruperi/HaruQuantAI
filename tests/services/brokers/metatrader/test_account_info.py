"""Unit tests for MetaTrader 5 FR 2: Account Properties and Balances."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._account_info as acc_mod
import pytest
from app.services.brokers.metatrader._account_info import (
    get_account_info,
    get_account_snapshot,
    get_balances,
    get_permissions,
)


def test_account_properties_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify querying live account properties and balances."""
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

    monkeypatch.setattr(acc_mod.mt5, "account_info", lambda: mock_acc)

    acc = get_account_info()
    assert acc["login"] == 61563411
    assert acc["balance"] == 53375.40

    balances = get_balances()
    assert balances["balance"] == 53375.40
    assert balances["currency"] == "USD"

    perms = get_permissions()
    assert "account:read" in perms
    assert "orders:create" in perms
    assert "algo_trading:allowed" in perms

    snap = get_account_snapshot()
    assert snap["login"] == 61563411
    assert "timestamp" in snap


def test_account_info_failure_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify account_info query failure strictly raises RuntimeError."""
    monkeypatch.setattr(acc_mod.mt5, "account_info", lambda: None)
    monkeypatch.setattr(
        acc_mod.mt5, "last_error", lambda: (-10004, "No IPC connection")
    )

    with pytest.raises(
        RuntimeError,
        match=r"Failed to retrieve MetaTrader 5 account info: \[-10004\] No IPC connection",
    ):
        get_account_info()
