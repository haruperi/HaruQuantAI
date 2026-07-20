"""Brokers service package.

Broker adapters are loaded lazily so optional provider SDKs are only required
when their adapter is actually used.
"""

from typing import TYPE_CHECKING

from app.services.utils.logger import logger

if TYPE_CHECKING:
    from app.services.brokers.binance import BinanceClient, get_binance_client
    from app.services.brokers.ctrader import (
        CTraderAccountInfo,
        CTraderClient,
        CTraderDealInfo,
        CTraderOrderInfo,
        CTraderPositionInfo,
        CTraderSymbolInfo,
        CTraderTerminalInfo,
        CTraderTradeResult,
        get_ctrader_client,
    )
    from app.services.brokers.dukascopy import (
        DukascopyClient,
        dukascopy_data_list_symbols,
        fetch,
        get_dukascopy_client,
        load_dukascopy,
    )
    from app.services.brokers.mt5 import (
        MT5Api,
        MT5Client,
        get_connected_mt5_client,
        get_mt5_api,
        get_mt5_client,
        get_mt5_credentials,
        load_mt5,
        mt5_data_get_bars_with_credentials,
        mt5_data_list_symbol_details_with_credentials,
        mt5_data_list_symbols,
    )
    from app.services.brokers.router import get_active_broker_name, get_broker_module
    from app.services.brokers.yahoo import YahooClient, get_yahoo_client

__all__ = [
    "BinanceClient",
    "CTraderAccountInfo",
    "CTraderClient",
    "CTraderDealInfo",
    "CTraderOrderInfo",
    "CTraderPositionInfo",
    "CTraderSymbolInfo",
    "CTraderTerminalInfo",
    "CTraderTradeResult",
    "DukascopyClient",
    "MT5Api",
    "MT5Client",
    "YahooClient",
    "dukascopy_data_list_symbols",
    "fetch",
    "get_active_broker_name",
    "get_binance_client",
    "get_broker_module",
    "get_connected_mt5_client",
    "get_ctrader_client",
    "get_dukascopy_client",
    "get_mt5_api",
    "get_mt5_client",
    "get_mt5_credentials",
    "get_yahoo_client",
    "load_dukascopy",
    "load_mt5",
    "mt5_data_get_bars_with_credentials",
    "mt5_data_list_symbol_details_with_credentials",
    "mt5_data_list_symbols",
]

_EXPORT_MODULES = {
    "BinanceClient": "app.services.brokers.binance",
    "get_binance_client": "app.services.brokers.binance",
    "CTraderClient": "app.services.brokers.ctrader",
    "CTraderAccountInfo": "app.services.brokers.ctrader",
    "CTraderDealInfo": "app.services.brokers.ctrader",
    "CTraderOrderInfo": "app.services.brokers.ctrader",
    "CTraderPositionInfo": "app.services.brokers.ctrader",
    "CTraderSymbolInfo": "app.services.brokers.ctrader",
    "CTraderTerminalInfo": "app.services.brokers.ctrader",
    "CTraderTradeResult": "app.services.brokers.ctrader",
    "get_ctrader_client": "app.services.brokers.ctrader",
    "DukascopyClient": "app.services.brokers.dukascopy",
    "dukascopy_data_list_symbols": "app.services.brokers.dukascopy",
    "fetch": "app.services.brokers.dukascopy",
    "get_dukascopy_client": "app.services.brokers.dukascopy",
    "load_dukascopy": "app.services.brokers.dukascopy",
    "MT5Client": "app.services.brokers.mt5",
    "MT5Api": "app.services.brokers.mt5",
    "get_connected_mt5_client": "app.services.brokers.mt5",
    "get_mt5_api": "app.services.brokers.mt5",
    "get_mt5_client": "app.services.brokers.mt5",
    "get_mt5_credentials": "app.services.brokers.mt5",
    "load_mt5": "app.services.brokers.mt5",
    "mt5_data_get_bars_with_credentials": "app.services.brokers.mt5",
    "mt5_data_list_symbol_details_with_credentials": "app.services.brokers.mt5",
    "mt5_data_list_symbols": "app.services.brokers.mt5",
    "YahooClient": "app.services.brokers.yahoo",
    "get_yahoo_client": "app.services.brokers.yahoo",
    "get_active_broker_name": "app.services.brokers.router",
    "get_broker_module": "app.services.brokers.router",
}


def __getattr__(name: str) -> object:
    """Description.
        Lazily import broker adapter exports.
    
    Args:
        name: str.
    
    Returns:
        object.
    """
    if name not in _EXPORT_MODULES:
        raise AttributeError(name)

    from importlib import import_module

    module = import_module(_EXPORT_MODULES[name])
    value = getattr(module, name)
    globals()[name] = value
    logger.debug("Loaded broker export %s.", name)
    return value
