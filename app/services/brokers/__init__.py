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

from app.services.brokers._base_data import DataBrokerBackend
from app.services.brokers.contracts import (
    AccountSnapshot,
    BridgeError,
    BridgeEvent,
    DealSnapshot,
    HistoryOrderSnapshot,
    MarketBar,
    MarketTick,
    OrderSnapshot,
    PositionSnapshot,
    Receipt,
    ReceiptStatus,
    SymbolSnapshot,
    SymbolSpec,
    TerminalSnapshot,
    Timeframe,
    TradeAction,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
)
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

# Pre-instantiated data broker singletons
yahoo = YahooBroker()
dukascopy = DukascopyBroker()
darwinex = DarwinexBroker()
sq_equity = SQEquityBroker()
sq_futures = SQFuturesBroker()
binance = BinanceBroker()
files = FilesBroker()
tick_downloader = TickDownloaderBroker()

_REGISTRY: dict[str, DataBrokerBackend] = {
    "yahoo": yahoo,
    "dukascopy": dukascopy,
    "darwinex": darwinex,
    "sq_equity": sq_equity,
    "equity": sq_equity,
    "sq_futures": sq_futures,
    "futures": sq_futures,
    "binance": binance,
    "crypto": binance,
    "files": files,
    "file": files,
    "tick_downloader": tick_downloader,
}


def get_broker(name: str) -> DataBrokerBackend:
    """Resolve a data broker by name or alias."""
    key = name.lower().strip()
    if key in _REGISTRY:
        return _REGISTRY[key]
    raise KeyError(f"Unknown broker: {name}")


__all__ = [
    "AccountSnapshot",
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
