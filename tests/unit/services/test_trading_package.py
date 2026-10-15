"""Unit tests for the app.services.trading package structure, exports, and layering.

Description:
    Verifies that app.services.trading satisfies the modular package architecture:
    - Layer 0: enums.py
    - Layer 1: snapshots.py, base.py
    - Layer 2: proxies.py, trade.py
    - Layer 3: facade.py
    - Unified package exports via __init__.py
    - Zero circular imports between submodules
    - Complete removal of app.services.libs.trading (no backward compatibility)

Purpose:
    FEAT-TRADING-PACKAGE-TESTS: Verification suite for modular trading package.

Key Capabilities:
    - FR-TRADING-PKG-EXPORTS: Verify public export parity between submodules and package.
    - FR-TRADING-PKG-LAYERING: Verify unidirectional dependencies and anti-circular rules.
    - FR-TRADING-PKG-CLEANUP: Verify deletion of app.services.libs.trading.

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

import app.services.trading as trading_pkg
import app.services.trading.base as trading_base
import app.services.trading.enums as trading_enums
import app.services.trading.facade as trading_facade
import app.services.trading.proxies as trading_proxies
import app.services.trading.snapshots as trading_snapshots
import app.services.trading.trade as trading_trade
import pytest


class TestTradingPackageExports:
    """Verify package-level public exports and submodule parity."""

    def test_enums_exports_identity(self) -> None:
        """Verify enum symbols and descriptions match between package and submodule."""
        assert trading_pkg.ReceiptStatus is trading_enums.ReceiptStatus
        assert trading_pkg.TradeResolution is trading_enums.TradeResolution
        assert trading_pkg.PropertyValue is trading_enums.PropertyValue
        assert trading_pkg.Receipt is trading_enums.Receipt
        assert trading_pkg.BridgeEvent is trading_enums.BridgeEvent
        assert trading_pkg.TradingBackend is trading_enums.TradingBackend
        assert trading_pkg.AccountTradeMode is trading_enums.AccountTradeMode
        assert trading_pkg.StopoutMode is trading_enums.StopoutMode
        assert trading_pkg.MarginMode is trading_enums.MarginMode
        assert trading_pkg.OrderType is trading_enums.OrderType
        assert trading_pkg.OrderFilling is trading_enums.OrderFilling
        assert trading_pkg.OrderTime is trading_enums.OrderTime
        assert trading_pkg.TradeAction is trading_enums.TradeAction
        assert trading_pkg.TradeRetcode is trading_enums.TradeRetcode
        assert trading_pkg.BookType is trading_enums.BookType
        assert (
            trading_pkg.ORDER_TYPE_DESCRIPTIONS is trading_enums.ORDER_TYPE_DESCRIPTIONS
        )
        assert (
            trading_pkg.ORDER_FILLING_DESCRIPTIONS
            is trading_enums.ORDER_FILLING_DESCRIPTIONS
        )
        assert (
            trading_pkg.ORDER_TIME_DESCRIPTIONS is trading_enums.ORDER_TIME_DESCRIPTIONS
        )
        assert (
            trading_pkg.BOOK_TYPE_DESCRIPTIONS is trading_enums.BOOK_TYPE_DESCRIPTIONS
        )

    def test_snapshots_exports_identity(self) -> None:
        """Verify snapshot models match between package and submodule."""
        assert trading_pkg.BookInfo is trading_snapshots.BookInfo
        assert trading_pkg.MqlBookInfo is trading_snapshots.MqlBookInfo
        assert trading_pkg.AccountSnapshot is trading_snapshots.AccountSnapshot
        assert trading_pkg.TerminalSnapshot is trading_snapshots.TerminalSnapshot
        assert trading_pkg.SymbolSnapshot is trading_snapshots.SymbolSnapshot
        assert trading_pkg.PositionSnapshot is trading_snapshots.PositionSnapshot
        assert trading_pkg.OrderSnapshot is trading_snapshots.OrderSnapshot
        assert (
            trading_pkg.HistoryOrderSnapshot is trading_snapshots.HistoryOrderSnapshot
        )
        assert trading_pkg.DealSnapshot is trading_snapshots.DealSnapshot
        assert trading_pkg.TradeRequest is trading_snapshots.TradeRequest
        assert trading_pkg.TradeResult is trading_snapshots.TradeResult
        assert trading_pkg.TradeCheckResult is trading_snapshots.TradeCheckResult

    def test_base_exports_identity(self) -> None:
        """Verify base trading proxy class matches between package and submodule."""
        assert trading_pkg.TradingClass is trading_base.TradingClass
        assert trading_pkg.BaseTradingClass is trading_base.BaseTradingClass

    def test_proxies_exports_identity(self) -> None:
        """Verify query proxy classes match between package and submodule."""
        assert trading_pkg.AccountInfo is trading_proxies.AccountInfo
        assert trading_pkg.TerminalInfo is trading_proxies.TerminalInfo
        assert trading_pkg.SymbolInfo is trading_proxies.SymbolInfo
        assert trading_pkg.PositionInfo is trading_proxies.PositionInfo
        assert trading_pkg.OrderInfo is trading_proxies.OrderInfo
        assert trading_pkg.HistoryOrderInfo is trading_proxies.HistoryOrderInfo
        assert trading_pkg.DealInfo is trading_proxies.DealInfo

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
            trading_enums,
            trading_snapshots,
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
        """Verify that app.services.libs.trading is completely deleted."""
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("app.services.libs.trading")
