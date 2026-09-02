"""FR 6: Deals and Account Financial Transactions."""

from __future__ import annotations

import time
from typing import Any

_deals_db: dict[int, dict[str, Any]] = {
    801: {
        "deal_id": 801,
        "order_id": 501,
        "position_id": 901,
        "symbol": "EURUSD",
        "type": "DEAL_TYPE_BUY",
        "entry": "ENTRY_IN",
        "volume": 0.5,
        "price": 1.08200,
        "commission": -1.75,
        "swap": 0.0,
        "profit": 0.0,
        "time": time.time() - 86390,
        "comment": "Auto execution",
    },
    802: {
        "deal_id": 802,
        "order_id": 502,
        "position_id": 902,
        "symbol": "USDJPY",
        "type": "DEAL_TYPE_SELL",
        "entry": "ENTRY_IN",
        "volume": 1.0,
        "price": 154.500,
        "commission": -3.50,
        "swap": -0.80,
        "profit": 0.0,
        "time": time.time() - 43190,
        "comment": "Auto short execution",
    },
}

_account_transactions: list[dict[str, Any]] = [
    {
        "tx_id": "tx_001",
        "type": "DEPOSIT",
        "amount": 10000.0,
        "currency": "USD",
        "time": time.time() - 604800,
        "comment": "Initial wire deposit",
    },
    {
        "tx_id": "tx_002",
        "type": "COMMISSION",
        "amount": -5.25,
        "currency": "USD",
        "time": time.time() - 43190,
        "comment": "Trade fees",
    },
]


def get_deals(deal_id: int | str | None = None) -> list[dict[str, Any]]:
    """Retrieve executed deals, optionally looking up by a specific deal ID.

    Args:
        deal_id: Optional deal identifier.

    Returns:
        List containing matching deals or all deals.
    """
    if deal_id is not None:
        did = int(deal_id) if str(deal_id).isdigit() else deal_id
        deal = _deals_db.get(did)  # type: ignore[arg-type]
        return [deal] if deal is not None else []
    return list(_deals_db.values())


def list_deal_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve deal history records filtered by symbol and time range.

    Args:
        symbol: Optional symbol filter.
        start: Optional start timestamp.
        end: Optional end timestamp.

    Returns:
        List of deal dictionaries.
    """
    deals = list(_deals_db.values())
    if symbol:
        sym = symbol.upper()
        deals = [d for d in deals if d["symbol"] == sym]
    if start is not None:
        deals = [d for d in deals if d["time"] >= float(start)]
    if end is not None:
        deals = [d for d in deals if d["time"] <= float(end)]
    return deals


def list_account_transactions(
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve financial account transactions (deposits, withdrawals, balance adjustments).

    Args:
        start: Optional start timestamp.
        end: Optional end timestamp.

    Returns:
        List of transaction records.
    """
    txs = list(_account_transactions)
    if start is not None:
        txs = [t for t in txs if t["time"] >= float(start)]
    if end is not None:
        txs = [t for t in txs if t["time"] <= float(end)]
    return txs
