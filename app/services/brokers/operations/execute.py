"""FR 9: Broker Operations Execution Bridge and Primary Service Module.

Purpose:
    Provide standard broker-neutral operational functions without business logic,
    bridging terminal info, account info, symbol market data, orders, deals,
    positions, and trade execution.

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
    from app.services.brokers.operations.execute import (
        connect,
        get_account_info,
        get_quote,
        place_order,
    )

    connect()
    account = get_account_info()
    quote = get_quote("EURUSD")
    order = place_order({"symbol": "EURUSD", "volume": 0.1, "type": "BUY"})

CLI usage:
    uv run python -m app.services.brokers.operations.execute
"""

from __future__ import annotations

from typing import Any

from app.contracts.broker.ports import BrokerOperationsCapability
from app.services.brokers.operations._account_info import (
    get_account_info,
    get_account_snapshot,
    get_balances,
    get_permissions,
)
from app.services.brokers.operations._deals_info import (
    get_deals,
    list_account_transactions,
    list_deal_history,
)
from app.services.brokers.operations._history_order_info import (
    get_history_order,
    list_order_history,
)
from app.services.brokers.operations._order_info import (
    check_order,
    get_order,
    get_orders,
)
from app.services.brokers.operations._positions_info import (
    get_position,
    get_positions,
)
from app.services.brokers.operations._symbol_info import (
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
from app.services.brokers.operations._terminal_info import (
    connect,
    disconnect,
    get_connection_status,
    get_platform_info,
    get_provider_specification,
    get_terminal_info,
    is_connected,
    ping,
)
from app.services.brokers.operations._trade import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    close_position,
    modify_order,
    modify_position,
    place_order,
)
from app.services.brokers.operations.config import BrokerOperationsConfig

__all__ = [
    "calculate_margin",
    "calculate_profit",
    "cancel_order",
    "check_order",
    "close_position",
    "connect",
    "disconnect",
    "fr_brk_operations",
    "get_account_info",
    "get_account_snapshot",
    "get_balances",
    "get_connection_status",
    "get_deals",
    "get_historical_bars",
    "get_history_order",
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


def fr_brk_operations(
    config: BrokerOperationsConfig | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Execute FR-BRK-OPERATIONS operational status report.

    Args:
        config: Optional BrokerOperationsConfig instance.

    Returns:
        Dictionary summarizing connection and account state.
    """
    return {
        "connected": is_connected(),
        "account": get_account_info(),
        "symbols": len(get_symbols()),
        "open_positions": len(get_positions()),
        "active_orders": len(get_orders()),
    }


class BrokerOperationsService(BrokerOperationsCapability):
    """Service class implementing standard broker-neutral operational capability."""

    def __init__(self, config: BrokerOperationsConfig | None = None) -> None:
        """Initialize the broker operations service.

        Args:
            config: Optional configuration instance.
        """
        self.config = config or BrokerOperationsConfig()

    def connect(
        self,
        account_id: str | int | None = None,
        server: str | None = None,
        password: str | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Connect to the active broker environment."""
        return connect(
            account_id=account_id,
            server=server,
            password=password,
            timeout=timeout,
        )

    def disconnect(self) -> bool:
        """Disconnect from the broker environment."""
        return disconnect()

    def is_connected(self) -> bool:
        """Check if connected to the broker."""
        return is_connected()

    def get_account_info(self) -> dict[str, Any]:
        """Retrieve active account properties and balances."""
        return get_account_info()

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Retrieve symbol metadata."""
        return get_symbol_info(symbol)

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Retrieve current bid/ask quote for symbol."""
        return get_quote(symbol)

    def get_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """List active and pending orders."""
        return get_orders(symbol)

    def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """List open trading positions."""
        return get_positions(symbol)

    def place_order(self, request: dict[str, Any]) -> dict[str, Any]:
        """Submit a new trade order."""
        return place_order(request)


def _run_usage_example() -> None:
    """Demonstrate broker operations standalone."""
    print("=== Broker Operations Demonstration ===")
    conn_result = connect(10001, "Demo-MT5-Live", "pass123")
    print(f"Connected: {conn_result}")

    acc = get_account_info()
    print(f"Account: {acc['name']} ({acc['currency']})")

    quote = get_quote("EURUSD")
    print(
        f"Quote EURUSD: Bid={quote['bid']}, Ask={quote['ask']}, Spread={quote['spread']}"
    )

    orders = get_orders()
    print(f"Active Orders ({len(orders)}): {[o['order_id'] for o in orders]}")

    positions = get_positions()
    print(f"Open Positions ({len(positions)}): {[p['position_id'] for p in positions]}")

    trade = place_order({"symbol": "EURUSD", "volume": 0.1, "type": "BUY"})
    print(f"Placed Trade: {trade}")


if __name__ == "__main__":
    _run_usage_example()
