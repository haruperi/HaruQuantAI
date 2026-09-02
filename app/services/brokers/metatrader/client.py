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
        MetaTraderClient,
        connect,
        get_account_info,
        get_quote,
        place_order,
    )

    client = MetaTraderClient()
    client.connect()
    account = client.get_account_info()
    quote = client.get_quote("EURUSD")

CLI usage:
    uv run python -m app.services.brokers.metatrader.client
"""

from __future__ import annotations

from typing import Any

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False

from app.contracts.broker.ports import BrokerOperationsCapability
from app.services.brokers.metatrader import (
    _account_info,
    _deals_info,
    _history_order_info,
    _order_info,
    _positions_info,
    _symbol_info,
    _terminal_info,
    _trade,
)
from app.services.brokers.metatrader._account_info import (
    get_account_snapshot,
    get_balances,
    get_permissions,
)
from app.services.brokers.metatrader._order_info import (
    check_order,
)
from app.services.brokers.metatrader._symbol_info import (
    get_historical_bars,
    get_spread,
    get_ticks,
    list_subscriptions,
    select_symbol,
    subscribe_bars,
    subscribe_quotes,
    subscribe_ticks,
    unsubscribe,
)
from app.services.brokers.metatrader._terminal_info import (
    get_connection_status,
    get_platform_info,
    get_provider_specification,
    get_terminal_info,
    ping,
)
from app.services.brokers.metatrader._trade import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    close_position,
    modify_order,
    modify_position,
)
from app.services.brokers.metatrader.config import MetaTraderConfig

__all__ = [
    "MetaTraderClient",
    "MetaTraderService",
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
    "get_default_client",
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
    "set_default_client",
    "subscribe_bars",
    "subscribe_quotes",
    "subscribe_ticks",
    "unsubscribe",
]


class MetaTraderClient:
    """Encapsulates the MetaTrader 5 terminal connection, SDK module, and session state."""

    def __init__(
        self,
        config: MetaTraderConfig | None = None,
        mt5_module: Any = None,
    ) -> None:
        """Initialize a MetaTrader 5 client instance.

        Args:
            config: Optional MetaTraderConfig settings.
            mt5_module: Optional injected MetaTrader5 module or mock.
        """
        self.config = config or MetaTraderConfig()
        self.mt5 = mt5_module if mt5_module is not None else mt5
        self.state: dict[str, Any] = {
            "connected": False,
            "login": None,
            "server": None,
            "terminal_path": None,
            "last_error": (0, "Success"),
        }
        self.subscriptions: dict[str, dict[str, Any]] = {}

    def is_available(self) -> bool:
        """Check if the MetaTrader 5 package is available."""
        return self.mt5 is not None

    def is_connected(self) -> bool:
        """Check if the terminal is connected."""
        return _terminal_info.is_connected(client=self)

    def connect(
        self,
        path: str | None = None,
        login: int | str | None = None,
        password: str | None = None,
        server: str | None = None,
        timeout: int = 30,
        portable: bool = False,
    ) -> dict[str, Any]:
        """Connect to MT5 terminal."""
        return _terminal_info.connect(
            path=path,
            login=login,
            password=password,
            server=server,
            timeout=timeout,
            portable=portable,
            config=self.config,
            client=self,
        )

    def disconnect(self) -> bool:
        """Disconnect from MT5 terminal."""
        return _terminal_info.disconnect(client=self)

    def ping(self) -> float:
        """Retrieve ping in milliseconds."""
        return _terminal_info.ping(client=self)

    def get_connection_status(self) -> dict[str, Any]:
        """Get connection status dictionary."""
        return _terminal_info.get_connection_status(client=self)

    def get_platform_info(self) -> dict[str, Any]:
        """Get platform info dictionary."""
        return _terminal_info.get_platform_info(client=self)

    def get_terminal_info(self) -> dict[str, Any]:
        """Get terminal info dictionary."""
        return _terminal_info.get_terminal_info(client=self)

    def get_last_error(self) -> tuple[int, str]:
        """Get last error tuple."""
        return _terminal_info.get_last_error(client=self)

    def get_account_info(self) -> dict[str, Any]:
        """Retrieve account info dictionary."""
        return _account_info.get_account_info(client=self)

    def get_balances(self) -> dict[str, Any]:
        """Retrieve balances dictionary."""
        return _account_info.get_balances(client=self)

    def get_permissions(self) -> list[str]:
        """Retrieve permissions list."""
        return _account_info.get_permissions(client=self)

    def get_account_snapshot(self) -> dict[str, Any]:
        """Retrieve account snapshot."""
        return _account_info.get_account_snapshot(client=self)

    def get_symbols(self) -> list[str]:
        """Retrieve available symbol tickers."""
        return _symbol_info.get_symbols(client=self)

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Retrieve symbol metadata."""
        return _symbol_info.get_symbol_info(symbol, client=self)

    def select_symbol(self, symbol: str, selected: bool = True) -> bool:
        """Select or deselect symbol in Market Watch."""
        return _symbol_info.select_symbol(symbol, selected=selected, client=self)

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Retrieve live quote for symbol."""
        return _symbol_info.get_quote(symbol, client=self)

    def get_spread(self, symbol: str) -> float:
        """Retrieve spread for symbol."""
        return _symbol_info.get_spread(symbol, client=self)

    def get_ticks(self, symbol: str, count: int = 100) -> list[dict[str, Any]]:
        """Retrieve tick records."""
        return _symbol_info.get_ticks(symbol, count=count, client=self)

    def get_historical_bars(
        self,
        symbol: str,
        timeframe: str = "1m",
        start: Any = None,
        end: Any = None,
        count: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve historical OHLCV bars."""
        return _symbol_info.get_historical_bars(
            symbol, timeframe=timeframe, start=start, end=end, count=count, client=self
        )

    def subscribe_quotes(self, symbols: list[str]) -> str:
        """Subscribe to quote streaming."""
        return _symbol_info.subscribe_quotes(symbols, client=self)

    def subscribe_ticks(self, symbols: list[str]) -> str:
        """Subscribe to tick streaming."""
        return _symbol_info.subscribe_ticks(symbols, client=self)

    def subscribe_bars(self, symbols: list[str], timeframe: str) -> str:
        """Subscribe to bar streaming."""
        return _symbol_info.subscribe_bars(symbols, timeframe=timeframe, client=self)

    def unsubscribe(self, sub_id: str) -> bool:
        """Unsubscribe from streaming handle."""
        return _symbol_info.unsubscribe(sub_id, client=self)

    def list_subscriptions(self) -> list[dict[str, Any]]:
        """List active streaming subscriptions."""
        return _symbol_info.list_subscriptions(client=self)

    def get_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Retrieve active orders."""
        return _order_info.get_orders(symbol=symbol, client=self)

    def get_order(self, order_id: int | str) -> dict[str, Any] | None:
        """Retrieve order by ID."""
        return _order_info.get_order(order_id, client=self)

    def check_order(self, request: dict[str, Any]) -> dict[str, Any]:
        """Perform pre-trade check on order."""
        return _order_info.check_order(request, client=self)

    def list_order_history(
        self,
        symbol: str | None = None,
        start: Any = None,
        end: Any = None,
    ) -> list[dict[str, Any]]:
        """Retrieve historical orders."""
        return _history_order_info.list_order_history(
            symbol=symbol, start=start, end=end, client=self
        )

    def get_history_order(self, order_id: int | str) -> dict[str, Any] | None:
        """Retrieve historical order by ID."""
        return _history_order_info.get_history_order(order_id, client=self)

    def get_deals(self, deal_id: int | str | None = None) -> list[dict[str, Any]]:
        """Retrieve executed deals."""
        return _deals_info.get_deals(deal_id=deal_id, client=self)

    def list_deal_history(
        self,
        symbol: str | None = None,
        start: Any = None,
        end: Any = None,
    ) -> list[dict[str, Any]]:
        """Retrieve deal history records."""
        return _deals_info.list_deal_history(
            symbol=symbol, start=start, end=end, client=self
        )

    def list_account_transactions(
        self, start: Any = None, end: Any = None
    ) -> list[dict[str, Any]]:
        """Retrieve account transaction records."""
        return _deals_info.list_account_transactions(start=start, end=end, client=self)

    def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Retrieve open positions."""
        return _positions_info.get_positions(symbol=symbol, client=self)

    def get_position(self, position_id: int | str) -> dict[str, Any] | None:
        """Retrieve open position by ID."""
        return _positions_info.get_position(position_id, client=self)

    def place_order(self, request: dict[str, Any]) -> dict[str, Any]:
        """Place order via MT5."""
        return _trade.place_order(request, client=self)

    def modify_order(self, request: dict[str, Any]) -> dict[str, Any]:
        """Modify order via MT5."""
        return _trade.modify_order(request, client=self)

    def cancel_order(
        self, order_id: int | str, client_request_id: str | None = None
    ) -> dict[str, Any]:
        """Cancel order via MT5."""
        return _trade.cancel_order(
            order_id, client_request_id=client_request_id, client=self
        )

    def modify_position(self, request: dict[str, Any]) -> dict[str, Any]:
        """Modify position via MT5."""
        return _trade.modify_position(request, client=self)

    def close_position(
        self, position_id: int | str, volume: float | None = None
    ) -> dict[str, Any]:
        """Close position via MT5."""
        return _trade.close_position(position_id, volume=volume, client=self)

    def calculate_margin(self, request: dict[str, Any]) -> float:
        """Calculate margin for order."""
        return _trade.calculate_margin(request, client=self)

    def calculate_profit(self, request: dict[str, Any]) -> float:
        """Calculate profit for order."""
        return _trade.calculate_profit(request, client=self)


_client_registry: dict[str, MetaTraderClient] = {}


def get_default_client() -> MetaTraderClient:
    """Retrieve the global default MetaTraderClient instance."""
    if "default" not in _client_registry:
        _client_registry["default"] = MetaTraderClient()
    return _client_registry["default"]


def set_default_client(new_client: MetaTraderClient) -> None:
    """Set the global default MetaTraderClient instance."""
    _client_registry["default"] = new_client


# Module-level convenience functions delegating to the client instance
def connect(
    path: str | None = None,
    login: int | str | None = None,
    password: str | None = None,
    server: str | None = None,
    timeout: int = 30,
    portable: bool = False,
    config: MetaTraderConfig | None = None,
    client: MetaTraderClient | None = None,
) -> dict[str, Any]:
    """Connect to MT5."""
    target_client = client or get_default_client()
    if config:
        target_client.config = config
    return target_client.connect(
        path=path,
        login=login,
        password=password,
        server=server,
        timeout=timeout,
        portable=portable,
    )


def disconnect(client: MetaTraderClient | None = None) -> bool:
    """Disconnect from MT5."""
    return (client or get_default_client()).disconnect()


def is_connected(client: MetaTraderClient | None = None) -> bool:
    """Check connection."""
    return (client or get_default_client()).is_connected()


def get_last_error(client: MetaTraderClient | None = None) -> tuple[int, str]:
    """Retrieve last error."""
    return (client or get_default_client()).get_last_error()


def get_account_info(
    client: MetaTraderClient | None = None,
) -> dict[str, Any]:
    """Retrieve account info."""
    return (client or get_default_client()).get_account_info()


def get_symbols(client: MetaTraderClient | None = None) -> list[str]:
    """Retrieve symbols."""
    return (client or get_default_client()).get_symbols()


def get_symbol_info(
    symbol: str, client: MetaTraderClient | None = None
) -> dict[str, Any]:
    """Retrieve symbol metadata."""
    return (client or get_default_client()).get_symbol_info(symbol)


def get_quote(symbol: str, client: MetaTraderClient | None = None) -> dict[str, Any]:
    """Retrieve quote."""
    return (client or get_default_client()).get_quote(symbol)


def get_orders(
    symbol: str | None = None, client: MetaTraderClient | None = None
) -> list[dict[str, Any]]:
    """Retrieve active orders."""
    return (client or get_default_client()).get_orders(symbol)


def get_order(
    order_id: int | str, client: MetaTraderClient | None = None
) -> dict[str, Any] | None:
    """Retrieve order."""
    return (client or get_default_client()).get_order(order_id)


def get_positions(
    symbol: str | None = None, client: MetaTraderClient | None = None
) -> list[dict[str, Any]]:
    """Retrieve positions."""
    return (client or get_default_client()).get_positions(symbol)


def get_position(
    position_id: int | str, client: MetaTraderClient | None = None
) -> dict[str, Any] | None:
    """Retrieve position."""
    return (client or get_default_client()).get_position(position_id)


def get_deals(
    deal_id: int | str | None = None, client: MetaTraderClient | None = None
) -> list[dict[str, Any]]:
    """Retrieve deals."""
    return (client or get_default_client()).get_deals(deal_id)


def get_history_order(
    order_id: int | str, client: MetaTraderClient | None = None
) -> dict[str, Any] | None:
    """Retrieve history order."""
    return (client or get_default_client()).get_history_order(order_id)


def list_order_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
    client: MetaTraderClient | None = None,
) -> list[dict[str, Any]]:
    """Retrieve historical orders."""
    return (client or get_default_client()).list_order_history(
        symbol=symbol, start=start, end=end
    )


def list_deal_history(
    symbol: str | None = None,
    start: Any = None,
    end: Any = None,
    client: MetaTraderClient | None = None,
) -> list[dict[str, Any]]:
    """Retrieve deal history records."""
    return (client or get_default_client()).list_deal_history(
        symbol=symbol, start=start, end=end
    )


def list_account_transactions(
    start: Any = None,
    end: Any = None,
    client: MetaTraderClient | None = None,
) -> list[dict[str, Any]]:
    """Retrieve account transaction records."""
    return (client or get_default_client()).list_account_transactions(
        start=start, end=end
    )


def place_order(
    request: dict[str, Any], client: MetaTraderClient | None = None
) -> dict[str, Any]:
    """Place order."""
    return (client or get_default_client()).place_order(request)


def fr_brk_metatrader(
    config: MetaTraderConfig | None = None,
    client: MetaTraderClient | None = None,
) -> dict[str, Any]:
    """Execute FR-BRK-METATRADER status report.

    Args:
        config: Optional configuration instance.
        client: Optional MetaTraderClient instance.

    Returns:
        Dictionary summarizing connection and account state.
    """
    target = client or get_default_client()
    if config:
        target.config = config
    return {
        "platform": "mt5",
        "mt5_package_available": target.is_available(),
        "connected": target.is_connected(),
        "account": target.get_account_info() if target.is_connected() else {},
        "symbols": len(target.get_symbols()) if target.is_connected() else 0,
    }


class MetaTraderService(BrokerOperationsCapability):
    """Service class implementing BrokerOperationsCapability for live MetaTrader 5."""

    def __init__(
        self,
        config: MetaTraderConfig | None = None,
        client: MetaTraderClient | None = None,
    ) -> None:
        """Initialize MetaTrader 5 service."""
        self.config = config or MetaTraderConfig()
        self.client = client or MetaTraderClient(config=self.config)

    def connect(
        self,
        account_id: str | int | None = None,
        server: str | None = None,
        password: str | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """Connect to MT5."""
        return self.client.connect(
            login=account_id,
            server=server,
            password=password,
            timeout=timeout,
        )

    def disconnect(self) -> bool:
        """Disconnect from MT5."""
        return self.client.disconnect()

    def is_connected(self) -> bool:
        """Check connection."""
        return self.client.is_connected()

    def get_account_info(self) -> dict[str, Any]:
        """Get account info."""
        return self.client.get_account_info()

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        """Get symbol metadata."""
        return self.client.get_symbol_info(symbol)

    def get_quote(self, symbol: str) -> dict[str, Any]:
        """Get quote."""
        return self.client.get_quote(symbol)

    def get_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get orders."""
        return self.client.get_orders(symbol)

    def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """Get positions."""
        return self.client.get_positions(symbol)

    def place_order(self, request: dict[str, Any]) -> dict[str, Any]:
        """Place order."""
        return self.client.place_order(request)


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
