"""MetaTrader 5 broker client service.

This module provides the MT5Client class responsible for managing the lifecycle
of the MetaTrader 5 terminal connection, user authentication, and Market Watch
symbol registration.
"""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import MetaTrader5 as mt5  # type: ignore[import-untyped, unused-ignore]  # noqa: N813
import pandas as pd
from app.services.utils.common import bars_to_records
from app.services.utils.errors import ConfigurationError, ExternalServiceError
from app.services.utils.logger import logger
from app.services.utils.settings import settings
from app.services.utils.validators import prepare_ohlcv_data
from data.database.sqlite.users import UserManager


class MT5Api:
    """Thin wrapper around MetaTrader5 with connection tracking."""

    def __init__(self, mt5_module: Any = mt5) -> None:  # noqa: ANN401
        """Description.
            Initialize the MT5 API wrapper.

        Args:
            mt5_module: Any.

        Returns:
            None.
        """
        self._mt5 = mt5_module
        self._initialized = False
        logger.debug("Initialized MT5 API wrapper.")

    def initialize(self, *args: Any, **kwargs: Any) -> bool:  # noqa: ANN401
        """Description.
            Initialize MetaTrader5 and remember the connection state.

        Args:
            args: Any.
            kwargs: Any.

        Returns:
            bool.
        """
        self._initialized = bool(self._mt5.initialize(*args, **kwargs))
        logger.debug(f"Initializing MetaTrader5 (success={self._initialized}).")
        return self._initialized

    def shutdown(self) -> None:
        """Description.
            Shutdown MetaTrader5 and clear the connection state.

        Args:
            None.

        Returns:
            None.
        """
        self._mt5.shutdown()
        self._initialized = False
        logger.debug("Shutting down MetaTrader5 connection and clearing wrapper state.")

    def last_error(self) -> Any:  # noqa: ANN401
        """Description.
            Return the last MetaTrader5 error.

        Args:
            None.

        Returns:
            Any.
        """
        logger.debug("Retrieving last MetaTrader5 execution error.")
        return self._mt5.last_error()

    def is_initialized(self) -> bool:
        """Description.
            Return whether this wrapper initialized MetaTrader5.

        Args:
            None.

        Returns:
            bool.
        """
        logger.debug(
            f"Checking if wrapper has initialized MetaTrader5 "
            f"(initialized={self._initialized})."
        )
        return self._initialized

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Description.
            Delegate unknown attributes to the MetaTrader5 package.

        Args:
            name: str.

        Returns:
            Any.
        """
        logger.debug("Delegating MT5 API attribute %s.", name)
        return getattr(self._mt5, name)


_MT5_API = MT5Api()


class MT5Client:
    """Client for interacting with the MetaTrader 5 trading terminal.

    Handles terminal initialization, user account authentication, checking the
    connection status, selecting default symbols in Market Watch, and closing
    the connection.
    """

    _instance: "MT5Client | None" = None

    def __init__(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        default_symbols: list[str] | None = None,
        timeout: int = 60000,
        portable: bool = False,
    ) -> None:
        """Description.
            Initialize the MetaTrader 5 client with credentials and configuration.

        Args:
            path: str | None.
            login: int | None.
            password: str | None.
            server: str | None.
            default_symbols: list[str] | None.
            timeout: int.
            portable: bool.

        Returns:
            None.
        """
        # Resolve config from parameters or settings fallback
        settings_obj = cast("Any", settings)
        self.path = path or settings_obj.mt5_terminal_path

        # Parse login ID
        raw_login = login if login is not None else settings_obj.mt5_login
        if isinstance(raw_login, str) and raw_login.strip().isdigit():
            self.login: int | None = int(raw_login)
        elif isinstance(raw_login, int):
            self.login = raw_login
        else:
            self.login = None

        self.password = password or settings_obj.mt5_password
        self.server = server or settings_obj.mt5_server
        self.timeout = timeout
        self.portable = portable
        self.connection_state = "DISCONNECTED"

        self.default_symbols = (
            default_symbols
            if default_symbols is not None
            else [
                "EURUSD",
                "GBPUSD",
                "USDJPY",
                "AUDUSD",
                "USDCAD",
                "USDCHF",
                "NZDUSD",
            ]
        )

        logger.info(
            "MT5Client initialized",
            extra={
                "path": self.path,
                "login": self.login,
                "server": self.server,
                "default_symbols_count": len(self.default_symbols),
            },
        )

    def connect(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
    ) -> bool:
        """Description.
            Start and initialize MT5 terminal, and login to the trading account.

        Args:
            path: str | None.
            login: int | None.
            password: str | None.
            server: str | None.

        Returns:
            bool.
        """
        logger.debug(
            f"Connecting MT5Client with parameters path={path}, "
            f"login={login}, server={server}."
        )
        if path is not None:
            self.path = path
        if login is not None:
            self.login = login
        if password is not None:
            self.password = password
        if server is not None:
            self.server = server

        self._validate_credentials()
        self._initialize_terminal()

        try:
            self._login_account()
        except Exception:
            # Ensure cleanup if login fails or throws
            mt5.shutdown()
            raise

        self._select_default_symbols()
        self.connection_state = "CONNECTED"
        return True

    def _validate_credentials(self) -> None:
        """Description.
            Validate that required MT5 credentials are provided.

        Args:
            None.

        Returns:
            None.
        """
        if not self.login:
            msg = "MT5 login account ID is required."
            logger.error(msg)
            raise ConfigurationError(msg)
        if not self.password:
            msg = "MT5 password is required."
            logger.error(msg)
            raise ConfigurationError(msg)
        if not self.server:
            msg = "MT5 server name is required."
            logger.error(msg)
            raise ConfigurationError(msg)

    def _initialize_terminal(self) -> None:
        """Description.
            Initialize the MT5 terminal connection.

        Args:
            None.

        Returns:
            None.
        """
        logger.info("Initializing MetaTrader 5 terminal...")
        init_kwargs: dict[str, Any] = {}
        if self.path:
            init_kwargs["path"] = self.path

        try:
            init_success = mt5.initialize(**init_kwargs)
        except Exception as e:
            msg = f"Failed to initialize MetaTrader 5 due to an exception: {e}"
            logger.exception(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        if not init_success:
            err_code = mt5.last_error()
            msg = f"MetaTrader 5 initialization failed. Error code: {err_code}"
            logger.error(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

        logger.info("MetaTrader 5 terminal initialized successfully.")

    def _login_account(self) -> None:
        """Description.
            Log in to the trading account on the initialized terminal.

        Args:
            None.

        Returns:
            None.
        """
        logger.info("Logging in to MetaTrader 5 account...")
        if self.login is None:
            msg = "MT5 login account ID is required."
            logger.error(msg)
            raise ConfigurationError(msg)
        try:
            login_success = mt5.login(
                self.login,
                password=self.password,
                server=self.server,
            )
        except Exception as e:
            msg = f"Failed to login to MetaTrader 5 due to an exception: {e}"
            logger.exception(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

        if not login_success:
            err_code = mt5.last_error()
            msg = (
                f"MetaTrader 5 login failed for account {self.login}. "
                f"Error code: {err_code}"
            )
            logger.error(msg)
            raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

        logger.info("Successfully logged in to MT5 account: {}", self.login)

    def _select_default_symbols(self) -> None:
        """Description.
            Add all default symbols to the terminal Market Watch.

        Args:
            None.

        Returns:
            None.
        """
        successful_symbols = []
        failed_symbols = []
        for symbol in self.default_symbols:
            try:
                selected = mt5.symbol_select(symbol, True)
                if selected:
                    successful_symbols.append(symbol)
                else:
                    err_code = mt5.last_error()
                    failed_symbols.append((symbol, err_code))
                    logger.warning(
                        "Failed to select symbol {} in Market Watch. Error code: {}",
                        symbol,
                        err_code,
                    )
            except Exception as e:  # noqa: BLE001
                failed_symbols.append((symbol, str(e)))
                logger.warning("Exception while selecting symbol {}: {}", symbol, e)

        logger.info(
            "Market Watch symbol selection complete",
            extra={
                "successful_count": len(successful_symbols),
                "failed_count": len(failed_symbols),
                "successful_symbols": successful_symbols,
                "failed_symbols": failed_symbols,
            },
        )

    def is_connected(self) -> bool:
        """Description.
            Check if client is currently connected to the MT5 terminal and server.

        Args:
            None.

        Returns:
            bool.
        """
        try:
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                return False
            return bool(terminal_info.connected)
        except Exception as e:  # noqa: BLE001
            logger.debug("Error checking MT5 connection status: {}", e)
            return False

    def shutdown(self) -> None:
        """Description.
            Shutdown the MT5 terminal connection and clean up resources.

        Args:
            None.

        Returns:
            None.
        """
        logger.info("Shutting down MetaTrader 5 terminal connection...")
        try:
            mt5.shutdown()
            self.connection_state = "DISCONNECTED"
            logger.info("MetaTrader 5 terminal connection shut down successfully.")
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Error during MetaTrader 5 shutdown: {}",
                e,
                exc_info=True,
            )

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        count: int = 100,
        start_pos: int = 0,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> pd.DataFrame:
        """Description.
            Get OHLCVS bars from MT5.

        Args:
            symbol: str.
            timeframe: str.
            count: int.
            start_pos: int.
            date_from: datetime | None.
            date_to: datetime | None.

        Returns:
            pd.DataFrame.
        """
        if not self.is_connected():
            self.connect()

        logger.debug(
            "Fetching MT5 bars for {} (timeframe={}, count={}).",
            symbol,
            timeframe,
            count,
        )

        # map timeframe to MT5 timeframe constants
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M2": mt5.TIMEFRAME_M2,
            "M3": mt5.TIMEFRAME_M3,
            "M4": mt5.TIMEFRAME_M4,
            "M5": mt5.TIMEFRAME_M5,
            "M6": mt5.TIMEFRAME_M6,
            "M10": mt5.TIMEFRAME_M10,
            "M12": mt5.TIMEFRAME_M12,
            "M15": mt5.TIMEFRAME_M15,
            "M20": mt5.TIMEFRAME_M20,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H2": mt5.TIMEFRAME_H2,
            "H3": mt5.TIMEFRAME_H3,
            "H4": mt5.TIMEFRAME_H4,
            "H6": mt5.TIMEFRAME_H6,
            "H8": mt5.TIMEFRAME_H8,
            "H12": mt5.TIMEFRAME_H12,
            "D1": mt5.TIMEFRAME_D1,
            "W1": mt5.TIMEFRAME_W1,
            "MN1": mt5.TIMEFRAME_MN1,
        }

        tf_upper = timeframe.upper()
        if tf_upper not in tf_map:
            msg = f"Unsupported MT5 timeframe: {timeframe}"
            logger.error(msg)
            raise ValueError(msg)
        mt5_tf = tf_map[tf_upper]

        mt5.symbol_select(symbol, True)

        if date_from is not None:
            dt_to = date_to if date_to is not None else datetime.now(UTC)
            rates = mt5.copy_rates_range(symbol, mt5_tf, date_from, dt_to)
        else:
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, start_pos, count)

        cols = ["Timestamp", "Open", "High", "Low", "Close", "Volume", "Spread"]
        if rates is None or len(rates) == 0:
            logger.warning("No MT5 bars returned for {}.", symbol)
            return pd.DataFrame(columns=cols)

        df = pd.DataFrame(rates)
        df["Timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True)
        df = df.rename(
            columns={
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "tick_volume": "Volume",
                "spread": "Spread",
            }
        )
        logger.info("Fetched {} MT5 bars for {}.", len(df), symbol)
        return df[cols]

    def get_ticks(
        self,
        symbol: str,
        count: int = 100,
        start: datetime | None = None,
        end: datetime | None = None,
        flags: int = mt5.COPY_TICKS_ALL,
        as_dataframe: bool = True,
    ) -> pd.DataFrame | list[dict[str, Any]] | None:
        """Description.
            Get ticks from MT5.

        Args:
            symbol: str.
            count: int.
            start: datetime | None.
            end: datetime | None.
            flags: int.
            as_dataframe: bool.

        Returns:
            pd.DataFrame | list[dict[str, Any]] | None.
        """
        if not self.is_connected():
            self.connect()

        logger.debug("Fetching MT5 ticks for {} (count={}).", symbol, count)

        mt5.symbol_select(symbol, True)

        if start is not None:
            dt_end = end if end is not None else datetime.now(UTC)
            ticks = mt5.copy_ticks_range(symbol, start, dt_end, flags)
        else:
            dt_start = datetime.now(UTC) - timedelta(hours=24)
            ticks = mt5.copy_ticks_from(symbol, dt_start, count, flags)

        if ticks is None:
            logger.warning("MT5 returned None ticks for {}.", symbol)
            return None

        if len(ticks) == 0:
            logger.warning("No MT5 ticks returned for {}.", symbol)
            return pd.DataFrame() if as_dataframe else []

        logger.info("Fetched {} MT5 ticks for {}.", len(ticks), symbol)

        if as_dataframe:
            return pd.DataFrame(ticks)

        names = ticks.dtype.names
        return [dict(zip(names, row, strict=False)) for row in ticks]

    @classmethod
    def get_instance(cls) -> "MT5Client":
        """Description.
            Get the shared singleton instance of MT5Client.

        Args:
            None.

        Returns:
            'MT5Client'.
        """
        if cls._instance is None:
            cls._instance = cls()
        logger.debug("Retrieving MT5Client singleton instance.")
        return cls._instance

    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        """Description.
            Delegate attribute/method calls to the underlying MetaTrader5 library.

        Args:
            name: str.

        Returns:
            Any.
        """
        if hasattr(mt5, name):
            attr = getattr(mt5, name)
            if callable(attr) and not self.is_connected():
                logger.info(
                    "MT5 client not connected. Auto-connecting on delegated call: {}",
                    name,
                )
                self.connect()
            return attr
        msg = f"'MT5Client' object has no attribute '{name}'"
        raise AttributeError(msg)


__all__ = [
    "MT5Api",
    "MT5Client",
    "get_account_info",
    "get_connected_mt5_client",
    "get_history_deal_info",
    "get_history_order_info",
    "get_mt5_api",
    "get_mt5_client",
    "get_mt5_credentials",
    "get_order_info",
    "get_position_info",
    "get_symbol_info",
    "get_terminal_info",
    "load_mt5",
    "mt5_data_get_bars_with_credentials",
    "mt5_data_list_symbol_details_with_credentials",
    "mt5_data_list_symbols",
    "trade",
]


def get_mt5_client() -> MT5Client:
    """Description.
        Get the shared singleton instance of MT5Client.

    Args:
        None.

    Returns:
        MT5Client.
    """
    logger.debug("Retrieving active MT5Client instance via public helper.")
    return MT5Client.get_instance()


def _ensure_connected() -> None:
    """Description.
        Ensure the shared MT5Client is initialized and connected.

    Args:
        None.

    Returns:
        None.
    """
    client = get_mt5_client()
    if not client.is_connected():
        logger.info("MT5 client is not connected. Attempting auto-connection...")
        client.connect()


def get_terminal_info() -> Any:  # noqa: ANN401
    """Description.
        Get the MT5 terminal settings and status.

    Args:
        None.

    Returns:
        Any.
    """
    _ensure_connected()
    logger.debug("Fetching MT5 terminal info.")
    return mt5.terminal_info()


def get_account_info() -> Any:  # noqa: ANN401
    """Description.
        Get information on the current trading account.

    Args:
        None.

    Returns:
        Any.
    """
    _ensure_connected()
    logger.debug("Fetching MT5 account info.")
    return mt5.account_info()


def get_symbol_info(symbol: str) -> Any:  # noqa: ANN401
    """Description.
        Get information about a specific symbol.

    Args:
        symbol: str.

    Returns:
        Any.
    """
    _ensure_connected()
    logger.debug("Fetching MT5 symbol info for {}.", symbol)
    mt5.symbol_select(symbol, True)
    return mt5.symbol_info(symbol)


def get_position_info(symbol: str | None = None, ticket: int | None = None) -> Any:  # noqa: ANN401
    """Description.
        Get open positions filtered by symbol or ticket.

    Args:
        symbol: str | None.
        ticket: int | None.

    Returns:
        Any.
    """
    _ensure_connected()
    logger.debug("Fetching MT5 positions (symbol={}, ticket={}).", symbol, ticket)
    if ticket is not None:
        return mt5.positions_get(ticket=ticket)
    if symbol is not None:
        return mt5.positions_get(symbol=symbol)
    return mt5.positions_get()


def get_order_info(symbol: str | None = None, ticket: int | None = None) -> Any:  # noqa: ANN401
    """Description.
        Get active pending orders filtered by symbol or ticket.

    Args:
        symbol: str | None.
        ticket: int | None.

    Returns:
        Any.
    """
    _ensure_connected()
    logger.debug("Fetching MT5 orders (symbol={}, ticket={}).", symbol, ticket)
    if ticket is not None:
        return mt5.orders_get(ticket=ticket)
    if symbol is not None:
        return mt5.orders_get(symbol=symbol)
    return mt5.orders_get()


def get_history_order_info(
    date_from: Any = None,  # noqa: ANN401
    date_to: Any = None,  # noqa: ANN401
    group: str | None = None,
    ticket: int | None = None,
) -> Any:  # noqa: ANN401
    """Description.
        Get historical orders from the specified time frame or ticket.

    Args:
        date_from: Any.
        date_to: Any.
        group: str | None.
        ticket: int | None.

    Returns:
        Any.
    """
    _ensure_connected()
    logger.debug("Fetching MT5 history orders (ticket={}).", ticket)
    if ticket is not None:
        return mt5.history_orders_get(ticket=ticket)

    from_val = date_from if date_from is not None else 1
    to_val = date_to if date_to is not None else datetime.now(UTC)

    if group is not None:
        return mt5.history_orders_get(from_val, to_val, group=group)
    return mt5.history_orders_get(from_val, to_val)


def get_history_deal_info(
    date_from: Any = None,  # noqa: ANN401
    date_to: Any = None,  # noqa: ANN401
    group: str | None = None,
    ticket: int | None = None,
) -> Any:  # noqa: ANN401
    """Description.
        Get historical deals from the specified time frame or ticket.

    Args:
        date_from: Any.
        date_to: Any.
        group: str | None.
        ticket: int | None.

    Returns:
        Any.
    """
    _ensure_connected()
    logger.debug("Fetching MT5 history deals (ticket={}).", ticket)
    if ticket is not None:
        return mt5.history_deals_get(ticket=ticket)

    from_val = date_from if date_from is not None else 1
    to_val = date_to if date_to is not None else datetime.now(UTC)

    if group is not None:
        return mt5.history_deals_get(from_val, to_val, group=group)
    return mt5.history_deals_get(from_val, to_val)


def trade(request: dict[str, Any]) -> Any:  # noqa: ANN401
    """Description.
        Send a trading request to the MT5 terminal.

    Args:
        request: dict[str, Any].

    Returns:
        Any.
    """
    _ensure_connected()
    try:
        result = mt5.order_send(request)
    except Exception as e:
        msg = f"Failed to send trade order due to exception: {e}"
        logger.exception(msg)
        raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE") from e

    if result is None:
        err_code = mt5.last_error()
        msg = f"Trade execution failed: order_send returned None. Error: {err_code}"
        logger.error(msg)
        raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

    if hasattr(result, "retcode") and result.retcode not in (10009, 10008):
        msg = (
            f"Trade order rejected. Retcode: {result.retcode}, "
            f"Comment: {getattr(result, 'comment', '')}"
        )
        logger.error(msg)
        raise ExternalServiceError(msg, code="BROKER_UNAVAILABLE")

    return result


def get_mt5_api() -> MT5Api:
    """Description.
        Return the shared MT5 API wrapper.

    Args:
        None.

    Returns:
        MT5Api.
    """
    logger.debug("Retrieving standard MetaTrader5 package API wrapper.")
    return _MT5_API


def get_mt5_credentials(
    user_id: int = 1,
    mt5_login: int | None = None,
) -> dict[str, Any] | None:
    """Description.
        Load stored MT5 credentials from the application database.

    Args:
        user_id: int.
        mt5_login: int | None.

    Returns:
        dict[str, Any] | None.
    """
    logger.debug(
        f"Loading stored MT5 credentials for user_id={user_id}, login={mt5_login}."
    )
    user_manager = UserManager()
    if mt5_login is not None:
        return cast(
            "dict[str, Any] | None",
            user_manager.get_mt5_credentials_by_login(user_id, mt5_login),
        )
    return cast("dict[str, Any] | None", user_manager.get_mt5_credentials(user_id))


def get_connected_mt5_client(
    user_id: int = 1,
    mt5_login: int | None = None,
) -> MT5Client | None:
    """Description.
        Create and connect an MT5 client using stored credentials.

    Args:
        user_id: int.
        mt5_login: int | None.

    Returns:
        MT5Client | None.
    """
    credentials = get_mt5_credentials(user_id=user_id, mt5_login=mt5_login)
    if not credentials:
        logger.error("No MT5 credentials available for user {}", user_id)
        return None

    client = MT5Client(
        path=credentials.get("path") or "",
        login=credentials.get("login"),
        password=credentials.get("password"),
        server=credentials.get("server"),
    )
    try:
        if client.connect():
            return client
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to connect MT5 client: {}", exc)
    client.shutdown()
    return None


def _load_mt5_impl(
    symbol: str,
    timeframe: str = "H1",
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    count: int | None = 0,
    user_id: int = 1,
    mt5_login: int | None = None,
) -> pd.DataFrame | None:
    """Description.
        Load OHLCV data from MT5 using stored credentials.

    Args:
        symbol: str.
        timeframe: str.
        start_date: str | datetime | None.
        end_date: str | datetime | None.
        count: int | None.
        user_id: int.
        mt5_login: int | None.

    Returns:
        pd.DataFrame | None.
    """
    logger.debug(
        f"Executing raw MT5 load operations for symbol={symbol}, timeframe={timeframe}."
    )
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    client = get_connected_mt5_client(user_id=user_id, mt5_login=mt5_login)
    if client is None:
        return None
    try:
        bars = client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            count=count if count and count > 0 else 1000,
            date_from=start_date,
            date_to=end_date,
        )
        if bars is None or bars.empty:
            return None
        return prepare_ohlcv_data(bars)
    finally:
        client.shutdown()


def load_mt5(
    symbol: str,
    timeframe: str = "H1",
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    count: int | None = 0,
    user_id: int = 1,
    mt5_login: int | None = None,
    request_id: str | None = None,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Description.
        Load OHLCV bars from MetaTrader 5 using stored credentials.

    Args:
        symbol: str.
        timeframe: str.
        start_date: str | datetime | None.
        end_date: str | datetime | None.
        count: int | None.
        user_id: int.
        mt5_login: int | None.
        request_id: str | None.
        _kwargs: Any.

    Returns:
        dict[str, Any].
    """
    logger.debug(
        f"Initiating public MT5 load workflow for symbol={symbol}, "
        f"timeframe={timeframe}, request_id={request_id}."
    )
    if not symbol:
        return {"status": "error", "message": "symbol argument is required."}
    try:
        frame = _load_mt5_impl(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            count=count,
            user_id=user_id,
            mt5_login=mt5_login,
        )
        if frame is None or frame.empty:
            return {"status": "error", "message": "No MT5 bars were returned."}
        return {
            "status": "success",
            "message": "MT5 data loaded successfully.",
            "data": {
                "source": "load_mt5",
                "symbol": symbol,
                "timeframe": timeframe,
                "rows": len(frame),
                "columns": [str(column) for column in frame.columns],
                "data": bars_to_records(frame),
            },
            "request_id": request_id,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Tool execution failed: {exc!s}"}


def _mt5_data_get_bars_with_credentials_impl(
    *,
    symbol: str,
    timeframe: str,
    login: int,
    password: str,
    server: str,
    path: str = "",
    count: int = 100,
    start_pos: int = 0,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> pd.DataFrame:
    """Description.
        Connect to MT5 with credentials, fetch bars, and close the client.

    Args:
        symbol: str.
        timeframe: str.
        login: int.
        password: str.
        server: str.
        path: str.
        count: int.
        start_pos: int.
        date_from: datetime | None.
        date_to: datetime | None.

    Returns:
        pd.DataFrame.
    """
    logger.debug(
        f"Retrieving bars from MT5 with explicit credentials for "
        f"symbol={symbol}, timeframe={timeframe}."
    )
    client = MT5Client(path=path, login=login, password=password, server=server)
    try:
        if not client.connect():
            return pd.DataFrame()
        return client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            start_pos=start_pos,
            date_from=date_from,
            date_to=date_to,
        )
    finally:
        client.shutdown()


def mt5_data_get_bars_with_credentials(
    *,
    symbol: str,
    timeframe: str,
    login: int,
    password: str,
    server: str,
    path: str = "",
    count: int = 100,
    start_pos: int = 0,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Load MT5 bars with explicit credentials.

    Args:
        symbol: str.
        timeframe: str.
        login: int.
        password: str.
        server: str.
        path: str.
        count: int.
        start_pos: int.
        date_from: datetime | None.
        date_to: datetime | None.
        request_id: str | None.

    Returns:
        dict[str, Any].
    """
    logger.debug(
        f"Public API loaded MT5 bars with explicit credentials for "
        f"symbol={symbol}, timeframe={timeframe}, request_id={request_id}."
    )
    try:
        frame = _mt5_data_get_bars_with_credentials_impl(
            symbol=symbol,
            timeframe=timeframe,
            login=login,
            password=password,
            server=server,
            path=path,
            count=count,
            start_pos=start_pos,
            date_from=date_from,
            date_to=date_to,
        )
        return {
            "status": "success",
            "message": "MT5 credential data loaded successfully.",
            "data": {
                "rows": len(frame),
                "columns": [str(column) for column in frame.columns],
                "data": bars_to_records(prepare_ohlcv_data(frame))
                if not frame.empty
                else [],
            },
            "request_id": request_id,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Tool execution failed: {exc!s}"}


def _mt5_data_list_symbol_details_with_credentials_impl(
    *,
    login: int,
    password: str,
    server: str,
    path: str = "",
) -> list[dict[str, Any]]:
    """Description.
        Connect to MT5 with credentials and return JSON-safe symbol metadata.

    Args:
        login: int.
        password: str.
        server: str.
        path: str.

    Returns:
        list[dict[str, Any]].
    """
    logger.debug(
        f"Retrieving symbol metadata details from MT5 with "
        f"credentials for login={login}."
    )
    client = MT5Client(path=path, login=login, password=password, server=server)
    try:
        if not client.connect():
            return []
        symbols = client.symbols_get()
        if symbols is None:
            return []
        result: list[dict[str, Any]] = []
        for symbol_info in symbols:
            name = getattr(symbol_info, "name", "")
            path_value = getattr(symbol_info, "path", "")
            result.append(
                {
                    "symbol": name,
                    "name": getattr(symbol_info, "description", name) or name,
                    "category": str(path_value).split("\\")[0]
                    if path_value
                    else "Other",
                    "path": path_value,
                }
            )
        return result
    finally:
        client.shutdown()


def mt5_data_list_symbol_details_with_credentials(
    *,
    login: int,
    password: str,
    server: str,
    path: str = "",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        List MT5 symbol metadata with explicit credentials.

    Args:
        login: int.
        password: str.
        server: str.
        path: str.
        request_id: str | None.

    Returns:
        dict[str, Any].
    """
    logger.debug(
        f"Public API listing MT5 symbol metadata with credentials "
        f"(request_id={request_id})."
    )
    try:
        symbols = _mt5_data_list_symbol_details_with_credentials_impl(
            login=login,
            password=password,
            server=server,
            path=path,
        )
        return {
            "status": "success",
            "message": "MT5 symbols loaded successfully.",
            "data": {"symbols": symbols},
            "request_id": request_id,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Tool execution failed: {exc!s}"}


def mt5_data_list_symbols(
    pattern: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        List available MT5 symbols from the local terminal.

    Args:
        pattern: str | None.
        request_id: str | None.

    Returns:
        dict[str, Any].
    """
    logger.debug(
        f"Listing available MT5 symbols matching pattern={pattern} "
        f"(request_id={request_id})."
    )
    try:
        symbols = mt5.symbols_get()
        names = [symbol.name for symbol in symbols] if symbols else []
        if pattern:
            import fnmatch

            names = [
                name for name in names if fnmatch.fnmatch(name.lower(), pattern.lower())
            ]
        return {
            "status": "success",
            "message": "MT5 symbols loaded successfully.",
            "data": {"symbols": names},
            "request_id": request_id,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "message": f"Tool execution failed: {exc!s}"}
