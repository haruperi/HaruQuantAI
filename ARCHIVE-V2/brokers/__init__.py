"""Brokers service package.

Broker adapters are loaded lazily so optional provider SDKs are only required
when their adapter is actually used.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.brokers.binance import BinanceClient, get_binance_client
    from app.services.brokers.ctrader import CTraderClient, get_ctrader_client
    from app.services.brokers.dukascopy import DukascopyClient, get_dukascopy_client
    from app.services.brokers.mt5 import MT5Client, get_mt5_client
    from app.services.brokers.router import get_active_broker_name, get_broker_module
    from app.services.brokers.yahoo import YahooClient, get_yahoo_client

__all__ = [
    "BinanceClient",
    "CTraderClient",
    "DukascopyClient",
    "MT5Client",
    "YahooClient",
    "get_active_broker_name",
    "get_binance_client",
    "get_broker_module",
    "get_ctrader_client",
    "get_dukascopy_client",
    "get_mt5_client",
    "get_yahoo_client",
]

_EXPORT_MODULES = {
    "BinanceClient": "app.services.brokers.binance",
    "get_binance_client": "app.services.brokers.binance",
    "CTraderClient": "app.services.brokers.ctrader",
    "get_ctrader_client": "app.services.brokers.ctrader",
    "DukascopyClient": "app.services.brokers.dukascopy",
    "get_dukascopy_client": "app.services.brokers.dukascopy",
    "MT5Client": "app.services.brokers.mt5",
    "get_mt5_client": "app.services.brokers.mt5",
    "YahooClient": "app.services.brokers.yahoo",
    "get_yahoo_client": "app.services.brokers.yahoo",
    "get_active_broker_name": "app.services.brokers.router",
    "get_broker_module": "app.services.brokers.router",
}


def __getattr__(name: str) -> object:
    """Lazily import broker adapter exports.

    Args:
        name: Exported broker symbol.

    Returns:
        Any: The requested broker class or factory.

    Raises:
        AttributeError: If ``name`` is not an exported broker symbol.
    """
    if name not in _EXPORT_MODULES:
        raise AttributeError(name)

    from importlib import import_module

    module = import_module(_EXPORT_MODULES[name])
    value = getattr(module, name)
    globals()[name] = value
    return value
