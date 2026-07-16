"""Broker import and export boundary tests."""

import importlib
import sys


def test_contract_exports_are_exact() -> None:
    """The contract package exposes only the documented public boundary."""
    contracts = importlib.import_module("app.services.brokers.contracts")
    assert set(contracts.__all__) == {
        "AccountProvider",
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
        "CalculationProvider",
        "MarketDataProvider",
        "TradeExecutionProvider",
    }
    assert not any(name.startswith("_") for name in contracts.__all__)


def test_root_exports_and_lazy_imports_are_exact() -> None:
    """Ordinary root import leaves every provider SDK unloaded."""
    brokers = importlib.import_module("app.services.brokers")
    assert "FakeBrokerAdapter" not in brokers.__all__
    assert "MetaTrader5" not in sys.modules
    assert "binance" not in sys.modules
    assert "yfinance" not in sys.modules
    assert brokers.YahooBrokerAdapter.__name__ == "YahooBrokerAdapter"
    assert "yfinance" not in sys.modules


def test_runtime_package_is_private() -> None:
    """Runtime initialization exposes no implementation symbol."""
    runtime = importlib.import_module("app.services.brokers.runtime")
    assert runtime.__all__ == []


def test_testing_export_is_exact_and_unregistered() -> None:
    """The fake exists only in the explicit testing utility package."""
    testing = importlib.import_module("app.services.brokers.testing")
    assert testing.__all__ == ["FakeBrokerAdapter"]


def test_mt5_export_is_exact() -> None:
    """The MT5 package exports only its approved adapter type."""
    mt5 = importlib.import_module("app.services.brokers.mt5")
    assert mt5.__all__ == ["MT5BrokerAdapter"]


def test_ctrader_export_is_exact() -> None:
    """The cTrader package exports only its approved adapter type."""
    ctrader = importlib.import_module("app.services.brokers.ctrader")
    assert ctrader.__all__ == ["CTraderBrokerAdapter"]


def test_binance_export_is_exact() -> None:
    """The Binance package exports only its approved adapter type."""
    binance = importlib.import_module("app.services.brokers.binance")
    assert binance.__all__ == ["BinanceBrokerAdapter"]


def test_dukascopy_export_is_exact() -> None:
    """The Dukascopy package exports only its approved adapter type."""
    dukascopy = importlib.import_module("app.services.brokers.dukascopy")
    assert dukascopy.__all__ == ["DukascopyBrokerAdapter"]


def test_yahoo_export_is_exact() -> None:
    """The Yahoo package exports only its approved adapter type."""
    yahoo = importlib.import_module("app.services.brokers.yahoo")
    assert yahoo.__all__ == ["YahooBrokerAdapter"]


def test_registry_exports_are_exact() -> None:
    """The registry package exports exactly its three public functions."""
    registry = importlib.import_module("app.services.brokers.registry")
    assert set(registry.__all__) == {
        "create_broker_adapter",
        "get_registered_brokers",
        "get_broker_capability_catalogue",
    }
