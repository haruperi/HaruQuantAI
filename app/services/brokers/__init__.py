# ruff: noqa: F822 -- lazy exports via PEP 562 __getattr__
"""Broker clients, execution backends, and data providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    TradingClient,
    _resolve_broker_export,
    get_broker,
    normalize_broker_name,
    normalize_provider_id,
)

if TYPE_CHECKING:
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


def __getattr__(name: str) -> Any:
    """Lazily import broker classes, contracts, and singletons on demand."""
    return _resolve_broker_export(name)


__all__ = [
    "BinanceClient",
    "BitfinexClient",
    "BridgeError",
    "BrokerClient",
    "CTraderClient",
    "CoinbaseClient",
    "CryptoClient",
    "DarwinexClient",
    "DukascopyClient",
    "FilesClient",
    "MetaTraderClient",
    "PoloniexClient",
    "SQEquityClient",
    "SQFuturesClient",
    "SimulatorClient",
    "TickDownloaderClient",
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
