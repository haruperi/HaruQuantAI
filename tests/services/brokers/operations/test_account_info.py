"""Unit tests for FR 2: Account Properties, Balances, and Permissions."""

from __future__ import annotations

from app.services.brokers.operations._account_info import (
    get_account_info,
    get_account_snapshot,
    get_balances,
    get_permissions,
)
from app.services.brokers.operations._terminal_info import connect


def test_account_properties_and_balances() -> None:
    """Verify account metadata and balance structures."""
    connect(10001)
    acc = get_account_info()
    assert acc["account_id"] == 10001
    assert acc["currency"] == "USD"
    assert acc["connected"] is True

    balances = get_balances()
    assert balances["balance"] > 0
    assert balances["equity"] > 0
    assert balances["margin_free"] > 0

    perms = get_permissions()
    assert "account:read" in perms
    assert "orders:create" in perms

    snap = get_account_snapshot()
    assert snap["account_id"] == 10001
    assert "timestamp" in snap
    assert snap["connected"] is True
