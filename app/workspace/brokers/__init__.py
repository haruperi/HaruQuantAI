# ruff: noqa: F822 -- lazy exports via PEP 562 __getattr__
"""Broker clients, execution backends, and data providers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import (
    BridgeError,
    BrokerClient,
    TradingClient,
    _resolve_broker_export,
    get_broker,
    normalize_broker_name,
    normalize_provider_id,
)

if TYPE_CHECKING:
    from .crypto import (
        BinanceClient,
        BitfinexClient,
        CoinbaseClient,
        CryptoClient,
        PoloniexClient,
    )
    from .ctrader import CTraderClient
    from .darwinex import DarwinexClient
    from .dukascopy import DukascopyClient
    from .files import FilesClient
    from .metatrader import MetaTraderClient
    from .registry import LiveTest, LiveTestCLI
    from .simulator import SimulatorClient
    from .sq_equity import SQEquityClient
    from .sq_futures import SQFuturesClient
    from .tick_downloader import TickDownloaderClient
    from .yahoo import YahooClient


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
    "LiveTest",
    "LiveTestCLI",
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
