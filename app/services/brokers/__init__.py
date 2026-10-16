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
    - BinanceBroker / CryptoBroker (Binance REST Spot & Futures)
    - SQEquityBroker (StrategyQuant US Equities)
    - SQFuturesBroker (StrategyQuant Continuous Futures)
    - FilesBroker (Local CSV / Parquet / HST / FXT data archives)
    - TickDownloaderBroker (Tick data downloader)
    As well as unified registry and typed data capabilities:
    - BrokerRegistry, BrokerKey, HistoricalProviderView
    - ProviderCapabilities, HistoryRequest, HistoryPage, ProviderHealth
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.base import BaseBrokerBackend, BridgeError, BrokerBackend
    from app.services.brokers.capabilities import (
        CancellationToken,
        HistoryKind,
        HistoryPage,
        HistoryRequest,
        ProviderAuthError,
        ProviderCancelledError,
        ProviderCapabilities,
        ProviderDisabledError,
        ProviderError,
        ProviderHealth,
        ProviderNotFoundError,
        ProviderRateLimitError,
        ProviderTimeoutError,
        ProviderUnsupportedError,
        ProviderValidationError,
    )
    from app.services.brokers.crypto import BinanceBroker, CryptoBroker
    from app.services.brokers.ctrader import CTraderBackend
    from app.services.brokers.darwinex import DarwinexBroker
    from app.services.brokers.dukascopy import DukascopyBroker
    from app.services.brokers.files import FilesBroker
    from app.services.brokers.metatrader import MT5Backend
    from app.services.brokers.registry import (
        BrokerKey,
        BrokerRegistry,
        HistoricalProviderView,
        normalize_broker_name,
    )
    from app.services.brokers.simulator import SimulationBackend
    from app.services.brokers.sq_equity import SQEquityBroker
    from app.services.brokers.sq_futures import SQFuturesBroker
    from app.services.brokers.tick_downloader import TickDownloaderBroker
    from app.services.brokers.yahoo import YahooBroker
    from app.services.include.contracts import (
        AccountInfo,
        BridgeEvent,
        DealInfo,
        OrderInfo,
        PositionInfo,
        Receipt,
        SymbolInfo,
        TerminalInfo,
        TradeCheckResult,
        TradeRequest,
        TradeResult,
        TradingBackend,
    )
    from app.services.include.enums import (
        ReceiptStatus,
        TradeAction,
    )
    from app.workspace.data_manager import (
        MarketBar,
        MarketTick,
        Timeframe,
    )
    from app.workspace.data_manager.history import DataBrokerBackend

_SINGLETONS: dict[str, Any] = {}

_MODULE_MAPPING: dict[str, tuple[str, str]] = {
    "BaseBrokerBackend": ("app.services.brokers.base", "BaseBrokerBackend"),
    "BrokerBackend": ("app.services.brokers.base", "BrokerBackend"),
    "BridgeError": ("app.services.brokers.base", "BridgeError"),
    "DataBrokerBackend": ("app.workspace.data_manager.history", "DataBrokerBackend"),
    "BinanceBroker": ("app.services.brokers.crypto", "BinanceBroker"),
    "CryptoBroker": ("app.services.brokers.crypto", "CryptoBroker"),
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
    "BrokerRegistry": ("app.services.brokers.registry", "BrokerRegistry"),
    "BrokerKey": ("app.services.brokers.registry", "BrokerKey"),
    "HistoricalProviderView": (
        "app.services.brokers.registry",
        "HistoricalProviderView",
    ),
    "normalize_broker_name": (
        "app.services.brokers.registry",
        "normalize_broker_name",
    ),
    "CancellationToken": ("app.services.brokers.capabilities", "CancellationToken"),
    "HistoryKind": ("app.services.brokers.capabilities", "HistoryKind"),
    "HistoryPage": ("app.services.brokers.capabilities", "HistoryPage"),
    "HistoryRequest": ("app.services.brokers.capabilities", "HistoryRequest"),
    "ProviderAuthError": ("app.services.brokers.capabilities", "ProviderAuthError"),
    "ProviderCapabilities": (
        "app.services.brokers.capabilities",
        "ProviderCapabilities",
    ),
    "ProviderCancelledError": (
        "app.services.brokers.capabilities",
        "ProviderCancelledError",
    ),
    "ProviderDisabledError": (
        "app.services.brokers.capabilities",
        "ProviderDisabledError",
    ),
    "ProviderError": ("app.services.brokers.capabilities", "ProviderError"),
    "ProviderHealth": ("app.services.brokers.capabilities", "ProviderHealth"),
    "ProviderNotFoundError": (
        "app.services.brokers.capabilities",
        "ProviderNotFoundError",
    ),
    "ProviderRateLimitError": (
        "app.services.brokers.capabilities",
        "ProviderRateLimitError",
    ),
    "ProviderTimeoutError": (
        "app.services.brokers.capabilities",
        "ProviderTimeoutError",
    ),
    "ProviderUnsupportedError": (
        "app.services.brokers.capabilities",
        "ProviderUnsupportedError",
    ),
    "ProviderValidationError": (
        "app.services.brokers.capabilities",
        "ProviderValidationError",
    ),
    "MarketBar": ("app.workspace.data_manager", "MarketBar"),
    "MarketTick": ("app.workspace.data_manager", "MarketTick"),
    "Timeframe": ("app.workspace.data_manager", "Timeframe"),
    "AccountInfo": ("app.services.include.contracts", "AccountInfo"),
    "BridgeEvent": ("app.services.include.contracts", "BridgeEvent"),
    "DealInfo": ("app.services.include.contracts", "DealInfo"),
    "OrderInfo": ("app.services.include.contracts", "OrderInfo"),
    "PositionInfo": ("app.services.include.contracts", "PositionInfo"),
    "Receipt": ("app.services.include.contracts", "Receipt"),
    "ReceiptStatus": ("app.services.include.enums", "ReceiptStatus"),
    "SymbolInfo": ("app.services.include.contracts", "SymbolInfo"),
    "TerminalInfo": ("app.services.include.contracts", "TerminalInfo"),
    "TradeAction": ("app.services.include.enums", "TradeAction"),
    "TradeCheckResult": ("app.services.include.contracts", "TradeCheckResult"),
    "TradeRequest": ("app.services.include.contracts", "TradeRequest"),
    "TradeResult": ("app.services.include.contracts", "TradeResult"),
    "TradingBackend": ("app.services.include.contracts", "TradingBackend"),
}

_SINGLETON_FACTORIES: dict[str, tuple[str, str]] = {
    "yahoo": ("app.services.brokers.yahoo", "YahooBroker"),
    "dukascopy": ("app.services.brokers.dukascopy", "DukascopyBroker"),
    "darwinex": ("app.services.brokers.darwinex", "DarwinexBroker"),
    "sq_equity": ("app.services.brokers.sq_equity", "SQEquityBroker"),
    "sq_futures": ("app.services.brokers.sq_futures", "SQFuturesBroker"),
    "crypto": ("app.services.brokers.crypto", "CryptoBroker"),
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
    "binance": "crypto",
    "crypto": "crypto",
    "files": "files",
    "file": "files",
    "tick_downloader": "tick_downloader",
}


def get_broker(name: str, registry: Any = None) -> Any:
    """Resolve a data broker singleton by name or alias, optionally querying a registry."""
    if registry is not None and hasattr(registry, "resolve_broker"):
        try:
            return registry.resolve_broker(name)
        except KeyError:
            pass

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
    "AccountInfo",
    "BaseBrokerBackend",
    "BinanceBroker",
    "BridgeError",
    "BridgeEvent",
    "BrokerBackend",
    "BrokerKey",
    "BrokerRegistry",
    "CancellationToken",
    "CTraderBackend",
    "CryptoBroker",
    "DarwinexBroker",
    "DataBrokerBackend",
    "DealInfo",
    "DukascopyBroker",
    "FilesBroker",
    "HistoricalProviderView",
    "HistoryKind",
    "HistoryPage",
    "HistoryRequest",
    "MT5Backend",
    "MarketBar",
    "MarketTick",
    "OrderInfo",
    "PositionInfo",
    "ProviderAuthError",
    "ProviderCapabilities",
    "ProviderCancelledError",
    "ProviderDisabledError",
    "ProviderError",
    "ProviderHealth",
    "ProviderNotFoundError",
    "ProviderRateLimitError",
    "ProviderTimeoutError",
    "ProviderUnsupportedError",
    "ProviderValidationError",
    "Receipt",
    "ReceiptStatus",
    "SQEquityBroker",
    "SQFuturesBroker",
    "SimulationBackend",
    "SymbolInfo",
    "TerminalInfo",
    "TickDownloaderBroker",
    "Timeframe",
    "TradeAction",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
    "TradingBackend",
    "YahooBroker",
    "binance",
    "crypto",
    "darwinex",
    "dukascopy",
    "files",
    "get_broker",
    "normalize_broker_name",
    "sq_equity",
    "sq_futures",
    "tick_downloader",
    "yahoo",
]
