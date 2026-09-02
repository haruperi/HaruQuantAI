"""FR 9 Bridge: Dukascopy Provider Client and Primary Service Module."""

from __future__ import annotations

from typing import Any

from app.contracts.broker.ports import BrokerOperationsCapability
from app.services.brokers.dukascopy._account_info import (
    get_account_info,
    get_account_snapshot,
    get_balances,
    get_permissions,
)
from app.services.brokers.dukascopy._deals_info import (
    get_deals,
    list_account_transactions,
    list_deal_history,
)
from app.services.brokers.dukascopy._history_order_info import (
    get_history_order,
    list_order_history,
)
from app.services.brokers.dukascopy._order_info import (
    check_order,
    get_order,
    get_orders,
)
from app.services.brokers.dukascopy._positions_info import (
    get_position,
    get_positions,
)
from app.services.brokers.dukascopy._symbol_info import (
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
from app.services.brokers.dukascopy._terminal_info import (
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
from app.services.brokers.dukascopy._trade import (
    calculate_margin,
    calculate_profit,
    cancel_order,
    close_position,
    modify_order,
    modify_position,
    place_order,
)
from app.services.brokers.dukascopy.config import DukascopyConfig

__all__ = [
    "calculate_margin",
    "calculate_profit",
    "cancel_order",
    "check_order",
    "close_position",
    "connect",
    "disconnect",
    "fr_brk_dukascopy",
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


def fr_brk_dukascopy(
    config: DukascopyConfig | None = None,  # noqa: ARG001
) -> dict[str, Any]:
    """Execute FR-BRK-DUKASCOPY status report."""
    return {
        "platform": "dukascopy",
        "connected": is_connected(),
        "symbols": len(get_symbols()),
    }


class DukascopyService(BrokerOperationsCapability):
    """Service implementing BrokerOperationsCapability for Dukascopy."""

    def __init__(self, config: DukascopyConfig | None = None) -> None:
        self.config = config or DukascopyConfig()

    def connect(
        self,
        account_id: str | int | None = None,
        server: str | None = None,
        password: str | None = None,
        timeout: int = 30,
    ) -> dict[str, Any]:
        return connect(
            username=str(account_id) if account_id else None,
            password=password,
            timeout=timeout,
            config=self.config,
        )

    def disconnect(self) -> bool:
        return disconnect()

    def is_connected(self) -> bool:
        return is_connected()

    def get_account_info(self) -> dict[str, Any]:
        return get_account_info()

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        return get_symbol_info(symbol)

    def get_quote(self, symbol: str) -> dict[str, Any]:
        return get_quote(symbol)

    def get_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        return get_orders(symbol)

    def get_positions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        return get_positions(symbol)

    def place_order(self, request: dict[str, Any]) -> dict[str, Any]:
        return place_order(request)


def _run_usage_example() -> None:
    print("=== Dukascopy Client Demonstration ===")
    print("Platform:", get_platform_info())
    print("Symbols Available:", get_symbols())


if __name__ == "__main__":
    _run_usage_example()
