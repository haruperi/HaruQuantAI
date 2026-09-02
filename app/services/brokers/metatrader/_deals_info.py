"""FR 6: MetaTrader 5 Deals and Account Financial Transactions."""

from __future__ import annotations

import time
from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False


def get_deals(deal_id: int | str | None = None) -> list[dict[str, Any]]:
    """Retrieve executed deals from MT5.

    Args:
        deal_id: Optional deal ticket ID.

    Returns:
        List of deal dictionaries.

    Raises:
        RuntimeError: If deals query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    if deal_id is not None and str(deal_id).isdigit():
        deals = mt5.history_deals_get(ticket=int(deal_id))
    else:
        deals = mt5.history_deals_get(0, int(time.time()))

    if deals is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve deals from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [d._asdict() for d in deals]


def list_deal_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve deal history records.

    Args:
        symbol: Optional symbol filter.
        start: Optional start timestamp.
        end: Optional end timestamp.

    Returns:
        List of deal history dictionaries.

    Raises:
        RuntimeError: If deals query fails.
    """
    if not _MT5_AVAILABLE or mt5 is None:
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    start_ts = int(start) if start else 0
    end_ts = int(end) if end else int(time.time())

    deals = (
        mt5.history_deals_get(start_ts, end_ts, symbol=symbol.upper())
        if symbol
        else mt5.history_deals_get(start_ts, end_ts)
    )
    if deals is None:
        err = mt5.last_error()
        msg = f"Failed to retrieve deal history from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [d._asdict() for d in deals]


def list_account_transactions(
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve account transactions from deals.

    Args:
        start: Optional start timestamp.
        end: Optional end timestamp.

    Returns:
        List of financial transaction records.

    Raises:
        RuntimeError: If deals query fails.
    """
    deals = list_deal_history(start=start, end=end)
    return [
        {
            "tx_id": f"mt5_tx_{d.get('ticket', i)}",
            "type": "BALANCE" if d.get("type") == 2 else "DEAL",
            "amount": d.get("profit", 0.0),
            "currency": "USD",
            "time": d.get("time", time.time()),
        }
        for i, d in enumerate(deals)
    ]
