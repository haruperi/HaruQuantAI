"""MetaTrader 5 market-data tools for HaruQuantAI.

Purpose:
    Provide safe, read-only, agent-callable MT5 market-data tools that load
    credentials from environment variables instead of accepting raw credentials
    in tool arguments.

Exported AI Tools:
    - mt5_connection_check: Check whether MT5 integration is enabled and can connect.
    - mt5_data_list_symbols: List broker-supported MT5 symbols.
    - mt5_data_get_bars: Fetch OHLCVS bars from MT5.
    - mt5_data_list_symbol_details: List JSON-safe symbol metadata.

Credential Source:
    Environment variables, usually loaded from `.env`:
        MT5_ENABLED
        MT5_LOGIN
        MT5_PASSWORD
        MT5_SERVER
        MT5_TERMINAL_PATH
        MT5_ENVIRONMENT

Internal Helpers:
    - _load_mt5_credentials_from_env: Load and validate MT5 credentials.
    - _validate_symbol: Validate symbol inputs.
    - _validate_timeframe: Validate timeframe inputs.
    - _standard_success/_standard_error: Build standard tool responses.

Classes:
    - MT5Credentials: Immutable MT5 credential/configuration object.
    - MT5Api: Thin wrapper around the MetaTrader5 module.
    - MT5Client: Small MT5 client focused on read-only market-data operations.

Safety:
    This module does not place trades, close positions, modify broker state,
    write files, or modify databases. Passwords are never returned or logged.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd
from dotenv import load_dotenv as _load_dotenv

try:  # pragma: no cover - exercised through mocks in unit tests.
    import MetaTrader5 as _mt5_module
except ImportError:  # pragma: no cover - allows tests/dev machines without MT5.
    _mt5_module = None

from tools.utils.logger import logger
from tools.utils.standard import ToolStandardSpec, standard_tool_response

from ._common import _filter_symbols, _serialize_frame_records

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = True

MT5_CONNECTION_CHECK_TOOL = "mt5_connection_check"
MT5_LIST_SYMBOLS_TOOL = "mt5_data_list_symbols"
MT5_GET_BARS_TOOL = "mt5_data_get_bars"
MT5_LIST_SYMBOL_DETAILS_TOOL = "mt5_data_list_symbol_details"

ENV_MT5_ENABLED = "MT5_ENABLED"
ENV_MT5_LOGIN = "MT5_LOGIN"
ENV_MT5_PASSWORD = "MT5_PASSWORD"
ENV_MT5_SERVER = "MT5_SERVER"
ENV_MT5_TERMINAL_PATH = "MT5_TERMINAL_PATH"
ENV_MT5_ENVIRONMENT = "MT5_ENVIRONMENT"

SUPPORTED_ENVIRONMENTS = frozenset({"demo", "live", "test", "paper"})
SUPPORTED_TIMEFRAMES = frozenset(
    {
        "M1",
        "M2",
        "M3",
        "M4",
        "M5",
        "M6",
        "M10",
        "M12",
        "M15",
        "M20",
        "M30",
        "H1",
        "H2",
        "H3",
        "H4",
        "H6",
        "H8",
        "H12",
        "D1",
        "W1",
        "MN1",
    }
)

REQUIRED_BAR_COLUMNS = frozenset({"open", "high", "low", "close"})
DEFAULT_TIMEOUT_MS = 60_000
DEFAULT_BARS = 100


@dataclass(frozen=True)
class MT5Credentials:
    """Validated MT5 credentials loaded from environment variables.

    Attributes:
        enabled: Whether MT5 integration is enabled.
        login: MT5 account login number.
        password: MT5 account password. This must never be logged or returned.
        server: MT5 broker server name.
        terminal_path: Optional Windows MT5 terminal executable path.
        environment: Account environment label such as "demo" or "live".
        timeout_ms: MT5 connection timeout in milliseconds.
        portable: Whether MT5 should be initialized in portable mode.
    """

    enabled: bool
    login: int
    password: str
    server: str
    terminal_path: str = ""
    environment: str = "demo"
    timeout_ms: int = DEFAULT_TIMEOUT_MS
    portable: bool = False

    @property
    def masked_login(self) -> str:
        """Return a redacted login value suitable for logs and responses."""
        text = str(self.login)
        return f"***{text[-4:]}" if len(text) > 4 else "***"


class ConnectionState(str, Enum):
    """Connection state for the local MT5 terminal session."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    FAILED = "failed"
    INITIALIZING = "initializing"


class MT5Api:
    """Thin wrapper around the MetaTrader5 Python module.

    This wrapper improves testability and avoids direct global usage of the
    MetaTrader5 module in official tool functions.
    """

    def __init__(self, mt5_module: Optional[Any] = None) -> None:
        """Initialize the wrapper with an optional injected MT5 module."""
        self._mt5 = mt5_module if mt5_module is not None else _mt5_module
        self._initialized = False

    def is_available(self) -> bool:
        """Return whether the MetaTrader5 module is importable."""
        return self._mt5 is not None

    def initialize(self, **kwargs: Any) -> bool:
        """Initialize the MT5 terminal connection."""
        if self._mt5 is None or not hasattr(self._mt5, "initialize"):
            return False
        ok = bool(self._mt5.initialize(**kwargs))
        self._initialized = ok
        return ok

    def login(self, **kwargs: Any) -> bool:
        """Login to an MT5 account."""
        if self._mt5 is None or not hasattr(self._mt5, "login"):
            return False
        return bool(self._mt5.login(**kwargs))

    def shutdown(self) -> None:
        """Shutdown the MT5 terminal connection when possible."""
        if self._mt5 is not None and hasattr(self._mt5, "shutdown"):
            self._mt5.shutdown()
        self._initialized = False

    def last_error(self) -> Any:
        """Return the last MT5 error if the module exposes it."""
        if self._mt5 is None or not hasattr(self._mt5, "last_error"):
            return None
        return self._mt5.last_error()

    def is_initialized(self) -> bool:
        """Return whether initialize succeeded in this wrapper instance."""
        return self._initialized

    def __getattr__(self, name: str) -> Any:
        """Delegate supported MT5 module attributes."""
        if self._mt5 is None:
            raise AttributeError("MetaTrader5 module is unavailable.")
        return getattr(self._mt5, name)


class MT5Client:
    """Small read-only MT5 client for market-data operations.

    The client can connect using validated `.env` credentials and retrieve
    symbols, symbol metadata, and OHLCVS bars. It intentionally does not expose
    trading operations.
    """

    def __init__(self, api: Optional[MT5Api] = None) -> None:
        """Initialize the client with an optional MT5 API wrapper."""
        self.api = api or MT5Api()
        self.connection_state = ConnectionState.DISCONNECTED
        self._credentials: Optional[MT5Credentials] = None

    def connect(self, credentials: MT5Credentials) -> bool:
        """Connect to the local MT5 terminal using validated credentials."""
        if not credentials.enabled:
            logger.warning("MT5 connection blocked because MT5_ENABLED is false")
            self.connection_state = ConnectionState.FAILED
            return False
        if not self.api.is_available():
            logger.warning("MetaTrader5 Python package is unavailable")
            self.connection_state = ConnectionState.FAILED
            return False

        self.connection_state = ConnectionState.INITIALIZING
        initialize_kwargs: dict[str, Any] = {
            "timeout": credentials.timeout_ms,
            "portable": credentials.portable,
        }
        if credentials.terminal_path.strip():
            initialize_kwargs["path"] = credentials.terminal_path.strip()

        logger.info(
            "Initializing MT5 terminal | login=%s | environment=%s | "
            "path_configured=%s",
            credentials.masked_login,
            credentials.environment,
            bool(credentials.terminal_path.strip()),
        )
        if not self.api.initialize(**initialize_kwargs):
            logger.warning(
                "MT5 terminal initialization failed | error=%s", self.api.last_error()
            )
            self.connection_state = ConnectionState.FAILED
            return False

        if not self.api.login(
            login=credentials.login,
            password=credentials.password,
            server=credentials.server,
            timeout=credentials.timeout_ms,
        ):
            logger.warning(
                "MT5 account login failed | login=%s | error=%s",
                credentials.masked_login,
                self.api.last_error(),
            )
            self.connection_state = ConnectionState.FAILED
            return False

        self._credentials = credentials
        self.connection_state = ConnectionState.CONNECTED
        logger.info(
            "MT5 connected successfully | login=%s | environment=%s",
            credentials.masked_login,
            credentials.environment,
        )
        return True

    def shutdown(self) -> None:
        """Close the MT5 terminal connection."""
        self.api.shutdown()
        self.connection_state = ConnectionState.DISCONNECTED

    def is_connected(self) -> bool:
        """Return whether this client believes it is connected."""
        return self.connection_state == ConnectionState.CONNECTED

    def timeframe_to_mt5(self, timeframe: str) -> int:
        """Convert HaruQuant timeframe text to an MT5 timeframe constant."""
        normalized = timeframe.upper()
        attr_name = f"TIMEFRAME_{normalized}"
        if not hasattr(self.api, attr_name):
            raise ValueError(f"MT5 timeframe constant is unavailable: {attr_name}")
        return int(getattr(self.api, attr_name))

    def list_symbols(self) -> list[str]:
        """Return available MT5 symbol names."""
        symbols = self.api.symbols_get()
        if symbols is None:
            return []
        return [
            str(getattr(symbol, "name", ""))
            for symbol in symbols
            if getattr(symbol, "name", "")
        ]

    def list_symbol_details(self) -> list[dict[str, Any]]:
        """Return JSON-safe symbol metadata from MT5."""
        symbols = self.api.symbols_get()
        if symbols is None:
            return []

        details: list[dict[str, Any]] = []
        for symbol_info in symbols:
            name = str(getattr(symbol_info, "name", ""))
            if not name:
                continue
            path_value = str(getattr(symbol_info, "path", "") or "")
            category = path_value.split("\\", maxsplit=1)[0] if path_value else "Other"
            details.append(
                {
                    "symbol": name,
                    "name": str(getattr(symbol_info, "description", name) or name),
                    "category": category,
                    "path": path_value,
                }
            )
        return details

    def get_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        count: int = DEFAULT_BARS,
        start_pos: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Fetch OHLCVS bars from MT5 as a normalized DataFrame."""
        if not self.is_connected():
            raise RuntimeError("MT5 client is not connected.")

        mt5_timeframe = self.timeframe_to_mt5(timeframe)
        if date_from is not None:
            clean_from = _strip_timezone(date_from)
            if date_to is not None:
                rates = self.api.copy_rates_range(
                    symbol, mt5_timeframe, clean_from, _strip_timezone(date_to)
                )
            else:
                rates = self.api.copy_rates_from(
                    symbol, mt5_timeframe, clean_from, count
                )
        else:
            rates = self.api.copy_rates_from_pos(
                symbol, mt5_timeframe, start_pos, count
            )

        if rates is None:
            raise RuntimeError(
                f"MT5 returned no rates. last_error={self.api.last_error()}"
            )

        frame = pd.DataFrame(rates)
        if frame.empty:
            return frame
        return _normalize_rates_frame(frame)

    def __repr__(self) -> str:
        """Return safe representation without exposing credentials."""
        login = self._credentials.masked_login if self._credentials else "not_connected"
        return f"MT5Client(state={self.connection_state.value}, login={login})"

    def __enter__(self) -> "MT5Client":
        """Return this client for context-manager usage."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Shutdown MT5 when leaving a context manager."""
        self.shutdown()


_MT5_API = MT5Api()


def get_mt5_api() -> MT5Api:
    """Return the shared MT5 API wrapper for internal code and tests."""
    return _MT5_API


def _tool_spec(tool_name: str) -> ToolStandardSpec:
    """Build the standard HaruQuant tool metadata object."""
    return ToolStandardSpec(
        tool_name=tool_name,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=TOOL_RISK_LEVEL,
        requires_approval=REQUIRES_APPROVAL,
        read_only=READ_ONLY,
        writes_file=WRITES_FILE,
        modifies_database=MODIFIES_DATABASE,
        places_trade=PLACES_TRADE,
        requires_network=REQUIRES_NETWORK,
    )


def _execution_ms(started_at: float) -> float:
    """Return elapsed execution time in milliseconds."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _standard_success(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    message: str,
    data: Any,
) -> Dict[str, Any]:
    """Return a standard successful tool response."""
    return standard_tool_response(
        _tool_spec(tool_name),
        "success",
        message,
        data=data,
        request_id=request_id,
        execution_ms=_execution_ms(started_at),
    )


def _standard_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    code: str,
    message: str,
    details: str,
) -> Dict[str, Any]:
    """Return a standard error tool response."""
    return standard_tool_response(
        _tool_spec(tool_name),
        "error",
        message,
        data=None,
        error={"code": code, "details": details},
        request_id=request_id,
        execution_ms=_execution_ms(started_at),
    )


def _parse_bool(value: Optional[str], *, default: bool) -> bool:
    """Parse a boolean-like environment variable."""
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _load_mt5_credentials_from_env(
    env_file: Optional[Union[str, Path]] = None,
) -> MT5Credentials:
    """Load MT5 credentials from `.env` or process environment.

    Args:
        env_file: Optional path to a dotenv file. When omitted, python-dotenv
            uses its default discovery behavior.

    Returns:
        MT5Credentials: Validated credential object.

    Raises:
        ValueError: If required environment variables are missing or invalid.
    """
    if env_file is not None:
        _load_dotenv(dotenv_path=Path(env_file), override=False)
    else:
        _load_dotenv(override=False)

    enabled = _parse_bool(os.getenv(ENV_MT5_ENABLED), default=False)
    raw_login = os.getenv(ENV_MT5_LOGIN, "").strip()
    password = os.getenv(ENV_MT5_PASSWORD, "")
    server = os.getenv(ENV_MT5_SERVER, "").strip()
    terminal_path = os.getenv(ENV_MT5_TERMINAL_PATH, "").strip()
    environment = os.getenv(ENV_MT5_ENVIRONMENT, "demo").strip().lower()

    if not enabled:
        raise ValueError(f"{ENV_MT5_ENABLED} must be true before MT5 tools can run.")
    if not raw_login:
        raise ValueError(f"{ENV_MT5_LOGIN} is required.")
    try:
        login = int(raw_login)
    except ValueError as error:
        raise ValueError(f"{ENV_MT5_LOGIN} must be an integer.") from error
    if login <= 0:
        raise ValueError(f"{ENV_MT5_LOGIN} must be positive.")
    if not password:
        raise ValueError(f"{ENV_MT5_PASSWORD} is required.")
    if not server:
        raise ValueError(f"{ENV_MT5_SERVER} is required.")
    if environment not in SUPPORTED_ENVIRONMENTS:
        supported = ", ".join(sorted(SUPPORTED_ENVIRONMENTS))
        raise ValueError(f"{ENV_MT5_ENVIRONMENT} must be one of: {supported}.")

    return MT5Credentials(
        enabled=enabled,
        login=login,
        password=password,
        server=server,
        terminal_path=terminal_path,
        environment=environment,
    )


def _strip_timezone(value: datetime) -> datetime:
    """Return a timezone-naive datetime for the MT5 Python API."""
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def _validate_symbol(symbol: Any) -> Optional[str]:
    """Return an error message when a symbol is invalid."""
    if not isinstance(symbol, str) or not symbol.strip():
        return "symbol must be a non-empty string."
    return None


def _validate_timeframe(timeframe: Any) -> Optional[str]:
    """Return an error message when a timeframe is invalid."""
    if not isinstance(timeframe, str) or not timeframe.strip():
        return "timeframe must be a non-empty string."
    if timeframe.upper() not in SUPPORTED_TIMEFRAMES:
        return f"timeframe must be one of: {', '.join(sorted(SUPPORTED_TIMEFRAMES))}."
    return None


def _validate_positive_int(value: Any, name: str) -> Optional[str]:
    """Return an error message when a value is not a positive int."""
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return f"{name} must be a positive integer."
    return None


def _validate_non_negative_int(value: Any, name: str) -> Optional[str]:
    """Return an error message when a value is not a non-negative int."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        return f"{name} must be a non-negative integer."
    return None


def _validate_optional_datetime(value: Any, name: str) -> Optional[str]:
    """Return an error message when an optional datetime is invalid."""
    if value is not None and not isinstance(value, datetime):
        return f"{name} must be a datetime instance when provided."
    return None


def _validate_date_range(
    date_from: Optional[datetime], date_to: Optional[datetime]
) -> Optional[str]:
    """Return an error message when a datetime range is invalid."""
    return (
        _validate_optional_datetime(date_from, "date_from")
        or _validate_optional_datetime(date_to, "date_to")
        or (
            "date_from must be earlier than or equal to date_to."
            if date_from is not None and date_to is not None and date_from > date_to
            else None
        )
    )


def _normalize_rates_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize an MT5 rates DataFrame into HaruQuant OHLCVS format."""
    if "time" not in frame.columns:
        raise ValueError("MT5 rates are missing required 'time' column.")
    lower_columns = {str(column).lower(): column for column in frame.columns}
    missing = REQUIRED_BAR_COLUMNS - set(lower_columns)
    if missing:
        raise ValueError(f"MT5 rates missing required columns: {sorted(missing)}")

    normalized = frame.copy()
    normalized.columns = [str(column).lower() for column in normalized.columns]
    normalized["time"] = pd.to_datetime(normalized["time"], unit="s")
    if "tick_volume" in normalized.columns and "volume" not in normalized.columns:
        normalized["volume"] = normalized["tick_volume"]
    if "spread" not in normalized.columns:
        normalized["spread"] = 0

    normalized = normalized[
        ["time", "open", "high", "low", "close", "volume", "spread"]
    ]
    normalized = normalized.rename(columns={"time": "timestamp"})
    normalized = normalized.set_index("timestamp").sort_index()
    return normalized


def _validate_bars_frame(frame: pd.DataFrame) -> Optional[str]:
    """Return an error message when normalized bar data is invalid."""
    if not isinstance(frame, pd.DataFrame):
        return "MT5 bars result must be a pandas DataFrame."
    if frame.empty:
        return "MT5 returned no bars."
    missing = REQUIRED_BAR_COLUMNS - set(map(str.lower, frame.columns))
    if missing:
        return f"MT5 bars are missing required columns: {sorted(missing)}."
    return None


def _connect_client() -> MT5Client:
    """Create and connect an MT5 client using `.env` credentials."""
    credentials = _load_mt5_credentials_from_env()
    client = MT5Client(api=get_mt5_api())
    if not client.connect(credentials):
        client.shutdown()
        raise RuntimeError("Failed to connect to MT5 terminal using .env credentials.")
    return client


def mt5_connection_check(request_id: Optional[str] = None) -> Dict[str, Any]:
    """Check whether MT5 is enabled, configured, and connectable.

    Use this read-only tool before MT5 workflows to verify that the local
    terminal, environment credentials, and Python package are available.

    Args:
        request_id: Optional workflow/request ID for traceable logs.

    Returns:
        Dict[str, Any]: Standard tool response with connection status and
        redacted account metadata.
    """
    tool_name = MT5_CONNECTION_CHECK_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        credentials = _load_mt5_credentials_from_env()
    except ValueError as error:
        logger.warning(
            "%s validation failed | request_id=%s | reason=%s",
            tool_name,
            request_id,
            error,
        )
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="INVALID_INPUT",
            message="MT5 environment configuration is invalid.",
            details=str(error),
        )

    client = MT5Client(api=get_mt5_api())
    try:
        if not client.connect(credentials):
            return _standard_error(
                tool_name=tool_name,
                started_at=started_at,
                request_id=request_id,
                code="BROKER_UNAVAILABLE",
                message="MT5 connection failed.",
                details="The local MT5 terminal could not be initialized or logged in.",
            )
        data = {
            "connected": True,
            "login": credentials.masked_login,
            "environment": credentials.environment,
            "server_configured": bool(credentials.server),
            "terminal_path_configured": bool(credentials.terminal_path),
        }
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _standard_success(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="MT5 connection checked successfully.",
            data=data,
        )
    except Exception as error:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="TOOL_EXECUTION_FAILED",
            message="Tool execution failed.",
            details=str(error),
        )
    finally:
        client.shutdown()


def mt5_data_list_symbols(
    pattern: Any = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """List available MT5 symbols from the configured local terminal.

    Use this read-only tool when an agent needs to discover broker-supported
    symbols before requesting market data or validating a trading universe.

    Args:
        pattern: Optional shell-style pattern filter, for example "EUR*".
        request_id: Optional workflow/request ID for traceable logs.

    Returns:
        Dict[str, Any]: Standard tool response with symbols in data["symbols"].
    """
    tool_name = MT5_LIST_SYMBOLS_TOOL
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | pattern=%s", tool_name, request_id, pattern
    )

    if pattern is not None and not isinstance(pattern, str):
        logger.warning(
            "%s validation failed | request_id=%s | reason=invalid_pattern",
            tool_name,
            request_id,
        )
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="INVALID_INPUT",
            message="Invalid input.",
            details="pattern must be a string or None.",
        )

    try:
        client = _connect_client()
        try:
            symbols = _filter_symbols(client.list_symbols(), pattern)
        finally:
            client.shutdown()
        return _standard_success(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="MT5 symbols listed successfully.",
            data={"symbols": symbols, "count": len(symbols)},
        )
    except ValueError as error:
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="INVALID_INPUT",
            message="MT5 environment configuration is invalid.",
            details=str(error),
        )
    except RuntimeError as error:
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="BROKER_UNAVAILABLE",
            message="MT5 broker connection is unavailable.",
            details=str(error),
        )
    except Exception as error:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="TOOL_EXECUTION_FAILED",
            message="Tool execution failed.",
            details=str(error),
        )


def mt5_data_get_bars(
    *,
    symbol: str,
    timeframe: str = "H1",
    count: int = DEFAULT_BARS,
    start_pos: int = 0,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Load OHLCVS bars from MT5 using credentials from `.env`.

    Use this read-only tool when an agent needs historical MT5 market data for
    analysis, validation, or backtesting preparation. The tool never accepts raw
    passwords as arguments.

    Args:
        symbol: Trading symbol, for example "EURUSD".
        timeframe: MT5 timeframe, for example "M1", "H1", or "D1".
        count: Number of bars to fetch when date_from is not provided.
        start_pos: Start position for position-based reads.
        date_from: Optional start datetime for date-based reads.
        date_to: Optional end datetime for date-range reads.
        request_id: Optional workflow/request ID for traceable logs.

    Returns:
        Dict[str, Any]: Standard tool response with row count, columns, and
        serialized bars in data["data"].
    """
    tool_name = MT5_GET_BARS_TOOL
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | symbol=%s | timeframe=%s",
        tool_name,
        request_id,
        symbol,
        timeframe,
    )

    validation_error = (
        _validate_symbol(symbol)
        or _validate_timeframe(timeframe)
        or _validate_positive_int(count, "count")
        or _validate_non_negative_int(start_pos, "start_pos")
        or _validate_date_range(date_from, date_to)
    )
    if validation_error:
        logger.warning(
            "%s validation failed | request_id=%s | reason=%s",
            tool_name,
            request_id,
            validation_error,
        )
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="INVALID_INPUT",
            message="Invalid input.",
            details=validation_error,
        )

    try:
        client = _connect_client()
        try:
            frame = client.get_bars(
                symbol=symbol.strip(),
                timeframe=timeframe.upper(),
                count=count,
                start_pos=start_pos,
                date_from=date_from,
                date_to=date_to,
            )
        finally:
            client.shutdown()

        frame_error = _validate_bars_frame(frame)
        if frame_error:
            return _standard_error(
                tool_name=tool_name,
                started_at=started_at,
                request_id=request_id,
                code="DATA_NOT_FOUND",
                message="No MT5 data found.",
                details=frame_error,
            )

        payload = {
            "source": "mt5",
            "symbol": symbol.strip(),
            "timeframe": timeframe.upper(),
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "data": _serialize_frame_records(frame),
        }
        logger.info(
            "%s completed successfully | request_id=%s | rows=%s",
            tool_name,
            request_id,
            payload["rows"],
        )
        return _standard_success(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="MT5 data loaded successfully.",
            data=payload,
        )
    except ValueError as error:
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="INVALID_INPUT",
            message="Invalid MT5 request or environment configuration.",
            details=str(error),
        )
    except RuntimeError as error:
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="BROKER_UNAVAILABLE",
            message="MT5 broker connection is unavailable.",
            details=str(error),
        )
    except Exception as error:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="TOOL_EXECUTION_FAILED",
            message="Tool execution failed.",
            details=str(error),
        )


def mt5_data_list_symbol_details(request_id: Optional[str] = None) -> Dict[str, Any]:
    """List JSON-safe MT5 symbol metadata using `.env` credentials.

    Use this read-only tool when an agent needs broker symbol descriptions,
    categories, or broker symbol paths from the configured MT5 account.

    Args:
        request_id: Optional workflow/request ID for traceable logs.

    Returns:
        Dict[str, Any]: Standard tool response with metadata in data["symbols"].
    """
    tool_name = MT5_LIST_SYMBOL_DETAILS_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        client = _connect_client()
        try:
            details = client.list_symbol_details()
        finally:
            client.shutdown()

        if not details:
            return _standard_error(
                tool_name=tool_name,
                started_at=started_at,
                request_id=request_id,
                code="EMPTY_RESULT",
                message="No MT5 symbols found.",
                details="The MT5 terminal returned no symbol metadata.",
            )

        return _standard_success(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="MT5 symbol details listed successfully.",
            data={"symbols": details, "count": len(details)},
        )
    except ValueError as error:
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="INVALID_INPUT",
            message="MT5 environment configuration is invalid.",
            details=str(error),
        )
    except RuntimeError as error:
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="BROKER_UNAVAILABLE",
            message="MT5 broker connection is unavailable.",
            details=str(error),
        )
    except Exception as error:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _standard_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            code="TOOL_EXECUTION_FAILED",
            message="Tool execution failed.",
            details=str(error),
        )


_TOOL_MARKER = "_haruquant_standardized_tool"
setattr(mt5_connection_check, _TOOL_MARKER, True)
setattr(mt5_data_get_bars, _TOOL_MARKER, True)
setattr(mt5_data_list_symbol_details, _TOOL_MARKER, True)
setattr(mt5_data_list_symbols, _TOOL_MARKER, True)


__all__ = [
    "ConnectionState",
    "MT5Api",
    "MT5Client",
    "MT5Credentials",
    "get_mt5_api",
    "mt5_connection_check",
    "mt5_data_get_bars",
    "mt5_data_list_symbol_details",
    "mt5_data_list_symbols",
]
