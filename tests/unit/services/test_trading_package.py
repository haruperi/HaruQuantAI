"""Unit tests for the app.services.trading package structure, exports, and layering.

Description:
    Verifies that app.services.trading satisfies the modular package architecture:
    - Layer 0: app.services.libs.enums
    - Layer 1: app.services.libs.contracts, base.py
    - Layer 2: proxies.py, trade.py
    - Layer 3: facade.py
    - Unified package exports via __init__.py
    - Zero circular imports between submodules
    - Complete removal of app.services.trading.enums, app.services.trading.snapshots,
      and app.services.libs.trading (strict zero backward compatibility)

Purpose:
    FEAT-TRADING-PACKAGE-TESTS: Verification suite for modular trading package.

Key Capabilities:
    - FR-TRADING-PKG-EXPORTS: Verify public export parity between submodules and package.
    - FR-TRADING-PKG-LAYERING: Verify unidirectional dependencies and anti-circular rules.
    - FR-TRADING-PKG-CLEANUP: Verify strict deletion of legacy snapshots, enums, and shims.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/test_trading_package.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_trading_package.py --no-cov
    ```
"""

from __future__ import annotations

import importlib
import inspect

import app.services.libs.contracts as libs_contracts
import app.services.libs.enums as libs_enums
import app.services.trading as trading_pkg
import app.services.trading.base as trading_base
import app.services.trading.facade as trading_facade
import app.services.trading.proxies as trading_proxies
import app.services.trading.trade as trading_trade
import pytest


class TestTradingPackageExports:
    """Verify package-level public exports and submodule parity."""

    def test_enums_exports_identity(self) -> None:
        """Verify enum symbols and descriptions match between package and submodule."""
        assert trading_pkg.ReceiptStatus is libs_enums.ReceiptStatus
        assert trading_pkg.TradeResolution is libs_enums.TradeResolution
        assert trading_pkg.PropertyValue is libs_enums.PropertyValue
        assert trading_pkg.Receipt is libs_enums.Receipt
        assert trading_pkg.BridgeEvent is libs_enums.BridgeEvent
        assert trading_pkg.TradingBackend is libs_enums.TradingBackend
        assert trading_pkg.AccountTradeMode is libs_enums.AccountTradeMode
        assert trading_pkg.StopoutMode is libs_enums.StopoutMode
        assert trading_pkg.MarginMode is libs_enums.MarginMode
        assert trading_pkg.OrderType is libs_enums.OrderType
        assert trading_pkg.OrderFilling is libs_enums.OrderFilling
        assert trading_pkg.OrderTime is libs_enums.OrderTime
        assert trading_pkg.TradeAction is libs_enums.TradeAction
        assert trading_pkg.TradeRetcode is libs_enums.TradeRetcode
        assert trading_pkg.BookType is libs_enums.BookType
        assert trading_pkg.PositionType is libs_enums.PositionType
        assert trading_pkg.OrderState is libs_enums.OrderState
        assert trading_pkg.DealType is libs_enums.DealType
        assert trading_pkg.DealEntry is libs_enums.DealEntry
        assert trading_pkg.SymbolTradeMode is libs_enums.SymbolTradeMode
        assert trading_pkg.SymbolTradeExecution is libs_enums.SymbolTradeExecution
        assert trading_pkg.SymbolSwapMode is libs_enums.SymbolSwapMode
        assert trading_pkg.SymbolCalcMode is libs_enums.SymbolCalcMode
        assert trading_pkg.ORDER_TYPE_DESCRIPTIONS is libs_enums.ORDER_TYPE_DESCRIPTIONS
        assert (
            trading_pkg.ORDER_FILLING_DESCRIPTIONS
            is libs_enums.ORDER_FILLING_DESCRIPTIONS
        )
        assert trading_pkg.ORDER_TIME_DESCRIPTIONS is libs_enums.ORDER_TIME_DESCRIPTIONS
        assert trading_pkg.BOOK_TYPE_DESCRIPTIONS is libs_enums.BOOK_TYPE_DESCRIPTIONS
        assert (
            trading_pkg.POSITION_TYPE_DESCRIPTIONS
            is libs_enums.POSITION_TYPE_DESCRIPTIONS
        )
        assert (
            trading_pkg.ORDER_STATE_DESCRIPTIONS is libs_enums.ORDER_STATE_DESCRIPTIONS
        )
        assert trading_pkg.DEAL_TYPE_DESCRIPTIONS is libs_enums.DEAL_TYPE_DESCRIPTIONS
        assert trading_pkg.DEAL_ENTRY_DESCRIPTIONS is libs_enums.DEAL_ENTRY_DESCRIPTIONS
        assert (
            trading_pkg.SYMBOL_TRADE_MODE_DESCRIPTIONS
            is libs_enums.SYMBOL_TRADE_MODE_DESCRIPTIONS
        )
        assert (
            trading_pkg.SYMBOL_TRADE_EXECUTION_DESCRIPTIONS
            is libs_enums.SYMBOL_TRADE_EXECUTION_DESCRIPTIONS
        )
        assert trading_pkg.SWAP_MODE_DESCRIPTIONS is libs_enums.SWAP_MODE_DESCRIPTIONS
        assert (
            trading_pkg.SYMBOL_CALC_MODE_DESCRIPTIONS
            is libs_enums.SYMBOL_CALC_MODE_DESCRIPTIONS
        )

    def test_contracts_exports_identity(self) -> None:
        """Verify contract models match between package and contracts submodule."""
        assert trading_pkg.BookInfo is libs_contracts.BookInfo
        assert trading_pkg.AccountInfo is libs_contracts.AccountInfo
        assert trading_pkg.TerminalInfo is libs_contracts.TerminalInfo
        assert trading_pkg.SymbolInfo is libs_contracts.SymbolInfo
        assert trading_pkg.PositionInfo is libs_contracts.PositionInfo
        assert trading_pkg.OrderInfo is libs_contracts.OrderInfo
        assert trading_pkg.DealInfo is libs_contracts.DealInfo
        assert trading_pkg.TradeRequest is libs_contracts.TradeRequest
        assert trading_pkg.TradeResult is libs_contracts.TradeResult
        assert trading_pkg.TradeCheckResult is libs_contracts.TradeCheckResult

    def test_base_exports_identity(self) -> None:
        """Verify base trading proxy class matches between package and submodule."""
        assert trading_pkg.TradingClass is trading_base.TradingClass
        assert trading_pkg.BaseTradingClass is trading_base.BaseTradingClass

    def test_proxies_exports_identity(self) -> None:
        """Verify query proxy classes match between package and submodule."""
        assert trading_pkg.AccountProxy is trading_proxies.AccountProxy
        assert trading_pkg.TerminalProxy is trading_proxies.TerminalProxy
        assert trading_pkg.SymbolProxy is trading_proxies.SymbolProxy
        assert trading_pkg.PositionProxy is trading_proxies.PositionProxy
        assert trading_pkg.OrderProxy is trading_proxies.OrderProxy
        assert trading_pkg.HistoryOrderProxy is trading_proxies.HistoryOrderProxy
        assert trading_pkg.DealProxy is trading_proxies.DealProxy

    def test_trade_exports_identity(self) -> None:
        """Verify trade mutation proxy and builders match between package and submodule."""
        assert trading_pkg.Trade is trading_trade.Trade
        assert (
            trading_pkg._serialize_dict_request is trading_trade._serialize_dict_request
        )
        assert trading_pkg._serialize_request is trading_trade._serialize_request
        assert trading_pkg._build_trade_request is trading_trade._build_trade_request
        assert trading_pkg._build_trade_result is trading_trade._build_trade_result
        assert (
            trading_pkg._build_trade_check_result
            is trading_trade._build_trade_check_result
        )

    def test_facade_exports_identity(self) -> None:
        """Verify master Trading facade matches between package and submodule."""
        assert trading_pkg.Trading is trading_facade.Trading

    def test_all_exports_present_in_package(self) -> None:
        """Ensure every name in __all__ can be resolved from the package."""
        for name in trading_pkg.__all__:
            assert hasattr(trading_pkg, name), f"Missing export: {name}"


class TestLayeringAndAntiCircularRules:
    """Verify architectural layering rules and absence of circular imports."""

    def test_submodules_do_not_import_package_init(self) -> None:
        """Rule 1: Submodules must not import upward from app.services.trading."""
        submodules = [
            trading_base,
            trading_proxies,
            trading_trade,
            trading_facade,
        ]
        for submod in submodules:
            source = inspect.getsource(submod)
            assert "from app.services.trading import" not in source, (
                f"{submod.__name__} violates Rule 1 by importing from package top"
            )
            assert "import app.services.trading\n" not in source, (
                f"{submod.__name__} violates Rule 1 by importing app.services.trading"
            )

    def test_no_backward_compatibility_shim(self) -> None:
        """Verify that legacy modules are completely deleted without shims."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.trading.enums")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.trading.snapshots")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.libs.trading")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.brokers.contracts")
