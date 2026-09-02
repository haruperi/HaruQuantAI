"""FR 6: cTrader Deals and Account Financial Transactions."""

from __future__ import annotations

from typing import Any

from app.services.brokers.ctrader._terminal_info import is_connected


def get_deals(deal_id: int | str | None = None) -> list[dict[str, Any]]:  # noqa: ARG001
    """Retrieve executed deals.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "cTrader is not connected. Call connect() first."
        raise RuntimeError(msg)
    return []


def list_deal_history(
    symbol: str | None = None,  # noqa: ARG001
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
) -> list[dict[str, Any]]:
    """Retrieve deal history.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "cTrader is not connected. Call connect() first."
        raise RuntimeError(msg)
    return []


def list_account_transactions(
    start: Any = None,  # noqa: ARG001
    end: Any = None,  # noqa: ARG001
) -> list[dict[str, Any]]:
    """Retrieve financial transaction history.

    Raises:
        RuntimeError: If not connected.
    """
    if not is_connected():
        msg = "cTrader is not connected. Call connect() first."
        raise RuntimeError(msg)
    return []
