"""Broker import and export boundary tests."""

import importlib
import inspect
import sys
from pathlib import Path


def test_contract_exports_are_exact() -> None:
    """The contract package exposes only the documented public boundary."""
    contracts = importlib.import_module("app.services.brokers.contracts")
    expected_exports = {
        "BROKER_ERROR_CATALOG",
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
        "BrokerServerTime",
        "BrokerSubscription",
        "BrokerSubscriptionInfo",
        "BrokerSymbolInfo",
        "BrokerTick",
        "BrokerTradingSession",
        "CalculationProvider",
        "MarketDataProvider",
        "StandardResponse",
        "TradeExecutionProvider",
    }
    assert set(contracts.__all__) == expected_exports


def test_root_exports_are_function_only() -> None:
    """Every symbol re-exported from app.services.brokers is a standalone function."""
    brokers = importlib.import_module("app.services.brokers")
    assert len(brokers.__all__) > 0
    for symbol_name in brokers.__all__:
        attr = getattr(brokers, symbol_name)
        assert inspect.isfunction(attr), (
            f"Exported symbol {symbol_name!r} must be a function, but got {type(attr)}"
        )


def test_root_exports_and_lazy_imports_are_exact() -> None:
    """Ordinary root import leaves every provider SDK unloaded."""
    modules_to_check = ["MetaTrader5", "binance", "yfinance"]
    stored = {
        name: sys.modules.pop(name) for name in modules_to_check if name in sys.modules
    }
    try:
        importlib.import_module("app.services.brokers")
        assert "MetaTrader5" not in sys.modules
        assert "binance" not in sys.modules
        assert "yfinance" not in sys.modules
    finally:
        sys.modules.update(stored)


def test_runtime_package_is_private() -> None:
    """Runtime initialization exposes no implementation symbol."""
    runtime = importlib.import_module("app.services.brokers.adapter_runtime")
    assert runtime.__all__ == []


def test_testing_export_is_exact_and_unregistered() -> None:
    """The fake testing utility package exports only approved symbols."""
    testing = importlib.import_module("app.services.brokers.testing")
    assert set(testing.__all__) == {"FakeBrokerAdapter", "create_fake_broker_adapter"}


def test_mt5_export_is_exact() -> None:
    """The MT5 package exports only its approved adapter type."""
    mt5 = importlib.import_module("app.services.brokers.mt5_account")
    assert mt5.__all__ == ["MT5BrokerAdapter"]


def test_ctrader_export_is_exact() -> None:
    """The cTrader package exports only its approved adapter type."""
    ctrader = importlib.import_module("app.services.brokers.ctrader_session")
    assert ctrader.__all__ == ["CTraderBrokerAdapter"]


def test_binance_export_is_exact() -> None:
    """The Binance package exports only its approved adapter type."""
    binance = importlib.import_module("app.services.brokers.binance_session")
    assert binance.__all__ == ["BinanceBrokerAdapter"]


def test_dukascopy_export_is_exact() -> None:
    """The Dukascopy package exports only its approved adapter type."""
    dukascopy = importlib.import_module("app.services.brokers.dukascopy_ticks")
    assert dukascopy.__all__ == ["DukascopyBrokerAdapter"]


def test_yahoo_export_is_exact() -> None:
    """The Yahoo package exports only its approved adapter type."""
    yahoo = importlib.import_module("app.services.brokers.yahoo_history")
    assert yahoo.__all__ == ["YahooBrokerAdapter"]


def test_registry_exports_are_exact() -> None:
    """The registry package exports exactly its three public functions."""
    registry = importlib.import_module("app.services.brokers.registry")
    assert set(registry.__all__) == {
        "create_broker_adapter",
        "get_registered_brokers",
        "get_broker_capability_catalogue",
    }


def test_broker_owned_public_consumers_use_only_the_root_boundary() -> None:
    """Usage, workflows, and integration evidence never deep-import Brokers."""
    test_root = Path(__file__).resolve().parents[1]
    consumer_paths = (
        *sorted((test_root / "usage").glob("*.py")),
        *sorted((test_root / "usage" / "workflows").glob("*.py")),
        *sorted((test_root / "integration").glob("*.py")),
    )
    violations = [
        str(path.relative_to(test_root))
        for path in consumer_paths
        if "app.services.brokers." in path.read_text(encoding="utf-8")
    ]
    assert not violations, f"Broker deep imports are prohibited: {violations}"
