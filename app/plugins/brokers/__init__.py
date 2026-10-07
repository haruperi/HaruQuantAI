"""Broker plugin registry, discovery, lifecycle routing, and unified functional facade.

Description:
    Serves as the centralized registry, dynamic discovery coordinator, and
    functional facade for all quantitative execution and market data brokers.
    Instead of coupling consumer components (such as backtesting pipelines, live
    trading executors, or CLI tools) directly to vendor-specific adapter classes,
    this module exposes a uniform operational surface. Callers can either invoke
    top-level router functions (e.g. `get_bars(broker=..., ...)`) or resolve
    pre-instantiated singletons (`mt5`, `yahoo`, `ctrader`, `dukascopy`,
    `darwinex`, `sq_equity`, `sq_futures`). Internally, the registry maintains
    a case-insensitive map of named broker instances, automatically validating
    capability bitmasks and returning canonical `StandardResponse` results.

Purpose:
    FEAT-BROKER-FACADE: Centralized Broker Registry and Unified Facade Routing.
    Provides decoupled access, dynamic lookup, and operational routing across
    all registered broker adapter plugins.

Key Capabilities:
    - FR-BROKER-REGISTRY-MANAGEMENT: Broker Registration & Case-Insensitive Lookup
      Associated: `[register_broker()]`, `[get_broker()]`, `[list_brokers()]`
      Logging: Emits INFO log upon broker registration and DEBUG log on lookup.
    - FR-BROKER-FACADE-ROUTING: Unified Operation Dispatch
      Associated: `[connect()]`, `[disconnect()]`, `[get_symbol_info()]`,
      `[get_bars()]`, `[trade()]`, `[check_order()]`
      Logging: Emits structured telemetry via delegated broker response
      envelopes for all routed operations.
    - FR-BROKER-INSTANCE-RESOLUTION: Polymorphic Broker Argument Resolution
      Associated: `[resolve_broker()]`
      Logging: Emits DEBUG log when resolving string identifiers or instances.

Python API Usage:
    ```python
    from app.plugins.brokers import (
        TimeFrame,
        get_bars,
        mt5,
        yahoo,
    )

    # Route operation via singleton instance
    resp = get_bars(broker=mt5, symbol="EURUSD", timeframe=TimeFrame.H1, count=5)
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
    ```
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.host.logging import get_logger
from app.plugins.brokers.contracts import (
    AccountInfo,
    Bar,
    BaseBroker,
    BookItem,
    BrokerCapability,
    DealInfo,
    OrderAction,
    OrderCheckResult,
    OrderFilling,
    OrderInfo,
    OrderTime,
    OrderType,
    PositionInfo,
    StandardError,
    StandardResponse,
    SymbolInfo,
    TerminalInfo,
    Tick,
    TimeFrame,
    TradeRequest,
    TradeResult,
)
from app.plugins.brokers.crypto.adapter import BinanceBroker
from app.plugins.brokers.ctrader.adapter import CTraderBroker
from app.plugins.brokers.darwinex.adapter import DarwinexBroker
from app.plugins.brokers.dukascopy.adapter import DukascopyBroker
from app.plugins.brokers.files.adapter import FilesBroker
from app.plugins.brokers.metatrader.adapter import MetaTraderBroker
from app.plugins.brokers.sq_equity.adapter import SQEquityBroker
from app.plugins.brokers.sq_futures.adapter import SQFuturesBroker
from app.plugins.brokers.yahoo.adapter import YahooBroker

logger = get_logger(__name__)

# ============================================================================
# Registry & Pre-instantiated Broker Singletons
# ============================================================================

_REGISTRY: dict[str, BaseBroker] = {}

mt5 = MetaTraderBroker()
yahoo = YahooBroker()
ctrader = CTraderBroker()
dukascopy = DukascopyBroker()
darwinex = DarwinexBroker()
sq_equity = SQEquityBroker()
sq_futures = SQFuturesBroker()
binance = BinanceBroker()
files = FilesBroker()

_REGISTRY["mt5"] = mt5
_REGISTRY["metatrader"] = mt5
_REGISTRY["metatrader5"] = mt5
_REGISTRY["yahoo"] = yahoo
_REGISTRY["ctrader"] = ctrader
_REGISTRY["dukascopy"] = dukascopy
_REGISTRY["darwinex"] = darwinex
_REGISTRY["sq_equity"] = sq_equity
_REGISTRY["equity"] = sq_equity
_REGISTRY["sq_futures"] = sq_futures
_REGISTRY["futures"] = sq_futures
_REGISTRY["binance"] = binance
_REGISTRY["crypto"] = binance
_REGISTRY["files"] = files
_REGISTRY["file"] = files


def register_broker(alias: str, broker_instance: BaseBroker) -> None:
    """Register a broker instance under an alias string.

    Args:
        alias: Unique string identifier (e.g. 'mt5', 'dukascopy').
        broker_instance: Concrete subclass instance of BaseBroker.
    """
    key = alias.lower().strip()
    _REGISTRY[key] = broker_instance
    logger.info(
        "FR-BROKER-REGISTRY-MANAGEMENT: Registered broker plugin '%s' -> %s",
        key,
        broker_instance.name,
    )


def get_broker(alias: str) -> BaseBroker:
    """Retrieve registered broker instance by alias.

    Args:
        alias: String key of registered broker.

    Returns:
        BaseBroker instance.

    Raises:
        KeyError: If alias is not registered.
    """
    key = alias.lower().strip()
    if key not in _REGISTRY:
        raise KeyError(
            f"Broker '{alias}' is not registered. Available: {list(_REGISTRY.keys())}"
        )
    return _REGISTRY[key]


def list_brokers() -> list[str]:
    """List unique registered broker identifiers."""
    return list(_REGISTRY.keys())


def resolve_broker(broker: BaseBroker | str | None) -> BaseBroker:
    """Resolve a broker argument into an active BaseBroker instance.

    Args:
        broker: Broker instance or string alias. Defaults to mt5 if None.

    Returns:
        BaseBroker instance.
    """
    if broker is None:
        return _REGISTRY.get("mt5", mt5)
    if isinstance(broker, BaseBroker):
        return broker
    if isinstance(broker, str):
        return get_broker(broker)
    raise TypeError(
        f"Invalid broker parameter: expected BaseBroker or str, got {type(broker).__name__}"
    )


# ============================================================================
# Standard Neutral Broker Functions
# ============================================================================


def connect(broker: BaseBroker | str = "mt5", **kwargs: Any) -> StandardResponse[bool]:
    """Connect to broker terminal/API."""
    return resolve_broker(broker).connect(**kwargs)


def disconnect(broker: BaseBroker | str = "mt5") -> StandardResponse[bool]:
    """Disconnect from broker terminal/API."""
    return resolve_broker(broker).disconnect()


def is_connected(broker: BaseBroker | str = "mt5") -> StandardResponse[bool]:
    """Check if broker connection is alive."""
    return resolve_broker(broker).is_connected()


def get_last_error(broker: BaseBroker | str = "mt5") -> StandardResponse[Any]:
    """Retrieve last error from broker API."""
    return resolve_broker(broker).get_last_error()


def get_terminal_info(
    broker: BaseBroker | str = "mt5",
) -> StandardResponse[TerminalInfo]:
    """Retrieve terminal properties and version."""
    return resolve_broker(broker).get_terminal_info()


def get_account_info(broker: BaseBroker | str = "mt5") -> StandardResponse[AccountInfo]:
    """Retrieve trading account status and metrics."""
    return resolve_broker(broker).get_account_info()


def get_symbol_info(
    broker: BaseBroker | str = "mt5", symbol: str = ""
) -> StandardResponse[SymbolInfo]:
    """Retrieve specifications for a given symbol."""
    return resolve_broker(broker).get_symbol_info(symbol=symbol)


def get_num_of_symbols(broker: BaseBroker | str = "mt5") -> StandardResponse[int]:
    """Get the total count of symbols available."""
    return resolve_broker(broker).get_num_of_symbols()


def get_symbols(
    broker: BaseBroker | str = "mt5", group: str | None = None
) -> StandardResponse[list[SymbolInfo]]:
    """Retrieve list of symbols, optionally matching group pattern."""
    return resolve_broker(broker).get_symbols(group=group)


def enable_symbol(
    broker: BaseBroker | str = "mt5",
    symbol: str = "",
    enable: bool = True,
) -> StandardResponse[bool]:
    """Select or deselect a symbol in Market Watch."""
    return resolve_broker(broker).enable_symbol(symbol=symbol, enable=enable)


def get_symbol_tick(
    broker: BaseBroker | str = "mt5", symbol: str = ""
) -> StandardResponse[Tick]:
    """Retrieve latest real-time tick for a symbol."""
    return resolve_broker(broker).get_symbol_tick(symbol=symbol)


def subscribe_market_depth(
    broker: BaseBroker | str = "mt5", symbol: str = ""
) -> StandardResponse[bool]:
    """Subscribe to Depth of Market (DOM) book for a symbol."""
    return resolve_broker(broker).subscribe_market_depth(symbol=symbol)


def get_market_depth(
    broker: BaseBroker | str = "mt5", symbol: str = ""
) -> StandardResponse[list[BookItem]]:
    """Get current Depth of Market (DOM) order book entries."""
    return resolve_broker(broker).get_market_depth(symbol=symbol)


def unsubscribe_market_depth(
    broker: BaseBroker | str = "mt5", symbol: str = ""
) -> StandardResponse[bool]:
    """Unsubscribe from Depth of Market (DOM) book."""
    return resolve_broker(broker).unsubscribe_market_depth(symbol=symbol)


def get_bars(
    broker: BaseBroker | str = "mt5",
    symbol: str = "",
    timeframe: TimeFrame | str | int = TimeFrame.H1,
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    start_pos: int | None = 0,
) -> StandardResponse[list[Bar]]:
    """Retrieve historical candlestick bars."""
    return resolve_broker(broker).get_bars(
        symbol=symbol,
        timeframe=timeframe,
        count=count,
        date_from=date_from,
        date_to=date_to,
        start_pos=start_pos,
    )


def get_ticks(
    broker: BaseBroker | str = "mt5",
    symbol: str = "",
    count: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    flags: int | None = None,
) -> StandardResponse[list[Tick]]:
    """Retrieve historical tick data."""
    return resolve_broker(broker).get_ticks(
        symbol=symbol,
        count=count,
        date_from=date_from,
        date_to=date_to,
        flags=flags,
    )


def get_position_info(
    broker: BaseBroker | str = "mt5",
    symbol: str | None = None,
    ticket: int | None = None,
) -> StandardResponse[list[PositionInfo]]:
    """Retrieve active open positions."""
    return resolve_broker(broker).get_position_info(symbol=symbol, ticket=ticket)


def get_num_positions(broker: BaseBroker | str = "mt5") -> StandardResponse[int]:
    """Get the total count of currently open positions."""
    return resolve_broker(broker).get_num_positions()


def get_order_info(
    broker: BaseBroker | str = "mt5",
    symbol: str | None = None,
    ticket: int | None = None,
    group: str | None = None,
) -> StandardResponse[list[OrderInfo]]:
    """Retrieve active pending orders."""
    return resolve_broker(broker).get_order_info(
        symbol=symbol, ticket=ticket, group=group
    )


def get_num_orders(broker: BaseBroker | str = "mt5") -> StandardResponse[int]:
    """Get the total count of active pending orders."""
    return resolve_broker(broker).get_num_orders()


def get_history_order_info(
    broker: BaseBroker | str = "mt5",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    ticket: int | None = None,
    position: int | None = None,
    group: str | None = None,
) -> StandardResponse[list[OrderInfo]]:
    """Retrieve historical orders."""
    return resolve_broker(broker).get_history_order_info(
        date_from=date_from,
        date_to=date_to,
        ticket=ticket,
        position=position,
        group=group,
    )


def get_num_history_orders(
    broker: BaseBroker | str = "mt5",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> StandardResponse[int]:
    """Get the total count of historical orders within time range."""
    return resolve_broker(broker).get_num_history_orders(
        date_from=date_from, date_to=date_to
    )


def get_history_deal_info(
    broker: BaseBroker | str = "mt5",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    ticket: int | None = None,
    position: int | None = None,
    group: str | None = None,
) -> StandardResponse[list[DealInfo]]:
    """Retrieve historical deals."""
    return resolve_broker(broker).get_history_deal_info(
        date_from=date_from,
        date_to=date_to,
        ticket=ticket,
        position=position,
        group=group,
    )


def get_num_history_deals(
    broker: BaseBroker | str = "mt5",
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> StandardResponse[int]:
    """Get the total count of historical deals within time range."""
    return resolve_broker(broker).get_num_history_deals(
        date_from=date_from, date_to=date_to
    )


def calculate_margin(
    broker: BaseBroker | str = "mt5",
    action: OrderType | str | int = OrderType.BUY,
    symbol: str = "",
    volume: float = 0.01,
    price: float = 0.0,
) -> StandardResponse[float]:
    """Calculate margin required for order."""
    return resolve_broker(broker).calculate_margin(
        action=action, symbol=symbol, volume=volume, price=price
    )


def calculate_profit(
    broker: BaseBroker | str = "mt5",
    action: OrderType | str | int = OrderType.BUY,
    symbol: str = "",
    volume: float = 0.01,
    price_open: float = 0.0,
    price_close: float = 0.0,
) -> StandardResponse[float]:
    """Calculate potential profit/loss."""
    return resolve_broker(broker).calculate_profit(
        action=action,
        symbol=symbol,
        volume=volume,
        price_open=price_open,
        price_close=price_close,
    )


def check_order(
    broker: BaseBroker | str = "mt5",
    request: TradeRequest | None = None,
) -> StandardResponse[OrderCheckResult]:
    """Perform pre-flight verification of a trade request."""
    req = request or TradeRequest()
    return resolve_broker(broker).check_order(req)


def trade(
    broker: BaseBroker | str = "mt5",
    request: TradeRequest | None = None,
) -> StandardResponse[TradeResult]:
    """Execute a trade order."""
    req = request or TradeRequest()
    return resolve_broker(broker).trade(req)


__all__ = [
    "AccountInfo",
    "Bar",
    "BaseBroker",
    "BinanceBroker",
    "BookItem",
    "BrokerCapability",
    "CTraderBroker",
    "DarwinexBroker",
    "DealInfo",
    "DukascopyBroker",
    "FilesBroker",
    "MetaTraderBroker",
    "OrderAction",
    "OrderCheckResult",
    "OrderFilling",
    "OrderInfo",
    "OrderTime",
    "OrderType",
    "PositionInfo",
    "SQEquityBroker",
    "SQFuturesBroker",
    "StandardError",
    "StandardResponse",
    "SymbolInfo",
    "TerminalInfo",
    "Tick",
    "TimeFrame",
    "TradeRequest",
    "TradeResult",
    "YahooBroker",
    "binance",
    "calculate_margin",
    "calculate_profit",
    "check_order",
    "connect",
    "ctrader",
    "darwinex",
    "disconnect",
    "dukascopy",
    "enable_symbol",
    "files",
    "get_account_info",
    "get_bars",
    "get_broker",
    "get_history_deal_info",
    "get_history_order_info",
    "get_last_error",
    "get_market_depth",
    "get_num_history_deals",
    "get_num_history_orders",
    "get_num_of_symbols",
    "get_num_orders",
    "get_num_positions",
    "get_order_info",
    "get_position_info",
    "get_symbol_info",
    "get_symbol_tick",
    "get_symbols",
    "get_terminal_info",
    "get_ticks",
    "is_connected",
    "list_brokers",
    "mt5",
    "register_broker",
    "resolve_broker",
    "sq_equity",
    "sq_futures",
    "subscribe_market_depth",
    "trade",
    "unsubscribe_market_depth",
    "yahoo",
]
