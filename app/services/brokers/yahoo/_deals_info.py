"""FR 6: Yahoo Finance Deals and Transactions (Capability Unavailable)."""

from __future__ import annotations

from typing import Any


def get_deals(deal_id: int | str | None = None) -> list[dict[str, Any]]:
    """Retrieve deals.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'deals:get' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def list_deal_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve deal history.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'deals:history' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)


def list_account_transactions(
    start: Any = None,
    end: Any = None,
) -> list[dict[str, Any]]:
    """Retrieve account transactions.

    Raises:
        NotImplementedError: Because Yahoo Finance is a market data provider only.
    """
    msg = "Broker capability 'transactions:list' is unavailable for Yahoo Finance provider."
    raise NotImplementedError(msg)
