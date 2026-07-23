"""Canonical Brokers domain API."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.brokers.binance_session import BinanceBrokerAdapter
    from app.services.brokers.ctrader_session import CTraderBrokerAdapter
    from app.services.brokers.dukascopy_ticks import DukascopyBrokerAdapter
    from app.services.brokers.mt5_account import MT5BrokerAdapter
    from app.services.brokers.yahoo_history import YahooBrokerAdapter

from app.services.brokers.contracts.enums import (
    BrokerCapabilityId,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)
from app.services.brokers.contracts.models import (
    BrokerAccountInfo,
    BrokerAccountTransaction,
    BrokerAssetInfo,
    BrokerBalance,
    BrokerBar,
    BrokerCapability,
    BrokerConnectionConfig,
    BrokerConnectionEvent,
    BrokerConnectionStatus,
    BrokerDeal,
    BrokerError,
    BrokerFeatureFlags,
    BrokerFeeEstimate,
    BrokerMarginRequest,
    BrokerMarketStatus,
    BrokerOrder,
    BrokerOrderBook,
    BrokerOrderCheck,
    BrokerOrderFilter,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPage,
    BrokerPermissions,
    BrokerPlatformInfo,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionFilter,
    BrokerPositionModificationRequest,
    BrokerProfitRequest,
    BrokerQuote,
    BrokerResult,
    BrokerServerTime,
    BrokerSubscriptionInfo,
    BrokerSymbolInfo,
    BrokerTick,
    BrokerTradingSession,
)
from app.services.brokers.contracts.protocols import (
    AccountProvider,
    BrokerAdapter,
    BrokerSubscription,
    CalculationProvider,
    MarketDataProvider,
    TradeExecutionProvider,
)
from app.services.brokers.registry.catalogue import (
    get_broker_capability_catalogue,
)
from app.services.brokers.registry.factory import (
    create_broker_adapter,
    get_registered_brokers,
)

_LAZY_ADAPTERS = {
    "MT5BrokerAdapter": "app.services.brokers.mt5_account",
    "CTraderBrokerAdapter": "app.services.brokers.ctrader_session",
    "BinanceBrokerAdapter": "app.services.brokers.binance_session",
    "DukascopyBrokerAdapter": "app.services.brokers.dukascopy_ticks",
    "YahooBrokerAdapter": "app.services.brokers.yahoo_history",
}

__all__ = (
    "AccountProvider",
    "BinanceBrokerAdapter",
    "BrokerAccountInfo",
    "BrokerAccountTransaction",
    "BrokerAdapter",
    "BrokerAssetInfo",
    "BrokerBalance",
    "BrokerBar",
    "BrokerCapability",
    "BrokerCapabilityId",
    "BrokerConnectionConfig",
    "BrokerConnectionEvent",
    "BrokerConnectionState",
    "BrokerConnectionStatus",
    "BrokerDeal",
    "BrokerEnvironment",
    "BrokerError",
    "BrokerErrorCode",
    "BrokerFeatureFlags",
    "BrokerFeeEstimate",
    "BrokerId",
    "BrokerMarginRequest",
    "BrokerMarketStatus",
    "BrokerOrder",
    "BrokerOrderBook",
    "BrokerOrderCheck",
    "BrokerOrderFilter",
    "BrokerOrderModificationRequest",
    "BrokerOrderRequest",
    "BrokerOrderResult",
    "BrokerPage",
    "BrokerPermissions",
    "BrokerPlatformInfo",
    "BrokerPosition",
    "BrokerPositionCloseRequest",
    "BrokerPositionFilter",
    "BrokerPositionModificationRequest",
    "BrokerProfitRequest",
    "BrokerQuote",
    "BrokerResult",
    "BrokerServerTime",
    "BrokerSubscription",
    "BrokerSubscriptionInfo",
    "BrokerSymbolInfo",
    "BrokerTick",
    "BrokerTradingSession",
    "CTraderBrokerAdapter",
    "CalculationProvider",
    "DukascopyBrokerAdapter",
    "MT5BrokerAdapter",
    "MarketDataProvider",
    "TradeExecutionProvider",
    "YahooBrokerAdapter",
    "create_broker_adapter",
    "get_broker_capability_catalogue",
    "get_registered_brokers",
)


def __getattr__(name: str) -> object:
    """Resolve one approved adapter type without importing SDKs eagerly.

    Args:
        name: Requested package attribute.

    Returns:
        Approved concrete adapter class.

    Raises:
        AttributeError: If ``name`` is not an approved lazy export.
    """
    module_name = _LAZY_ADAPTERS.get(name)
    if module_name is None:
        raise AttributeError(name)
    value = getattr(importlib.import_module(module_name), name)
    globals()[name] = value
    return value
