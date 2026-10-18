"""Unit tests for the app.services.include.trading module structure and exports.

Description:
    Verifies that app.services.include.trading satisfies the consolidated module architecture:
    - Layer 0: app.services.include.enums
    - Layer 1: app.services.include.contracts
    - Consolidated single-module exports via app.services.include.trading
    - Complete removal of legacy app.services.trading module
    - Zero backward-compatibility shims

Purpose:
    FEAT-TRADING-PACKAGE-TESTS: Verification suite for include trading module.

Key Capabilities:
    - FR-TRADING-PKG-EXPORTS: Verify public exports parity and contract identities.
    - FR-TRADING-PKG-LAYERING: Verify module consolidation and include re-exports.
    - FR-TRADING-PKG-CLEANUP: Verify strict deletion of legacy trading module and shims.

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

import app.services.include as include_pkg
import app.services.include.contracts as include_contracts
import app.services.include.enums as include_enums
import app.services.include.trading as trading_mod
import pytest


class TestTradingModuleExports:
    """Verify module-level public exports and contract parity."""

    def test_enums_exports_identity(self) -> None:
        """Verify enum symbols match between module and enums definition."""
        assert trading_mod.ReceiptStatus is include_enums.ReceiptStatus
        assert trading_mod.TradeResolution is include_enums.TradeResolution
        assert trading_mod.AccountTradeMode is include_enums.AccountTradeMode
        assert trading_mod.StopoutMode is include_enums.StopoutMode
        assert trading_mod.MarginMode is include_enums.MarginMode
        assert trading_mod.OrderType is include_enums.OrderType
        assert trading_mod.OrderFilling is include_enums.OrderFilling
        assert trading_mod.OrderTime is include_enums.OrderTime
        assert trading_mod.TradeAction is include_enums.TradeAction
        assert trading_mod.TradeRetcode is include_enums.TradeRetcode
        assert trading_mod.BookType is include_enums.BookType
        assert trading_mod.PositionType is include_enums.PositionType
        assert trading_mod.OrderState is include_enums.OrderState
        assert trading_mod.DealType is include_enums.DealType
        assert trading_mod.DealEntry is include_enums.DealEntry
        assert trading_mod.SymbolTradeMode is include_enums.SymbolTradeMode
        assert trading_mod.SymbolTradeExecution is include_enums.SymbolTradeExecution
        assert trading_mod.SymbolSwapMode is include_enums.SymbolSwapMode
        assert trading_mod.SymbolCalcMode is include_enums.SymbolCalcMode

    def test_contracts_exports_identity(self) -> None:
        """Verify contract models, bridge types, and descriptions match between module and contracts."""
        assert trading_mod.BookInfo is include_contracts.BookInfo
        assert trading_mod.AccountInfo is include_contracts.AccountInfo
        assert trading_mod.TerminalInfo is include_contracts.TerminalInfo
        assert trading_mod.SymbolInfo is include_contracts.SymbolInfo
        assert trading_mod.PositionInfo is include_contracts.PositionInfo
        assert trading_mod.OrderInfo is include_contracts.OrderInfo
        assert trading_mod.DealInfo is include_contracts.DealInfo
        assert trading_mod.TradeRequest is include_contracts.TradeRequest
        assert trading_mod.TradeResult is include_contracts.TradeResult
        assert trading_mod.TradeCheckResult is include_contracts.TradeCheckResult
        assert trading_mod.PropertyValue is include_contracts.PropertyValue
        assert trading_mod.Receipt is include_contracts.Receipt
        assert trading_mod.BridgeEvent is include_contracts.BridgeEvent
        assert trading_mod.TradingBackend is include_contracts.TradingBackend
        assert (
            trading_mod.ORDER_TYPE_DESCRIPTIONS
            is include_contracts.ORDER_TYPE_DESCRIPTIONS
        )
        assert (
            trading_mod.ORDER_FILLING_DESCRIPTIONS
            is include_contracts.ORDER_FILLING_DESCRIPTIONS
        )
        assert (
            trading_mod.ORDER_TIME_DESCRIPTIONS
            is include_contracts.ORDER_TIME_DESCRIPTIONS
        )
        assert (
            trading_mod.BOOK_TYPE_DESCRIPTIONS
            is include_contracts.BOOK_TYPE_DESCRIPTIONS
        )
        assert (
            trading_mod.POSITION_TYPE_DESCRIPTIONS
            is include_contracts.POSITION_TYPE_DESCRIPTIONS
        )
        assert (
            trading_mod.ORDER_STATE_DESCRIPTIONS
            is include_contracts.ORDER_STATE_DESCRIPTIONS
        )
        assert (
            trading_mod.DEAL_TYPE_DESCRIPTIONS
            is include_contracts.DEAL_TYPE_DESCRIPTIONS
        )
        assert (
            trading_mod.DEAL_ENTRY_DESCRIPTIONS
            is include_contracts.DEAL_ENTRY_DESCRIPTIONS
        )
        assert (
            trading_mod.SYMBOL_TRADE_MODE_DESCRIPTIONS
            is include_contracts.SYMBOL_TRADE_MODE_DESCRIPTIONS
        )
        assert (
            trading_mod.SYMBOL_TRADE_EXECUTION_DESCRIPTIONS
            is include_contracts.SYMBOL_TRADE_EXECUTION_DESCRIPTIONS
        )
        assert (
            trading_mod.SYMBOL_SWAP_MODE_DESCRIPTIONS
            is include_contracts.SYMBOL_SWAP_MODE_DESCRIPTIONS
        )
        assert (
            trading_mod.SYMBOL_CALC_MODE_DESCRIPTIONS
            is include_contracts.SYMBOL_CALC_MODE_DESCRIPTIONS
        )
        assert trading_mod.SymbolInfo is include_contracts.SymbolInfo
        assert trading_mod.PositionInfo is include_contracts.PositionInfo
        assert trading_mod.OrderInfo is include_contracts.OrderInfo
        assert trading_mod.DealInfo is include_contracts.DealInfo
        assert trading_mod.TradeRequest is include_contracts.TradeRequest
        assert trading_mod.TradeResult is include_contracts.TradeResult
        assert trading_mod.TradeCheckResult is include_contracts.TradeCheckResult

    def test_base_exports_identity(self) -> None:
        """Verify base trading proxy classes exist and are identical."""
        assert issubclass(trading_mod.TradingClass, object)
        assert trading_mod.BaseTradingClass is trading_mod.TradingClass

    def test_proxies_exports_identity(self) -> None:
        """Verify query proxy classes exist and subclass TradingClass."""
        for proxy_cls in (
            trading_mod.AccountProxy,
            trading_mod.TerminalProxy,
            trading_mod.SymbolProxy,
            trading_mod.PositionProxy,
            trading_mod.OrderProxy,
            trading_mod.HistoryOrderProxy,
            trading_mod.DealProxy,
        ):
            assert issubclass(proxy_cls, trading_mod.TradingClass)

    def test_trade_exports_identity(self) -> None:
        """Verify trade mutation proxy and builders exist and subclass TradingClass."""
        assert issubclass(trading_mod.Trade, trading_mod.TradingClass)
        assert callable(trading_mod._serialize_dict_request)
        assert callable(trading_mod._serialize_request)
        assert callable(trading_mod._build_trade_request)
        assert callable(trading_mod._build_trade_result)
        assert callable(trading_mod._build_trade_check_result)

    def test_facade_exports_identity(self) -> None:
        """Verify master Trading facade exists and is a class."""
        assert inspect.isclass(trading_mod.Trading)

    def test_all_exports_present_in_module(self) -> None:
        """Ensure every name in __all__ can be resolved from the module."""
        for name in trading_mod.__all__:
            assert hasattr(trading_mod, name), f"Missing export: {name}"
        assert len(trading_mod.__all__) == 61

    def test_include_package_reexports_trading(self) -> None:
        """Verify that app.services.include package re-exports Trading facade and proxies."""
        assert include_pkg.Trading is trading_mod.Trading
        assert include_pkg.Trade is trading_mod.Trade
        assert include_pkg.TradingClass is trading_mod.TradingClass
        assert include_pkg.BaseTradingClass is trading_mod.BaseTradingClass
        assert include_pkg.AccountProxy is trading_mod.AccountProxy
        assert include_pkg.SymbolProxy is trading_mod.SymbolProxy
        assert include_pkg.PositionProxy is trading_mod.PositionProxy
        assert include_pkg.OrderProxy is trading_mod.OrderProxy
        assert include_pkg.HistoryOrderProxy is trading_mod.HistoryOrderProxy
        assert include_pkg.DealProxy is trading_mod.DealProxy
        assert include_pkg.TerminalProxy is trading_mod.TerminalProxy


class TestModuleConsolidationAndNoShims:
    """Verify architectural consolidation and absence of lingering submodules."""

    def test_trading_legacy_module_cannot_be_imported(self) -> None:
        """Verify that former app.services.trading cannot be imported."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.trading")

    def test_submodules_cannot_be_imported(self) -> None:
        """Verify that former package submodules cannot be imported."""
        for submod_name in (
            "app.services.trading.base",
            "app.services.trading.proxies",
            "app.services.trading.trade",
            "app.services.trading.facade",
        ):
            with pytest.raises(ModuleNotFoundError):
                importlib.import_module(submod_name)

    def test_no_backward_compatibility_shim(self) -> None:
        """Verify that legacy modules are completely deleted without shims."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.trading.enums")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.trading.snapshots")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.libs")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.libs.trading")
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.brokers.contracts")
