"""Load, cache, and persist Parquet-backed market data.

Purpose:
    Provide Parquet-backed helper functions and AI-callable tools for loading,
    checking, saving, and reloading local market data artifacts.

Exported AI Tools:
    - parquet_data_load: Load a Parquet file into a JSON-safe market-data payload.
    - parquet_data_saver_file_exists: Check whether a saved Parquet artifact exists.
    - parquet_data_saver_save: Save market-data payloads to Parquet with metadata.
    - parquet_data_saver_load: Load saved Parquet market data and metadata.

Internal Helpers:
    - get_data_dir: Return the project data directory.
    - load_parquet: Load a Parquet file as a DataFrame for implementation code.

Classes:
    None
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.utils.logger import logger

from .csv import get_cached_data
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


def get_data_dir() -> Path:
    """Description.
        Return the project data directory for implementation code.
    
    Args:
        None.
    
    Returns:
        Path.
    """
    logger.debug("Resolving global project data directory path.")
    return Path(__file__).resolve().parents[3] / "data"


def load_parquet(file_path: str | Path) -> pd.DataFrame:
    """Description.
        Load a Parquet file as a DataFrame with cache support.
    
    Args:
        file_path: str | Path.
    
    Returns:
        pd.DataFrame.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    def _loader() -> pd.DataFrame:
        """Description.
            Load the Parquet file from disk for the cache miss path.
        
        Args:
            None.
        
        Returns:
            pd.DataFrame.
        """
        logger.debug(f"Cache miss: Reading Parquet file directly from disk: {path}")
        return pd.read_parquet(path)

    logger.debug(f"Attempting to load Parquet file from path={file_path} (checking cache first).")
    return get_cached_data(str(path.resolve()), _loader)


def parquet_data_load(
    path: str | Path,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Load a Parquet file into a JSON-safe OHLCV payload.
    
    Args:
        path: str | Path.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "parquet_data_load"
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
        frame = load_parquet(path)
        frame.columns = [str(column).lower() for column in frame.columns]
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
            message="Parquet data loaded successfully.",
            data=payload,
        )
    except FileNotFoundError as error:
        logger.warning("{} data not found | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="error",
            message="Parquet data was not found.",
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


def parquet_data_saver_file_exists(
    path: str | Path | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Check whether a saved Parquet market-data file exists.
    
    Args:
        path: str | Path | None.
        symbol: str.
        timeframe: str.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "parquet_data_saver_file_exists"
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
            extension="parquet",
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
            message="Parquet file existence checked successfully.",
            data={"exists": exists},
        )
    except Exception as error:
        return _data_tool_execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def parquet_data_saver_save(
    data: Data | dict[str, Any],
    path: str | Path | None = None,
    is_initial: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Save market data to Parquet with sidecar metadata.
    
    Args:
        data: Data | dict[str, Any].
        path: str | Path | None.
        is_initial: bool.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "parquet_data_saver_save"
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
        payload = _save_data(
            data, extension="parquet", path=path, is_initial=is_initial
        )
        logger.info("{} completed successfully | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="Parquet data saved successfully.",
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


def parquet_data_saver_load(
    path: str | Path | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Load saved Parquet data and sidecar metadata.
    
    Args:
        path: str | Path | None.
        symbol: str.
        timeframe: str.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    tool_name = "parquet_data_saver_load"
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
            message="Saved Parquet data loaded successfully.",
            data=payload,
        )
    except FileNotFoundError as error:
        logger.warning("{} data not found | request_id={}", tool_name, request_id)
        return _data_tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="error",
            message="Saved Parquet data was not found.",
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
    "get_data_dir",
    "load_parquet",
    "parquet_data_load",
    "parquet_data_saver_file_exists",
    "parquet_data_saver_load",
    "parquet_data_saver_save",
]
