"""Private tabular and OHLC implementation for Data domain processing."""

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import numpy as np
import pandas as pd

from app.services.data.contracts import MarketDataset
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.records import OHLCVRecord, TickRecord
from app.utils import logger

_MAX_MISMATCH_SAMPLES = 10
_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume", "spread")
_TICK_COLUMNS = ("bid", "ask", "last", "volume")


def _raise_naive_datetime(field: str) -> None:
    """Reject ambiguous timestamps instead of guessing UTC.

    Raises:
        DataError: Always, because the supplied timestamp evidence is ambiguous.
    """
    logger.error("Rejecting ambiguous DATA timestamp evidence")
    raise DataError(
        "VALIDATION_FAILED",
        safe_details={"field": field},
    )


def align_dataframe_datetime(
    df: pd.DataFrame, datetime_col: str | None = None
) -> pd.DataFrame:
    """Align a private tabular market-data copy to an aware UTC datetime index.

    This function does not mutate the caller input.

    Args:
        df: The pandas DataFrame to align.
        datetime_col: The column containing datetime values. If None, the
          index is used.

    Returns:
        A new DataFrame with sorted DatetimeIndex localized to UTC.

    Raises:
        DataError: If the index/column cannot be aligned or contains NaT.
    """
    logger.info("Aligning dataframe datetime column or index to UTC")
    df = df.copy()

    if datetime_col is not None and datetime_col not in df.columns:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": f"Datetime column '{datetime_col}' not found."},
        )

    try:
        series = df[datetime_col] if datetime_col is not None else df.index.to_series()

        dt_series = pd.to_datetime(series, errors="raise")
    except Exception as error:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"operation": "datetime_conversion"},
        ) from error

    if dt_series.isna().any():
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "Datetime series contains null or NaT values."},
        )

    try:
        if dt_series.dt.tz is None:
            _raise_naive_datetime(datetime_col or "index")
        dt_series = dt_series.dt.tz_convert("UTC")

        if datetime_col is not None:
            df[datetime_col] = dt_series

        df.index = pd.DatetimeIndex(dt_series)
        df = df.sort_index()
        return df
    except Exception as error:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"operation": "datetime_alignment"},
        ) from error


def bars_to_records(records: Sequence[OHLCVRecord]) -> list[dict[str, Any]]:
    """Convert bar rows to deterministic JSON-safe records.

    Args:
        records: A sequence of OHLCVRecord objects.

    Returns:
        A list of JSON-safe dicts.

    Raises:
        DataError: If conversion fails.
    """
    logger.info("Converting %d bar records to serializable dicts", len(records))
    try:
        return [r.model_dump(mode="json") for r in records]
    except Exception as error:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"operation": "bar_serialization"},
        ) from error


def to_ohlcv_dataframe(dataset: MarketDataset) -> pd.DataFrame:
    """Project one canonical bar dataset to an analytical OHLCV/spread DataFrame.

    The returned frame is a new mutable analytical copy. The source
    ``MarketDataset`` remains the authoritative precision, quality, provenance,
    and availability evidence.

    Args:
        dataset: Canonical Data-owned market dataset containing OHLCV bars.

    Returns:
        A DataFrame with a UTC ``timestamp`` index and float64 ``open``,
        ``high``, ``low``, ``close``, ``volume``, and ``spread`` columns. The
        provider-reported spread unit is stored in ``frame.attrs["spread_unit"]``.

    Raises:
        DataError: If the dataset is not bars, contains a non-OHLCV record, or
            cannot be represented as finite float64 analytical values.
    """
    logger.info("Projecting canonical OHLCV dataset to analytical dataframe")
    if dataset.data_kind != "bars":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "data_kind"},
            request_id=dataset.request_id,
        )
    if any(not isinstance(record, OHLCVRecord) for record in dataset.records):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "records"},
            request_id=dataset.request_id,
        )

    records = tuple(
        record for record in dataset.records if isinstance(record, OHLCVRecord)
    )
    if any(record.spread is None or record.spread_unit is None for record in records):
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": "spread"},
            request_id=dataset.request_id,
        )
    spread_units = {record.spread_unit for record in records}
    if len(spread_units) > 1:
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": "spread_unit"},
            request_id=dataset.request_id,
        )
    try:
        values = {
            column: np.asarray(
                [float(getattr(record, column)) for record in records],
                dtype="float64",
            )
            for column in _OHLCV_COLUMNS
        }
    except (OverflowError, TypeError, ValueError) as error:
        raise DataError(
            "PRECISION_MISMATCH",
            safe_details={"operation": "ohlcv_dataframe_projection"},
            request_id=dataset.request_id,
        ) from error
    if any(not np.isfinite(column_values).all() for column_values in values.values()):
        raise DataError(
            "PRECISION_MISMATCH",
            safe_details={"operation": "ohlcv_dataframe_projection"},
            request_id=dataset.request_id,
        )

    index = pd.DatetimeIndex(
        [record.timestamp for record in records],
        tz=UTC,
        name="timestamp",
    )
    frame = pd.DataFrame(values, index=index, columns=_OHLCV_COLUMNS)
    frame.attrs["spread_unit"] = next(iter(spread_units), None)
    return frame


def to_tick_dataframe(dataset: MarketDataset) -> pd.DataFrame:
    """Project one canonical tick dataset to an analytical DataFrame.

    Genuine missing optional tick values become ``NaN``. The returned frame is a
    new mutable analytical copy; the canonical ``MarketDataset`` remains the
    authoritative precision, quality, provenance, and availability evidence.

    Args:
        dataset: Canonical Data-owned market dataset containing ticks.

    Returns:
        A DataFrame with a UTC ``timestamp`` index and float64 ``bid``, ``ask``,
        ``last``, and ``volume`` columns. Common units are stored in
        ``frame.attrs["price_unit"]`` and ``frame.attrs["volume_unit"]``.

    Raises:
        DataError: If the dataset is not ticks, contains a non-tick record, has
            inconsistent units, or cannot be represented safely as float64.
    """
    logger.info("Projecting canonical tick dataset to analytical dataframe")
    if dataset.data_kind != "ticks":
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "data_kind"},
            request_id=dataset.request_id,
        )
    if any(not isinstance(record, TickRecord) for record in dataset.records):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "records"},
            request_id=dataset.request_id,
        )

    records = tuple(
        record for record in dataset.records if isinstance(record, TickRecord)
    )
    price_units = {record.price_unit for record in records}
    volume_units = {
        record.volume_unit for record in records if record.volume_unit is not None
    }
    if len(price_units) > 1:
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": "price_unit"},
            request_id=dataset.request_id,
        )
    if len(volume_units) > 1:
        raise DataError(
            "DATA_QUALITY_FAILED",
            safe_details={"field": "volume_unit"},
            request_id=dataset.request_id,
        )

    try:
        values = {
            column: np.asarray(
                [
                    (
                        np.nan
                        if getattr(record, column) is None
                        else float(getattr(record, column))
                    )
                    for record in records
                ],
                dtype="float64",
            )
            for column in _TICK_COLUMNS
        }
    except (OverflowError, TypeError, ValueError) as error:
        raise DataError(
            "PRECISION_MISMATCH",
            safe_details={"operation": "tick_dataframe_projection"},
            request_id=dataset.request_id,
        ) from error
    if any(np.isinf(column_values).any() for column_values in values.values()):
        raise DataError(
            "PRECISION_MISMATCH",
            safe_details={"operation": "tick_dataframe_projection"},
            request_id=dataset.request_id,
        )

    index = pd.DatetimeIndex(
        [record.timestamp for record in records],
        tz=UTC,
        name="timestamp",
    )
    frame = pd.DataFrame(values, index=index, columns=_TICK_COLUMNS)
    frame.attrs["price_unit"] = next(iter(price_units), None)
    frame.attrs["volume_unit"] = next(iter(volume_units), None)
    return frame


def _serialize_value(val: object) -> object:
    """Serialize one private tabular cell safely for JSON.

    Returns:
        JSON-safe scalar value.

    Raises:
        DataError: If the value is non-finite, ambiguous, or unsupported.
    """
    logger.debug("Running DATA function: _serialize_value")
    res: object
    if isinstance(val, datetime):
        if val.tzinfo is None:
            _raise_naive_datetime("datetime")
        res = val.astimezone(UTC).isoformat().replace("+00:00", "Z")
    elif isinstance(val, Decimal):
        if not val.is_finite():
            raise DataError("PRECISION_MISMATCH")
        res = str(val)
    elif isinstance(val, (int, float, str, bool, np.integer, np.floating)):
        if isinstance(val, (float, np.floating)) and not np.isfinite(val):
            raise DataError("PRECISION_MISMATCH")
        res = val.item() if isinstance(val, (np.integer, np.floating)) else val
    elif pd.isna(val):
        res = None
    else:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "tabular_value"},
        )
    return res


def _raise_naive_index() -> None:
    """Reject an ambiguous private tabular timestamp index."""
    logger.error("Rejecting a naive DATA tabular index")
    _raise_naive_datetime("index")


def serialize_dataframe_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a private DataFrame to deterministic JSON-safe records.

    Args:
        df: The pandas DataFrame to serialize.

    Returns:
        A list of JSON-safe dicts with UTC ISO 8601 timestamps.

    Raises:
        DataError: If serialization fails.
    """
    logger.info("Serializing private dataframe to JSON-safe records")
    try:
        records = []
        for idx, row in df.iterrows():
            record: dict[str, Any] = {}
            if isinstance(idx, datetime):
                # Format to ISO 8601 UTC string
                if idx.tzinfo is None:
                    _raise_naive_index()
                record["timestamp"] = (
                    idx.astimezone(UTC).isoformat().replace("+00:00", "Z")
                )
            else:
                record["index"] = idx

            for col, val in row.items():
                record[str(col)] = _serialize_value(val)
            records.append(record)
        return records
    except Exception as error:
        if isinstance(error, DataError):
            raise
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"operation": "dataframe_serialization"},
        ) from error


def compare_dataframes(  # noqa: C901, PLR0912 - explicit bounded type dispatch.
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    tolerance: Decimal | float | None = None,
) -> bool:
    """Compare aligned private DataFrames using explicit finite tolerance.

    Args:
        df1: First DataFrame to compare.
        df2: Second DataFrame to compare.
        tolerance: Numeric difference tolerance limit.

    Returns:
        True if the dataframes match.

    Raises:
        DataError: If shapes/columns mismatch, count exceeds limit, or values
          differ.
    """
    logger.info("Comparing two aligned dataframes")
    max_limit = 100000
    if len(df1) > max_limit or len(df2) > max_limit:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={
                "message": (
                    f"DataFrame exceeds row limit of {max_limit} for comparison."
                )
            },
        )

    if df1.shape != df2.shape:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (f"DataFrame shapes mismatch: {df1.shape} vs {df2.shape}.")
            },
        )

    if not df1.columns.equals(df2.columns):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={
                "message": (
                    f"DataFrame columns mismatch: {df1.columns} vs {df2.columns}."
                )
            },
        )

    if not df1.index.equals(df2.index):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"message": "DataFrame indices mismatch."},
        )

    tol = Decimal(str(tolerance)) if tolerance is not None else Decimal("1e-9")
    if not tol.is_finite() or tol < 0:
        raise DataError("PRECISION_MISMATCH")

    mismatches = []
    for col in df1.columns:
        s1 = df1[col]
        s2 = df2[col]

        if pd.api.types.is_numeric_dtype(s1) and pd.api.types.is_numeric_dtype(s2):
            for idx in s1.index:
                left = Decimal(str(s1.loc[idx]))
                right = Decimal(str(s2.loc[idx]))
                if not left.is_finite() or not right.is_finite():
                    raise DataError("PRECISION_MISMATCH")
                if abs(left - right) > tol:
                    mismatches.append(str(idx))
                    if len(mismatches) >= _MAX_MISMATCH_SAMPLES:
                        break
        else:
            bad_indices = s1[s1 != s2].index
            for idx in bad_indices[:10]:
                mismatches.append(str(idx))

    if mismatches:
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"mismatch_count": len(mismatches)},
        )

    return True


def compare_ohlc(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    tolerance: Decimal | float | None = None,
) -> bool:
    """Compare OHLC columns after schema and alignment validation.

    Args:
        df1: First DataFrame.
        df2: Second DataFrame.
        tolerance: Numeric difference tolerance limit.

    Returns:
        True if the OHLC columns match.

    Raises:
        DataError: If columns are missing or values mismatch.
    """
    logger.info("Executing compare_ohlc validation")
    required = ["open", "high", "low", "close"]
    for col in required:
        if col not in df1.columns or col not in df2.columns:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"message": f"Missing required OHLC column: '{col}'."},
            )

    aligned1 = align_dataframe_datetime(df1)
    aligned2 = align_dataframe_datetime(df2)

    return compare_dataframes(aligned1[required], aligned2[required], tolerance)


def compare_ohlcv(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    tolerance: Decimal | float | None = None,
) -> bool:
    """Compare OHLCV columns after schema and alignment validation.

    Args:
        df1: First DataFrame.
        df2: Second DataFrame.
        tolerance: Numeric difference tolerance limit.

    Returns:
        True if the OHLCV columns match.

    Raises:
        DataError: If columns are missing or values mismatch.
    """
    logger.info("Executing compare_ohlcv validation")
    required = ["open", "high", "low", "close", "volume"]
    for col in required:
        if col not in df1.columns or col not in df2.columns:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"message": f"Missing required OHLCV column: '{col}'."},
            )

    aligned1 = align_dataframe_datetime(df1)
    aligned2 = align_dataframe_datetime(df2)

    return compare_dataframes(aligned1[required], aligned2[required], tolerance)
