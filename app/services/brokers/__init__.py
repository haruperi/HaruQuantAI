# ruff: noqa: F822 -- lazy exports via PEP 562 __getattr__
"""Broker clients, execution backends, and data providers.

Description:
    Exposes uniform BrokerClient and TradingClient implementations:
    - MetaTraderClient (pilot MetaTrader 4/5 EA bridge and archives)
    - CTraderClient (cTrader Open API Protobuf/TLS)
    - SimulatorClient (deterministic in-memory trading engine)
    And uniform market data broker clients:
    - YahooClient (Yahoo Finance v8 chart / v7 quote)
    - DukascopyClient (Dukascopy CDN & datafeed)
    - DarwinexClient (Darwinex CDN ticks & bars)
    - CryptoClient / BinanceClient / BitfinexClient / CoinbaseClient / PoloniexClient
    - SQEquityClient (StrategyQuant US Equities)
    - SQFuturesClient (StrategyQuant Continuous Futures)
    - FilesClient (Local CSV / Parquet / HST / FXT data archives)
    - TickDownloaderClient (Tick data downloader)
    Along with base client contracts, errors, and data contracts.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.base import (
        BridgeError,
        BrokerClient,
        TradingClient,
    )
    from app.services.brokers.crypto import (
        BinanceClient,
        BitfinexClient,
        CoinbaseClient,
        CryptoClient,
        PoloniexClient,
    )
    from app.services.brokers.ctrader import CTraderClient
    from app.services.brokers.darwinex import DarwinexClient
    from app.services.brokers.dukascopy import DukascopyClient
    from app.services.brokers.files import FilesClient
    from app.services.brokers.metatrader import MetaTraderClient
    from app.services.brokers.simulator import SimulatorClient
    from app.services.brokers.sq_equity import SQEquityClient
    from app.services.brokers.sq_futures import SQFuturesClient
    from app.services.brokers.tick_downloader import TickDownloaderClient
    from app.services.brokers.yahoo import YahooClient
    from app.services.include.contracts import (
        AccountInfo,
        BridgeEvent,
        DealInfo,
        MarketBar,
        MarketTick,
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
        Timeframe,
        TradeAction,
    )

_SINGLETONS: dict[str, Any] = {}

_MODULE_MAPPING: dict[str, tuple[str, str]] = {
    # Base Client and Error Hierarchy
    "BrokerClient": ("app.services.brokers.base", "BrokerClient"),
    "TradingClient": ("app.services.brokers.base", "TradingClient"),
    "BridgeError": ("app.services.brokers.base", "BridgeError"),
    # Uniform Clients
    "MetaTraderClient": ("app.services.brokers.metatrader", "MetaTraderClient"),
    "CTraderClient": ("app.services.brokers.ctrader", "CTraderClient"),
    "SimulatorClient": ("app.services.brokers.simulator", "SimulatorClient"),
    "YahooClient": ("app.services.brokers.yahoo", "YahooClient"),
    "DukascopyClient": ("app.services.brokers.dukascopy", "DukascopyClient"),
    "DarwinexClient": ("app.services.brokers.darwinex", "DarwinexClient"),
    "CryptoClient": ("app.services.brokers.crypto", "CryptoClient"),
    "BinanceClient": ("app.services.brokers.crypto", "BinanceClient"),
    "BitfinexClient": ("app.services.brokers.crypto", "BitfinexClient"),
    "CoinbaseClient": ("app.services.brokers.crypto", "CoinbaseClient"),
    "PoloniexClient": ("app.services.brokers.crypto", "PoloniexClient"),
    "FilesClient": ("app.services.brokers.files", "FilesClient"),
    "SQEquityClient": ("app.services.brokers.sq_equity", "SQEquityClient"),
    "SQFuturesClient": ("app.services.brokers.sq_futures", "SQFuturesClient"),
    "TickDownloaderClient": (
        "app.services.brokers.tick_downloader",
        "TickDownloaderClient",
    ),
    # Contracts & Enums
    "MarketBar": ("app.services.include.contracts", "MarketBar"),
    "MarketTick": ("app.services.include.contracts", "MarketTick"),
    "Timeframe": ("app.services.include.enums", "Timeframe"),
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
    "yahoo": ("app.services.brokers.yahoo", "YahooClient"),
    "dukascopy": ("app.services.brokers.dukascopy", "DukascopyClient"),
    "darwinex": ("app.services.brokers.darwinex", "DarwinexClient"),
    "sq_equity": ("app.services.brokers.sq_equity", "SQEquityClient"),
    "sq_futures": ("app.services.brokers.sq_futures", "SQFuturesClient"),
    "crypto": ("app.services.brokers.crypto", "CryptoClient"),
    "binance": ("app.services.brokers.crypto", "BinanceClient"),
    "files": ("app.services.brokers.files", "FilesClient"),
    "tick_downloader": ("app.services.brokers.tick_downloader", "TickDownloaderClient"),
    "metatrader": ("app.services.brokers.metatrader", "MetaTraderClient"),
    "ctrader": ("app.services.brokers.ctrader", "CTraderClient"),
    "simulator": ("app.services.brokers.simulator", "SimulatorClient"),
}


def normalize_provider_id(name: str) -> str:
    """Normalize broker name or alias to canonical identifier."""
    cleaned = name.lower().strip().replace("-", "_").replace(" ", "_")
    for suffix in ("_broker", "_backend", "_client"):
        cleaned = cleaned.removesuffix(suffix)
    aliases = {
        "strategyquant_equity": "sq_equity",
        "strategyquant_futures": "sq_futures",
        "csv": "files",
        "parquet": "files",
        "local": "files",
        "yahoo_finance": "yahoo",
        "yfinance": "yahoo",
        "mt5": "metatrader",
    }
    return aliases.get(cleaned, cleaned)


def normalize_broker_name(name: str) -> str:
    """Backward-compatible alias for normalize_provider_id."""
    return normalize_provider_id(name)


def get_broker(name: str, registry: Any = None) -> Any:
    """Resolve a broker singleton by name or alias."""
    del registry
    target = normalize_provider_id(name)
    if target not in _SINGLETON_FACTORIES:
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
    "BinanceClient",
    "BitfinexClient",
    "BridgeError",
    "BridgeEvent",
    "BrokerClient",
    "CTraderClient",
    "CoinbaseClient",
    "CryptoClient",
    "DarwinexClient",
    "DealInfo",
    "DukascopyClient",
    "FilesClient",
    "MarketBar",
    "MarketTick",
    "MetaTraderClient",
    "OrderInfo",
    "PoloniexClient",
    "PositionInfo",
    "Receipt",
    "ReceiptStatus",
    "SQEquityClient",
    "SQFuturesClient",
    "SimulatorClient",
    "SymbolInfo",
    "TerminalInfo",
    "TickDownloaderClient",
    "Timeframe",
    "TradeAction",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResult",
    "TradingBackend",
    "TradingClient",
    "YahooClient",
    "binance",
    "crypto",
    "ctrader",
    "darwinex",
    "dukascopy",
    "files",
    "get_broker",
    "metatrader",
    "normalize_broker_name",
    "normalize_provider_id",
    "simulator",
    "sq_equity",
    "sq_futures",
    "tick_downloader",
    "yahoo",
]
