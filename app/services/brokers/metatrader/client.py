"""FR 9 Bridge: MetaTrader 5 Provider Client and Primary Service Module.

Purpose:
    Provide real MetaTrader 5 terminal connection and standard broker-neutral
    operational functions, bridging terminal info, account data, symbol quotes,
    market subscriptions, orders, deals, positions, and trade execution.

Key capabilities:
    * FR 1: Broker Environment & Terminal Properties (connect, disconnect, ping, platform info).
    * FR 2: Account Properties & Balances (get_account_info, get_balances, get_permissions).
    * FR 3: Symbols & Market Data (get_symbols, get_quote, get_historical_bars, subscribe).
    * FR 4: Pending & Active Orders (get_orders, get_order, check_order).
    * FR 5: Historical Orders (list_order_history, get_history_order).
    * FR 6: Deals & Transactions (get_deals, list_deal_history, list_account_transactions).
    * FR 7: Open Positions (get_positions, get_position).
    * FR 8: Trade Execution Functions (place_order, modify_order, cancel_order, close_position).

Python API usage:
    from app.services.brokers.metatrader.client import (
        connect,
        get_account_info,
        get_quote,
        place_order,
    )

    connect()
    account = get_account_info()
    quote = get_quote("EURUSD")

CLI usage:
    uv run python -m app.services.brokers.metatrader.client
"""

from __future__ import annotations

from typing import Any

from app.contracts.broker.ports import BrokerOperationsCapability
from app.services.brokers.metatrader._account_info import (
    get_account_info,
    get_account_snapshot,
    get_balances,
    get_permissions,
)
from app.services.brokers.metatrader._deals_info import (
    get_deals,
    list_account_transactions,
    list_deal_history,
)
from app.services.brokers.metatrader._history_order_info import (
    get_history_order,
    list_order_history,
)
from app.services.brokers.metatrader._order_info import (
    check_order,
    get_order,
    get_orders,
)
from app.services.brokers.metatrader._positions_info import (
    get_position,
    get_positions,
)
from app.services.brokers.metatrader._symbol_info import (
    get_historical_bars,
    get_quote,
    get_spread,
    get_symbol_info,
    get_symbols,
    get_ticks,
    list_subscriptions,
    select_symbol,
    subscribe_bars,
    subscribe_quotes,
    subscribe_ticks,
    unsubscribe,
)
from app.services.brokers.metatrader._terminal_info import (
    _MT5_AVAILABLE,
    connect,
    disconnect,
    get_connection_status,
    get_last_error,
    get_platform_info,
    get_provider_specification,
    get_terminal_info,
    is_connected,
    ping,
)
from app.services.brokers.metatrader._trade import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    close_position,
    modify_order,
    modify_position,
    place_order,
)
from app.services.brokers.metatrader.config import MetaTraderConfig

__all__ = [
    "calculate_margin",
    "calculate_profit",
    "cancel_order",
    "check_order",
    "close_position",
    "connect",
    "disconnect",
    "fr_brk_metatrader",
    "get_account_info",
    "get_account_snapshot",
    "get_balances",
    "get_connection_status",
    "get_deals",
    "get_historical_bars",
    "get_history_order",
    "get_last_error",
    "get_order",
    "get_orders",
    "get_permissions",
    "get_platform_info",
    "get_position",
    "get_positions",
    "get_provider_specification",
    "get_quote",
    "get_spread",
    "get_symbol_info",
    "get_symbols",
    "get_terminal_info",
    "get_ticks",
    "is_connected",
    "list_account_transactions",
    "list_deal_history",
    "list_order_history",
    "list_subscriptions",
    "modify_order",
    "modify_position",
    "ping",
    "place_order",
    "select_symbol",
    "subscribe_bars",
    "subscribe_quotes",
    "subscribe_ticks",
    "unsubscribe",
]


def fr_brk_metatrader(
    config: MetaTraderConfig | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Execute FR-BRK-METATRADER status report.

    Args:
        config: Optional configuration instance.

    Returns:
        Dictionary summarizing connection and account state.
    """
    return {
        "platform": "mt5",
        "mt5_package_available": _MT5_AVAILABLE,
        "connected": is_connected(),
        "account": get_account_info(),
        "symbols": len(get_symbols()),
    }


class MetaTraderService(BrokerOperationsCapability):
    """Service class implementing BrokerOperationsCapability for live MetaTrader 5."""

    def __init__(self, config: MetaTraderConfig | None = None) -> None:
        """Initialize MetaTrader 5 service."""
        self.config = config or MetaTraderConfig()

    def connect(
        self,
        account_id: str | int | None = None,
        server: str | None = None,
        password: str | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Connect to MT5."""
        return connect(
            login=account_id,
            server=server,
            password=password,
            timeout=timeout,
            config=self.config,
        )

    def disconnect(self) -> bool:
        """Disconnect from MT5."""
        return disconnect()

    def is_connected(self) -> bool:
        """Check connection."""
        return is_connected()

    def get_account_info(self) -> dict[str, Any]:
        """Get account info."""
        return get_account_info()

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Get symbol metadata."""
        return get_symbol_info(symbol)

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Get quote."""
        return get_quote(symbol)

    def get_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get orders."""
        return get_orders(symbol)

    def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get positions."""
        return get_positions(symbol)

    def place_order(self, request: dict[str, Any]) -> dict[str, Any]:
        """Place order."""
        return place_order(request)


def _run_usage_example() -> None:
    """Demonstrate MetaTrader 5 client operations."""
    print("=== MetaTrader 5 Client Demonstration ===")
    conn_res = connect()
    print(f"Connection Result: {conn_res}")
    print(f"Platform: {get_platform_info()}")
    print(f"Account: {get_account_info()['name']}")
    print(f"Symbols Available: {get_symbols()}")
    print(f"Quote EURUSD: {get_quote('EURUSD')}")


if __name__ == "__main__":
    _run_usage_example()
