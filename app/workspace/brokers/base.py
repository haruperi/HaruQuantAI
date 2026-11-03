"""Base broker client architecture, HTTP transport, and provider registry.

Description:
    Provides the foundational BrokerClient base class for all market data providers,
    TradingClient for execution-capable brokers, bounded HTTP session pooling with
    retry backoff, rate limiting, and credential redaction, plus lazy provider
    registry resolution.
"""

from __future__ import annotations

import importlib
from typing import Any

import app.core.data.contracts as _contracts
import app.core.enums as _enums
import app.core.trading.connection.contracts as _trading_contracts
from app.core.trading.connection.base import (
    MAX_RESPONSE_BYTES,
    BridgeError,
    BrokerClient,
    RateLimiter,
    TradingClient,
    create_http_session,
    epoch_millis,
    epoch_seconds,
    execute_bounded_get,
    redact_url_or_message,
    utc_now,
)
from app.core.trading.connection.trading_dispatch import TradingDispatcher

__all__ = [
    "BridgeError",
    "BrokerClient",
    "MAX_RESPONSE_BYTES",
    "RateLimiter",
    "TradingClient",
    "TradingDispatcher",
    "create_http_session",
    "epoch_millis",
    "epoch_seconds",
    "execute_bounded_get",
    "get_broker",
    "normalize_broker_name",
    "normalize_provider_id",
    "redact_url_or_message",
    "utc_now",
]

_SINGLETONS: dict[str, Any] = {}
_FACTORIES_RAW = (
    "yahoo:yahoo:YahooClient dukascopy:dukascopy:DukascopyClient "
    "darwinex:darwinex:DarwinexClient sq_equity:sq_equity:SQEquityClient "
    "sq_futures:sq_futures:SQFuturesClient crypto:crypto:CryptoClient "
    "binance:crypto:BinanceClient files:files:FilesClient "
    "metatrader:metatrader:MetaTraderClient ctrader:ctrader:CTraderClient "
    "simulator:simulator:SimulatorClient live_test:registry:LiveTest"
)
_SINGLETON_FACTORIES: dict[str, tuple[str, str]] = {
    p[0]: (p[1], p[2]) for p in (item.split(":") for item in _FACTORIES_RAW.split())
}
_EXTRA_MAP = (
    "BrokerClient:base TradingClient:base BridgeError:base "
    "BitfinexClient:crypto CoinbaseClient:crypto "
    "PoloniexClient:crypto LiveTestCLI:registry"
)
_CLASS_TO_MODULE: dict[str, str] = {
    cls: mod for mod, cls in _SINGLETON_FACTORIES.values()
} | dict(p.split(":") for p in _EXTRA_MAP.split())
_ALIASES_RAW = (
    "strategyquant_equity:sq_equity strategyquant_futures:sq_futures "
    "csv:files parquet:files local:files "
    "yahoo_finance:yahoo yfinance:yahoo mt5:metatrader"
)
_PROVIDER_ALIASES: dict[str, str] = dict(p.split(":") for p in _ALIASES_RAW.split())


def normalize_provider_id(name: str) -> str:
    """Normalize broker name or alias to canonical identifier."""
    cleaned = name.lower().strip().replace("-", "_").replace(" ", "_")
    for suffix in ("_broker", "_backend", "_client"):
        cleaned = cleaned.removesuffix(suffix)
    return _PROVIDER_ALIASES.get(cleaned, cleaned)


normalize_broker_name = normalize_provider_id


def get_broker(name: str, registry: Any = None) -> Any:
    """Resolve a broker singleton by name or alias."""
    del registry
    target = normalize_provider_id(name)
    if target not in _SINGLETON_FACTORIES:
        raise KeyError(f"Unknown broker: {name}")
    if target not in _SINGLETONS:
        mod_name, cls_name = _SINGLETON_FACTORIES[target]
        mod = importlib.import_module(f"app.workspace.brokers.{mod_name}")
        factory = (
            mod.create_mt5_client if target == "metatrader" else getattr(mod, cls_name)
        )
        _SINGLETONS[target] = factory()
    return _SINGLETONS[target]


def _resolve_broker_export(name: str) -> Any:
    """Lazily import broker classes, contracts, and singletons on demand."""
    if name in _SINGLETON_FACTORIES:
        return get_broker(name)
    if name in _CLASS_TO_MODULE:
        mod = importlib.import_module(f"app.workspace.brokers.{_CLASS_TO_MODULE[name]}")
        return getattr(mod, name)
    for source in (_contracts, _trading_contracts, _enums):
        if hasattr(source, name):
            return getattr(source, name)
    raise AttributeError(f"module 'app.workspace.brokers' has no attribute {name!r}")
