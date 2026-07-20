"""Load, cache, and persist CSV-backed market data.

Purpose:
    Provide CSV-backed data helpers and AI-callable tools for loading,
    slicing, checking, saving, and reloading local market data files.

Exported AI Tools:
    - csv_data_fetch_range: Fetch a bar-position range from a CSV file.
    - csv_data_load: Load a CSV file into a JSON-safe market-data payload.
    - csv_data_saver_file_exists: Check whether a saved CSV artifact exists.
    - csv_data_saver_save: Save market-data payloads to CSV with metadata.
    - csv_data_saver_load: Load saved CSV market data and metadata.

Internal Helpers:
    - load_csv: Load a CSV file as a DataFrame for implementation code.
    - clear_data_cache: Clear the process-local DataFrame cache.
    - get_cached_data: Load or retrieve a cached DataFrame.

Classes:
    - CSVDataSource: Internal CSV-backed DataSource implementation.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.utils.common import clear_dataframe_cache, get_cached_dataframe
from app.services.utils.logger import logger

from .frames import (
    Data,
    _data_to_metadata,
    _load_saved_data,
    _save_data,
    _saved_data_path,
    _serialize_frame_records,
)
from .responses import (
    _data_tool_execution_error,
    _data_tool_response,
    _data_tool_validation_error,
)


def load_csv(
    file_path: str | Path,
    *,
    index_col: int | str | None = 0,
    parse_dates: bool = True,
) -> pd.DataFrame:
    """Description.
        Load a CSV file into a DataFrame with lowercase column names.
    
    Args:
        file_path: str | Path.
        index_col: int | str | None.
        parse_dates: bool.
    
    Returns:
        pd.DataFrame.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    key = f"csv_load:{path.resolve()}:{index_col}:{parse_dates}"

    def _loader() -> pd.DataFrame:
        """Description.
            Load the CSV from disk for the cache miss path.
        
        Args:
            None.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(f"Cache miss: Reading CSV file directly from path: {path}")
        frame = pd.read_csv(path, index_col=index_col, parse_dates=parse_dates)
        frame.columns = [str(column).lower() for column in frame.columns]
        return frame

    logger.debug(f"Attempting to load CSV file from path={file_path} (checking cache first).")
    return get_cached_data(key, _loader)


class CSVDataSource:
    """CSV-backed DataSource implementation for internal data pipelines.

    Use this class when implementation code needs a DataSource-style object
    that can load OHLCV rows from a CSV file and slice them by position.
    Agents should call the exported CSV tools instead of constructing this
    class directly.
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
        "spread": "spread",
    }

    def __init__(
        self,
        filepath: str | Path,
        *,
        date_column: str | None = None,
        cache: bool = True,
        **read_csv_kwargs: Any,
    ) -> None:
        """Description.
            Initialize the CSV data source.
        
        Args:
            filepath: str | Path.
            date_column: str | None.
            cache: bool.
            read_csv_kwargs: Any.
        
        Returns:
            None.
        """
        self._filepath = Path(filepath)
        self._date_column = date_column
        self._cache = cache
        self._read_csv_kwargs = read_csv_kwargs
        self._loaded: pd.DataFrame | None = None
        logger.debug("Initialized CSVDataSource for %s.", self._filepath)

    def _detect_date_column(self, columns: list[str]) -> str | None:
        """Description.
            Return the first column name that looks like a datetime field.
        
        Args:
            columns: list[str].
        
        Returns:
            str | None.
        """
        logger.debug(f"Detecting date column from columns: {columns}")
        hints = set(self._DATETIME_HINTS)
        for col in columns:
            if col.lower() in hints:
                return col
        return None

    def _load(self) -> pd.DataFrame:
        """Description.
            Load and normalize the CSV into a DataFrame with DatetimeIndex.
        
        Args:
            None.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(f"Loading and normalizing CSV file at path: {self._filepath}")
        if not self._filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {self._filepath}")

        df = pd.read_csv(self._filepath, **dict(self._read_csv_kwargs))
        if df.empty:
            raise ValueError(f"CSV file is empty: {self._filepath}")

        df.columns = [str(column).strip().lower() for column in df.columns]
        date_col = self._date_column.lower() if self._date_column is not None else None
        date_col = date_col or self._detect_date_column(list(df.columns))
        if date_col is None:
            raise ValueError(
                f"No date/time column detected in {self._filepath}. "
                f"Provide date_column or a column named {'/'.join(self._DATETIME_HINTS)}."
            )

        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).sort_index()
        existing_columns = {str(column).lower() for column in df.columns}
        rename_map = {}
        for column in df.columns:
            source_column = str(column).lower()
            target_column = self._COLUMN_MAP.get(source_column)
            if target_column is None:
                continue
            if target_column in existing_columns and source_column != target_column:
                continue
            rename_map[column] = target_column
            existing_columns.add(target_column)
        if rename_map:
            df = df.rename(columns=rename_map)

        for column in set(df.columns) & {
            "open",
            "high",
            "low",
            "close",
            "volume",
            "spread",
        }:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        return df

    def _get_cached_or_load(self) -> pd.DataFrame:
        """Description.
            Load from cache or disk.
        
        Args:
            None.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(f"Getting cached or loading CSV data from path: {self._filepath}")
        if self._loaded is not None:
            return self._loaded.copy()

        if self._cache:
            key = f"csv:{self._filepath.resolve()}"
            frame = get_cached_dataframe(key, self._load)
            if isinstance(frame, dict) and frame.get("status") == "success":
                frame = frame["data"]
        else:
            frame = self._load()

        self._loaded = frame
        return frame.copy()

    def fetch_data(
        self,
        symbol: str,
        timeframe: str,
        start_pos: int,
        end_pos: int,
    ) -> pd.DataFrame | None:
        """Description.
            Fetch OHLCV data sliced to the requested bar-position range.
        
        Args:
            symbol: str.
            timeframe: str.
            start_pos: int.
            end_pos: int.
        
        Returns:
            pd.DataFrame | None.
        """
        logger.info(
            "CSVDataSource loading | symbol={} | timeframe={} | path={} | range={}:{}",
            symbol,
            timeframe,
            self._filepath,
            start_pos,
            end_pos,
        )
        frame = self._get_cached_or_load()
        if start_pos < 0 or end_pos > len(frame) or start_pos >= end_pos:
            logger.warning(
                "CSVDataSource invalid range | rows={} | range={}:{}",
                len(frame),
                start_pos,
                end_pos,
            )
            return None
        return frame.iloc[start_pos:end_pos]


def clear_data_cache() -> None:
    """Description.
        Clear the internal DataFrame cache used by CSV helpers.
    
    Args:
        None.
    
    Returns:
        None.
    """
    clear_dataframe_cache()
    logger.info("Data cache cleared")


def get_cached_data(key: str, loader_func: Callable[[], pd.DataFrame]) -> pd.DataFrame:
    """Description.
        Get data from cache or load it using the provided loader function.
    
    Args:
        key: str.
        loader_func: Callable[[], pd.DataFrame].
    
    Returns:
        pd.DataFrame.
    """
    result = get_cached_dataframe(key, loader_func)
    logger.debug(f"Retrieving cached dataframe for key: {key}")
    if isinstance(result, dict) and result.get("status") == "success":
        return result["data"]
    return result


def csv_data_fetch_range(
    path: str | Path,
    *,
    symbol: str,
    timeframe: str,
    start_pos: int,
    end_pos: int,
    date_column: str | None = None,
    cache: bool = True,
    request_id: str | None = None,
    **read_csv_kwargs: Any,
) -> dict[str, Any]:
    """Description.
        Fetch an OHLCV range from a CSV file.
    
    Args:
        path: str | Path.
        symbol: str.
        timeframe: str.
        start_pos: int.
        end_pos: int.
        date_column: str | None.
        cache: bool.
        request_id: str | None.
        read_csv_kwargs: Any.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "csv_data_fetch_range"
    started_at = time.perf_counter()
    logger.info("{} called | request_id={} | path={}", tool_name, request_id, path)

    if not path or not symbol or not timeframe:
        return _data_tool_validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="path, symbol, and timeframe are required.",
        )
    if start_pos < 0 or end_pos <= start_pos:
        return _data_tool_validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="start_pos and end_pos define an invalid range.",
            details="start_pos must be >= 0 and end_pos must be greater than start_pos.",
        )

    try:
        source = CSVDataSource(
            path, date_column=date_column, cache=cache, **read_csv_kwargs
        )
        frame = source.fetch_data(
            symbol=symbol,
            timeframe=timeframe,
            start_pos=start_pos,
            end_pos=end_pos,
        )
        if frame is None:
            return _data_tool_response(
                tool_name=tool_name,
                started_at=started_at,
                request_id=request_id,
                status="error",
                message="CSV data range is unavailable.",
                error_code="DATA_NOT_FOUND",
                error_details="Invalid range or no data available for the requested slice.",
            )

        payload = {
            "source": tool_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "data": _serialize_frame_records(frame),
        }
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="CSV data range loaded successfully.",
            data=payload,
        )
    except Exception as error:
        return _data_tool_execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def csv_data_load(
    path: str | Path,
    index_col: int | str | None = 0,
    parse_dates: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Load a CSV file into a JSON-safe OHLCV payload.
    
    Args:
        path: str | Path.
        index_col: int | str | None.
        parse_dates: bool.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "csv_data_load"
    started_at = time.perf_counter()
    logger.info("{} called | request_id={} | path={}", tool_name, request_id, path)

    if not path:
        return _data_tool_validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="path argument is required.",
        )

    try:
        frame = load_csv(path, index_col=index_col, parse_dates=parse_dates)
        source_path = Path(path)
        payload = {
            "source": tool_name,
            "path": str(source_path),
            "symbol": source_path.stem,
            "rows": int(len(frame)),
            "columns": [str(column) for column in frame.columns],
            "data": _serialize_frame_records(frame),
        }
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="CSV data loaded successfully.",
            data=payload,
        )
    except Exception as error:
        return _data_tool_execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def csv_data_saver_file_exists(
    path: str | Path | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Check whether a saved CSV market-data file exists.
    
    Args:
        path: str | Path | None.
        symbol: str.
        timeframe: str.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "csv_data_saver_file_exists"
    started_at = time.perf_counter()
    logger.info("{} called | request_id={} | path={}", tool_name, request_id, path)

    if not symbol or not timeframe:
        return _data_tool_validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="symbol and timeframe are required.",
        )

    try:
        exists = _saved_data_path(
            extension="csv",
            path=path,
            symbol=symbol,
            timeframe=timeframe,
        ).exists()
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="CSV file existence checked successfully.",
            data={"exists": exists},
        )
    except Exception as error:
        return _data_tool_execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def csv_data_saver_save(
    data: Data | dict[str, Any],
    path: str | Path | None = None,
    is_initial: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Save market data to CSV with sidecar metadata.
    
    Args:
        data: Data | dict[str, Any].
        path: str | Path | None.
        is_initial: bool.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "csv_data_saver_save"
    started_at = time.perf_counter()
    logger.info("{} called | request_id={} | path={}", tool_name, request_id, path)

    if data is None:
        return _data_tool_validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="data argument is required.",
            read_only=False,
            writes_file=True,
        )

    try:
        payload = _save_data(data, extension="csv", path=path, is_initial=is_initial)
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="CSV data saved successfully.",
            data=payload,
            tool_risk_level="medium",
            read_only=False,
            writes_file=True,
        )
    except Exception as error:
        return _data_tool_execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
            read_only=False,
            writes_file=True,
        )


def csv_data_saver_load(
    path: str | Path | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Load saved CSV data and sidecar metadata.
    
    Args:
        path: str | Path | None.
        symbol: str.
        timeframe: str.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "csv_data_saver_load"
    started_at = time.perf_counter()
    logger.info("{} called | request_id={} | path={}", tool_name, request_id, path)

    if not symbol or not timeframe:
        return _data_tool_validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="symbol and timeframe are required.",
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
        payload = {
            "source": tool_name,
            "path": str(target_path),
            "metadata": _data_to_metadata(data_obj),
            "rows": int(len(data_obj.df)),
            "columns": [str(column) for column in data_obj.df.columns],
            "candles": _serialize_frame_records(data_obj.df),
        }
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="Saved CSV data loaded successfully.",
            data=payload,
        )
    except FileNotFoundError as error:
        logger.warning("{} data not found | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="error",
            message="Saved CSV data was not found.",
            error_code="DATA_NOT_FOUND",
            error_details=str(error),
        )
    except Exception as error:
        return _data_tool_execution_error(
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
