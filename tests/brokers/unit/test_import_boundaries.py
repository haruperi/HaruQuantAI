"""Broker import and export boundary tests."""

import importlib
import inspect
import sys
from pathlib import Path


def test_contract_exports_are_exact() -> None:
    """The contract package exposes only the documented public boundary."""
    contracts = importlib.import_module("app.services.brokers.canonical_contracts")
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


def test_instrument_identity_surface_is_retired() -> None:
    """Brokers exposes no canonical profile or provider-symbol administration."""
    brokers = importlib.import_module("app.services.brokers")
    retired = {
        "build_instrument_venue_profile",
        "parse_instrument_venue_profile",
        "register_broker_symbol_mapping",
        "close_broker_symbol_mapping",
        "disable_broker_symbol_mapping",
        "resolve_broker_canonical_symbol",
        "resolve_broker_provider_symbol",
        "resolve_broker_provider_symbol_as_of",
        "get_broker_capability_catalogue",
        "get_broker_dashboard_snapshot",
    }
    assert retired.isdisjoint(brokers.__all__)
    assert all(not hasattr(brokers, name) for name in retired)
    assert not (Path("app/services/brokers") / "instrument_profiles").exists()
    assert not (Path("app/services/brokers") / "capabilities").exists()


def test_runtime_package_is_private() -> None:
    """Runtime initialization exposes no implementation symbol."""
    runtime = importlib.import_module("app.services.brokers._shared")
    assert getattr(runtime, "__all__", []) == []


def test_conformance_feature_is_retired_from_production() -> None:
    """The conformance suite lives in test infrastructure and is not in production."""
    assert not (Path("app/services/brokers") / "conformance").exists()
    brokers = importlib.import_module("app.services.brokers")
    retired = {
        "build_broker_calculation_fixture",
        "collect_broker_calculation_fixture",
        "create_configured_fake_broker_adapter",
        "create_fake_broker_adapter",
        "dump_broker_calculation_fixture",
        "parse_broker_calculation_fixture",
        "run_broker_adapter_conformance",
        "set_fake_broker_error",
    }
    assert retired.isdisjoint(brokers.__all__)
    assert all(not hasattr(brokers, name) for name in retired)


def test_mt5_feature_is_internal() -> None:
    """The MT5 feature does not create a second public boundary."""
    mt5 = importlib.import_module("app.services.brokers.metatrader")
    assert getattr(mt5, "__all__", []) == []


def test_ctrader_feature_is_internal() -> None:
    """The cTrader feature does not create a second public boundary."""
    ctrader = importlib.import_module("app.services.brokers.ctrader")
    assert getattr(ctrader, "__all__", []) == []


def test_binance_feature_is_internal() -> None:
    """The Binance feature does not create a second public boundary."""
    binance = importlib.import_module("app.services.brokers.binance")
    assert getattr(binance, "__all__", []) == []


def test_dukascopy_feature_is_internal() -> None:
    """The Dukascopy feature does not create a second public boundary."""
    dukascopy = importlib.import_module("app.services.brokers.dukascopy")
    assert getattr(dukascopy, "__all__", []) == []


def test_yahoo_feature_is_internal() -> None:
    """The Yahoo feature does not create a second public boundary."""
    yahoo = importlib.import_module("app.services.brokers.yahoo")
    assert getattr(yahoo, "__all__", []) == []


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
