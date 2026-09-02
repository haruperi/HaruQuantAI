"""FR 6: MetaTrader 5 Deals and Account Financial Transactions."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.metatrader.client import MetaTraderClient


def _resolve_client(client: MetaTraderClient | Any | None = None) -> Any:
    """Resolve the provided client instance or fall back to the active default."""
    if client is not None:
        return client
    from app.services.brokers.metatrader.client import get_default_client

    return get_default_client()


def get_deals(
    deal_id: int | str | None = None,
    client: MetaTraderClient | Any | None = None,
) -> list[dict[str, Any]]:
    """Retrieve executed deals from MT5.

    Args:
        deal_id: Optional deal ticket ID.
        client: Optional MetaTraderClient instance.

    Returns:
        List of deal dictionaries.

    Raises:
        RuntimeError: If deals query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
        msg = "MetaTrader5 package is not available."
        raise RuntimeError(msg)

    if deal_id is not None and str(deal_id).isdigit():
        deals = mt5.history_deals_get(ticket=int(deal_id))
    else:
        deals = mt5.history_deals_get(0, int(time.time()))

    if deals is None:
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Deals query failed")
        )
        msg = f"Failed to retrieve deals from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [d._asdict() for d in deals]


def list_deal_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
    client: MetaTraderClient | Any | None = None,
) -> list[dict[str, Any]]:
    """Retrieve deal history records.

    Args:
        symbol: Optional symbol filter.
        start: Optional start timestamp.
        end: Optional end timestamp.
        client: Optional MetaTraderClient instance.

    Returns:
        List of deal history dictionaries.

    Raises:
        RuntimeError: If deals query fails.
    """
    client_inst = _resolve_client(client)
    mt5 = getattr(client_inst, "mt5", client_inst)
    if mt5 is None or not getattr(client_inst, "is_available", lambda: True)():
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
        err = (
            mt5.last_error()
            if hasattr(mt5, "last_error")
            else (-1, "Deal history query failed")
        )
        msg = f"Failed to retrieve deal history from MetaTrader 5: [{err[0]}] {err[1]}"
        raise RuntimeError(msg)

    return [d._asdict() for d in deals]


def list_account_transactions(
    start: Any = None,
    end: Any = None,
    client: MetaTraderClient | Any | None = None,
) -> list[dict[str, Any]]:
    """Retrieve account transactions from deals.

    Args:
        start: Optional start timestamp.
        end: Optional end timestamp.
        client: Optional MetaTraderClient instance.

    Returns:
        List of financial transaction records.

    Raises:
        RuntimeError: If deals query fails.
    """
    deals = list_deal_history(start=start, end=end, client=client)
    txs: list[dict[str, Any]] = []
    for d in deals:
        txs.append(
            {
                "transaction_id": str(d.get("ticket")),
                "order_id": str(d.get("order")),
                "symbol": d.get("symbol"),
                "type": d.get("type"),
                "entry": d.get("entry"),
                "volume": d.get("volume"),
                "price": d.get("price"),
                "profit": d.get("profit"),
                "amount": float(d.get("profit", 0.0)),
                "swap": d.get("swap"),
                "commission": d.get("commission"),
                "fee": d.get("fee"),
                "time": d.get("time"),
                "comment": d.get("comment"),
            }
        )
    return txs
