"""Parquet-backed market-data tools for HaruQuantAI.

Purpose:
    Load, validate, cache, save, and reload local Parquet-backed market-data
    artifacts.

This module contains both implementation helpers and official AI-callable tools.
Any function exported through ``tools.data.__all__`` is treated as an official
HaruQuantAI tool and must return the standard tool response schema.

Exported AI Tools:
    - parquet_data_load: Load a Parquet file into a JSON-safe market-data payload.
    - parquet_data_saver_file_exists: Check whether a saved Parquet artifact exists.
    - parquet_data_saver_save: Save market-data payloads to Parquet with metadata.
    - parquet_data_saver_load: Load saved Parquet market data and metadata.

Internal/Public Helpers:
    - get_data_dir: Return the project data directory.
    - load_parquet: Load a Parquet file as a normalized DataFrame.

Classes:
    None
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Union

import pandas as pd

from tools.utils import logger
from tools.utils.common import get_cached_dataframe

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

PARQUET_DATA_LOAD_TOOL = "parquet_data_load"
PARQUET_DATA_SAVER_FILE_EXISTS_TOOL = "parquet_data_saver_file_exists"
PARQUET_DATA_SAVER_SAVE_TOOL = "parquet_data_saver_save"
PARQUET_DATA_SAVER_LOAD_TOOL = "parquet_data_saver_load"

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
        message="Parquet tool execution failed.",
        error_code="TOOL_EXECUTION_FAILED",
        error_details=str(error),
        tool_risk_level=tool_risk_level,
        read_only=read_only,
        writes_file=writes_file,
    )


def _validate_parquet_path(
    path: PathLike,
    *,
    must_exist: bool,
    parent_must_exist: bool = False,
) -> Path:
    """Validate and normalize a Parquet path.

    Args:
        path: User-provided path-like value.
        must_exist: Whether the path must already exist.
        parent_must_exist: Whether the parent directory must already exist.

    Returns:
        Path: Normalized path object.

    Raises:
        FileNotFoundError: If the path or required parent directory is missing.
        ValueError: If the path is missing, points to a directory, or is not Parquet.
    """
    if not isinstance(path, (str, Path)) or str(path).strip() == "":
        raise ValueError("path must be a non-empty string or pathlib.Path.")

    candidate = Path(path).expanduser()
    if candidate.suffix.lower() != ".parquet":
        raise ValueError(f"path must point to a .parquet file: {candidate}")

    if candidate.exists() and candidate.is_dir():
        raise ValueError(
            f"path must point to a Parquet file, not a directory: {candidate}"
        )

    if must_exist and not candidate.exists():
        raise FileNotFoundError(f"Parquet file not found: {candidate}")

    if parent_must_exist and candidate.parent and not candidate.parent.exists():
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
            "Parquet market data is missing required OHLC columns: "
            + ", ".join(missing)
        )


def _normalize_market_frame(frame: pd.DataFrame, *, require_ohlc: bool) -> pd.DataFrame:
    """Return a normalized market-data DataFrame copy."""
    result = _validate_dataframe(frame, source="Parquet loader").copy()
    result.columns = [str(column).strip().lower() for column in result.columns]

    for column in sorted(set(result.columns) & NUMERIC_MARKET_COLUMNS):
        result[column] = pd.to_numeric(result[column], errors="coerce")

    _validate_market_columns(result, require_ohlc=require_ohlc)
    return result


def get_data_dir() -> Path:
    """Return the project data directory for implementation code.

    Returns:
        Path: The repository-level ``data`` directory.
    """
    return Path(__file__).resolve().parents[2] / "data"


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


def load_parquet(file_path: PathLike, *, require_ohlc: bool = True) -> pd.DataFrame:
    """Load a Parquet file as a normalized DataFrame with cache support.

    This helper is intended for implementation code. Agents should call
    ``parquet_data_load`` from ``tools.data`` instead.

    Args:
        file_path: Path to the Parquet file.
        require_ohlc: Whether to require open/high/low/close columns.

    Returns:
        pd.DataFrame: Loaded DataFrame with normalized lowercase columns.

    Raises:
        FileNotFoundError: If the Parquet file does not exist.
        ValueError: If the file is invalid or missing required columns.
        TypeError: If the cache layer returns a non-DataFrame object.
    """
    if not isinstance(require_ohlc, bool):
        raise ValueError("require_ohlc must be a boolean.")

    path = _validate_parquet_path(file_path, must_exist=True)
    key = f"parquet_load:{path.resolve()}:{require_ohlc}"

    def _loader() -> pd.DataFrame:
        """Load the Parquet file from disk for the cache miss path."""
        frame = pd.read_parquet(path)
        return _normalize_market_frame(frame, require_ohlc=require_ohlc)

    return get_cached_data(key, _loader)


def parquet_data_load(
    path: PathLike,
    request_id: Optional[str] = None,
    require_ohlc: bool = True,
) -> ToolResponse:
    """Load a Parquet file into a JSON-safe OHLCV/OHLCVS payload.

    Use this read-only tool when an agent needs to inspect or pass local Parquet
    market data through a standardized tool response for research, validation,
    preprocessing, or backtest preparation.

    Args:
        path: Path to the Parquet file.
        request_id: Optional workflow trace ID.
        require_ohlc: Whether to require open/high/low/close columns.

    Returns:
        ToolResponse: Standard tool response with serialized market-data records.
    """
    tool_name = PARQUET_DATA_LOAD_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        source_path = _validate_parquet_path(path, must_exist=False)
        if not isinstance(require_ohlc, bool):
            raise ValueError("require_ohlc must be a boolean.")
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid Parquet load request.",
            details=str(error),
        )

    try:
        frame = load_parquet(source_path, require_ohlc=require_ohlc)
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
            message="Parquet data loaded successfully.",
            data=payload,
        )
    except FileNotFoundError as error:
        logger.warning("%s data not found | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="error",
            message="Parquet file was not found.",
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


def parquet_data_saver_file_exists(
    path: Optional[PathLike] = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    request_id: Optional[str] = None,
) -> ToolResponse:
    """Check whether a saved Parquet market-data file exists.

    Use this read-only tool before saving or loading Parquet artifacts to decide
    whether a workflow should create a new artifact or reuse an existing one.

    Args:
        path: Optional explicit Parquet path.
        symbol: Symbol for the default saved filename when ``path`` is omitted.
        timeframe: Timeframe for the default saved filename when ``path`` is omitted.
        request_id: Optional workflow trace ID.

    Returns:
        ToolResponse: Standard tool response containing ``exists`` and ``path``.
    """
    tool_name = PARQUET_DATA_SAVER_FILE_EXISTS_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        symbol = _validate_symbol(symbol)
        timeframe = _validate_timeframe(timeframe)
        if path is not None:
            _validate_parquet_path(path, must_exist=False)
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid Parquet file-exists request.",
            details=str(error),
        )

    try:
        target_path = _saved_data_path(
            extension="parquet",
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
            message="Parquet file existence checked successfully.",
            data={"exists": exists, "path": str(target_path)},
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def parquet_data_saver_save(
    data: Union[Data, Dict[str, Any]],
    path: Optional[PathLike] = None,
    is_initial: bool = False,
    request_id: Optional[str] = None,
) -> ToolResponse:
    """Save market data to Parquet with sidecar metadata.

    Use this medium-risk file-writing tool when an agent workflow needs to
    persist local market data as a Parquet artifact. This tool writes local
    files but does not modify databases, place trades, or require network
    access.

    Args:
        data: Data object or market-data payload accepted by ``_save_data``.
        path: Optional output Parquet path.
        is_initial: Whether this is the first saved snapshot.
        request_id: Optional workflow trace ID.

    Returns:
        ToolResponse: Standard tool response with saved file metadata.
    """
    tool_name = PARQUET_DATA_SAVER_SAVE_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        if data is None:
            raise ValueError("data argument is required.")
        if not isinstance(is_initial, bool):
            raise ValueError("is_initial must be a boolean.")
        if path is not None:
            _validate_parquet_path(
                path,
                must_exist=False,
                parent_must_exist=True,
            )
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid Parquet save request.",
            details=str(error),
            tool_risk_level=MEDIUM_RISK,
            read_only=False,
            writes_file=True,
        )

    try:
        payload = _save_data(
            data,
            extension="parquet",
            path=path,
            is_initial=is_initial,
        )
        logger.info("%s completed successfully | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="Parquet data saved successfully.",
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


def parquet_data_saver_load(
    path: Optional[PathLike] = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    request_id: Optional[str] = None,
    require_ohlc: bool = True,
) -> ToolResponse:
    """Load saved Parquet data and sidecar metadata.

    Use this read-only tool when an agent needs to retrieve a previously
    persisted Parquet market-data artifact.

    Args:
        path: Optional explicit Parquet path.
        symbol: Symbol for the default saved filename when ``path`` is omitted.
        timeframe: Timeframe for the default saved filename when ``path`` is omitted.
        request_id: Optional workflow trace ID.
        require_ohlc: Whether to require open/high/low/close columns.

    Returns:
        ToolResponse: Standard tool response with candles and metadata.
    """
    tool_name = PARQUET_DATA_SAVER_LOAD_TOOL
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s | path=%s", tool_name, request_id, path)

    try:
        symbol = _validate_symbol(symbol)
        timeframe = _validate_timeframe(timeframe)
        if not isinstance(require_ohlc, bool):
            raise ValueError("require_ohlc must be a boolean.")
        if path is not None:
            _validate_parquet_path(path, must_exist=False)
    except Exception as error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid saved Parquet load request.",
            details=str(error),
        )

    try:
        data_obj = _load_saved_data(
            extension="parquet",
            path=path,
            symbol=symbol,
            timeframe=timeframe,
        )
        target_path = _saved_data_path(
            extension="parquet",
            path=path,
            symbol=symbol,
            timeframe=timeframe,
        )
        frame = _normalize_market_frame(data_obj.df, require_ohlc=require_ohlc)
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
            message="Saved Parquet data loaded successfully.",
            data=payload,
        )
    except FileNotFoundError as error:
        logger.warning("%s data not found | request_id=%s", tool_name, request_id)
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="error",
            message="Saved Parquet data was not found.",
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
    "get_data_dir",
    "get_cached_data",
    "load_parquet",
    "parquet_data_load",
    "parquet_data_saver_file_exists",
    "parquet_data_saver_load",
    "parquet_data_saver_save",
]
