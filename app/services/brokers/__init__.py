# ruff: noqa: F822 -- lazy exports via PEP 562 __getattr__
"""Broker backends, providers, and unified registry.

Description:
    Exposes modern TradingBackend implementations:
    - MT5Backend (pilot MetaTrader 5 EA bridge)
    - CTraderBackend (cTrader Open API Protobuf/TLS)
    - SimulationBackend (deterministic in-memory trading engine)
    And market data broker providers:
    - YahooBroker (Yahoo Finance v8 chart / v7 quote)
    - DukascopyBroker (Dukascopy CDN & datafeed)
    - DarwinexBroker (Darwinex CDN ticks & bars)
    - BinanceBroker (Binance REST Spot & Futures)
    - SQEquityBroker (StrategyQuant US Equities)
    - SQFuturesBroker (StrategyQuant Continuous Futures)
    - FilesBroker (Local CSV / Parquet data archives)
    - TickDownloaderBroker (Tick data downloader)
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.base import BaseBrokerBackend
    from app.services.brokers.contracts import SymbolSpec
    from app.services.brokers.crypto import BinanceBroker
    from app.services.brokers.ctrader import CTraderBackend
    from app.services.brokers.darwinex import DarwinexBroker
    from app.services.brokers.dukascopy import DukascopyBroker
    from app.services.brokers.files import FilesBroker
    from app.services.brokers.metatrader import MT5Backend
    from app.services.brokers.simulator import SimulationBackend
    from app.services.brokers.sq_equity import SQEquityBroker
    from app.services.brokers.sq_futures import SQFuturesBroker
    from app.services.brokers.tick_downloader import TickDownloaderBroker
    from app.services.brokers.yahoo import YahooBroker
    from app.services.data import (
        BridgeError,
        DataBrokerBackend,
        MarketBar,
        MarketTick,
        Timeframe,
    )
    from app.services.trading import (
        AccountSnapshot,
        BridgeEvent,
        DealSnapshot,
        HistoryOrderSnapshot,
        OrderSnapshot,
        PositionSnapshot,
        Receipt,
        ReceiptStatus,
        SymbolSnapshot,
        TerminalSnapshot,
        TradeAction,
        TradeCheckResult,
        TradeRequest,
        TradeResult,
        TradingBackend,
    )

_SINGLETONS: dict[str, Any] = {}

_MODULE_MAPPING: dict[str, tuple[str, str]] = {
    "BaseBrokerBackend": ("app.services.brokers.base", "BaseBrokerBackend"),
    "BridgeError": ("app.services.brokers.base", "BridgeError"),
    "DataBrokerBackend": ("app.services.data", "DataBrokerBackend"),
    "BinanceBroker": ("app.services.brokers.crypto", "BinanceBroker"),
    "CTraderBackend": ("app.services.brokers.ctrader", "CTraderBackend"),
    "DarwinexBroker": ("app.services.brokers.darwinex", "DarwinexBroker"),
    "DukascopyBroker": ("app.services.brokers.dukascopy", "DukascopyBroker"),
    "FilesBroker": ("app.services.brokers.files", "FilesBroker"),
    "MT5Backend": ("app.services.brokers.metatrader", "MT5Backend"),
    "SimulationBackend": ("app.services.brokers.simulator", "SimulationBackend"),
    "SQEquityBroker": ("app.services.brokers.sq_equity", "SQEquityBroker"),
    "SQFuturesBroker": ("app.services.brokers.sq_futures", "SQFuturesBroker"),
    "TickDownloaderBroker": (
        "app.services.brokers.tick_downloader",
        "TickDownloaderBroker",
    ),
    "YahooBroker": ("app.services.brokers.yahoo", "YahooBroker"),
    "SymbolSpec": ("app.services.brokers.contracts", "SymbolSpec"),
    "MarketBar": ("app.services.data", "MarketBar"),
    "MarketTick": ("app.services.data", "MarketTick"),
    "Timeframe": ("app.services.data", "Timeframe"),
    "AccountSnapshot": ("app.services.trading", "AccountSnapshot"),
    "BridgeEvent": ("app.services.trading", "BridgeEvent"),
    "DealSnapshot": ("app.services.trading", "DealSnapshot"),
    "HistoryOrderSnapshot": ("app.services.trading", "HistoryOrderSnapshot"),
    "OrderSnapshot": ("app.services.trading", "OrderSnapshot"),
    "PositionSnapshot": ("app.services.trading", "PositionSnapshot"),
    "Receipt": ("app.services.trading", "Receipt"),
    "ReceiptStatus": ("app.services.trading", "ReceiptStatus"),
    "SymbolSnapshot": ("app.services.trading", "SymbolSnapshot"),
    "TerminalSnapshot": ("app.services.trading", "TerminalSnapshot"),
    "TradeAction": ("app.services.trading", "TradeAction"),
    "TradeCheckResult": ("app.services.trading", "TradeCheckResult"),
    "TradeRequest": ("app.services.trading", "TradeRequest"),
    "TradeResult": ("app.services.trading", "TradeResult"),
    "TradingBackend": ("app.services.trading", "TradingBackend"),
}

_SINGLETON_FACTORIES: dict[str, tuple[str, str]] = {
    "yahoo": ("app.services.brokers.yahoo", "YahooBroker"),
    "dukascopy": ("app.services.brokers.dukascopy", "DukascopyBroker"),
    "darwinex": ("app.services.brokers.darwinex", "DarwinexBroker"),
    "sq_equity": ("app.services.brokers.sq_equity", "SQEquityBroker"),
    "sq_futures": ("app.services.brokers.sq_futures", "SQFuturesBroker"),
    "binance": ("app.services.brokers.crypto", "BinanceBroker"),
    "files": ("app.services.brokers.files", "FilesBroker"),
    "tick_downloader": ("app.services.brokers.tick_downloader", "TickDownloaderBroker"),
}

_ALIASES: dict[str, str] = {
    "yahoo": "yahoo",
    "dukascopy": "dukascopy",
    "darwinex": "darwinex",
    "sq_equity": "sq_equity",
    "equity": "sq_equity",
    "sq_futures": "sq_futures",
    "futures": "sq_futures",
    "binance": "binance",
    "crypto": "binance",
    "files": "files",
    "file": "files",
    "tick_downloader": "tick_downloader",
}


def get_broker(name: str) -> Any:
    """Resolve a data broker singleton by name or alias."""
    key = name.lower().strip()
    target = _ALIASES.get(key)
    if target is None:
        raise KeyError(f"Unknown broker: {name}")
    if target not in _SINGLETONS:
        mod_path, cls_name = _SINGLETON_FACTORIES[target]
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        _SINGLETONS[target] = cls()
    return _SINGLETONS[target]


def __getattr__(name: str) -> Any:
    """Lazily import broker classes and singletons on demand."""
    if name in _SINGLETON_FACTORIES:
        return get_broker(name)
    if name in _MODULE_MAPPING:
        mod_path, attr_name = _MODULE_MAPPING[name]
        mod = importlib.import_module(mod_path)
        return getattr(mod, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AccountSnapshot",
    "BaseBrokerBackend",
    "BinanceBroker",
    "BridgeError",
    "BridgeEvent",
    "CTraderBackend",
    "DarwinexBroker",
    "DataBrokerBackend",
    "DealSnapshot",
    "DukascopyBroker",
    "FilesBroker",
    "HistoryOrderSnapshot",
    "MT5Backend",
    "MarketBar",
    "MarketTick",
    "OrderSnapshot",
    "PositionSnapshot",
    "Receipt",
    "ReceiptStatus",
    "SQEquityBroker",
    "SQFuturesBroker",
    "SimulationBackend",
    "SymbolSnapshot",
    "SymbolSpec",
    "TerminalSnapshot",
    "TickDownloaderBroker",
    "Timeframe",
    "TradeAction",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
    "TradingBackend",
    "YahooBroker",
    "binance",
    "darwinex",
    "dukascopy",
    "files",
    "get_broker",
    "sq_equity",
    "sq_futures",
    "tick_downloader",
    "yahoo",
]
