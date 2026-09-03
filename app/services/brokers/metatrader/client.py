"""MetaTrader 5 Direct Provider Client and Primary Service Module.

Purpose:
    Provide direct MetaTrader 5 terminal connection and raw operational functions,
    returning MetaTrader 5 objects wrapped in StandardResponse envelopes without
    business logic or auxiliary helper transformations.

Operations provided by MT5Client:
    * connect
    * disconnect
    * is_connected
    * get_last_error
    * get_terminal_info
    * get_account_info
    * get_symbol_info
    * get_num_of_symbols
    * get_symbols
    * enable_symbol
    * get_symbol_tick
    * subscribe_market_depth
    * get_market_depth
    * unsubscribe_market_depth
    * get_bars
    * get_ticks
    * get_position_info
    * get_num_positions
    * get_order_info
    * get_num_orders
    * get_history_order_info
    * get_num_history_orders
    * get_history_deal_info
    * get_num_history_deals
    * calculate_margin
    * calculate_profit
    * check_order
    * trade
"""

from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path
from typing import Any, override

import pandas as pd

try:
    import MetaTrader5 as mt5  # noqa: N813

    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    _MT5_AVAILABLE = False

from app.composition.logging import get_logger
from app.contracts.broker.metatrader import (
    MT5_TERMINAL_ERROR_DESCRIPTIONS,
    MT5_TRADE_RETCODE_DESCRIPTIONS,
    TIMEFRAME_MAP,
    MT5TerminalError,
    MT5TradeRetcode,
    get_mt5_error_description,
    get_mt5_retcode_description,
    resolve_timeframe,
)
from app.contracts.broker.models import (
    BrokerAccountInfo,
    BrokerSymbolInfo,
    BrokerTerminalInfo,
)
from app.contracts.broker.ports import BrokerOperationsCapability
from app.contracts.common.response import StandardResponse
from app.services.brokers.metatrader._persistence import get_mt5_credentials
from app.services.brokers.metatrader.config import MetaTraderConfig

logger = get_logger(__name__)


def get_credentials(db_path: Path | str | None = None) -> dict[str, Any]:
    """Retrieve MT5 login credentials and terminal settings from the database.

    Args:
        db_path: Optional path to SQLite central database.

    Returns:
        Dictionary containing login, password, server, terminal_path, and enabled status.
    """
    return get_mt5_credentials(db_path)


__all__ = [
    "MT5_TERMINAL_ERROR_DESCRIPTIONS",
    "MT5_TRADE_RETCODE_DESCRIPTIONS",
    "TIMEFRAME_MAP",
    "BrokerAccountInfo",
    "BrokerSymbolInfo",
    "BrokerTerminalInfo",
    "MT5Client",
    "MT5TerminalError",
    "MT5TradeRetcode",
    "get_credentials",
    "get_mt5_error_description",
    "get_mt5_retcode_description",
    "resolve_timeframe",
]


def _records_to_dict_list(records: Any) -> list[dict[str, Any]]:
    """Convert numpy recarray, tuple of namedtuples, or sequence of objects to list of dicts."""
    if records is None:
        return []
    if (
        hasattr(records, "dtype")
        and hasattr(records.dtype, "names")
        and records.dtype.names
    ):
        names = records.dtype.names
        return [
            {
                name: (row[name].item() if hasattr(row[name], "item") else row[name])
                for name in names
            }
            for row in records
        ]
    result: list[dict[str, Any]] = []
    for item in records:
        if hasattr(item, "_asdict"):
            result.append(item._asdict())
        elif isinstance(item, dict):
            result.append(item)
        elif hasattr(item, "__dict__"):
            result.append(dict(item.__dict__))
        else:
            try:
                result.append(dict(item))
            except TypeError, ValueError:
                result.append({"value": item})
    return result


def _format_bars_dataframe(raw_data: Any) -> pd.DataFrame:
    """Transform raw bar records or dicts into standardized OHLCV DataFrame."""
    empty_df = pd.DataFrame(
        columns=["Open", "High", "Low", "Close", "Volume", "Spread"],
        index=pd.DatetimeIndex([], name="DateTime"),
    )
    if raw_data is None:
        return empty_df

    records = (
        _records_to_dict_list(raw_data) if not isinstance(raw_data, list) else raw_data
    )
    if not records:
        return empty_df

    df = pd.DataFrame(records)
    if df.empty:
        return empty_df

    col_map = {c: str(c).lower() for c in df.columns}
    df = df.rename(columns=col_map)

    time_col = None
    for candidate in ("datetime", "time", "date", "timestamp"):
        if candidate in df.columns:
            time_col = candidate
            break

    if time_col is not None:
        s = df[time_col]
        if pd.api.types.is_numeric_dtype(s):
            if (s > 1e11).any():
                dt_series = pd.to_datetime(s, unit="ms", utc=True)
            else:
                dt_series = pd.to_datetime(s, unit="s", utc=True)
        else:
            dt_series = pd.to_datetime(s, utc=True)
        df.index = pd.DatetimeIndex(dt_series, name="DateTime")
    else:
        df.index = pd.DatetimeIndex(pd.to_datetime(df.index, utc=True), name="DateTime")

    if "tick_volume" in df.columns:
        volume_series = df["tick_volume"]
    elif "volume" in df.columns:
        volume_series = df["volume"]
    elif "real_volume" in df.columns:
        volume_series = df["real_volume"]
    else:
        volume_series = 0

    spread_series = df["spread"] if "spread" in df.columns else 0

    result = pd.DataFrame(
        {
            "Open": df.get("open", 0.0),
            "High": df.get("high", 0.0),
            "Low": df.get("low", 0.0),
            "Close": df.get("close", 0.0),
            "Volume": volume_series,
            "Spread": spread_series,
        },
        index=df.index,
    )
    result.index.name = "DateTime"
    return result


def _format_ticks_dataframe(raw_data: Any) -> pd.DataFrame:
    """Transform raw tick records or dicts into standardized tick DataFrame."""
    empty_df = pd.DataFrame(
        columns=["Bid", "Ask", "Volume"],
        index=pd.DatetimeIndex([], name="DateTime"),
    )
    if raw_data is None:
        return empty_df

    records = (
        _records_to_dict_list(raw_data) if not isinstance(raw_data, list) else raw_data
    )
    if not records:
        return empty_df

    df = pd.DataFrame(records)
    if df.empty:
        return empty_df

    col_map = {c: str(c).lower() for c in df.columns}
    df = df.rename(columns=col_map)

    time_col = None
    for candidate in ("datetime", "time", "date", "timestamp", "time_msc"):
        if candidate in df.columns:
            time_col = candidate
            break

    if time_col is not None:
        s = df[time_col]
        if pd.api.types.is_numeric_dtype(s):
            if time_col == "time_msc" or (s > 1e11).any():
                dt_series = pd.to_datetime(s, unit="ms", utc=True)
            else:
                dt_series = pd.to_datetime(s, unit="s", utc=True)
        else:
            dt_series = pd.to_datetime(s, utc=True)
        df.index = pd.DatetimeIndex(dt_series, name="DateTime")
    else:
        df.index = pd.DatetimeIndex(pd.to_datetime(df.index, utc=True), name="DateTime")

    if "volume" in df.columns:
        volume_series = df["volume"]
    elif "volume_real" in df.columns:
        volume_series = df["volume_real"]
    elif "vol" in df.columns:
        volume_series = df["vol"]
    else:
        volume_series = 0

    result = pd.DataFrame(
        {
            "Bid": df.get("bid", 0.0),
            "Ask": df.get("ask", 0.0),
            "Volume": volume_series,
        },
        index=df.index,
    )
    result.index.name = "DateTime"
    return result


class MT5Client(BrokerOperationsCapability):
    """Encapsulates the MetaTrader 5 terminal connection and direct API functions."""

    def __init__(
        self,
        config: MetaTraderConfig | None = None,
        mt5_module: Any = None,
    ) -> None:
        """Initialize an MT5 client instance with self-contained configuration.

        Args:
            config: Optional MetaTraderConfig settings. If omitted, default configuration
                    is initialized and credentials are automatically loaded from database.
            mt5_module: Optional injected MetaTrader5 module or mock.
        """
        self.config = config or MetaTraderConfig()
        self.load_credentials_from_db()
        self.mt5 = mt5_module if mt5_module is not None else mt5
        self.state: dict[str, Any] = {
            "connected": False,
            "login": self.config.login,
            "server": self.config.server,
            "terminal_path": self.config.terminal_path,
            "last_error": (0, "Success"),
        }

    def load_credentials_from_db(
        self, db_path: Path | str | None = None
    ) -> dict[str, Any]:
        """Load and apply credentials from the database to this client instance.

        Args:
            db_path: Optional custom database path.

        Returns:
            Dictionary of credentials loaded from database.
        """
        creds = get_credentials(db_path or self.config.database_path)
        updates: dict[str, Any] = {}
        if creds.get("login") is not None and not self.config.login:
            updates["login"] = creds["login"]
        if creds.get("password") is not None and not self.config.password:
            updates["password"] = creds["password"]
        if creds.get("server") is not None and not self.config.server:
            updates["server"] = creds["server"]
        if creds.get("terminal_path") is not None and not self.config.terminal_path:
            updates["terminal_path"] = creds["terminal_path"]

        if updates:
            self.config = replace(self.config, **updates)
        return creds

    def is_available(self) -> bool:
        """Check if the MetaTrader 5 package is available."""
        return self.mt5 is not None

    @override
    def is_connected(self) -> bool:
        """Check if the terminal is currently connected."""
        if (
            self.mt5 is not None
            and hasattr(self.mt5, "terminal_info")
            and self.state.get("connected", False)
        ):
            t_info = self.mt5.terminal_info()
            return bool(t_info.connected) if t_info is not None else False
        return False

    def get_last_error(self) -> tuple[int, str]:
        """Retrieve last MetaTrader 5 error code and description.

        Returns:
            Tuple of (code, description). If description from MT5 is empty or generic,
            the official description from MT5_TERMINAL_ERROR_DESCRIPTIONS is returned.
        """
        if self.mt5 is not None and hasattr(self.mt5, "last_error"):
            err = self.mt5.last_error()
            if isinstance(err, tuple) and len(err) >= 2:
                code = int(err[0])
                desc = str(err[1])
                if not desc or desc.strip() in ("", "Unknown"):
                    desc = get_mt5_error_description(code)
                return (code, desc)
        res = self.state.get("last_error", (0, "Success"))
        return (int(res[0]), str(res[1]))

    @override
    def connect(
        self,
        account_id: str | int | None = None,
        server: str | None = None,
        password: str | None = None,
        timeout: int = 30,
        path: str | None = None,
        login: int | str | None = None,
        portable: bool = False,
        config: MetaTraderConfig | None = None,
    ) -> StandardResponse[Any]:
        """Connect to MT5 terminal with database or explicit credentials.

        Args:
            path: Path to terminal64.exe executable.
            login: Account login number.
            password: Account password.
            server: Trade server name.
            timeout: Connection timeout in seconds.
            portable: Whether to launch terminal in portable mode.
            config: Optional MetaTraderConfig instance.

        Returns:
            StandardResponse containing connection summary data.
        """
        if self.mt5 is None or not self.is_available():
            logger.error(
                "MetaTrader 5 Python package is not installed or available in the environment."
            )
            return StandardResponse(
                status="error",
                message="MetaTrader5 Python package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="connect",
            )

        cfg = config or self.config
        db_creds = get_mt5_credentials(cfg.database_path)

        final_path = path or cfg.terminal_path or db_creds.get("terminal_path")
        final_login = account_id or login or cfg.login or db_creds.get("login")
        final_pwd = password or cfg.password or db_creds.get("password")
        final_server = server or cfg.server or db_creds.get("server")
        final_timeout = timeout or cfg.timeout or 30

        login_int = (
            int(final_login) if final_login and str(final_login).isdigit() else None
        )

        init_kwargs: dict[str, Any] = {
            "timeout": final_timeout * 1000,
            "portable": portable,
        }
        if final_path:
            init_kwargs["path"] = final_path
        if login_int:
            init_kwargs["login"] = login_int
        if final_pwd:
            init_kwargs["password"] = final_pwd
        if final_server:
            init_kwargs["server"] = final_server

        logger.info(
            "Connecting to MetaTrader 5 (server=%s, login=%s, timeout=%s)...",
            final_server,
            login_int,
            final_timeout,
        )
        initialized = self.mt5.initialize(**init_kwargs)
        if not initialized:
            err = (
                self.mt5.last_error()
                if hasattr(self.mt5, "last_error")
                else (-1, "Init failed")
            )
            logger.error(
                "Failed to initialize MetaTrader 5 terminal: [%s] %s", err[0], err[1]
            )
            self.state["connected"] = False
            self.state["last_error"] = err
            return StandardResponse(
                status="error",
                message=f"Failed to initialize MetaTrader 5 terminal: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="connect",
            )

        self.state["connected"] = True
        self.state["login"] = login_int
        self.state["server"] = final_server
        self.state["terminal_path"] = final_path
        self.state["last_error"] = (0, "Success")
        logger.info(
            "Connected to MetaTrader 5 terminal successfully (login=%s, server=%s).",
            login_int,
            final_server,
        )

        return StandardResponse(
            status="connected",
            message="Connected to MetaTrader 5 terminal successfully.",
            data={
                "connected": True,
                "login": login_int,
                "server": final_server,
                "platform": "mt5",
            },
            operation="connect",
        )

    @override
    def disconnect(self) -> StandardResponse[Any]:
        """Disconnect and shut down MetaTrader 5 terminal connection."""
        logger.info("Disconnecting from MetaTrader 5 terminal.")
        if self.mt5 is not None and hasattr(self.mt5, "shutdown"):
            self.mt5.shutdown()
        self.state["connected"] = False
        return StandardResponse(
            status="success",
            message="Disconnected from MetaTrader 5 terminal.",
            data={"connected": False},
            operation="disconnect",
        )

    def get_terminal_info(self) -> StandardResponse[BrokerTerminalInfo]:
        """Retrieve detailed terminal environment properties."""
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_terminal_info",
            )

        info = self.mt5.terminal_info()
        if info is None:
            err = self.get_last_error()
            logger.warning(
                "Failed to retrieve MetaTrader 5 terminal info: [%s] %s", err[0], err[1]
            )
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve MetaTrader 5 terminal info: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_terminal_info",
            )

        terminal_info = BrokerTerminalInfo.from_dict(info)
        return StandardResponse(
            status="success",
            message="Terminal info retrieved successfully.",
            data=terminal_info,
            operation="get_terminal_info",
        )

    @override
    def get_account_info(self) -> StandardResponse[BrokerAccountInfo]:
        """Retrieve live MT5 account properties and configuration."""
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_account_info",
            )

        acc = self.mt5.account_info()
        if acc is None:
            err = self.get_last_error()
            logger.warning(
                "Failed to retrieve MetaTrader 5 account info: [%s] %s", err[0], err[1]
            )
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve MetaTrader 5 account info: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_account_info",
            )

        account_info = BrokerAccountInfo.from_dict(acc)
        return StandardResponse(
            status="success",
            message="Account info retrieved successfully.",
            data=account_info,
            operation="get_account_info",
        )

    @override
    def get_symbol_info(self, symbol: str) -> StandardResponse[BrokerSymbolInfo]:
        """Retrieve symbol specifications directly from MT5.

        Args:
            symbol: Symbol ticker.

        Returns:
            StandardResponse containing symbol specification data.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_symbol_info",
            )

        sym = symbol.upper()
        info = self.mt5.symbol_info(sym)
        if info is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Symbol '{symbol}' not found in MetaTrader 5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_symbol_info",
            )

        symbol_info = BrokerSymbolInfo.from_dict(info)
        return StandardResponse(
            status="success",
            message=f"Symbol info for {sym} retrieved successfully.",
            data=symbol_info,
            operation="get_symbol_info",
        )

    def get_num_of_symbols(self) -> StandardResponse[int]:
        """Retrieve the total count of available financial instruments in MT5.

        Returns:
            StandardResponse containing the total number of symbols.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_num_of_symbols",
            )
        total = self.mt5.symbols_total()
        if total is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve symbols total from MT5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_num_of_symbols",
            )
        return StandardResponse(
            status="success",
            message="Symbols total retrieved successfully.",
            data=int(total),
            operation="get_num_of_symbols",
        )

    def get_symbols(
        self, group: str | None = None
    ) -> StandardResponse[list[BrokerSymbolInfo]]:
        """Retrieve financial instruments from MT5, optionally filtered by group.

        Args:
            group: Optional symbol group filter (e.g. "*USD*", "*EUR*", etc.).

        Returns:
            StandardResponse containing list of symbol specifications.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_symbols",
            )
        symbols = (
            self.mt5.symbols_get(group) if group is not None else self.mt5.symbols_get()
        )
        if symbols is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve symbols from MT5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_symbols",
            )
        data = [BrokerSymbolInfo.from_dict(s) for s in symbols]
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(data)} symbols successfully.",
            data=data,
            operation="get_symbols",
        )

    def enable_symbol(self, symbol: str, enable: bool = True) -> StandardResponse[bool]:
        """Select or deselect a symbol in the MarketWatch window.

        Args:
            symbol: Ticker symbol to select/deselect.
            enable: True to show in MarketWatch, False to hide.

        Returns:
            StandardResponse containing boolean success state.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="enable_symbol",
            )
        sym = symbol.upper()
        res = self.mt5.symbol_select(sym, enable)
        if not res:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to {'enable' if enable else 'disable'} symbol '{sym}' in MT5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="enable_symbol",
            )
        return StandardResponse(
            status="success",
            message=f"Symbol '{sym}' {'enabled' if enable else 'disabled'} successfully.",
            data=True,
            operation="enable_symbol",
        )

    def get_symbol_tick(self, symbol: str) -> StandardResponse[dict[str, Any]]:
        """Retrieve the last tick for a specified symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            StandardResponse containing the last tick prices and volumes.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_symbol_tick",
            )
        sym = symbol.upper()
        tick = self.mt5.symbol_info_tick(sym)
        if tick is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve tick for '{sym}' from MT5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_symbol_tick",
            )
        data = tick._asdict() if hasattr(tick, "_asdict") else dict(tick)
        return StandardResponse(
            status="success",
            message=f"Tick for '{sym}' retrieved successfully.",
            data=data,
            operation="get_symbol_tick",
        )

    def subscribe_market_depth(self, symbol: str) -> StandardResponse[bool]:
        """Subscribe MT5 terminal to receive Depth of Market (DOM) events for symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            StandardResponse containing subscription success status.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="subscribe_market_depth",
            )
        sym = symbol.upper()
        res = self.mt5.market_book_add(sym)
        if not res:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to subscribe to market depth for '{sym}': [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="subscribe_market_depth",
            )
        return StandardResponse(
            status="success",
            message=f"Subscribed to market depth for '{sym}' successfully.",
            data=True,
            operation="subscribe_market_depth",
        )

    def get_market_depth(self, symbol: str) -> StandardResponse[list[dict[str, Any]]]:
        """Retrieve current Depth of Market (DOM) records for symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            StandardResponse containing list of DOM price and volume records.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_market_depth",
            )
        sym = symbol.upper()
        book = self.mt5.market_book_get(sym)
        if book is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to get market depth for '{sym}': [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_market_depth",
            )
        data = [b._asdict() if hasattr(b, "_asdict") else dict(b) for b in book]
        return StandardResponse(
            status="success",
            message=f"Market depth for '{sym}' retrieved successfully.",
            data=data,
            operation="get_market_depth",
        )

    def unsubscribe_market_depth(self, symbol: str) -> StandardResponse[bool]:
        """Unsubscribe MT5 terminal from Depth of Market (DOM) events for symbol.

        Args:
            symbol: Ticker symbol.

        Returns:
            StandardResponse containing unsubscription success status.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="unsubscribe_market_depth",
            )
        sym = symbol.upper()
        res = self.mt5.market_book_release(sym)
        if not res:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to release market depth for '{sym}': [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="unsubscribe_market_depth",
            )
        return StandardResponse(
            status="success",
            message=f"Unsubscribed from market depth for '{sym}' successfully.",
            data=True,
            operation="unsubscribe_market_depth",
        )

    def get_bars(
        self,
        symbol: str,
        timeframe: Any = "1m",
        date_from: Any = None,
        date_to: Any = None,
        start_pos: int | None = None,
        count: int | None = None,
    ) -> StandardResponse[pd.DataFrame]:
        """Retrieve historical OHLCV bar rates from MT5 as a DataFrame.

        Switches automatically based on provided arguments:
        - date_from and date_to: calls mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        - start_pos and count: calls mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        - date_from and count: calls mt5.copy_rates_from(symbol, timeframe, date_from, count)
        - count only: calls mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        - default (no range/pos/count specified): calls mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)

        Args:
            symbol: Ticker symbol.
            timeframe: Timeframe identifier (string e.g. '1m', '1h', '1d' or MT5 integer constant).
            date_from: Optional starting datetime or timestamp.
            date_to: Optional ending datetime or timestamp.
            start_pos: Optional starting bar index (0 = latest).
            count: Optional number of bars to retrieve.

        Returns:
            StandardResponse containing list of bar dictionaries.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_bars",
            )
        sym = symbol.upper()
        tf = resolve_timeframe(timeframe)

        if date_from is not None and date_to is not None:
            rates = self.mt5.copy_rates_range(sym, tf, date_from, date_to)
        elif start_pos is not None and count is not None:
            rates = self.mt5.copy_rates_from_pos(sym, tf, start_pos, count)
        elif date_from is not None and count is not None:
            rates = self.mt5.copy_rates_from(sym, tf, date_from, count)
        elif count is not None:
            rates = self.mt5.copy_rates_from_pos(sym, tf, 0, count)
        else:
            rates = self.mt5.copy_rates_from_pos(sym, tf, 0, 100)

        if rates is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to copy rates for '{sym}': [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_bars",
            )

        data = _format_bars_dataframe(rates)
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(data)} bars for '{sym}'.",
            data=data,
            operation="get_bars",
        )

    # Convenience alias
    get_historical_bars = get_bars

    def get_ticks(
        self,
        symbol: str,
        date_from: Any = None,
        date_to: Any = None,
        count: int = 100,
        flags: int = 0,
    ) -> StandardResponse[pd.DataFrame]:
        """Retrieve historical tick records from MT5 as a DataFrame.

        Switches automatically based on provided arguments:
        - date_from and date_to: calls mt5.copy_ticks_range(symbol, date_from, date_to, flags)
        - otherwise: calls mt5.copy_ticks_from(symbol, date_from, count, flags)

        Args:
            symbol: Ticker symbol.
            date_from: Optional starting datetime or timestamp.
            date_to: Optional ending datetime or timestamp.
            count: Number of ticks to retrieve if copying from start (default 100).
            flags: Copy ticks flags (default 0).

        Returns:
            StandardResponse containing DataFrame of tick records with DateTime index and Bid, Ask, Volume columns.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_ticks",
            )
        sym = symbol.upper()

        if date_from is not None and date_to is not None:
            ticks = self.mt5.copy_ticks_range(sym, date_from, date_to, flags)
        else:
            d_from = date_from if date_from is not None else int(time.time())
            ticks = self.mt5.copy_ticks_from(sym, d_from, count, flags)

        if ticks is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to copy ticks for '{sym}': [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_ticks",
            )

        data = _format_ticks_dataframe(ticks)
        return StandardResponse(
            status="success",
            message=f"Retrieved {len(data)} ticks for '{sym}'.",
            data=data,
            operation="get_ticks",
        )

    def get_position_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[Any]:
        """Retrieve open trading positions directly from MT5.

        Args:
            symbol: Optional symbol filter.
            ticket: Optional specific position ticket ID.
            group: Optional symbol group filter.

        Returns:
            StandardResponse containing position data.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_position_info",
            )

        if ticket is not None:
            pos = self.mt5.positions_get(ticket=ticket)
        elif symbol is not None:
            pos = self.mt5.positions_get(symbol=symbol.upper())
        elif group is not None:
            pos = self.mt5.positions_get(group=group)
        else:
            pos = self.mt5.positions_get()

        if pos is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve positions from MetaTrader 5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_position_info",
            )

        if ticket is not None:
            data = (
                pos[0]._asdict()
                if len(pos) > 0 and hasattr(pos[0], "_asdict")
                else (dict(pos[0]) if len(pos) > 0 else None)
            )
        else:
            data = [p._asdict() if hasattr(p, "_asdict") else dict(p) for p in pos]

        return StandardResponse(
            status="success",
            message="Position info retrieved successfully.",
            data=data,
            operation="get_position_info",
        )

    def get_num_positions(self) -> StandardResponse[int]:
        """Retrieve total count of open positions from MT5.

        Returns:
            StandardResponse containing total open positions count.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_num_positions",
            )
        total = self.mt5.positions_total()
        if total is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to get positions total: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_num_positions",
            )
        return StandardResponse(
            status="success",
            message="Positions total retrieved successfully.",
            data=int(total),
            operation="get_num_positions",
        )

    def get_order_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
    ) -> StandardResponse[Any]:
        """Retrieve active and pending orders directly from MT5.

        Args:
            symbol: Optional symbol filter.
            ticket: Optional specific order ticket ID.
            group: Optional symbol group filter.

        Returns:
            StandardResponse containing order data.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_order_info",
            )

        if ticket is not None:
            orders = self.mt5.orders_get(ticket=ticket)
        elif symbol is not None:
            orders = self.mt5.orders_get(symbol=symbol.upper())
        elif group is not None:
            orders = self.mt5.orders_get(group=group)
        else:
            orders = self.mt5.orders_get()

        if orders is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve orders from MetaTrader 5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_order_info",
            )

        if ticket is not None:
            data = (
                orders[0]._asdict()
                if len(orders) > 0 and hasattr(orders[0], "_asdict")
                else (dict(orders[0]) if len(orders) > 0 else None)
            )
        else:
            data = [o._asdict() if hasattr(o, "_asdict") else dict(o) for o in orders]

        return StandardResponse(
            status="success",
            message="Order info retrieved successfully.",
            data=data,
            operation="get_order_info",
        )

    def get_num_orders(self) -> StandardResponse[int]:
        """Retrieve total count of active orders from MT5.

        Returns:
            StandardResponse containing total active orders count.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_num_orders",
            )
        total = self.mt5.orders_total()
        if total is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to get orders total: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_num_orders",
            )
        return StandardResponse(
            status="success",
            message="Orders total retrieved successfully.",
            data=int(total),
            operation="get_num_orders",
        )

    def get_history_order_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
        date_from: Any = None,
        date_to: Any = None,
    ) -> StandardResponse[Any]:
        """Retrieve historical orders directly from MT5.

        Args:
            symbol: Optional symbol filter.
            ticket: Optional specific historical order ticket.
            group: Optional symbol group filter.
            date_from: Optional start timestamp/datetime.
            date_to: Optional end timestamp/datetime.

        Returns:
            StandardResponse containing historical order data.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_history_order_info",
            )

        if ticket is not None:
            orders = self.mt5.history_orders_get(ticket=ticket)
        elif date_from is not None and date_to is not None:
            if group is not None:
                orders = self.mt5.history_orders_get(date_from, date_to, group=group)
            elif symbol is not None:
                orders = self.mt5.history_orders_get(
                    date_from, date_to, group=f"*{symbol.upper()}*"
                )
            else:
                orders = self.mt5.history_orders_get(date_from, date_to)
        elif group is not None:
            orders = self.mt5.history_orders_get(group=group)
        elif symbol is not None:
            orders = self.mt5.history_orders_get(group=f"*{symbol.upper()}*")
        else:
            d_from = int(date_from) if date_from else 0
            d_to = int(date_to) if date_to else int(time.time())
            orders = self.mt5.history_orders_get(d_from, d_to)

        if orders is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve historical orders from MetaTrader 5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_history_order_info",
            )

        if ticket is not None:
            data = (
                orders[0]._asdict()
                if len(orders) > 0 and hasattr(orders[0], "_asdict")
                else (dict(orders[0]) if len(orders) > 0 else None)
            )
        else:
            data = [o._asdict() if hasattr(o, "_asdict") else dict(o) for o in orders]

        return StandardResponse(
            status="success",
            message="Historical order info retrieved successfully.",
            data=data,
            operation="get_history_order_info",
        )

    def get_num_history_orders(
        self, date_from: Any = None, date_to: Any = None
    ) -> StandardResponse[int]:
        """Retrieve total count of historical orders from MT5.

        Args:
            date_from: Optional starting datetime or timestamp.
            date_to: Optional ending datetime or timestamp.

        Returns:
            StandardResponse containing historical orders count.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_num_history_orders",
            )
        if date_from is not None and date_to is not None:
            total = self.mt5.history_orders_total(date_from, date_to)
        else:
            total = self.mt5.history_orders_total()

        if total is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to get history orders total: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_num_history_orders",
            )
        return StandardResponse(
            status="success",
            message="Historical orders total retrieved successfully.",
            data=int(total),
            operation="get_num_history_orders",
        )

    def get_history_deal_info(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        group: str | None = None,
        date_from: Any = None,
        date_to: Any = None,
    ) -> StandardResponse[Any]:
        """Retrieve historical executed deals directly from MT5.

        Args:
            symbol: Optional symbol filter.
            ticket: Optional specific historical deal ticket.
            group: Optional symbol group filter.
            date_from: Optional start timestamp/datetime.
            date_to: Optional end timestamp/datetime.

        Returns:
            StandardResponse containing historical deal data.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_history_deal_info",
            )

        if ticket is not None:
            deals = self.mt5.history_deals_get(ticket=ticket)
        elif date_from is not None and date_to is not None:
            if group is not None:
                deals = self.mt5.history_deals_get(date_from, date_to, group=group)
            elif symbol is not None:
                deals = self.mt5.history_deals_get(
                    date_from, date_to, group=f"*{symbol.upper()}*"
                )
            else:
                deals = self.mt5.history_deals_get(date_from, date_to)
        elif group is not None:
            deals = self.mt5.history_deals_get(group=group)
        elif symbol is not None:
            deals = self.mt5.history_deals_get(group=f"*{symbol.upper()}*")
        else:
            d_from = int(date_from) if date_from else 0
            d_to = int(date_to) if date_to else int(time.time())
            deals = self.mt5.history_deals_get(d_from, d_to)

        if deals is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to retrieve deals from MetaTrader 5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_history_deal_info",
            )

        if ticket is not None:
            data = (
                deals[0]._asdict()
                if len(deals) > 0 and hasattr(deals[0], "_asdict")
                else (dict(deals[0]) if len(deals) > 0 else None)
            )
        else:
            data = [d._asdict() if hasattr(d, "_asdict") else dict(d) for d in deals]

        return StandardResponse(
            status="success",
            message="Historical deal info retrieved successfully.",
            data=data,
            operation="get_history_deal_info",
        )

    def get_num_history_deals(
        self, date_from: Any = None, date_to: Any = None
    ) -> StandardResponse[int]:
        """Retrieve total count of historical deals from MT5.

        Args:
            date_from: Optional starting datetime or timestamp.
            date_to: Optional ending datetime or timestamp.

        Returns:
            StandardResponse containing historical deals count.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="get_num_history_deals",
            )
        if date_from is not None and date_to is not None:
            total = self.mt5.history_deals_total(date_from, date_to)
        else:
            total = self.mt5.history_deals_total()

        if total is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to get history deals total: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="get_num_history_deals",
            )
        return StandardResponse(
            status="success",
            message="Historical deals total retrieved successfully.",
            data=int(total),
            operation="get_num_history_deals",
        )

    def calculate_margin(
        self, action: int, symbol: str, volume: float, price: float
    ) -> StandardResponse[float]:
        """Calculate required margin for an order in account currency.

        Args:
            action: Order action (e.g. 0 for BUY, 1 for SELL).
            symbol: Ticker symbol.
            volume: Trade volume in lots.
            price: Open price.

        Returns:
            StandardResponse containing required margin amount.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="calculate_margin",
            )
        sym = symbol.upper()
        margin = self.mt5.order_calc_margin(action, sym, volume, price)
        if margin is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to calculate margin for '{sym}': [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="calculate_margin",
            )
        return StandardResponse(
            status="success",
            message="Margin calculated successfully.",
            data=float(margin),
            operation="calculate_margin",
        )

    def calculate_profit(
        self,
        action: int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> StandardResponse[float]:
        """Calculate expected profit for an order in account currency.

        Args:
            action: Order action (e.g. 0 for BUY, 1 for SELL).
            symbol: Ticker symbol.
            volume: Trade volume in lots.
            price_open: Open price.
            price_close: Close price.

        Returns:
            StandardResponse containing calculated profit amount.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="calculate_profit",
            )
        sym = symbol.upper()
        profit = self.mt5.order_calc_profit(
            action, sym, volume, price_open, price_close
        )
        if profit is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Failed to calculate profit for '{sym}': [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="calculate_profit",
            )
        return StandardResponse(
            status="success",
            message="Profit calculated successfully.",
            data=float(profit),
            operation="calculate_profit",
        )

    def check_order(self, request: dict[str, Any]) -> StandardResponse[dict[str, Any]]:
        """Verify order margin and execution parameters before submitting to broker.

        Args:
            request: Order request structure matching MT5 MqlTradeRequest.

        Returns:
            StandardResponse containing OrderCheckResult details.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="check_order",
            )
        res = self.mt5.order_check(request)
        if res is None:
            err = self.get_last_error()
            return StandardResponse(
                status="error",
                message=f"Order check failed: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="check_order",
            )
        data = res._asdict() if hasattr(res, "_asdict") else dict(res)
        retcode = int(data.get("retcode", 0))
        retcode_desc = get_mt5_retcode_description(retcode)
        comment = data.get("comment", "")
        is_success = retcode in (0, MT5TradeRetcode.DONE, MT5TradeRetcode.PLACED)

        return StandardResponse(
            status="success" if is_success else "error",
            message=comment or retcode_desc,
            data=data,
            error=None
            if is_success
            else {"code": retcode, "message": comment or retcode_desc},
            operation="check_order",
        )

    def trade(self, request: dict[str, Any]) -> StandardResponse[Any]:
        """Submit trade request to MT5 via order_send.

        Args:
            request: Trade request dictionary matching MT5 MqlTradeRequest structure.

        Returns:
            StandardResponse containing trade execution results.
        """
        if self.mt5 is None or not self.is_available():
            return StandardResponse(
                status="error",
                message="MetaTrader5 package is not installed or available in the environment.",
                error={"code": -1, "message": "MT5_UNAVAILABLE"},
                operation="trade",
            )

        logger.info(
            "Submitting MT5 trade order: action=%s, symbol=%s, volume=%s, type=%s",
            request.get("action"),
            request.get("symbol"),
            request.get("volume"),
            request.get("type"),
        )
        res = self.mt5.order_send(request)
        if res is None:
            err = self.get_last_error()
            logger.error(
                "Failed to execute trade in MetaTrader 5: [%s] %s", err[0], err[1]
            )
            return StandardResponse(
                status="error",
                message=f"Failed to execute trade in MetaTrader 5: [{err[0]}] {err[1]}",
                error={"code": err[0], "message": err[1]},
                operation="trade",
            )

        res_dict = res._asdict() if hasattr(res, "_asdict") else dict(res)
        retcode = getattr(res, "retcode", res_dict.get("retcode", 0))
        comment = getattr(res, "comment", res_dict.get("comment", ""))
        retcode_desc = get_mt5_retcode_description(retcode)
        is_success = (
            retcode in (MT5TradeRetcode.DONE, MT5TradeRetcode.PLACED) or retcode == 0
        )
        final_msg = comment or (
            "Trade executed successfully."
            if is_success
            else f"Trade failed with retcode [{retcode}]: {retcode_desc}"
        )
        if is_success:
            logger.info(
                "MetaTrader 5 trade executed successfully: retcode [%s], order=%s",
                retcode,
                res_dict.get("order"),
            )
        else:
            logger.warning(
                "MetaTrader 5 trade rejected/failed: retcode [%s]: %s",
                retcode,
                final_msg,
            )

        return StandardResponse(
            status="success" if is_success else "error",
            message=final_msg,
            data=res_dict,
            error=None
            if is_success
            else {"code": retcode, "message": comment or retcode_desc},
            operation="trade",
        )


def _run_usage_example() -> None:
    """Demonstrate MetaTrader 5 client operations."""
    print("=== MetaTrader 5 Client Demonstration ===")
    client = MT5Client()
    conn_res = client.connect()
    print(f"Connection Result: {conn_res}")
    print(f"Terminal Info: {client.get_terminal_info()}")
    print(f"Account Info: {client.get_account_info()}")
    print(f"Symbol Info EURUSD: {client.get_symbol_info('EURUSD')}")


if __name__ == "__main__":
    _run_usage_example()
