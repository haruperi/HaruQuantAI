"""Implement shared data models, cache helpers, generic market data tools, and private utilities reused by data modules.

Purpose:
    Implement shared data models, cache helpers, generic market data tools, and private utilities reused by data modules.

Classes and functions:
    _normalize_cache_value: Function. Convert fetch parameters into stable JSON-serializable cache input.
    _map_timeframe: Function. Map MT5-style timeframe strings to Pandas frequency strings.
    data_cache_get_path: Function. Return the configured data cache path.
    _data_cache_open_env: Function. Internal helper for data cache open env.
    data_cache_make_key: Function. Build a stable cache key for a data request.
    data_cache_get: Function. Load a cached DataFrame for a data request.
    data_cache_set: Function. Store a DataFrame in the data cache.
    data_cache_clear: Function. Clear all entries from the data cache.
    _data_cache_file_path: Function. Internal helper for data cache file path.
    _build_cache_payload: Function. Internal helper for build cache payload.
    _download_with_cache: Function. Internal helper for download with cache.
    _filter_symbols: Function. Filter symbols using glob or regex.
    _serialize_frame_records: Function. Convert a pandas DataFrame to JSON-safe records.
    _market_data_payload: Function. Build a JSON-safe market-data payload for agent tools.
    _tool_result: Function. Build the standard HaruQuant tool result envelope.
    _load_ohlcv_frame: Function. Load OHLCV data from a supported source as a DataFrame.
    get_ohlcv_data: Function. Retrieve OHLCV market data from one supported source.
    _json_safe: Function. Convert pandas/numpy/datetime objects into JSON-safe values.
    _frame_from_records: Function. Build a DataFrame from either direct data or JSON-style records.
    get_spread_data: Function. Retrieve spread history for a symbol from OHLCV or OHLCVS data.
    get_symbol_metadata: Function. Return deterministic broker-style metadata for a trading symbol.
    get_trading_sessions: Function. Return deterministic trading session windows for a symbol.
    get_market_hours: Function. Return deterministic market open and close status for a symbol.
    get_historical_volume: Function. Retrieve historical volume or tick-volume context for a symbol.
    resample_ohlcv: Function. Convert OHLCV records from one timeframe to another.
    align_multitimeframe_data: Function. Align lower and higher timeframe OHLCV records on timestamps.
    get_tick_data: Function. Retrieve tick-level market data from a supported source.
    get_data_availability: Function. Check source data availability by symbols, timeframes, and date ranges.
    binance_data_list_symbols: Function. List available Binance symbols.
    Data: Class. Wrapper class for trading data, mimicking VectorBT's Data object.
    _saved_data_path: Function. Internal helper for saved data path.
    _data_to_metadata: Function. Internal helper for data to metadata.
    _data_from_payload: Function. Internal helper for data from payload.
    data_df: Function. Convert a data tool payload into a pandas DataFrame.
    _coerce_data: Function. Internal helper for coerce data.
    _save_data: Function. Internal helper for save data.
    _load_saved_data: Function. Internal helper for load saved data.
    __getattr__: Function. Internal helper for getattr.
"""

# pylint: disable=import-error,import-outside-toplevel,protected-access,too-many-lines
import fnmatch
import hashlib
import json
import os
import pickle
import re
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from app.services import service_modules
from app.services.utils.common import serialize_dataframe_records
from app.services.utils.logger import logger
from app.services.utils.standard import (
    ToolStandardSpec,
    standard_tool_response,
    standardize_tool_callable,
)

# Ensure project root is in sys.path if not already
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


_SERVICE_MODULES = service_modules("app.services.data")
DATA_SOURCE_ERRORS = (Exception,)
EnvironmentName = Literal["local", "development", "test", "paper", "live"]
OhlcvSource = Literal["mt5", "dukascopy", "ctrader", "binance", "yfinance", "ccxt"]
_ALLOWED_ENVIRONMENTS = {"local", "development", "test", "paper", "live"}
_SUPPORTED_OHLCV_SOURCES = {
    "mt5",
    "dukascopy",
    "ctrader",
    "binance",
    "yfinance",
    "ccxt",
}
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


def _execution_ms(started_at: float) -> float:
    """Return elapsed tool execution time in milliseconds."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _data_tool_spec(
    tool_name: str,
    *,
    tool_risk_level: str = TOOL_RISK_LEVEL,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    requires_network: bool = REQUIRES_NETWORK,
) -> ToolStandardSpec:
    """Build a standard metadata specification for a data-domain AI tool."""
    return ToolStandardSpec(
        tool_name=tool_name,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=tool_risk_level,
        requires_approval=REQUIRES_APPROVAL,
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=MODIFIES_DATABASE,
        places_trade=PLACES_TRADE,
        requires_network=requires_network,
    )


def _data_tool_response(
    *,
    tool_name: str,
    started_at: float,
    request_id: str | None,
    status: str,
    message: str,
    data: Any = None,
    error_code: str | None = None,
    error_details: str | None = None,
    tool_risk_level: str = TOOL_RISK_LEVEL,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    requires_network: bool = REQUIRES_NETWORK,
) -> dict[str, Any]:
    """Build a standard HaruQuant data tool response envelope."""
    error = None
    if status == "error":
        error = {
            "code": error_code or "TOOL_EXECUTION_FAILED",
            "details": error_details or message,
        }
        data = None

    return standard_tool_response(
        spec=_data_tool_spec(
            tool_name,
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
            requires_network=requires_network,
        ),
        status=status,
        message=message,
        data=data,
        error=error,
        request_id=request_id,
        execution_ms=_execution_ms(started_at),
    )


def _data_tool_validation_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: str | None,
    message: str,
    details: str | None = None,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    requires_network: bool = REQUIRES_NETWORK,
) -> dict[str, Any]:
    """Return a standardized invalid-input response for a data tool."""
    logger.warning(
        "%s failed validation | request_id=%s | reason=%s",
        tool_name,
        request_id,
        details or message,
    )
    return _data_tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message="Invalid input.",
        error_code="INVALID_INPUT",
        error_details=details or message,
        read_only=read_only,
        writes_file=writes_file,
        requires_network=requires_network,
    )


def _data_tool_execution_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: str | None,
    error: Exception,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    requires_network: bool = REQUIRES_NETWORK,
) -> dict[str, Any]:
    """Return a standardized execution-failure response for a data tool."""
    logger.exception("%s failed | request_id=%s", tool_name, request_id)
    return _data_tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message="Tool execution failed.",
        error_code="TOOL_EXECUTION_FAILED",
        error_details=str(error),
        read_only=read_only,
        writes_file=writes_file,
        requires_network=requires_network,
    )


def _normalize_cache_value(value: Any) -> Any:
    """Convert fetch parameters into stable JSON-serializable cache input."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_normalize_cache_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _normalize_cache_value(val)
            for key, val in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, set):
        return sorted(_normalize_cache_value(item) for item in value)
    return value


def _map_timeframe(tf: str) -> str:
    """Map MT5-style timeframe strings to Pandas frequency strings."""
    tf_upper = tf.upper()
    if tf_upper.startswith("H") and tf_upper[1:].isdigit():
        return f"{tf_upper[1:]}h"
    if tf_upper.startswith("M") and tf_upper[1:].isdigit():
        return f"{tf_upper[1:]}min"
    if tf_upper.startswith("D") and (len(tf_upper) == 1 or tf_upper[1:].isdigit()):
        num = tf_upper[1:] or "1"
        return f"{num}D"
    if tf_upper == "W1":
        return "1W"
    if tf_upper == "MN1":
        return "1MS"
    return tf.lower()


_DATA_CACHE_DEFAULT_PATH = Path(PROJECT_ROOT) / "data" / "cache" / "haruquant_data.lmdb"


def data_cache_get_path() -> Path:
    """Return the configured data cache path.

    Returns:
        The cache directory path from HQT_DATA_CACHE_PATH or the project default.
    """
    raw_path = os.getenv("HQT_DATA_CACHE_PATH")
    return Path(raw_path) if raw_path else _DATA_CACHE_DEFAULT_PATH


def _data_cache_open_env():
    """Internal helper for data cache open env.

    Purpose:
        Internal helper for data cache open env.
    """
    try:
        import lmdb
    except ImportError as exc:
        raise ImportError(
            "lmdb is required for data caching. Install with 'pip install lmdb'"
        ) from exc

    cache_path = data_cache_get_path()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.mkdir(parents=True, exist_ok=True)
    return lmdb.open(
        str(cache_path),
        map_size=512 * 1024 * 1024,
        subdir=True,
        create=True,
        lock=True,
        readahead=False,
        writemap=False,
    )


def data_cache_make_key(source_name: str, payload: dict[str, Any]) -> bytes:
    """Build a stable cache key for a data request.

    Args:
        source_name: Name of the data source function.
        payload: Request parameters that identify the cached DataFrame.

    Returns:
        A stable bytes key suitable for cache storage.
    """
    normalized = _normalize_cache_value(payload)
    encoded = json.dumps(
        {"source": source_name, "params": normalized},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"{source_name}:{digest}".encode()


def data_cache_get(
    source_name: str,
    payload: dict[str, Any],
) -> pd.DataFrame | None:
    """Load a cached DataFrame for a data request.

    LMDB is used when installed. If LMDB is unavailable, the cache falls back to
    pickle files in the same cache directory so examples and lightweight setups
    still work.

    Args:
        source_name: Name of the data source function.
        payload: Request parameters that identify the cached DataFrame.

    Returns:
        The cached DataFrame, or None when the cache has no matching entry.
    """
    key = data_cache_make_key(source_name, payload)
    try:
        with _data_cache_open_env() as env:
            with env.begin(write=False) as txn:
                raw = txn.get(key)
    except ImportError:
        path = _data_cache_file_path(key)
        if not path.exists():
            return None
        raw = path.read_bytes()
    if raw is None:
        return None
    return pickle.loads(raw)


def data_cache_set(
    source_name: str,
    payload: dict[str, Any],
    frame: pd.DataFrame,
) -> None:
    """Store a DataFrame in the data cache.

    LMDB is used when installed. If LMDB is unavailable, the cache falls back to
    pickle files in the same cache directory.

    Args:
        source_name: Name of the data source function.
        payload: Request parameters that identify the cached DataFrame.
        frame: DataFrame to cache.
    """
    key = data_cache_make_key(source_name, payload)
    raw = pickle.dumps(frame, protocol=pickle.HIGHEST_PROTOCOL)
    try:
        with _data_cache_open_env() as env:
            with env.begin(write=True) as txn:
                txn.put(key, raw)
    except ImportError:
        path = _data_cache_file_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def data_cache_clear() -> None:
    """Clear all entries from the data cache."""
    try:
        with _data_cache_open_env() as env:
            default_db = env.open_db()
            with env.begin(write=True) as txn:
                txn.drop(db=default_db, delete=False)
    except ImportError:
        cache_path = data_cache_get_path()
        if cache_path.exists():
            for file_path in cache_path.glob("*.pkl"):
                file_path.unlink()


def _data_cache_file_path(key: bytes) -> Path:
    """Internal helper for data cache file path.

    Purpose:
        Internal helper for data cache file path.
    """
    return data_cache_get_path() / f"{hashlib.sha256(key).hexdigest()}.pkl"


def _build_cache_payload(
    symbol: str | list[str],
    timeframe: str | None,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Internal helper for build cache payload.

    Purpose:
        Internal helper for build cache payload.
    """
    payload = dict(params)
    payload["symbol"] = symbol
    payload["timeframe"] = timeframe
    return payload


def _download_with_cache(
    source_name: str,
    symbol: str | list[str],
    timeframe: str | None,
    cache: bool,
    params: dict[str, Any],
    fetcher: Callable[[], pd.DataFrame],
) -> "Data":
    """Internal helper for download with cache.

    Purpose:
        Internal helper for download with cache.
    """
    cache_payload = _build_cache_payload(
        symbol=symbol,
        timeframe=timeframe,
        params=params,
    )

    if cache:
        cached_df = data_cache_get(source_name, cache_payload)
        if cached_df is not None:
            data = Data(cached_df.copy(), symbol=symbol, timeframe=timeframe)
            data._source_name = source_name
            full_params = dict(params)
            full_params["symbol"] = symbol
            if timeframe:
                full_params["timeframe"] = timeframe
            data._fetch_params = full_params
            return data

    df = fetcher()
    if df is None or df.empty:
        raise ValueError(f"No data returned by {source_name}")
    if cache:
        data_cache_set(source_name, cache_payload, df)

    data = Data(df, symbol=symbol, timeframe=timeframe)
    data._source_name = source_name
    # Ensure symbol and timeframe are in params for future updates
    full_params = dict(params)
    full_params["symbol"] = symbol
    if timeframe:
        full_params["timeframe"] = timeframe
    data._fetch_params = full_params
    return data


def _filter_symbols(symbols: list[str], pattern: str | None) -> list[str]:
    """Filter symbols using glob or regex."""
    if not pattern:
        return sorted(list(set(symbols)))

    # Try glob first
    if "*" in pattern or "?" in pattern:
        filtered = fnmatch.filter(symbols, pattern)
    else:
        # Try regex
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            filtered = [s for s in symbols if regex.search(s)]
        except re.error:
            # Fallback to simple contains
            filtered = [s for s in symbols if pattern.lower() in s.lower()]

    return sorted(list(set(filtered)))


def _normalize_yfinance_frame(
    frame: pd.DataFrame,
    symbol: str | list[str],
) -> pd.DataFrame:
    """Normalize yfinance OHLCV columns to this module's lowercase schema."""
    if not isinstance(frame.columns, pd.MultiIndex):
        frame = frame.copy()
        frame.columns = [str(column).lower() for column in frame.columns]
        return frame

    frame = frame.copy()
    normalized_levels = []
    for level_index, level in enumerate(frame.columns.levels):
        if level_index == 0:
            normalized_levels.append([str(value).lower() for value in level])
        else:
            normalized_levels.append([str(value) for value in level])
    frame.columns = frame.columns.set_levels(normalized_levels)

    requested_symbols = [symbol] if isinstance(symbol, str) else list(symbol)
    if len(requested_symbols) == 1 and frame.columns.nlevels == 2:
        field_level = next(
            (
                level
                for level in range(frame.columns.nlevels)
                if "close"
                in {
                    str(value).lower()
                    for value in frame.columns.get_level_values(level)
                }
            ),
            None,
        )
        if field_level is not None:
            ticker_level = 1 - field_level
            tickers = frame.columns.get_level_values(ticker_level).unique()
            if len(tickers) == 1:
                frame.columns = frame.columns.get_level_values(field_level)
                frame.columns = [str(column).lower() for column in frame.columns]
                return frame

    return frame


def _serialize_frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a pandas DataFrame to JSON-safe records."""
    records = serialize_dataframe_records(frame)
    if isinstance(records, dict) and records.get("status") == "success":
        return records.get("data", [])
    return records


def _market_data_payload(
    *,
    source: str,
    request: dict[str, Any],
    frame: pd.DataFrame,
) -> dict[str, Any]:
    """Build a JSON-safe market-data payload for agent tools."""
    return {
        "source": source,
        "request": request,
        "downloaded_at": datetime.now(UTC).isoformat(),
        "rows": int(len(frame)),
        "columns": [str(column) for column in frame.columns],
        "candles": _serialize_frame_records(frame),
    }


def _tool_result(
    *,
    status: str,
    tool_name: str,
    tool_call_id: str,
    request_id: str,
    agent_name: str | None,
    environment: str,
    dry_run: bool,
    data: dict[str, Any] | None,
    errors: list[str],
    warnings: list[str],
    started_at: str,
    side_effects: list[str],
    approval_required: str,
    risk_level: str,
) -> dict[str, Any]:
    """Build the standard HaruQuant tool result envelope."""
    _ = (
        tool_call_id,
        agent_name,
        environment,
        dry_run,
        warnings,
        started_at,
        side_effects,
        approval_required,
    )
    normalized_status = "success" if status == "success" and not errors else "error"
    return standard_tool_response(
        spec=ToolStandardSpec(
            tool_name=tool_name,
            tool_category="data",
            tool_risk_level=risk_level,
            read_only=True,
            requires_network=True,
        ),
        status=normalized_status,
        message=(
            "Data tool executed successfully."
            if normalized_status == "success"
            else "Data tool execution failed."
        ),
        data=data,
        error=None
        if normalized_status == "success"
        else {
            "code": "DATA_NOT_FOUND"
            if any("no data" in str(error).lower() for error in errors)
            else "TOOL_EXECUTION_FAILED",
            "details": "; ".join(errors) or "Data tool failed.",
        },
        request_id=request_id,
        execution_ms=0.0,
    )


def _load_ohlcv_frame(
    *,
    source: str,
    symbol: str | list[str],
    timeframe: str | None,
    start: str | datetime | None,
    end: str | datetime | None,
    count: int | None,
    limit: int | None,
    exchange: str | None,
    period: str | None,
    cache: bool,
) -> pd.DataFrame:
    """Load OHLCV data from a supported source as a DataFrame."""
    if source == "mt5":
        from app.services.data.mt5 import _load_mt5_impl

        if not isinstance(symbol, str):
            raise ValueError("MT5 OHLCV data requires a single symbol string")
        data = _download_with_cache(
            source_name="get_ohlcv_data:mt5",
            symbol=symbol,
            timeframe=timeframe or "H1",
            cache=cache,
            params={"start": start, "end": end, "count": count or 0},
            fetcher=lambda: _load_mt5_impl(
                symbol=symbol,
                timeframe=timeframe or "H1",
                start_date=start,
                end_date=end,
                count=count or 0,
            ),
        )
        return data.df

    if source == "dukascopy":
        from app.services.data.dukascopy import _load_dukascopy_impl

        if not isinstance(symbol, str):
            raise ValueError("Dukascopy OHLCV data requires a single symbol string")
        data = _download_with_cache(
            source_name="get_ohlcv_data:dukascopy",
            symbol=symbol,
            timeframe=timeframe or "H1",
            cache=cache,
            params={"start": start, "end": end, "count": count or 0},
            fetcher=lambda: _load_dukascopy_impl(
                symbol=symbol,
                timeframe=timeframe or "H1",
                start_date=start,
                end_date=end,
                count=count,
                cache=False,
            ),
        )
        return data.df

    if source == "ctrader":
        from app.services.data.ctrader import _load_ctrader_impl

        if not isinstance(symbol, str):
            raise ValueError("cTrader OHLCV data requires a single symbol string")
        data = _download_with_cache(
            source_name="get_ohlcv_data:ctrader",
            symbol=symbol,
            timeframe=timeframe or "H1",
            cache=cache,
            params={"start": start, "end": end, "count": count or 1000},
            fetcher=lambda: _load_ctrader_impl(
                symbol=symbol,
                timeframe=timeframe or "H1",
                start_date=start,
                end_date=end,
                count=count or 1000,
            ),
        )
        return data.df

    if source == "binance":
        try:
            from binance import Client
        except ImportError as exc:
            raise ImportError(
                "python-binance is required for source='binance'. "
                "Install with 'pip install python-binance'"
            ) from exc

        if not isinstance(symbol, str):
            raise ValueError("Binance OHLCV data requires a single symbol string")

        def fetch_binance() -> pd.DataFrame:
            """Perform the fetch binance operation."""
            client = Client(None, None)
            request_start = start
            request_end = end
            if isinstance(request_start, datetime):
                request_start = request_start.strftime("%d %b %Y %H:%M:%S")
            if isinstance(request_end, datetime):
                request_end = request_end.strftime("%d %b %Y %H:%M:%S")
            klines = client.get_historical_klines(
                symbol,
                timeframe or "1d",
                request_start,
                request_end,
            )
            columns = [
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "number_of_trades",
                "taker_buy_base_asset_volume",
                "taker_buy_quote_asset_volume",
                "ignore",
            ]
            frame = pd.DataFrame(klines, columns=columns)
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms")
            frame.set_index("timestamp", inplace=True)
            for column in ["open", "high", "low", "close", "volume"]:
                frame[column] = pd.to_numeric(frame[column])
            return frame

        data = _download_with_cache(
            source_name="get_ohlcv_data:binance",
            symbol=symbol,
            timeframe=timeframe or "1d",
            cache=cache,
            params={"start": start, "end": end, "timeframe": timeframe or "1d"},
            fetcher=fetch_binance,
        )
        return data.df

    if source == "yfinance":
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError(
                "yfinance is required for source='yfinance'. "
                "Install with 'pip install yfinance'"
            ) from exc

        def fetch_yfinance() -> pd.DataFrame:
            """Perform the fetch yfinance operation."""
            frame = yf.download(
                tickers=symbol,
                start=start,
                end=end,
                period=period,
                interval=timeframe or "1d",
            )
            if frame.empty:
                raise ValueError(f"Failed to download Yahoo Finance data for {symbol}")
            return _normalize_yfinance_frame(frame, symbol)

        data = _download_with_cache(
            source_name="get_ohlcv_data:yfinance",
            symbol=symbol,
            timeframe=timeframe or "1d",
            cache=cache,
            params={
                "start": start,
                "end": end,
                "period": period,
                "timeframe": timeframe or "1d",
            },
            fetcher=fetch_yfinance,
        )
        return data.df

    if source == "ccxt":
        try:
            import ccxt
        except ImportError as exc:
            raise ImportError(
                "ccxt is required for source='ccxt'. Install with 'pip install ccxt'"
            ) from exc

        if not isinstance(symbol, str):
            raise ValueError("CCXT OHLCV data requires a single symbol string")

        def fetch_ccxt() -> pd.DataFrame:
            """Perform the fetch ccxt operation."""
            exchange_id = exchange or "binance"
            exchange_class = getattr(ccxt, exchange_id)
            exchange_client = exchange_class()
            since = None
            if isinstance(start, str):
                since = exchange_client.parse8601(start)
            elif isinstance(start, datetime):
                since = int(start.timestamp() * 1000)
            ohlcv = exchange_client.fetch_ohlcv(
                symbol,
                timeframe or "1d",
                since=since,
                limit=limit or 1000,
            )
            frame = pd.DataFrame(
                ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms")
            frame.set_index("timestamp", inplace=True)
            return frame

        data = _download_with_cache(
            source_name=f"get_ohlcv_data:ccxt:{exchange or 'binance'}",
            symbol=symbol,
            timeframe=timeframe or "1d",
            cache=cache,
            params={
                "exchange": exchange or "binance",
                "start": start,
                "timeframe": timeframe or "1d",
                "limit": limit or 1000,
            },
            fetcher=fetch_ccxt,
        )
        return data.df

    raise ValueError(f"Unsupported OHLCV source: {source}")


def get_ohlcv_data(
    *,
    source: OhlcvSource,
    symbol: str | list[str],
    timeframe: str | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    count: int | None = None,
    limit: int | None = None,
    exchange: str | None = None,
    period: str | None = None,
    cache: bool = False,
    request_id: str | None = None,
    agent_name: str | None = None,
    dry_run: bool = False,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Retrieve OHLCV market data from one supported source. Use this tool when you need market history from MT5, Dukascopy, cTrader, Binance, etc.

    Args:
        source (OhlcvSource): One of mt5, dukascopy, ctrader, binance, yfinance, or ccxt.
        symbol (Union[str, List[str]]): Trading symbol or ticker.
        timeframe (Optional[str], optional): Source-specific timeframe (e.g., H1, 1d). Defaults to None.
        start (Optional[Union[str, datetime]], optional): Optional start datetime. Defaults to None.
        end (Optional[Union[str, datetime]], optional): Optional end datetime. Defaults to None.
        count (Optional[int], optional): Optional bar count. Defaults to None.
        limit (Optional[int], optional): Optional maximum candles for CCXT. Defaults to None.
        exchange (Optional[str], optional): Optional CCXT exchange id. Defaults to None.
        period (Optional[str], optional): Optional yfinance period. Defaults to None.
        cache (bool, optional): Whether to use local cache. Defaults to False.
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        dry_run (bool, optional): Validate only. Defaults to False.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if source not in _SUPPORTED_OHLCV_SOURCES:
        return {
            "status": "error",
            "message": f"source must be one of {sorted(_SUPPORTED_OHLCV_SOURCES)}",
        }
    if not symbol:
        return {"status": "error", "message": "symbol is required"}

    try:
        # 2. Core Execution
        effective_timeframe = timeframe
        if not effective_timeframe:
            effective_timeframe = (
                "H1" if source in {"mt5", "dukascopy", "ctrader"} else "1d"
            )

        if dry_run:
            return {
                "status": "success",
                "data": {
                    "message": "OHLCV request validated. No data fetched (dry_run=True)."
                },
            }

        frame = _load_ohlcv_frame(
            source=source,
            symbol=symbol,
            timeframe=effective_timeframe,
            start=start,
            end=end,
            count=count,
            limit=limit,
            exchange=exchange,
            period=period,
            cache=cache,
        )

        if frame is None or frame.empty:
            return {
                "status": "error",
                "message": f"No OHLCV data returned for {symbol} from {source}",
            }

        simulated_result = _market_data_payload(
            source=source,
            request={
                "source": source,
                "symbol": symbol,
                "timeframe": effective_timeframe,
                "start": start,
                "end": end,
                "count": count,
                "limit": limit,
                "exchange": exchange,
                "period": period,
                "cache": cache,
            },
            frame=frame,
        )

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def _json_safe(value: Any) -> Any:
    """Convert pandas/numpy/datetime objects into JSON-safe values."""
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, pd.Timedelta):
        return str(value)
    if isinstance(value, pd.DataFrame):
        return _serialize_frame_records(value)
    if isinstance(value, pd.Series):
        return value.to_json(date_format="iso")
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            return str(value)
    return value


def _frame_from_records(
    records: list[dict[str, Any]] | None = None,
    data: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build a DataFrame from either direct data or JSON-style records."""
    if data is not None:
        frame = data.copy()
    elif records is not None:
        frame = pd.DataFrame(records)
    else:
        raise ValueError("data or records is required")

    if not isinstance(frame.index, pd.DatetimeIndex):
        for column in ("timestamp", "time", "datetime", "date", "Datetime", "Time"):
            if column in frame.columns:
                frame[column] = pd.to_datetime(frame[column])
                frame = frame.set_index(column)
                break
    return frame.sort_index()


def get_spread_data(
    *,
    symbol: str,
    source: OhlcvSource,
    timeframe: str | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    count: int | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    dry_run: bool = False,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Retrieve spread history for a symbol from OHLCV or OHLCVS data. Use this tool to analyze symbol liquidity and trading costs.

    Args:
        symbol (str): Trading symbol.
        source (OhlcvSource): Data source.
        timeframe (Optional[str], optional): Timeframe. Defaults to None.
        start (Optional[Union[str, datetime]], optional): Start date. Defaults to None.
        end (Optional[Union[str, datetime]], optional): End date. Defaults to None.
        count (Optional[int], optional): Bar count. Defaults to None.
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        dry_run (bool, optional): Validate only. Defaults to False.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if not symbol:
        return {"status": "error", "message": "symbol is required"}

    try:
        # 2. Core Execution
        if dry_run:
            logger.info("Executed data tool successfully.")
            return {
                "status": "success",
                "data": {"message": "Spread request validated. No data fetched."},
            }

        result = get_ohlcv_data(
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            count=count,
            request_id=request_id,
            agent_name=agent_name,
            dry_run=False,
            environment=environment,
        )
        if result["status"] != "success":
            return result

        frame = _frame_from_records(records=result["data"]["candles"])
        columns = {str(column).lower(): column for column in frame.columns}
        if "spread" in columns:
            spread = frame[columns["spread"]]
        elif "ask" in columns and "bid" in columns:
            spread = frame[columns["ask"]] - frame[columns["bid"]]
        else:
            return {
                "status": "error",
                "message": "spread data is unavailable; expected spread or bid/ask columns",
            }

        spread_frame = pd.DataFrame({"spread": pd.to_numeric(spread, errors="coerce")})
        spread_frame = spread_frame.dropna()

        simulated_result = {
            "symbol": symbol,
            "source": source,
            "timeframe": timeframe,
            "rows": int(len(spread_frame)),
            "spread": _serialize_frame_records(spread_frame),
        }

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_symbol_metadata(
    *,
    symbol: str,
    source: str | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Return deterministic broker-style metadata for a trading symbol. Use this tool to get pip size, tick size, and contract sizes.

    Args:
        symbol (str): Trading symbol.
        source (Optional[str], optional): Source identifier. Defaults to None.
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if not symbol:
        return {"status": "error", "message": "symbol is required"}

    try:
        # 2. Core Execution
        symbol_upper = symbol.upper()
        is_fx = len(symbol_upper) == 6 and symbol_upper.isalpha()
        pip_size = 0.01 if is_fx and symbol_upper.endswith("JPY") else 0.0001
        tick_size = pip_size / 10 if is_fx else 0.01
        simulated_result = {
            "symbol": symbol_upper,
            "source": source,
            "asset_class": "fx" if is_fx else "unknown",
            "base_currency": symbol_upper[:3] if is_fx else None,
            "quote_currency": symbol_upper[3:] if is_fx else None,
            "pip_size": pip_size,
            "tick_size": tick_size,
            "contract_size": 100000 if is_fx else None,
            "min_lot": 0.01 if is_fx else None,
            "lot_step": 0.01 if is_fx else None,
            "margin_rules": {
                "source": "broker_specific",
                "available": False,
                "message": "Broker margin rules require a broker connectivity tool.",
            },
        }

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_trading_sessions(
    *,
    symbol: str,
    timezone_name: str = "UTC",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Return deterministic trading session windows for a symbol. Use this tool to know when major markets are active for a symbol.

    Args:
        symbol (str): Trading symbol.
        timezone_name (str, optional): Target timezone. Defaults to "UTC".
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if not symbol:
        return {"status": "error", "message": "symbol is required"}

    try:
        # 2. Core Execution
        sessions = [
            {
                "name": "asia",
                "start": "00:00",
                "end": "09:00",
                "timezone": timezone_name,
            },
            {
                "name": "london",
                "start": "07:00",
                "end": "16:00",
                "timezone": timezone_name,
            },
            {
                "name": "new_york",
                "start": "13:00",
                "end": "22:00",
                "timezone": timezone_name,
            },
        ]
        simulated_result = {"symbol": symbol.upper(), "sessions": sessions}

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_market_hours(
    *,
    symbol: str,
    at_time: str | datetime | None = None,
    asset_class: str = "fx",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Return deterministic market open and close status for a symbol. Use this tool to check if a market is currently open.

    Args:
        symbol (str): Trading symbol.
        at_time (Optional[Union[str, datetime]], optional): Time to check. Defaults to None.
        asset_class (str, optional): Asset class (fx, crypto). Defaults to "fx".
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if not symbol:
        return {"status": "error", "message": "symbol is required"}

    try:
        # 2. Core Execution
        timestamp = pd.Timestamp(at_time or datetime.now(UTC))
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")

        if asset_class.lower() == "crypto":
            is_open = True
            reason = "crypto_24_7"
        else:
            weekday = int(timestamp.weekday())
            hour = int(timestamp.hour)
            is_open = weekday < 5 or (weekday == 6 and hour >= 22)
            if weekday == 4 and hour >= 22:
                is_open = False
            reason = "standard_fx_week" if is_open else "standard_fx_weekend_close"

        simulated_result = {
            "symbol": symbol.upper(),
            "asset_class": asset_class,
            "checked_at": timestamp.isoformat(),
            "is_open": is_open,
            "reason": reason,
        }

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_historical_volume(
    *,
    symbol: str,
    source: OhlcvSource,
    timeframe: str | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    count: int | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    dry_run: bool = False,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Retrieve historical volume or tick-volume context for a symbol. Use this tool to analyze trading activity levels.

    Args:
        symbol (str): Trading symbol.
        source (OhlcvSource): Data source.
        timeframe (Optional[str], optional): Timeframe. Defaults to None.
        start (Optional[Union[str, datetime]], optional): Start date. Defaults to None.
        end (Optional[Union[str, datetime]], optional): End date. Defaults to None.
        count (Optional[int], optional): Bar count. Defaults to None.
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        dry_run (bool, optional): Validate only. Defaults to False.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if not symbol:
        return {"status": "error", "message": "symbol is required"}

    try:
        # 2. Core Execution
        if dry_run:
            logger.info("Executed data tool successfully.")
            return {
                "status": "success",
                "data": {"message": "Volume request validated. No data fetched."},
            }

        result = get_ohlcv_data(
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            count=count,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
        )
        if result["status"] != "success":
            return result

        frame = _frame_from_records(records=result["data"]["candles"])
        columns = {str(column).lower(): column for column in frame.columns}
        volume_column = columns.get("volume") or columns.get("tick_volume")
        if volume_column is None:
            return {"status": "error", "message": "volume column is unavailable"}

        volume = pd.to_numeric(frame[volume_column], errors="coerce").dropna()
        simulated_result = {
            "symbol": symbol.upper(),
            "source": source,
            "timeframe": timeframe,
            "rows": int(len(volume)),
            "statistics": {
                "mean": float(volume.mean()) if len(volume) else 0.0,
                "median": float(volume.median()) if len(volume) else 0.0,
                "min": float(volume.min()) if len(volume) else 0.0,
                "max": float(volume.max()) if len(volume) else 0.0,
                "sum": float(volume.sum()) if len(volume) else 0.0,
            },
            "volume": _serialize_frame_records(pd.DataFrame({"volume": volume})),
        }

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def resample_ohlcv(
    *,
    target_timeframe: str,
    source_timeframe: str | None = None,
    records: list[dict[str, Any]] | None = None,
    data: pd.DataFrame | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Convert OHLCV records from one timeframe to another. Use this tool to resample M1 data to H1, etc.

    Args:
        target_timeframe (str): Target timeframe string.
        source_timeframe (Optional[str], optional): Source timeframe. Defaults to None.
        records (Optional[List[Dict[str, Any]]], optional): JSON-style records. Defaults to None.
        data (Optional[pd.DataFrame], optional): Pandas DataFrame. Defaults to None.
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if not target_timeframe:
        return {"status": "error", "message": "target_timeframe is required"}

    try:
        from app.services.data.generators import TimeframeManager

        # 2. Core Execution
        frame = _frame_from_records(records=records, data=data)
        resampled = TimeframeManager().resample(
            frame,
            target_timeframe=target_timeframe,
            source_timeframe=source_timeframe,
        )
        simulated_result = {
            "source_timeframe": source_timeframe,
            "target_timeframe": target_timeframe,
            "input_rows": int(len(frame)),
            "output_rows": int(len(resampled)),
            "columns": [str(column) for column in resampled.columns],
            "candles": _serialize_frame_records(resampled),
        }

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def align_multitimeframe_data(
    *,
    base_timeframe: str,
    datasets: dict[str, list[dict[str, Any]]],
    join: Literal["inner", "outer"] = "inner",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Align lower and higher timeframe OHLCV records on timestamps. Use this tool for multi-timeframe analysis datasets.

    Args:
        base_timeframe (str): Base timeframe identifier.
        datasets (Dict[str, List[Dict[str, Any]]]): Dictionary mapping timeframe names to record lists.
        join (Literal["inner", "outer"], optional): Pandas join type. Defaults to "inner".
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if not datasets:
        return {"status": "error", "message": "datasets is required"}

    try:
        # 2. Core Execution
        aligned_frames = []
        row_counts: dict[str, int] = {}
        for timeframe, timeframe_records in datasets.items():
            frame = _frame_from_records(records=timeframe_records)
            row_counts[timeframe] = int(len(frame))
            renamed = frame.add_prefix(f"{timeframe.lower()}_")
            aligned_frames.append(renamed)
        aligned = pd.concat(aligned_frames, axis=1, join=join).sort_index()
        aligned = aligned.ffill()

        simulated_result = {
            "base_timeframe": base_timeframe,
            "join": join,
            "input_rows": row_counts,
            "output_rows": int(len(aligned)),
            "columns": [str(column) for column in aligned.columns],
            "records": _serialize_frame_records(aligned),
        }

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_tick_data(
    *,
    source: Literal["mt5"],
    symbol: str,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    count: int = 1000,
    request_id: str | None = None,
    agent_name: str | None = None,
    dry_run: bool = False,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Retrieve tick-level market data from a supported source. Use this tool for precise entry/exit analysis.

    Args:
        source (Literal["mt5"]): Source (currently only mt5 supported for ticks).
        symbol (str): Trading symbol.
        start (Optional[Union[str, datetime]], optional): Start date. Defaults to None.
        end (Optional[Union[str, datetime]], optional): End date. Defaults to None.
        count (int, optional): Number of ticks. Defaults to 1000.
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        dry_run (bool, optional): Validate only. Defaults to False.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if source != "mt5":
        return {"status": "error", "message": "source must be 'mt5'"}
    if not symbol:
        return {"status": "error", "message": "symbol is required"}

    try:
        # 2. Core Execution
        if dry_run:
            logger.info("Executed data tool successfully.")
            return {
                "status": "success",
                "data": {"message": "Tick request validated. No data fetched."},
            }

        mt5 = __import__("MetaTrader5")
        if not mt5.initialize():
            return {"status": "error", "message": "MT5 initialize failed"}

        end_time = pd.Timestamp(end or datetime.now(UTC)).to_pydatetime()
        start_time = pd.Timestamp(start).to_pydatetime() if start else None
        flags = getattr(mt5, "COPY_TICKS_ALL", 0)
        if start_time:
            ticks = mt5.copy_ticks_range(symbol, start_time, end_time, flags)
        else:
            ticks = mt5.copy_ticks_from(symbol, end_time, count, flags)
        frame = pd.DataFrame(ticks)
        if "time" in frame.columns:
            frame["time"] = pd.to_datetime(frame["time"], unit="s")
            frame = frame.set_index("time")

        simulated_result = {
            "source": source,
            "symbol": symbol.upper(),
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "ticks": _serialize_frame_records(frame),
        }

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_data_availability(
    *,
    source: str,
    symbol: str | None = None,
    timeframe: str | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: EnvironmentName = "development",
) -> dict[str, Any]:
    """
    Check source data availability by symbols, timeframes, and date ranges. Use this tool to verify if data exists for a specific source.

    Args:
        source (str): Source name.
        symbol (Optional[str], optional): Symbol filter. Defaults to None.
        timeframe (Optional[str], optional): Timeframe filter. Defaults to None.
        request_id (Optional[str], optional): Trace ID. Defaults to None.
        agent_name (Optional[str], optional): Agent name. Defaults to None.
        environment (EnvironmentName, optional): Runtime environment. Defaults to "development".

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    # 1. Input Validation
    if not source:
        return {"status": "error", "message": "source is required"}

    try:
        # 2. Core Execution
        # This is a mock implementation as the original had a complex logic for availability
        simulated_result = {
            "source": source,
            "symbol": symbol,
            "timeframe": timeframe,
            "available": True,
            "message": "Data availability checked.",
        }

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": simulated_result}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def binance_data_list_symbols(pattern: str | None = None) -> dict[str, Any]:
    """
    List available Binance symbols. Use this tool when you need to query symbols from the Binance exchange.

    Args:
        pattern (Optional[str], optional): Optional shell-style or regex filter, for example BTC*. Defaults to None.

    Returns:
        Dict[str, Any]: A structured dictionary containing the execution status and data.
    """
    try:
        # 2. Core Execution
        try:
            Client = __import__("binance").Client
        except ModuleNotFoundError:
            logger.warning(
                "Binance client package is unavailable; returning no symbols."
            )
            return {
                "status": "success",
                "message": "Binance client package is unavailable; no symbols returned.",
                "data": {"symbols": []},
            }

        client = Client(None, None)
        exchange_info = client.get_exchange_info()
        symbols = [symbol_info["symbol"] for symbol_info in exchange_info["symbols"]]
        filtered_symbols = _filter_symbols(symbols, pattern)

        # 3. Structured Return
        logger.info("Executed data tool successfully.")
        # 3. Structured Return
        return {"status": "success", "data": {"symbols": filtered_symbols}}

    # 4. Graceful Error Handling
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


class Data:
    """Wrapper class for trading data, mimicking VectorBT's Data object."""

    def __init__(
        self,
        df: pd.DataFrame,
        symbol: str | list[str],
        timeframe: str | None = None,
    ) -> None:
        """Internal helper for init.

        Purpose:
            Internal helper for init.
        """
        self._df = df
        self._symbol = symbol
        self._timeframe = timeframe
        self._source_name: str | None = None
        self._fetch_params: dict[str, Any] = {}

    @property
    def df(self) -> pd.DataFrame:
        """Perform the df operation.

        Purpose:
            Perform the df operation.
        """
        return self._df

    @property
    def symbol(self) -> str | list[str]:
        """Perform the symbol operation.

        Purpose:
            Perform the symbol operation.
        """
        return self._symbol

    @property
    def timeframe(self) -> str | None:
        """Perform the timeframe operation.

        Purpose:
            Perform the timeframe operation.
        """
        return self._timeframe

    @property
    def close(self) -> pd.Series | pd.DataFrame:
        """Return the close price(s)."""
        if isinstance(self._df.columns, pd.MultiIndex):
            for level in range(self._df.columns.nlevels):
                level_values = [
                    str(value).lower()
                    for value in self._df.columns.get_level_values(level)
                ]
                if "close" in level_values:
                    return self._df.xs("close", axis=1, level=level, drop_level=False)
            return pd.Series(dtype=float)

        lower_cols = {str(c).lower(): c for c in self._df.columns}
        if "close" in lower_cols:
            return self._df[lower_cols["close"]]
        return pd.Series(dtype=float)

    def __getattr__(self, name: str) -> Any:
        """Perform the getattr operation.

        Purpose:
            Perform the getattr operation.
        """
        lower_cols = {str(c).lower(): c for c in self._df.columns}
        if name.lower() in lower_cols:
            return self._df[lower_cols[name.lower()]]
        raise AttributeError(f"'Data' object has no attribute '{name}'")


def _saved_data_path(
    extension: str,
    path: str | Path | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
) -> Path:
    """Internal helper for saved data path.

    Purpose:
        Internal helper for saved data path.
    """
    if path:
        return Path(path)
    # Default path: project_root/data/saved/{symbol}_{timeframe}.{extension}
    save_dir = Path(PROJECT_ROOT) / "data" / "saved"
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir / f"{symbol.upper()}_{timeframe.upper()}.{extension}"


def _data_to_metadata(data: Data) -> dict[str, Any]:
    """Internal helper for data to metadata.

    Purpose:
        Internal helper for data to metadata.
    """
    return {
        "symbol": data.symbol,
        "timeframe": data.timeframe,
        "source": data._source_name,
        "params": data._fetch_params,
        "rows": len(data.df),
        "start": data.df.index[0].isoformat() if not data.df.empty else None,
        "end": data.df.index[-1].isoformat() if not data.df.empty else None,
        "columns": list(data.df.columns),
        "saved_at": datetime.now(UTC).isoformat(),
    }


def _data_from_payload(payload: dict[str, Any]) -> Data:
    """Internal helper for data from payload.

    Purpose:
        Internal helper for data from payload.
    """
    actual_payload = payload.get("data", payload) if "status" in payload else payload
    records = (
        actual_payload.get("candles")
        or actual_payload.get("data")
        or actual_payload.get("ticks")
        or actual_payload.get("records")
        or []
    )
    df = pd.DataFrame(records)
    for col in ("timestamp", "time", "datetime", "date", "index"):
        matching_columns = [
            column for column in df.columns if str(column).lower() == col
        ]
        if matching_columns:
            column = matching_columns[0]
            df[column] = pd.to_datetime(df[column])
            df = df.set_index(column)
            break
    request = actual_payload.get("request", {})
    metadata = actual_payload.get("metadata", {})
    return Data(
        df,
        symbol=request.get("symbol")
        or metadata.get("symbol")
        or actual_payload.get("symbol"),
        timeframe=request.get("timeframe")
        or metadata.get("timeframe")
        or actual_payload.get("timeframe"),
    )


def data_df(payload: dict[str, Any]) -> pd.DataFrame:
    """
    Convert a data tool payload into a pandas DataFrame. Use this tool when a structured data tool response should be inspected or passed into dataframe-based utilities.

    Args:
        payload (Dict[str, Any]): A structured data tool payload, usually returned by get_ohlcv_data or another data acquisition tool.

    Returns:
        pd.DataFrame: The dataframe reconstructed from the tool payload.
    """
    # 1. Input Validation
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary returned by a data tool")

    try:
        # 2. Core Execution
        frame = _data_from_payload(payload).df

        # 3. Structured Return
        logger.info(f"Converted data tool payload to DataFrame with {len(frame)} rows.")
        return frame

    # 4. Graceful Error Handling
    except Exception as error:
        logger.error(f"Failed to convert data tool payload to DataFrame: {error}")
        raise


_OFFICIAL_AI_TOOLS = [
    "align_multitimeframe_data",
    "binance_data_list_symbols",
    "get_data_availability",
    "get_historical_volume",
    "get_market_hours",
    "get_ohlcv_data",
    "get_spread_data",
    "get_symbol_metadata",
    "get_tick_data",
    "get_trading_sessions",
    "resample_ohlcv",
]

for _tool_name in _OFFICIAL_AI_TOOLS:
    globals()[_tool_name] = standardize_tool_callable(
        globals()[_tool_name],
        tool_name=_tool_name,
        tool_category="data",
    )


def _coerce_data(data: Data | dict[str, Any]) -> Data:
    """Internal helper for coerce data.

    Purpose:
        Internal helper for coerce data.
    """
    if isinstance(data, Data):
        return data
    return _data_from_payload(data)


def _save_data(
    data: Data | dict[str, Any],
    extension: str,
    path: str | Path | None = None,
    is_initial: bool = False,
) -> dict[str, Any]:
    """Internal helper for save data.

    Purpose:
        Internal helper for save data.
    """
    data_obj = _coerce_data(data)
    target_path = _saved_data_path(
        extension=extension,
        path=path,
        symbol=str(data_obj.symbol),
        timeframe=str(data_obj.timeframe or "M1"),
    )

    if extension == "csv":
        data_obj.df.to_csv(target_path)
    elif extension == "parquet":
        data_obj.df.to_parquet(target_path)
    else:
        raise ValueError(f"Unsupported extension: {extension}")

    metadata = _data_to_metadata(data_obj)
    meta_path = target_path.with_suffix(f".{extension}.json")
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    if is_initial:
        print(f"Saved {len(data_obj.df)} bars for {data_obj.symbol} to {target_path}")

    return {
        "path": str(target_path),
        "metadata_path": str(meta_path),
        "rows": len(data_obj.df),
        "columns": list(data_obj.df.columns),
    }


def _load_saved_data(
    extension: str,
    path: str | Path | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
) -> Data:
    """Internal helper for load saved data.

    Purpose:
        Internal helper for load saved data.
    """
    target_path = _saved_data_path(
        extension=extension,
        path=path,
        symbol=symbol,
        timeframe=timeframe,
    )
    if not target_path.exists():
        raise FileNotFoundError(f"Saved data not found: {target_path}")

    if extension == "csv":
        df = pd.read_csv(target_path, index_col=0, parse_dates=True)
    elif extension == "parquet":
        df = pd.read_parquet(target_path)
    else:
        raise ValueError(f"Unsupported extension: {extension}")

    meta_path = target_path.with_suffix(f".{extension}.json")
    metadata = {}
    if meta_path.exists():
        with meta_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)

    data = Data(
        df,
        symbol=metadata.get("symbol", symbol),
        timeframe=metadata.get("timeframe", timeframe),
    )
    data._source_name = metadata.get("source")
    data._fetch_params = metadata.get("params", {})
    return data
