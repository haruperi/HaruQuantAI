"""CSV-backed market-data tools for HaruQuantAI.

Purpose:
    Load, validate, slice, cache, save, and reload local CSV-backed market data.

This module contains both internal helpers and official AI-callable tools. Any
function exported through ``tools.data.__all__`` is treated as an official
HaruQuantAI tool and must return the standard tool response schema.

Exported AI Tools:
    - csv_data_fetch_range: Fetch a bar-position range from a CSV file.
    - csv_data_load: Load a CSV file into a JSON-safe market-data payload.
    - csv_data_saver_file_exists: Check whether a saved CSV artifact exists.
    - csv_data_saver_save: Save market-data payloads to CSV with metadata.
    - csv_data_saver_load: Load saved CSV market data and metadata.

Internal/Public Helpers:
    - load_csv: Load a CSV file as a normalized DataFrame for implementation code.
    - clear_data_cache: Clear the process-local DataFrame cache.
    - get_cached_data: Load or retrieve a cached DataFrame.

Classes:
    - CSVDataSource: Internal CSV-backed data source implementation.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Union

import pandas as pd

from tools.utils import logger
from tools.utils.common import clear_dataframe_cache, get_cached_dataframe

from ._common import (
    Data,
    _data_to_metadata,
    _load_saved_data,
    _save_data,
    _saved_data_path,
    _serialize_frame_records,
)

PathLike = Union[str, Path]
ToolResponse = Dict[str, Any]

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
LOW_RISK = "low"
MEDIUM_RISK = "medium"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

CSV_DATA_FETCH_RANGE_TOOL = "csv_data_fetch_range"
CSV_DATA_LOAD_TOOL = "csv_data_load"
CSV_DATA_SAVER_FILE_EXISTS_TOOL = "csv_data_saver_file_exists"
CSV_DATA_SAVER_SAVE_TOOL = "csv_data_saver_save"
CSV_DATA_SAVER_LOAD_TOOL = "csv_data_saver_load"

REQUIRED_PRICE_COLUMNS = frozenset({"open", "high", "low", "close"})
OPTIONAL_MARKET_COLUMNS = frozenset({"volume", "spread"})
NUMERIC_MARKET_COLUMNS = REQUIRED_PRICE_COLUMNS | OPTIONAL_MARKET_COLUMNS
SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9._:/-]{2,32}$")
TIMEFRAME_PATTERN = re.compile(r"^[A-Za-z0-9_:-]{1,16}$")


def _execution_ms(started_at: float) -> float:
    """Return elapsed milliseconds rounded for stable tool metadata."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _tool_response(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    status: str,
    message: str,
    data: Any = None,
    error_code: Optional[str] = None,
    error_details: Optional[str] = None,
    tool_risk_level: str = LOW_RISK,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
) -> ToolResponse:
    """Build a standard HaruQuantAI tool response."""
    error = None
    if status == "error":
        error = {
            "code": error_code or "UNKNOWN_ERROR",
            "details": error_details or message,
        }

    return {
        "status": status,
        "message": message,
        "data": data if status == "success" else None,
        "error": error,
        "metadata": {
            "tool_name": tool_name,
            "tool_version": TOOL_VERSION,
            "tool_category": TOOL_CATEGORY,
            "tool_risk_level": tool_risk_level,
            "request_id": request_id,
            "execution_ms": _execution_ms(started_at),
            "read_only": read_only,
            "writes_file": writes_file,
            "modifies_database": MODIFIES_DATABASE,
            "places_trade": PLACES_TRADE,
            "requires_network": REQUIRES_NETWORK,
        },
    }


def _validation_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    message: str,
    details: Optional[str] = None,
    tool_risk_level: str = LOW_RISK,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
) -> ToolResponse:
    """Return a logged INVALID_INPUT tool response."""
    logger.warning(
        "%s validation failed | request_id=%s | reason=%s",
        tool_name,
        request_id,
        details or message,
    )
    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message=message,
        error_code="INVALID_INPUT",
        error_details=details or message,
        tool_risk_level=tool_risk_level,
        read_only=read_only,
        writes_file=writes_file,
    )


def _execution_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    error: Exception,
    tool_risk_level: str = LOW_RISK,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
) -> ToolResponse:
    """Return a logged TOOL_EXECUTION_FAILED response."""
    logger.exception(
        "%s failed | request_id=%s | error_type=%s",
        tool_name,
        request_id,
        type(error).__name__,
    )
    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message="CSV tool execution failed.",
        error_code="TOOL_EXECUTION_FAILED",
        error_details=str(error),
        tool_risk_level=tool_risk_level,
        read_only=read_only,
        writes_file=writes_file,
    )


def _validate_csv_path(
    path: PathLike,
    *,
    must_exist: bool,
    allow_directory: bool = False,
) -> Path:
    """Validate and normalize a CSV path.

    Args:
        path: User-provided path-like value.
        must_exist: Whether the path must already exist.
        allow_directory: Whether a directory path is accepted.

    Returns:
        Path: Normalized path object.

    Raises:
        ValueError: If the path is missing, unsafe, not CSV, or not found.
    """
    if not isinstance(path, (str, Path)) or str(path).strip() == "":
        raise ValueError("path must be a non-empty string or pathlib.Path.")

    candidate = Path(path).expanduser()
    if candidate.suffix.lower() != ".csv":
        raise ValueError(f"path must point to a .csv file: {candidate}")

    if must_exist and not candidate.exists():
        raise FileNotFoundError(f"CSV file not found: {candidate}")

    if candidate.exists() and candidate.is_dir() and not allow_directory:
        raise ValueError(f"path must point to a CSV file, not a directory: {candidate}")

    if not must_exist and candidate.parent and not candidate.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {candidate.parent}")

    return candidate


def _validate_symbol(symbol: str) -> str:
    """Validate and normalize a trading symbol."""
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must be a non-empty string.")
    normalized = symbol.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(normalized):
        raise ValueError(
            "symbol contains unsupported characters. Use letters, digits, '.', "
            "'_', '-', ':', or '/'."
        )
    return normalized


def _validate_timeframe(timeframe: str) -> str:
    """Validate and normalize a timeframe string."""
    if not isinstance(timeframe, str) or not timeframe.strip():
        raise ValueError("timeframe must be a non-empty string.")
    normalized = timeframe.strip().upper()
    if not TIMEFRAME_PATTERN.fullmatch(normalized):
        raise ValueError("timeframe contains unsupported characters.")
    return normalized


def _validate_position_range(start_pos: int, end_pos: int) -> None:
    """Validate bar-position range arguments."""
    if not isinstance(start_pos, int) or not isinstance(end_pos, int):
        raise ValueError("start_pos and end_pos must be integers.")
    if start_pos < 0:
        raise ValueError("start_pos must be greater than or equal to 0.")
    if end_pos <= start_pos:
        raise ValueError("end_pos must be greater than start_pos.")


def _validate_dataframe(frame: Any, *, source: str) -> pd.DataFrame:
    """Ensure a loaded or cached object is a non-empty DataFrame."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{source} did not return a pandas DataFrame.")
    if frame.empty:
        raise ValueError(f"{source} returned an empty DataFrame.")
    return frame


def _validate_market_columns(frame: pd.DataFrame, *, require_ohlc: bool = True) -> None:
    """Validate required market-data columns when OHLC data is expected."""
    if not require_ohlc:
        return

    columns = {str(column).lower() for column in frame.columns}
    missing = sorted(REQUIRED_PRICE_COLUMNS - columns)
    if missing:
        raise ValueError(
            "CSV market data is missing required OHLC columns: " + ", ".join(missing)
        )


def _coerce_market_numeric_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with known market-data columns converted to numeric values."""
    result = frame.copy()
    for column in sorted(set(result.columns) & NUMERIC_MARKET_COLUMNS):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def load_csv(
    file_path: PathLike,
    *,
    index_col: Union[int, str, None] = 0,
    parse_dates: bool = True,
    require_ohlc: bool = True,
) -> pd.DataFrame:
    """Load a CSV file into a normalized DataFrame.

    This helper is intended for implementation code. Agents should call
    ``csv_data_load`` from ``tools.data`` instead.

    Args:
        file_path: Path to the CSV file.
        index_col: Column to use as the DataFrame index. Defaults to ``0``.
        parse_dates: Whether pandas should parse date columns. Defaults to ``True``.
        require_ohlc: Whether to require open/high/low/close columns.

    Returns:
        pd.DataFrame: Loaded DataFrame with normalized lowercase column names.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV file is invalid or missing required columns.
        TypeError: If the cache layer returns a non-DataFrame object.
    """
    if not isinstance(parse_dates, bool):
        raise ValueError("parse_dates must be a boolean.")
    if index_col is not None and not isinstance(index_col, (int, str)):
        raise ValueError("index_col must be an int, str, or None.")

    path = _validate_csv_path(file_path, must_exist=True)
    key = f"csv_load:{path.resolve()}:{index_col}:{parse_dates}:{require_ohlc}"

    def _loader() -> pd.DataFrame:
        """Load the CSV from disk for the cache miss path."""
        frame = pd.read_csv(path, index_col=index_col, parse_dates=parse_dates)
        frame = _validate_dataframe(frame, source=str(path))
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        frame = _coerce_market_numeric_columns(frame)
        _validate_market_columns(frame, require_ohlc=require_ohlc)
        return frame

    return get_cached_data(key, _loader)


class CSVDataSource:
    """CSV-backed DataSource implementation for internal data pipelines.

    Use this class when implementation code needs a DataSource-style object
    that can load OHLCV/OHLCVS rows from a CSV file and slice them by position.
    Agents should call the exported CSV tools instead of constructing this class
    directly.
    """

    _DATETIME_HINTS = ("date", "time", "timestamp", "datetime", "ts")
    _COLUMN_MAP = {
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "volume": "volume",
        "tick_volume": "volume",
        "tickvolume": "volume",
        "real_volume": "volume",
        "spread": "spread",
    }

    def __init__(
        self,
        filepath: PathLike,
        *,
        date_column: Optional[str] = None,
        cache: bool = True,
        require_ohlc: bool = True,
        **read_csv_kwargs: Any,
    ) -> None:
        """Initialize the CSV data source.

        Args:
            filepath: Path to the CSV file.
            date_column: Optional explicit date/time column name. If omitted,
                the first datetime-like column is used.
            cache: Whether to cache the loaded DataFrame.
            require_ohlc: Whether to require open/high/low/close columns.
            **read_csv_kwargs: Extra keyword arguments for ``pd.read_csv``.

        Raises:
            ValueError: If constructor arguments are invalid.
        """
        if date_column is not None and not isinstance(date_column, str):
            raise ValueError("date_column must be a string or None.")
        if not isinstance(cache, bool):
            raise ValueError("cache must be a boolean.")
        if not isinstance(require_ohlc, bool):
            raise ValueError("require_ohlc must be a boolean.")

        self._filepath = _validate_csv_path(filepath, must_exist=True)
        self._date_column = date_column.strip().lower() if date_column else None
        self._cache = cache
        self._require_ohlc = require_ohlc
        self._read_csv_kwargs = read_csv_kwargs
        self._loaded: Optional[pd.DataFrame] = None

    def _detect_date_column(self, columns: list[str]) -> Optional[str]:
        """Return the first column name that looks like a datetime field."""
        hints = set(self._DATETIME_HINTS)
        for column in columns:
            if column.lower() in hints:
                return column
        return None

    def _load(self) -> pd.DataFrame:
        """Load and normalize the CSV into a DataFrame with DatetimeIndex.

        Raises:
            ValueError: If the CSV is empty, has no date column, has an
                unparsable date column, or lacks required OHLC columns.
        """
        frame = pd.read_csv(self._filepath, **dict(self._read_csv_kwargs))
        frame = _validate_dataframe(frame, source=str(self._filepath))
        frame.columns = [str(column).strip().lower() for column in frame.columns]

        date_col = self._date_column or self._detect_date_column(list(frame.columns))
        if date_col is None:
            raise ValueError(
                f"No date/time column detected in {self._filepath}. "
                "Provide date_column "
                f"or a column named {'/'.join(self._DATETIME_HINTS)}."
            )
        if date_col not in frame.columns:
            raise ValueError(
                f"date_column '{date_col}' does not exist in {self._filepath}."
            )

        try:
            frame[date_col] = pd.to_datetime(frame[date_col], errors="raise")
        except Exception as error:  # pandas raises several parser-specific errors.
            raise ValueError(
                f"Could not parse date/time column '{date_col}' "
                f"in {self._filepath}: {error}"
            ) from error

        frame = frame.set_index(date_col).sort_index()
        rename_map = {
            column: self._COLUMN_MAP[column.lower()]
            for column in frame.columns
            if column.lower() in self._COLUMN_MAP
        }
        if rename_map:
            frame = frame.rename(columns=rename_map)

        frame = _coerce_market_numeric_columns(frame)
        _validate_market_columns(frame, require_ohlc=self._require_ohlc)
        return frame

    def _get_cached_or_load(self) -> pd.DataFrame:
        """Load from cache or disk and return a defensive DataFrame copy."""
        if self._loaded is not None:
            return self._loaded.copy()

        if self._cache:
            key = (
                f"csv:{self._filepath.resolve()}:"
                f"{self._date_column}:{self._require_ohlc}"
            )
            frame = get_cached_dataframe(key, self._load)
            if isinstance(frame, Mapping) and frame.get("status") == "success":
                frame = frame.get("data")
        else:
            frame = self._load()

        frame = _validate_dataframe(frame, source="CSV cache")
        self._loaded = frame
        return frame.copy()

    def fetch_data(
        self,
        symbol: str,
        timeframe: str,
        start_pos: int,
        end_pos: int,
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data sliced to the requested bar-position range.

        Args:
            symbol: Trading symbol, used for logging context.
            timeframe: Timeframe string, used for logging context.
            start_pos: Start bar index, inclusive.
            end_pos: End bar index, exclusive.

        Returns:
            Optional[pd.DataFrame]: Requested range, or ``None`` if the range is
            outside the loaded frame.

        Raises:
            ValueError: If symbol, timeframe, or range arguments are invalid.
        """
        normalized_symbol = _validate_symbol(symbol)
        normalized_timeframe = _validate_timeframe(timeframe)
        _validate_position_range(start_pos, end_pos)

        logger.info(
            "CSVDataSource loading | symbol=%s | timeframe=%s | path=%s | range=%s:%s",
            normalized_symbol,
            normalized_timeframe,
            self._filepath,
            start_pos,
            end_pos,
        )
        frame = self._get_cached_or_load()
        if end_pos > len(frame):
            logger.warning(
                "CSVDataSource invalid range | rows=%s | range=%s:%s",
                len(frame),
                start_pos,
                end_pos,
            )
            return None
        return frame.iloc[start_pos:end_pos]


def clear_data_cache() -> None:
    """Clear the internal DataFrame cache used by CSV helpers."""
    clear_dataframe_cache()
    logger.info("CSV data cache cleared")


def get_cached_data(key: str, loader_func: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    """Get data from cache or load it using the provided loader function.

    Args:
        key: Unique cache key.
        loader_func: Loader called on cache miss.

    Returns:
        pd.DataFrame: Cached or freshly loaded DataFrame.

    Raises:
        ValueError: If ``key`` is missing.
        TypeError: If the cache returns a non-DataFrame object.
    """
    if not isinstance(key, str) or not key.strip():
        raise ValueError("cache key must be a non-empty string.")
    if not callable(loader_func):
        raise ValueError("loader_func must be callable.")

    result = get_cached_dataframe(key, loader_func)
    if isinstance(result, Mapping) and result.get("status") == "success":
        result = result.get("data")
    return _validate_dataframe(result, source="cache loader")


def csv_data_fetch_range(
    path: PathLike,
    *,
    symbol: str,
    timeframe: str,
    start_pos: int,
    end_pos: int,
    date_column: Optional[str] = None,
    cache: bool = True,
    request_id: Optional[str] = None,
    require_ohlc: bool = True,
    **read_csv_kwargs: Any,
) -> ToolResponse:
    """Fetch an OHLCV/OHLCVS range from a CSV file.

    Use this read-only tool when an agent needs a specific bar-position slice
    from a local CSV market-data file for validation, research, preprocessing,
    or backtest preparation.

    Args:
        path: Path to the CSV file.
        symbol: Trading symbol represented by the CSV data.
        timeframe: Timeframe of the CSV data.
        start_pos: Start bar index, inclusive.
        end_pos: End bar index, exclusive.
        date_column: Optional explicit date/time column name.
        cache: Whether to cache the loaded DataFrame.
        request_id: Optional workflow trace ID.
        require_ohlc: Whether to require open/high/low/close columns.
        **read_csv_kwargs: Additional pandas CSV loading options.

    Returns:
        ToolResponse: Standard tool response with serialized records.
    """
    tool_name = CSV_DATA_FETCH_RANGE_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        _validate_csv_path(path, must_exist=True)
        symbol = _validate_symbol(symbol)
        timeframe = _validate_timeframe(timeframe)
        _validate_position_range(start_pos, end_pos)
        if not isinstance(cache, bool):
            raise ValueError("cache must be a boolean.")
        if not isinstance(require_ohlc, bool):
            raise ValueError("require_ohlc must be a boolean.")
        if date_column is not None and not isinstance(date_column, str):
            raise ValueError("date_column must be a string or None.")
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid CSV range request.",
            details=str(error),
        )

    try:
        source = CSVDataSource(
            path,
            date_column=date_column,
            cache=cache,
            require_ohlc=require_ohlc,
            **read_csv_kwargs,
        )
        frame = source.fetch_data(
            symbol=symbol,
            timeframe=timeframe,
            start_pos=start_pos,
            end_pos=end_pos,
        )
        if frame is None:
            return _tool_response(
                tool_name=tool_name,
                started_at=started_at,
                request_id=request_id,
                status="error",
                message="CSV data range is unavailable.",
                error_code="DATA_NOT_FOUND",
                error_details="The requested range exceeds the available CSV rows.",
            )

        payload = {
            "source": tool_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "data": _serialize_frame_records(frame),
        }
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="CSV data range loaded successfully.",
            data=payload,
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def csv_data_load(
    path: PathLike,
    index_col: Union[int, str, None] = 0,
    parse_dates: bool = True,
    request_id: Optional[str] = None,
    require_ohlc: bool = True,
) -> ToolResponse:
    """Load a CSV file into a JSON-safe OHLCV/OHLCVS payload.

    Use this read-only tool when an agent needs to inspect or pass local CSV
    market data through a standardized tool response.

    Args:
        path: Path to the CSV file.
        index_col: Column to use as index.
        parse_dates: Whether pandas should parse date columns.
        request_id: Optional workflow trace ID.
        require_ohlc: Whether to require open/high/low/close columns.

    Returns:
        ToolResponse: Standard tool response with serialized market-data records.
    """
    tool_name = CSV_DATA_LOAD_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        source_path = _validate_csv_path(path, must_exist=True)
        if not isinstance(parse_dates, bool):
            raise ValueError("parse_dates must be a boolean.")
        if index_col is not None and not isinstance(index_col, (int, str)):
            raise ValueError("index_col must be an int, str, or None.")
        if not isinstance(require_ohlc, bool):
            raise ValueError("require_ohlc must be a boolean.")
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid CSV load request.",
            details=str(error),
        )

    try:
        frame = load_csv(
            source_path,
            index_col=index_col,
            parse_dates=parse_dates,
            require_ohlc=require_ohlc,
        )
        payload = {
            "source": tool_name,
            "path": str(source_path),
            "symbol": source_path.stem.upper(),
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "data": _serialize_frame_records(frame),
        }
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="CSV data loaded successfully.",
            data=payload,
        )
    except FileNotFoundError as error:
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="error",
            message="CSV file was not found.",
            error_code="DATA_NOT_FOUND",
            error_details=str(error),
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def csv_data_saver_file_exists(
    path: Optional[PathLike] = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    request_id: Optional[str] = None,
) -> ToolResponse:
    """Check whether a saved CSV market-data file exists.

    Use this read-only tool before saving or loading CSV artifacts to decide
    whether a workflow should create a new artifact or reuse an existing one.

    Args:
        path: Optional explicit CSV path.
        symbol: Symbol for the default saved filename when ``path`` is omitted.
        timeframe: Timeframe for the default saved filename when ``path`` is omitted.
        request_id: Optional workflow trace ID.

    Returns:
        ToolResponse: Standard tool response containing ``exists`` and ``path``.
    """
    tool_name = CSV_DATA_SAVER_FILE_EXISTS_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        symbol = _validate_symbol(symbol)
        timeframe = _validate_timeframe(timeframe)
        if path is not None:
            _validate_csv_path(path, must_exist=False)
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid CSV file-exists request.",
            details=str(error),
        )

    try:
        target_path = _saved_data_path(
            extension="csv",
            path=path,
            symbol=symbol,
            timeframe=timeframe,
        )
        exists = target_path.exists()
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="CSV file existence checked successfully.",
            data={"exists": exists, "path": str(target_path)},
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def csv_data_saver_save(
    data: Union[Data, Dict[str, Any]],
    path: Optional[PathLike] = None,
    is_initial: bool = False,
    request_id: Optional[str] = None,
) -> ToolResponse:
    """Save market data to CSV with sidecar metadata.

    Use this medium-risk file-writing tool when an agent workflow needs to
    persist local market data as a CSV artifact. This tool writes local files
    but does not modify databases, place trades, or require network access.

    Args:
        data: Data object or market-data payload accepted by ``_save_data``.
        path: Optional output CSV path.
        is_initial: Whether this is the first saved snapshot.
        request_id: Optional workflow trace ID.

    Returns:
        ToolResponse: Standard tool response with saved file metadata.
    """
    tool_name = CSV_DATA_SAVER_SAVE_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        if data is None:
            raise ValueError("data argument is required.")
        if not isinstance(is_initial, bool):
            raise ValueError("is_initial must be a boolean.")
        if path is not None:
            _validate_csv_path(path, must_exist=False)
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid CSV save request.",
            details=str(error),
            tool_risk_level=MEDIUM_RISK,
            read_only=False,
            writes_file=True,
        )

    try:
        payload = _save_data(data, extension="csv", path=path, is_initial=is_initial)
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="CSV data saved successfully.",
            data=payload,
            tool_risk_level=MEDIUM_RISK,
            read_only=False,
            writes_file=True,
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
            tool_risk_level=MEDIUM_RISK,
            read_only=False,
            writes_file=True,
        )


def csv_data_saver_load(
    path: Optional[PathLike] = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    request_id: Optional[str] = None,
) -> ToolResponse:
    """Load saved CSV data and sidecar metadata.

    Use this read-only tool when an agent needs to retrieve a previously
    persisted CSV market-data artifact.

    Args:
        path: Optional explicit CSV path.
        symbol: Symbol for the default saved filename when ``path`` is omitted.
        timeframe: Timeframe for the default saved filename when ``path`` is omitted.
        request_id: Optional workflow trace ID.

    Returns:
        ToolResponse: Standard tool response with candles and metadata.
    """
    tool_name = CSV_DATA_SAVER_LOAD_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        symbol = _validate_symbol(symbol)
        timeframe = _validate_timeframe(timeframe)
        if path is not None:
            _validate_csv_path(path, must_exist=False)
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid saved CSV load request.",
            details=str(error),
        )

    try:
        data_obj = _load_saved_data(
            extension="csv",
            path=path,
            symbol=symbol,
            timeframe=timeframe,
        )
        target_path = _saved_data_path(
            extension="csv",
            path=path,
            symbol=symbol,
            timeframe=timeframe,
        )
        frame = _validate_dataframe(data_obj.df, source=str(target_path))
        payload = {
            "source": tool_name,
            "path": str(target_path),
            "metadata": _data_to_metadata(data_obj),
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "candles": _serialize_frame_records(frame),
        }
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="Saved CSV data loaded successfully.",
            data=payload,
        )
    except FileNotFoundError as error:
        logger.warning("%s data not found | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="error",
            message="Saved CSV data was not found.",
            error_code="DATA_NOT_FOUND",
            error_details=str(error),
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


__all__ = [
    "CSVDataSource",
    "clear_data_cache",
    "csv_data_fetch_range",
    "csv_data_load",
    "csv_data_saver_file_exists",
    "csv_data_saver_load",
    "csv_data_saver_save",
    "get_cached_data",
    "load_csv",
]
