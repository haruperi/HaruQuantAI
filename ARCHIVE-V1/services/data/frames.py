"""Provide the in-memory market-data container and frame helpers.

Purpose:
    Hold the shared ``Data`` container plus the DataFrame/record conversion,
    serialization, and CSV/Parquet persistence helpers reused across the data,
    indicator, optimization, and utility modules. These primitives previously
    lived in ``app.services.data._common`` and were extracted so that legacy
    module can be retired.

Classes and functions:
    Data: Class. Wrapper class for trading data, mimicking VectorBT's Data object.
    _frame_from_records: Build a DataFrame from either direct data or JSON-style records.
    _serialize_frame_records: Convert a pandas DataFrame to JSON-safe records.
    _json_safe: Convert pandas/numpy/datetime objects into JSON-safe values.
    _data_from_payload: Build a Data object from a data tool payload.
    _coerce_data: Coerce a Data object or payload dict into a Data object.
    _data_to_metadata: Build JSON-safe metadata describing a Data object.
    _saved_data_path: Resolve the on-disk path for saved market data.
    _save_data: Persist a Data object to CSV or Parquet with metadata.
    _load_saved_data: Load a previously saved Data object from disk.
    data_df: Convert a data tool payload into a pandas DataFrame.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd
from app.services.utils.common import serialize_dataframe_records
from app.services.utils.logger import logger

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Data:
    """Wrapper class for trading data, mimicking VectorBT's Data object."""

    def __init__(
        self,
        df: pd.DataFrame,
        symbol: str | list[str],
        timeframe: str | None = None,
    ) -> None:
        """Description.
            Initialize the data container.

        Args:
            df: pd.DataFrame.
            symbol: str | list[str].
            timeframe: str | None.

        Returns:
            None.
        """
        self._df = df
        self._symbol = symbol
        self._timeframe = timeframe
        self._source_name: str | None = None
        self._fetch_params: dict[str, Any] = {}
        logger.debug("Initialized Data container for %s.", symbol)

    @property
    def df(self) -> pd.DataFrame:
        """Description.
            Return the underlying market-data frame.

        Args:
            None.

        Returns:
            pd.DataFrame.
        """
        logger.debug("Converted data container to DataFrame.")
        return self._df

    @property
    def symbol(self) -> str | list[str]:
        """Description.
            Return the symbol(s) the data represents.

        Args:
            None.

        Returns:
            str | list[str].
        """
        logger.debug("Implemented symbol.")
        return self._symbol

    @property
    def timeframe(self) -> str | None:
        """Description.
            Return the timeframe identifier.

        Args:
            None.

        Returns:
            str | None.
        """
        logger.debug("Implemented timeframe.")
        return self._timeframe

    @property
    def close(self) -> pd.Series | pd.DataFrame:
        """Description.
            Return the close price(s).

        Args:
            None.

        Returns:
            pd.Series | pd.DataFrame.
        """
        logger.debug("Implemented close.")
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
        """Description.
            Return a DataFrame column matching ``name`` (case-insensitive).

        Args:
            name: str.

        Returns:
            Any.
        """
        logger.debug("Resolving Data attribute %s.", name)
        lower_cols = {str(c).lower(): c for c in self._df.columns}
        if name.lower() in lower_cols:
            return self._df[lower_cols[name.lower()]]
        raise AttributeError(f"'Data' object has no attribute '{name}'")


def _frame_from_records(
    records: list[dict[str, Any]] | None = None,
    data: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Description.
        Build a DataFrame from either direct data or JSON-style records.

    Args:
        records: list[dict[str, Any]] | None.
        data: pd.DataFrame | None.

    Returns:
        pd.DataFrame.
    """
    logger.debug("Implemented frame from records.")
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


def _serialize_frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Description.
        Convert a pandas DataFrame to JSON-safe records.

    Args:
        frame: pd.DataFrame.

    Returns:
        list[dict[str, Any]].
    """
    logger.debug("Implemented serialize frame records.")
    records = serialize_dataframe_records(frame)
    if isinstance(records, dict) and records.get("status") == "success":
        return cast("list[dict[str, Any]]", records.get("data", []))
    return cast("list[dict[str, Any]]", records)


def _json_safe(value: Any) -> Any:
    """Description.
        Convert pandas/numpy/datetime objects into JSON-safe values.

    Args:
        value: Any.

    Returns:
        Any.
    """
    logger.debug("Implemented json safe.")
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


def _data_from_payload(payload: dict[str, Any]) -> Data:
    """Description.
        Build a Data object from a data tool payload.

    Args:
        payload: dict[str, Any].

    Returns:
        Data.
    """
    logger.debug("Implemented data from payload.")
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
    symbol = (
        request.get("symbol")
        or metadata.get("symbol")
        or actual_payload.get("symbol")
        or ""
    )
    return Data(
        df,
        symbol=cast("str | list[str]", symbol),
        timeframe=request.get("timeframe")
        or metadata.get("timeframe")
        or actual_payload.get("timeframe"),
    )


def _coerce_data(data: Data | dict[str, Any]) -> Data:
    """Description.
        Coerce a Data object or payload dict into a Data object.

    Args:
        data: Data | dict[str, Any].

    Returns:
        Data.
    """
    logger.debug("Implemented coerce data.")
    if isinstance(data, Data):
        return data
    return _data_from_payload(data)


def _data_to_metadata(data: Data) -> dict[str, Any]:
    """Description.
        Build JSON-safe metadata describing a Data object.

    Args:
        data: Data.

    Returns:
        dict[str, Any].
    """
    logger.debug("Implemented data to metadata.")
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


def _saved_data_path(
    extension: str,
    path: str | Path | None = None,
    symbol: str = "EURUSD",
    timeframe: str = "M1",
) -> Path:
    """Description.
        Resolve the on-disk path for saved market data.

    Args:
        extension: str.
        path: str | Path | None.
        symbol: str.
        timeframe: str.

    Returns:
        Path.
    """
    logger.debug("Implemented saved data path.")
    if path:
        return Path(path)
    # Default path: project_root/data/saved/{symbol}_{timeframe}.{extension}
    save_dir = Path(PROJECT_ROOT) / "data" / "saved"
    save_dir.mkdir(parents=True, exist_ok=True)
    return save_dir / f"{symbol.upper()}_{timeframe.upper()}.{extension}"


def _save_data(
    data: Data | dict[str, Any],
    extension: str,
    path: str | Path | None = None,
    is_initial: bool = False,
) -> dict[str, Any]:
    """Description.
        Persist a Data object to CSV or Parquet with metadata.

    Args:
        data: Data | dict[str, Any].
        extension: str.
        path: str | Path | None.
        is_initial: bool.

    Returns:
        dict[str, Any].
    """
    logger.debug("Implemented save data.")
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
    """Description.
        Load a previously saved Data object from disk.

    Args:
        extension: str.
        path: str | Path | None.
        symbol: str.
        timeframe: str.

    Returns:
        Data.
    """
    logger.debug("Implemented load saved data.")
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


def data_df(payload: dict[str, Any]) -> pd.DataFrame:
    """Description.
        Convert a data tool payload into a pandas DataFrame. Use this tool when a structured data tool response should be inspected or passed into dataframe-based utilities.

    Args:
        payload: dict[str, Any].

    Returns:
        pd.DataFrame.
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


__all__ = [
    "Data",
    "data_df",
]
