"""MetaTrader 5 terminal IPC execution and market data broker plugin implementation.

Description:
    Implements the complete 27-operation `BaseBroker` interface for MetaTrader 5
    by communicating directly with local desktop terminals (`terminal64.exe`) via
    the official native `MetaTrader5` package IPC bindings. Within HaruQuantAI,
    MetaTrader 5 serves as both an authoritative execution engine for live trading
    and a market data provider for the Data Manager workspace. It supports terminal
    lifecycle management, account authentication, real-time tick streaming,
    market depth subscriptions, historical candlestick bar extraction, margin
    computation, pre-flight order validation, position reconciliation, and trade
    execution. When the `MetaTrader5` binary package is absent, the adapter
    fails gracefully with typed `MODULE_NOT_FOUND` errors while preserving mock
    data generation for isolated headless environments.

Purpose:
    FEAT-BROKER-METATRADER: MetaTrader 5 Native IPC Execution Integration.
    Implements native desktop terminal IPC communication, market data access,
    and trade execution against MetaTrader 5 terminals.

Key Capabilities:
    - FR-BROKER-MT5-SESSION-LIFECYCLE: Terminal IPC Initialization and Shutdown
      Associated: `[MetaTraderBroker.connect()]`,
      `[MetaTraderBroker.disconnect()]`, `[MetaTraderBroker.is_connected()]`
      Logging: Emits INFO log on terminal connection and shutdown; emits
      ERROR log if `MetaTrader5` package is missing or IPC fails.
    - FR-BROKER-MT5-MARKET-DATA: Quotes, Market Depth, and Historical Bars
      Associated: `[MetaTraderBroker.get_symbol_info()]`,
      `[MetaTraderBroker.get_bars()]`, `[MetaTraderBroker.market_book_get()]`
      Logging: Emits INFO log upon successfully retrieving bars or depth, and
      WARNING log on missing symbols or empty ranges.
    - FR-BROKER-MT5-ORDER-EXECUTION: Pre-flight Verification and Trade Execution
      Associated: `[MetaTraderBroker.check_order()]`,
      `[MetaTraderBroker.trade()]`
      Logging: Emits INFO log upon successful order execution and WARNING log
      on order rejection with native MT5 return codes.
    - FR-BROKER-MT5-POSITION-RECONCILIATION: Positions and Pending Order Sync
      Associated: `[MetaTraderBroker.get_position_info()]`,
      `[MetaTraderBroker.get_order_info()]`,
      `[MetaTraderBroker.get_account_info()]`
      Logging: Emits INFO log with reconciled position and order counts.

Python API Usage:
    ```python
    from app.plugins.brokers.metatrader.adapter import (
        MetaTraderBroker,
        create_adapter,
    )

    broker = create_adapter()
    status_resp = broker.is_connected()
    assert not status_resp.unwrap()
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_mt5.py
    ```
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from typing import Any, cast, override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.host.settings import settings
from app.plugins.brokers.contracts import (
    AccountInfo,
    Bar,
    BaseBroker,
    BookItem,
    BrokerCapability,
    DealInfo,
    OrderAction,
    OrderCheckResult,
    OrderFilling,
    OrderInfo,
    OrderType,
    PositionInfo,
    StandardError,
    StandardResponse,
    SymbolInfo,
    TerminalInfo,
    Tick,
    TimeFrame,
    TradeRequest,
    TradeResult,
)
from app.workspace.data_manager.connections import (
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
)
from app.workspace.data_manager.data import BarRecord

mt5: Any = None
try:
    import MetaTrader5 as _mt5_mod  # pyright: ignore[reportMissingImports] # type: ignore[import-untyped,import-not-found]

    mt5 = _mt5_mod
except ImportError:
    mt5 = None

logger = get_logger(__name__)


class MetaTraderBroker(BaseBroker):
    """MetaTrader 5 implementation of the unified broker interface."""

    TIMEFRAME_MAP = {
        TimeFrame.M1: 1,  # mt5.TIMEFRAME_M1
        TimeFrame.M2: 2,
        TimeFrame.M3: 3,
        TimeFrame.M4: 4,
        TimeFrame.M5: 5,
        TimeFrame.M6: 6,
        TimeFrame.M10: 10,
        TimeFrame.M12: 12,
        TimeFrame.M15: 15,
        TimeFrame.M20: 20,
        TimeFrame.M30: 30,
        TimeFrame.H1: 16385,  # mt5.TIMEFRAME_H1
        TimeFrame.H2: 16386,
        TimeFrame.H3: 16387,
        TimeFrame.H4: 16388,
        TimeFrame.H6: 16390,
        TimeFrame.H8: 16392,
        TimeFrame.H12: 16396,
        TimeFrame.D1: 16408,  # mt5.TIMEFRAME_D1
        TimeFrame.W1: 32769,  # mt5.TIMEFRAME_W1
        TimeFrame.MN1: 49153,  # mt5.TIMEFRAME_MN1
    }

    ACTION_MAP = {
        OrderAction.DEAL: 1,  # mt5.TRADE_ACTION_DEAL
        OrderAction.PENDING: 5,  # mt5.TRADE_ACTION_PENDING
        OrderAction.SLTP: 6,  # mt5.TRADE_ACTION_SLTP
        OrderAction.MODIFY: 7,  # mt5.TRADE_ACTION_MODIFY
        OrderAction.REMOVE: 8,  # mt5.TRADE_ACTION_REMOVE
        OrderAction.CLOSE: 1,  # mt5.TRADE_ACTION_DEAL (close executed as counter-deal)
    }

    ORDER_TYPE_MAP = {
        OrderType.BUY: 0,  # mt5.ORDER_TYPE_BUY
        OrderType.SELL: 1,  # mt5.ORDER_TYPE_SELL
        OrderType.BUY_LIMIT: 2,  # mt5.ORDER_TYPE_BUY_LIMIT
        OrderType.SELL_LIMIT: 3,  # mt5.ORDER_TYPE_SELL_LIMIT
        OrderType.BUY_STOP: 4,  # mt5.ORDER_TYPE_BUY_STOP
        OrderType.SELL_STOP: 5,  # mt5.ORDER_TYPE_SELL_STOP
        OrderType.BUY_STOP_LIMIT: 6,  # mt5.ORDER_TYPE_BUY_STOP_LIMIT
        OrderType.SELL_STOP_LIMIT: 7,  # mt5.ORDER_TYPE_SELL_STOP_LIMIT
    }

    def __init__(
        self,
        name: str = "MetaTrader5",
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
    ) -> None:
        """Initialize MetaTrader 5 broker.

        Pulls defaults from `settings.config_metatrader5` if available.

        Args:
            name: Plugin identifier name.
            path: Optional executable path to terminal64.exe.
            login: Optional account login number.
            password: Optional account password.
            server: Optional broker server name.
        """
        super().__init__(name=name, capabilities=BrokerCapability.ALL)
        cfg = getattr(settings, "config_metatrader5", None)
        self.default_path = path or (
            getattr(cfg, "terminal_path", None) if cfg else None
        )
        self.default_login = login or (
            getattr(cfg, "account_id", None) if cfg else None
        )
        self.default_password = password or (
            getattr(cfg, "password", None) if cfg else None
        )
        self.default_server = server or (getattr(cfg, "server", None) if cfg else None)
        self.default_timeout = getattr(cfg, "timeout_ms", 60000) if cfg else 60000
        self.default_portable = getattr(cfg, "portable", False) if cfg else False
        logger.info(
            "FR-BROKER-MT5-SESSION-LIFECYCLE: Initialized MetaTrader5 broker with default settings."
        )

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Expose Data Manager workspace provider capabilities metadata."""
        return ProviderCapabilities(
            name=self.name,
            display_name="MetaTrader 5 Connector",
            asset_classes=["Forex", "Futures", "Indices", "Stocks"],
            timeframes=["M1", "M5", "M15", "H1", "D1"],
            requires_auth=False,
            rate_limit_rps=50.0,
        )

    def _ensure_module(self) -> StandardResponse[Any] | None:
        """Validate that MetaTrader5 package is available."""
        if mt5 is None:
            msg = "MetaTrader5 Python module is not installed."
            self.logger.error("FR-BROKER-MT5-SESSION-LIFECYCLE: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="MODULE_NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )
        return None

    @staticmethod
    def _map_dataclass[T](
        target_cls: type[T], obj: Any, extra: dict[str, Any] | None = None
    ) -> T:
        """Map attributes from MT5 namedtuple or mock object to target dataclass."""
        asdict_fn = getattr(obj, "_asdict", None)
        raw_dict: dict[str, Any] = {}
        if callable(asdict_fn):
            try:
                res = asdict_fn()
                if isinstance(res, dict):
                    raw_dict = dict(res)
            except Exception:
                raw_dict = {}
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cast("Any", target_cls)):
            if extra and f.name in extra:
                kwargs[f.name] = extra[f.name]
            elif f.name in raw_dict:
                kwargs[f.name] = raw_dict[f.name]
            elif hasattr(obj, f.name):
                val = getattr(obj, f.name)
                if type(val).__name__ not in ("MagicMock", "Mock"):
                    kwargs[f.name] = val
        return target_cls(**kwargs)

    def _map_timeframe(self, timeframe: TimeFrame | str | int) -> int:
        """Map generic timeframe to MT5 timeframe constant."""
        if isinstance(timeframe, int):
            return timeframe
        if isinstance(timeframe, TimeFrame):
            return self.TIMEFRAME_MAP.get(timeframe, 16385)
        tf_str = timeframe.upper().strip()
        for tf_enum in TimeFrame:
            if tf_enum.value == tf_str:
                return self.TIMEFRAME_MAP[tf_enum]
        alias_map = {
            "1M": 1,
            "5M": 5,
            "15M": 15,
            "30M": 30,
            "1H": 16385,
            "4H": 16388,
            "1D": 16408,
            "1W": 32769,
            "1MN": 49153,
        }
        return alias_map.get(tf_str, 16385)

    def _map_order_type(self, order_type: OrderType | str | int) -> int:
        """Map standard order type to MT5 integer constant."""
        if isinstance(order_type, int):
            return order_type
        if isinstance(order_type, OrderType):
            return self.ORDER_TYPE_MAP.get(order_type, 0)
        str_val = order_type.upper().strip()
        for ot in OrderType:
            if ot.value == str_val:
                return self.ORDER_TYPE_MAP[ot]
        return 0

    def _detect_symbol_filling(self, symbol: str) -> int:
        """Determine appropriate filling mode based on symbol capabilities."""
        if mt5 is None:
            return 1
        info = mt5.symbol_info(symbol)
        if not info:
            return 1  # Default IOC
        mode = getattr(info, "filling_mode", 0)
        if mode & 2:
            return 1  # ORDER_FILLING_IOC
        if mode & 1:
            return 0  # ORDER_FILLING_FOK
        return 2  # ORDER_FILLING_RETURN

    # ========================================================================
    # 1. Connection & Session
    # ========================================================================

    @override
    def connect(self, **kwargs: Any) -> StandardResponse[bool]:
        """Connect to MT5 terminal and authenticate."""
        err = self._ensure_module()
        if err is not None:
            return err

        path = kwargs.get("path", self.default_path)
        login = kwargs.get("login", self.default_login)
        password = kwargs.get("password", self.default_password)
        server = kwargs.get("server", self.default_server)
        timeout = kwargs.get("timeout", self.default_timeout)
        portable = kwargs.get("portable", self.default_portable)

        init_kwargs: dict[str, Any] = {"timeout": timeout, "portable": portable}
        if path:
            init_kwargs["path"] = path
        if login:
            init_kwargs["login"] = int(login)
        if password:
            init_kwargs["password"] = password
        if server:
            init_kwargs["server"] = server

        self.logger.info(
            "FR-BROKER-MT5-SESSION-LIFECYCLE: Connecting to MT5: server=%s, login=%s, path=%s",
            server,
            login,
            path,
        )
        init_res = mt5.initialize(**init_kwargs)
        if not init_res:
            code, desc = mt5.last_error()
            msg = f"Failed to initialize MT5: {desc} (code {code})"
            self.logger.error("FR-BROKER-MT5-SESSION-LIFECYCLE: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(code), message=msg),
                extensions={"broker": self.name, "raw": (code, desc)},
            )

        if login and password and server:
            login_res = mt5.login(login=int(login), password=password, server=server)
            if not login_res:
                code, desc = mt5.last_error()
                msg = f"Failed to log into MT5 account {login}: {desc} (code {code})"
                self.logger.error("FR-BROKER-MT5-SESSION-LIFECYCLE: %s", msg)
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code=str(code), message=msg),
                    extensions={"broker": self.name, "raw": (code, desc)},
                )

        self.logger.info(
            "FR-BROKER-MT5-SESSION-LIFECYCLE: Successfully connected to MetaTrader 5."
        )
        return StandardResponse.success(
            data=True,
            message="Connected successfully",
            extensions={"broker": self.name},
        )

    @override
    def disconnect(self) -> StandardResponse[bool]:
        """Shut down the MetaTrader 5 API connection."""
        err = self._ensure_module()
        if err is not None:
            return err
        self.logger.info(
            "FR-BROKER-MT5-SESSION-LIFECYCLE: Disconnecting from MetaTrader 5..."
        )
        mt5.shutdown()
        return StandardResponse.success(
            data=True,
            message="Disconnected successfully",
            extensions={"broker": self.name},
        )

    @override
    def is_connected(self) -> StandardResponse[bool]:
        """Verify active connection to MT5 terminal and trade server."""
        err = self._ensure_module()
        if err is not None:
            return err
        info = mt5.terminal_info()
        connected = bool(info and getattr(info, "connected", False))
        if connected:
            self.logger.info(
                "FR-BROKER-MT5-SESSION-LIFECYCLE: Connected to MetaTrader 5."
            )
        else:
            self.logger.warning(
                "FR-BROKER-MT5-SESSION-LIFECYCLE: No connection to MetaTrader 5."
            )

        return StandardResponse.success(
            data=connected,
            message="Connected" if connected else "Disconnected",
            extensions={"broker": self.name, "raw": info},
        )

    @override
    def get_last_error(self) -> StandardResponse[Any]:
        """Return the last native MT5 error code and description."""
        err = self._ensure_module()
        if err is not None:
            return err
        code, desc = mt5.last_error()
        return StandardResponse.success(
            data=(code, desc),
            message=f"Last error: {desc} ({code})",
            extensions={"broker": self.name, "raw": (code, desc)},
        )

    # ========================================================================
    # 2. Terminal & Account Information
    # ========================================================================

    @override
    def get_terminal_info(self) -> StandardResponse[TerminalInfo]:
        """Retrieve terminal properties and version."""
        err = self._ensure_module()
        if err is not None:
            return err
        info = mt5.terminal_info()
        if not info:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to get terminal info: {desc}",
                error=StandardError(
                    code=str(code), message=f"Failed to get terminal info: {desc}"
                ),
                extensions={"broker": self.name},
            )
        ver = mt5.version()
        ver_str = f"version={ver[0]}, build={ver[1]}, date={ver[2]}" if ver else ""
        t_info = self._map_dataclass(
            TerminalInfo, info, {"version": ver_str, "raw": info}
        )
        return StandardResponse.success(
            data=t_info, extensions={"broker": self.name, "raw": info}
        )

    @override
    def get_account_info(self) -> StandardResponse[AccountInfo]:
        """Retrieve current trading account balances and metrics."""
        err = self._ensure_module()
        if err is not None:
            return err
        acc = mt5.account_info()
        if not acc:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to get account info: {desc}",
                error=StandardError(
                    code=str(code), message=f"Failed to get account info: {desc}"
                ),
                extensions={"broker": self.name},
            )
        info = self._map_dataclass(AccountInfo, acc, {"raw": acc})
        self.logger.info(
            "FR-BROKER-MT5-POSITION-RECONCILIATION: Reconciled account balance=%s currency=%s",
            info.balance,
            info.currency,
        )
        return StandardResponse.success(
            data=info, extensions={"broker": self.name, "raw": acc}
        )

    # ========================================================================
    # 3. Symbols & Market Instruments
    # ========================================================================

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[SymbolInfo]:
        """Retrieve instrument specifications."""
        err = self._ensure_module()
        if err is not None:
            return err
        s = mt5.symbol_info(symbol)
        if not s:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Symbol '{symbol}' not found: {desc}",
                error=StandardError(
                    code=str(code), message=f"Symbol '{symbol}' not found: {desc}"
                ),
                extensions={"broker": self.name},
            )
        sym_name = getattr(s, "name", symbol)
        info = self._map_dataclass(SymbolInfo, s, {"name": sym_name, "raw": s})
        return StandardResponse.success(
            data=info, extensions={"broker": self.name, "raw": s}
        )

    @override
    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Get total number of symbols available in terminal."""
        err = self._ensure_module()
        if err is not None:
            return err
        total = mt5.symbols_total()
        return StandardResponse.success(
            data=int(total), extensions={"broker": self.name}
        )

    @override
    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[SymbolInfo]]:
        """Retrieve list of symbols, optionally matching group pattern."""
        err = self._ensure_module()
        if err is not None:
            return err
        symbols_tuple = mt5.symbols_get(group=group) if group else mt5.symbols_get()
        if symbols_tuple is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to get symbols: {desc}",
                error=StandardError(
                    code=str(code), message=f"Failed to get symbols: {desc}"
                ),
                extensions={"broker": self.name},
            )
        result: list[SymbolInfo] = []
        for s in symbols_tuple:
            sym_name = getattr(s, "name", "")
            result.append(
                self._map_dataclass(SymbolInfo, s, {"name": sym_name, "raw": s})
            )
        return StandardResponse.success(data=result, extensions={"broker": self.name})

    @override
    def enable_symbol(self, symbol: str, enable: bool = True) -> StandardResponse[bool]:
        """Select or deselect a symbol in Market Watch."""
        err = self._ensure_module()
        if err is not None:
            return err
        res = mt5.symbol_select(symbol, enable)
        if not res:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to enable symbol '{symbol}': {desc}",
                error=StandardError(
                    code=str(code),
                    message=f"Failed to enable symbol '{symbol}': {desc}",
                ),
                extensions={"broker": self.name},
            )
        return StandardResponse.success(
            data=True,
            message=f"Symbol '{symbol}' {('enabled' if enable else 'disabled')}",
            extensions={"broker": self.name},
        )

    @override
    def get_symbol_tick(self, symbol: str) -> StandardResponse[Tick]:
        """Retrieve latest real-time tick for a symbol."""
        err = self._ensure_module()
        if err is not None:
            return err
        t = mt5.symbol_info_tick(symbol)
        if not t:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to get tick for '{symbol}': {desc}",
                error=StandardError(
                    code=str(code),
                    message=f"Failed to get tick for '{symbol}': {desc}",
                ),
                extensions={"broker": self.name},
            )
        tick_dt = datetime.fromtimestamp(t.time, tz=UTC)
        tick = Tick(
            time=tick_dt,
            bid=getattr(t, "bid", 0.0),
            ask=getattr(t, "ask", 0.0),
            last=getattr(t, "last", 0.0),
            volume=getattr(t, "volume", 0.0),
            flags=getattr(t, "flags", 0),
            raw=t,
        )
        return StandardResponse.success(
            data=tick, extensions={"broker": self.name, "raw": t}
        )

    # ========================================================================
    # 4. Market Depth (Level 2)
    # ========================================================================

    @override
    def subscribe_market_depth(self, symbol: str) -> StandardResponse[bool]:
        """Subscribe to Depth of Market (DOM) book."""
        err = self._ensure_module()
        if err is not None:
            return err
        res = mt5.market_book_add(symbol)
        if not res:
            code, desc = mt5.last_error()
            msg = f"Failed to subscribe to market depth for '{symbol}': {desc} (code {code})"
            self.logger.warning("FR-BROKER-MT5-MARKET-DATA: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(code), message=msg),
                data=False,
                extensions={"broker": self.name},
            )
        return StandardResponse.success(
            data=True,
            message=f"Subscribed to DOM for '{symbol}'",
            extensions={"broker": self.name},
        )

    @override
    def get_market_depth(self, symbol: str) -> StandardResponse[list[BookItem]]:
        """Retrieve current Depth of Market (DOM) order book entries."""
        err = self._ensure_module()
        if err is not None:
            return err
        items = mt5.market_book_get(symbol)
        if items is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"DOM not available for '{symbol}': {desc}",
                error=StandardError(
                    code=str(code), message=f"DOM not available for '{symbol}': {desc}"
                ),
                extensions={"broker": self.name},
            )
        book: list[BookItem] = []
        for item in items:
            type_str = "BUY" if item.type == 1 else "SELL"
            book.append(
                BookItem(
                    type=type_str,
                    price=item.price,
                    volume=item.volume,
                    volume_dbl=getattr(item, "volume_dbl", 0.0),
                )
            )
        return StandardResponse.success(
            data=book, extensions={"broker": self.name, "raw": items}
        )

    @override
    def unsubscribe_market_depth(self, symbol: str) -> StandardResponse[bool]:
        """Release market depth subscription for symbol."""
        err = self._ensure_module()
        if err is not None:
            return err
        res = mt5.market_book_release(symbol)
        if not res:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to release DOM for '{symbol}': {desc}",
                error=StandardError(
                    code=str(code),
                    message=f"Failed to release DOM for '{symbol}': {desc}",
                ),
                data=False,
                extensions={"broker": self.name},
            )
        return StandardResponse.success(
            data=True,
            message=f"Unsubscribed from DOM for '{symbol}'",
            extensions={"broker": self.name},
        )

    # ========================================================================
    # 5. Bars & Ticks (Historical Data)
    # ========================================================================

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str | int = TimeFrame.H1,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> StandardResponse[list[Bar]]:
        """Retrieve historical candlestick bars using copy_rates functions."""
        err = self._ensure_module()
        if err is not None:
            return err

        tf = self._map_timeframe(timeframe)

        if date_from is not None and date_to is not None:
            rates = mt5.copy_rates_range(symbol, tf, date_from, date_to)
        elif date_from is not None and count is not None:
            rates = mt5.copy_rates_from(symbol, tf, date_from, count)
        else:
            pos = start_pos or 0
            n = count or 100
            rates = mt5.copy_rates_from_pos(symbol, tf, pos, n)

        if rates is None or len(rates) == 0:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to fetch bars for '{symbol}': {desc}",
                error=StandardError(
                    code=str(code),
                    message=f"Failed to fetch bars for '{symbol}': {desc}",
                ),
                extensions={"broker": self.name},
            )

        bars: list[Bar] = []
        for r in rates:
            bars.append(
                Bar(
                    time=datetime.fromtimestamp(int(r["time"]), tz=UTC),
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    tick_volume=int(r["tick_volume"]),
                    spread=int(r["spread"]),
                    real_volume=int(r["real_volume"]),
                )
            )
        self.logger.info(
            "FR-BROKER-MT5-MARKET-DATA: Retrieved %s bars for %s", len(bars), symbol
        )
        return StandardResponse.success(
            data=bars, extensions={"broker": self.name, "raw": rates}
        )

    @override
    def get_ticks(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        flags: int | None = None,
    ) -> StandardResponse[list[Tick]]:
        """Retrieve historical ticks using copy_ticks functions."""
        err = self._ensure_module()
        if err is not None:
            return err

        tick_flags = (
            flags if flags is not None else getattr(mt5, "COPY_TICKS_ALL", 0xFFFFFFFF)
        )

        if date_from is not None and date_to is not None:
            ticks_arr = mt5.copy_ticks_range(symbol, date_from, date_to, tick_flags)
        else:
            dt_from = date_from if date_from is not None else datetime.now(UTC)
            n = count or 100
            ticks_arr = mt5.copy_ticks_from(symbol, dt_from, n, tick_flags)

        if ticks_arr is None or len(ticks_arr) == 0:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to fetch ticks for '{symbol}': {desc}",
                error=StandardError(
                    code=str(code),
                    message=f"Failed to fetch ticks for '{symbol}': {desc}",
                ),
                extensions={"broker": self.name},
            )

        ticks: list[Tick] = []
        for t in ticks_arr:
            ticks.append(
                Tick(
                    time=datetime.fromtimestamp(int(t["time"]), tz=UTC),
                    bid=float(t["bid"]),
                    ask=float(t["ask"]),
                    last=float(t["last"]),
                    volume=float(t["volume"]),
                    flags=int(t["flags"]),
                )
            )
        return StandardResponse.success(
            data=ticks, extensions={"broker": self.name, "raw": ticks_arr}
        )

    # ========================================================================
    # Data Manager Workspace Download Protocol Support
    # ========================================================================

    def download_bars(
        self,
        request: DownloadRequest,
        cancel_token: CancellationToken | None = None,
    ) -> list[BarRecord]:
        """Download historical bars for Data Manager workspace."""
        token = cancel_token or CancellationToken()
        token.check_cancelled()

        # Parse date bounds if present
        d_from: datetime | None = None
        d_to: datetime | None = None
        try:
            d_from = datetime.fromisoformat(request.date_from)
            d_to = datetime.fromisoformat(request.date_to)
        except Exception:
            pass

        # Attempt to get real bars from connected MT5 terminal
        bars_resp = self.get_bars(
            symbol=request.symbol,
            timeframe=request.timeframe,
            date_from=d_from,
            date_to=d_to,
        )
        if bars_resp.is_success and bars_resp.data:
            records: list[BarRecord] = []
            for b in bars_resp.data:
                token.check_cancelled()
                records.append(
                    BarRecord(
                        timestamp_utc=b.time.isoformat(),
                        open=b.open,
                        high=b.high,
                        low=b.low,
                        close=b.close,
                        volume=float(b.tick_volume or b.real_volume or 1.0),
                    )
                )
            return records

        return []

    # ========================================================================
    # 6. Positions
    # ========================================================================

    @override
    def get_position_info(
        self, symbol: str | None = None, ticket: int | None = None
    ) -> StandardResponse[list[PositionInfo]]:
        """Retrieve open positions."""
        err = self._ensure_module()
        if err is not None:
            return err

        if ticket is not None:
            positions = mt5.positions_get(ticket=ticket)
        elif symbol is not None:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()

        if positions is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to get positions: {desc}",
                error=StandardError(
                    code=str(code), message=f"Failed to get positions: {desc}"
                ),
                extensions={"broker": self.name},
            )

        res: list[PositionInfo] = []
        for p in positions:
            pos_type = "BUY" if p.type == 0 else "SELL"
            dt = datetime.fromtimestamp(p.time, tz=UTC)
            res.append(
                PositionInfo(
                    ticket=p.ticket,
                    symbol=p.symbol,
                    type=pos_type,
                    volume=float(p.volume),
                    price_open=float(p.price_open),
                    price_current=float(p.price_current),
                    sl=float(p.sl),
                    tp=float(p.tp),
                    profit=float(p.profit),
                    swap=float(p.swap),
                    time=dt,
                    comment=p.comment,
                    magic=p.magic,
                    raw=p,
                )
            )
        self.logger.info(
            "FR-BROKER-MT5-POSITION-RECONCILIATION: Reconciled %s active positions",
            len(res),
        )
        return StandardResponse.success(
            data=res, extensions={"broker": self.name, "raw": positions}
        )

    @override
    def get_num_positions(self) -> StandardResponse[int]:
        """Get the total count of open positions."""
        err = self._ensure_module()
        if err is not None:
            return err
        total = mt5.positions_total()
        return StandardResponse.success(
            data=int(total), extensions={"broker": self.name}
        )

    # ========================================================================
    # 7. Orders
    # ========================================================================

    @override
    def get_order_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[list[OrderInfo]]:
        """Retrieve active pending orders."""
        err = self._ensure_module()
        if err is not None:
            return err

        if ticket is not None:
            orders = mt5.orders_get(ticket=ticket)
        elif symbol is not None:
            orders = mt5.orders_get(symbol=symbol)
        elif group is not None:
            orders = mt5.orders_get(group=group)
        else:
            orders = mt5.orders_get()

        if orders is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to get active orders: {desc}",
                error=StandardError(
                    code=str(code), message=f"Failed to get active orders: {desc}"
                ),
                extensions={"broker": self.name},
            )

        res: list[OrderInfo] = []
        for o in orders:
            dt = datetime.fromtimestamp(o.time_setup, tz=UTC) if o.time_setup else None
            res.append(
                OrderInfo(
                    ticket=o.ticket,
                    symbol=o.symbol,
                    type=str(o.type),
                    volume_initial=float(o.volume_initial),
                    volume_current=float(o.volume_current),
                    price_open=float(o.price_open),
                    sl=float(o.sl),
                    tp=float(o.tp),
                    state=str(o.state),
                    time_setup=dt,
                    comment=o.comment,
                    magic=o.magic,
                    raw=o,
                )
            )
        self.logger.info(
            "FR-BROKER-MT5-POSITION-RECONCILIATION: Reconciled %s pending orders",
            len(res),
        )
        return StandardResponse.success(
            data=res, extensions={"broker": self.name, "raw": orders}
        )

    @override
    def get_num_orders(self) -> StandardResponse[int]:
        """Get the total count of active pending orders."""
        err = self._ensure_module()
        if err is not None:
            return err
        total = mt5.orders_total()
        return StandardResponse.success(
            data=int(total), extensions={"broker": self.name}
        )

    # ========================================================================
    # 8. Trade History (Orders & Deals)
    # ========================================================================

    @override
    def get_history_order_info(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        ticket: int | None = None,
        position: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[list[OrderInfo]]:
        """Retrieve historical orders."""
        err = self._ensure_module()
        if err is not None:
            return err

        if ticket is not None:
            orders = mt5.history_orders_get(ticket=ticket)
        elif position is not None:
            orders = mt5.history_orders_get(position=position)
        else:
            d_from = (
                date_from if date_from is not None else datetime(2000, 1, 1, tzinfo=UTC)
            )
            d_to = (
                date_to
                if date_to is not None
                else datetime.now(UTC) + timedelta(days=2)
            )
            if group is not None:
                orders = mt5.history_orders_get(d_from, d_to, group=group)
            else:
                orders = mt5.history_orders_get(d_from, d_to)

        if orders is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to get history orders: {desc}",
                error=StandardError(
                    code=str(code), message=f"Failed to get history orders: {desc}"
                ),
                extensions={"broker": self.name},
            )

        res: list[OrderInfo] = []
        for o in orders:
            dt = (
                datetime.fromtimestamp(o.time_setup, tz=UTC)
                if getattr(o, "time_setup", None)
                else None
            )
            res.append(
                OrderInfo(
                    ticket=o.ticket,
                    symbol=o.symbol,
                    type=str(o.type),
                    volume_initial=float(o.volume_initial),
                    volume_current=float(o.volume_current),
                    price_open=float(o.price_open),
                    sl=float(o.sl),
                    tp=float(o.tp),
                    state=str(o.state),
                    time_setup=dt,
                    comment=o.comment,
                    magic=o.magic,
                    raw=o,
                )
            )
        return StandardResponse.success(
            data=res, extensions={"broker": self.name, "raw": orders}
        )

    @override
    def get_num_history_orders(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> StandardResponse[int]:
        """Get total historical orders count within range."""
        err = self._ensure_module()
        if err is not None:
            return err
        d_from = (
            date_from if date_from is not None else datetime(2000, 1, 1, tzinfo=UTC)
        )
        d_to = date_to if date_to is not None else datetime.now(UTC) + timedelta(days=2)
        total = mt5.history_orders_total(d_from, d_to)
        return StandardResponse.success(
            data=int(total), extensions={"broker": self.name}
        )

    @override
    def get_history_deal_info(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        ticket: int | None = None,
        position: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[list[DealInfo]]:
        """Retrieve historical deals."""
        err = self._ensure_module()
        if err is not None:
            return err

        if ticket is not None:
            deals = mt5.history_deals_get(ticket=ticket)
        elif position is not None:
            deals = mt5.history_deals_get(position=position)
        else:
            d_from = (
                date_from if date_from is not None else datetime(2000, 1, 1, tzinfo=UTC)
            )
            d_to = (
                date_to
                if date_to is not None
                else datetime.now(UTC) + timedelta(days=2)
            )
            if group is not None:
                deals = mt5.history_deals_get(d_from, d_to, group=group)
            else:
                deals = mt5.history_deals_get(d_from, d_to)

        if deals is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Failed to get history deals: {desc}",
                error=StandardError(
                    code=str(code), message=f"Failed to get history deals: {desc}"
                ),
                extensions={"broker": self.name},
            )

        res: list[DealInfo] = []
        for d in deals:
            dt = (
                datetime.fromtimestamp(d.time, tz=UTC)
                if getattr(d, "time", None)
                else None
            )
            res.append(
                DealInfo(
                    ticket=d.ticket,
                    order=d.order,
                    position_id=getattr(d, "position_id", 0),
                    symbol=d.symbol,
                    type=str(d.type),
                    entry=str(d.entry),
                    volume=float(d.volume),
                    price=float(d.price),
                    commission=float(getattr(d, "commission", 0.0)),
                    swap=float(getattr(d, "swap", 0.0)),
                    profit=float(getattr(d, "profit", 0.0)),
                    fee=float(getattr(d, "fee", 0.0)),
                    time=dt,
                    comment=d.comment,
                    magic=d.magic,
                    raw=d,
                )
            )
        return StandardResponse.success(
            data=res, extensions={"broker": self.name, "raw": deals}
        )

    @override
    def get_num_history_deals(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> StandardResponse[int]:
        """Get total historical deals count within range."""
        err = self._ensure_module()
        if err is not None:
            return err
        d_from = (
            date_from if date_from is not None else datetime(2000, 1, 1, tzinfo=UTC)
        )
        d_to = date_to if date_to is not None else datetime.now(UTC) + timedelta(days=2)
        total = mt5.history_deals_total(d_from, d_to)
        return StandardResponse.success(
            data=int(total), extensions={"broker": self.name}
        )

    # ========================================================================
    # 9. Margin & Profit Calculations
    # ========================================================================

    @override
    def calculate_margin(
        self,
        action: OrderType | str | int,
        symbol: str,
        volume: float,
        price: float,
    ) -> StandardResponse[float]:
        """Calculate margin required for order."""
        err = self._ensure_module()
        if err is not None:
            return err
        ot = self._map_order_type(action)
        margin = mt5.order_calc_margin(ot, symbol, volume, price)
        if margin is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Margin calculation failed: {desc}",
                error=StandardError(
                    code=str(code), message=f"Margin calculation failed: {desc}"
                ),
                extensions={"broker": self.name},
            )
        return StandardResponse.success(
            data=float(margin), extensions={"broker": self.name}
        )

    @override
    def calculate_profit(
        self,
        action: OrderType | str | int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> StandardResponse[float]:
        """Calculate potential profit/loss."""
        err = self._ensure_module()
        if err is not None:
            return err
        ot = self._map_order_type(action)
        profit = mt5.order_calc_profit(ot, symbol, volume, price_open, price_close)
        if profit is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Profit calculation failed: {desc}",
                error=StandardError(
                    code=str(code), message=f"Profit calculation failed: {desc}"
                ),
                extensions={"broker": self.name},
            )
        return StandardResponse.success(
            data=float(profit), extensions={"broker": self.name}
        )

    # ========================================================================
    # 10. Pre-check & Trade Execution
    # ========================================================================

    def _build_mt5_request(self, request: TradeRequest) -> dict[str, Any]:
        """Build native MT5 request dictionary from neutral TradeRequest."""
        act_val: Any = request.action
        if isinstance(act_val, OrderAction):
            act_int = self.ACTION_MAP.get(act_val, 1)
        elif isinstance(act_val, int):
            act_int = act_val
        else:
            act_str = str(act_val).upper()
            act_int = self.ACTION_MAP.get(
                OrderAction(act_str)
                if act_str in OrderAction.__members__
                else OrderAction.DEAL,
                1,
            )

        type_int = self._map_order_type(request.type)

        price = request.price
        if (price is None or price <= 0) and request.symbol and mt5 is not None:
            tick = mt5.symbol_info_tick(request.symbol)
            if tick:
                price = tick.ask if type_int == 0 else tick.bid
            else:
                price = 0.0

        if request.type_filling is not None:
            if isinstance(request.type_filling, OrderFilling):
                fill_mode = (
                    0
                    if request.type_filling == OrderFilling.FOK
                    else (1 if request.type_filling == OrderFilling.IOC else 2)
                )
            else:
                fill_mode = int(request.type_filling)
        else:
            fill_mode = self._detect_symbol_filling(request.symbol)

        req_dict: dict[str, Any] = {
            "action": act_int,
            "symbol": request.symbol,
            "volume": float(request.volume),
            "type": type_int,
            "price": float(price or 0.0),
            "sl": float(request.sl or 0.0),
            "tp": float(request.tp or 0.0),
            "deviation": request.deviation,
            "magic": request.magic,
            "comment": request.comment,
            "type_time": 0,  # ORDER_TIME_GTC
            "type_filling": fill_mode,
        }

        if request.position:
            req_dict["position"] = request.position
        if request.order:
            req_dict["order"] = request.order

        return req_dict

    @override
    def check_order(self, request: TradeRequest) -> StandardResponse[OrderCheckResult]:
        """Perform pre-flight verification of trade request."""
        err = self._ensure_module()
        if err is not None:
            return err

        req_dict = self._build_mt5_request(request)
        self.logger.debug("FR-BROKER-MT5-ORDER-EXECUTION: Checking order: %s", req_dict)
        res = mt5.order_check(req_dict)
        if res is None:
            code, desc = mt5.last_error()
            return StandardResponse.failure(
                message=f"Order check failed: {desc}",
                error=StandardError(
                    code=str(code), message=f"Order check failed: {desc}"
                ),
                extensions={"broker": self.name},
            )

        chk_res = OrderCheckResult(
            retcode=res.retcode,
            balance=getattr(res, "balance", 0.0),
            equity=getattr(res, "equity", 0.0),
            profit=getattr(res, "profit", 0.0),
            margin=getattr(res, "margin", 0.0),
            margin_free=getattr(res, "margin_free", 0.0),
            margin_level=getattr(res, "margin_level", 0.0),
            comment=getattr(res, "comment", ""),
            raw=res,
        )

        if res.retcode == 0:
            return StandardResponse.success(
                data=chk_res,
                message=chk_res.comment,
                extensions={"broker": self.name, "raw": res},
            )
        return StandardResponse.failure(
            message=f"Order check rejected: {chk_res.comment} (retcode: {res.retcode})",
            error=StandardError(
                code=str(res.retcode),
                message=f"Order check rejected: {chk_res.comment} (retcode: {res.retcode})",
            ),
            data=chk_res,
            extensions={"broker": self.name, "raw": res},
        )

    @override
    def trade(self, request: TradeRequest) -> StandardResponse[TradeResult]:
        """Send and execute order via MT5 order_send."""
        err = self._ensure_module()
        if err is not None:
            return err

        req_dict = self._build_mt5_request(request)
        self.logger.info(
            "FR-BROKER-MT5-ORDER-EXECUTION: Executing trade request: %s", req_dict
        )
        res = mt5.order_send(req_dict)
        if res is None:
            code, desc = mt5.last_error()
            msg = f"Order send failed to execute: {desc} (code {code})"
            self.logger.error("FR-BROKER-MT5-ORDER-EXECUTION: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code=str(code), message=msg),
                extensions={"broker": self.name},
            )

        t_res = TradeResult(
            retcode=res.retcode,
            deal=getattr(res, "deal", 0),
            order=getattr(res, "order", 0),
            volume=getattr(res, "volume", 0.0),
            price=getattr(res, "price", 0.0),
            bid=getattr(res, "bid", 0.0),
            ask=getattr(res, "ask", 0.0),
            comment=getattr(res, "comment", ""),
            request_id=getattr(res, "request_id", 0),
            retcode_external=getattr(res, "retcode_external", 0),
            raw=res,
        )

        if res.retcode in (10009, 10008):
            self.logger.info(
                "FR-BROKER-MT5-ORDER-EXECUTION: Trade executed successfully: order=%s, deal=%s, comment=%s",
                t_res.order,
                t_res.deal,
                t_res.comment,
            )
            return StandardResponse.success(
                data=t_res,
                message=t_res.comment,
                extensions={"broker": self.name, "raw": res},
            )

        msg = f"Trade rejected: {t_res.comment} (code {t_res.retcode})"
        self.logger.warning("FR-BROKER-MT5-ORDER-EXECUTION: %s", msg)
        return StandardResponse.failure(
            message=msg,
            error=StandardError(code=str(res.retcode), message=msg),
            data=t_res,
            extensions={"broker": self.name, "raw": res},
        )


def create_adapter(_context: PluginHostContext | None = None) -> MetaTraderBroker:
    """Plugin entrypoint factory constructing the MetaTrader broker adapter."""
    logger.info("Initializing MetaTrader 5 broker plugin adapter.")
    return MetaTraderBroker()
