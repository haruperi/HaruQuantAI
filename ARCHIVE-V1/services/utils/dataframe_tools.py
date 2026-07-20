"""Lazy-pandas dataframe helpers for utility workflows.

This module provides support helpers, not official AI tools. Pandas is imported
only inside functions that need it. Helpers return native Python objects where
practical and never mutate caller-owned dataframes; returned dataframes are
copies or transformed copies as documented by each function.
"""
# ruff: noqa: ANN401

from __future__ import annotations

import importlib
import math
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from itertools import product
from typing import Any, Final, TypeVar, cast

from app.services.utils.errors import ConfigurationError, ValidationError
from app.services.utils.logger import logger
from app.services.utils.normalization import format_utc_timestamp

T = TypeVar("T")
OHLC_COLUMNS: Final[tuple[str, ...]] = ("open", "high", "low", "close")
OHLCV_COLUMNS: Final[tuple[str, ...]] = (*OHLC_COLUMNS, "volume")


def _pandas() -> Any:
    """Return pandas lazily or raise a clear configuration error."""
    try:
        res = importlib.import_module("pandas")
        logger.debug("Implemented lazy pandas import")
        return res
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatch
        message = "pandas is required for dataframe helpers."
        raise ConfigurationError(message, code="CONFIGURATION_ERROR") from exc


def _is_dataframe(value: object) -> bool:
    """Return whether a value is a pandas DataFrame."""
    pd = _pandas()
    res = isinstance(value, pd.DataFrame)
    logger.debug("Implemented dataframe type check")
    return res


def _require_dataframe(value: object, field_name: str = "dataframe") -> Any:
    """Validate and return a pandas DataFrame."""
    if not _is_dataframe(value):
        message = f"{field_name} must be a pandas DataFrame."
        raise ValidationError(message, code="INVALID_INPUT")
    logger.debug("Implemented requiring dataframe validation")
    return value


def _validate_columns(dataframe: Any, columns: Sequence[str]) -> None:
    """Raise when required dataframe columns are missing."""
    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        message = f"dataframe is missing required columns: {missing}"
        raise ValidationError(message, code="INVALID_INPUT")
    logger.debug("Implemented validating dataframe columns presence")


def align_dataframe_datetime(
    dataframe: object,
    *,
    timestamp_column: str | None = None,
) -> Any:
    """Return a dataframe copy with UTC-normalized datetime alignment.

    Args:
        dataframe: Pandas DataFrame to transform.
        timestamp_column: Optional timestamp column to normalize. If omitted,
            the index must be datetime-compatible.

    Returns:
        A copied dataframe with either the timestamp column or index converted
        to UTC-aware pandas timestamps.
    """
    pd = _pandas()
    frame = _require_dataframe(dataframe).copy(deep=True)
    if frame.empty:
        logger.info("Implemented aligning dataframe datetime index/column")
        return frame
    try:
        if timestamp_column is None:
            frame.index = pd.to_datetime(frame.index, utc=True, errors="raise")
        else:
            _validate_columns(frame, [timestamp_column])
            frame[timestamp_column] = pd.to_datetime(
                frame[timestamp_column],
                utc=True,
                errors="raise",
            )
    except (TypeError, ValueError) as exc:
        message = "datetime alignment failed for dataframe."
        raise ValidationError(message, code="INVALID_INPUT") from exc
    logger.info("Implemented aligning dataframe datetime index/column")
    return frame


def _json_safe(value: object) -> object:
    """Return a JSON-safe scalar value where practical."""
    pd = _pandas()
    res: object
    if value is None:
        res = None
    elif isinstance(value, pd.Timestamp):
        res = format_utc_timestamp(value.to_pydatetime())
    elif isinstance(value, datetime | date):
        res = format_utc_timestamp(value)
    elif isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        res = None
    elif hasattr(pd, "isna") and not isinstance(value, list | dict | tuple | set):
        try:
            if bool(pd.isna(value)):
                res = None
            else:
                res = value
        except (TypeError, ValueError):
            res = value
    elif isinstance(value, Mapping):
        res = {str(key): _json_safe(item) for key, item in value.items()}
    elif isinstance(value, list | tuple):
        res = [_json_safe(item) for item in value]
    else:
        res = value
    logger.info("Implemented json safe serialization")
    return res


def serialize_dataframe_records(
    dataframe: object,
    *,
    timestamp_columns: Sequence[str] = (),
    include_index: bool = False,
    index_name: str = "index",
) -> list[dict[str, object]]:
    """Serialize a dataframe into JSON-safe row records.

    Args:
        dataframe: Pandas DataFrame to serialize.
        timestamp_columns: Columns that must be emitted as UTC ``Z`` strings.
        include_index: Whether to include the dataframe index in each record.
        index_name: Field name used when including the index.

    Returns:
        List of JSON-safe row dictionaries.
    """
    frame = _require_dataframe(dataframe)
    _validate_columns(frame, timestamp_columns)
    if frame.empty:
        logger.info("Implemented serializing dataframe to records")
        return []
    records: list[dict[str, object]] = []
    for index, row in frame.iterrows():
        record = {str(key): _json_safe(value) for key, value in row.to_dict().items()}
        for column in timestamp_columns:
            record[column] = format_utc_timestamp(row[column])
        if include_index:
            record[index_name] = _json_safe(index)
        records.append(record)
    logger.info("Implemented serializing dataframe to records")
    return records


def bar_to_record(
    bar: Mapping[str, object],
    *,
    timestamp_field: str = "timestamp",
) -> dict[str, object]:
    """Convert a bar-like mapping into a JSON-safe record.

    Args:
        bar: Bar-like mapping with OHLCV and optional timestamp fields.
        timestamp_field: Name of the timestamp field to normalize as a
            UTC ``Z`` ISO string. Defaults to ``"timestamp"``.

    Returns:
        JSON-safe record dict with the timestamp field normalized.

    Raises:
        ValidationError: If ``bar`` is not a mapping or if the timestamp
            field value is not datetime-like.

    Side effects:
        None. The input mapping is not mutated.
    """
    if not isinstance(bar, Mapping):
        raise ValidationError("bar must be a mapping.", code="INVALID_INPUT")
    record = {str(key): _json_safe(value) for key, value in bar.items()}
    if timestamp_field in record and record[timestamp_field] is not None:
        timestamp_value = record[timestamp_field]
        if not isinstance(timestamp_value, datetime | date | str | int | float):
            raise ValidationError("timestamp field must be datetime-like.")
        record[timestamp_field] = format_utc_timestamp(
            cast("datetime | date | str | float", timestamp_value),
        )
    logger.info("Implemented bar to record conversion")
    return record


def bars_to_records(
    bars: Iterable[Mapping[str, object]],
    *,
    timestamp_field: str = "timestamp",
) -> list[dict[str, object]]:
    """Convert an iterable of bar-like mappings to JSON-safe records.

    Args:
        bars: Iterable of bar-like mappings.
        timestamp_field: Timestamp field name to normalize in each bar.

    Returns:
        List of JSON-safe record dicts.

    Side effects:
        None.
    """
    res = [bar_to_record(bar, timestamp_field=timestamp_field) for bar in bars]
    logger.info("Implemented batch bars to records conversion")
    return res


def chunked(values: Sequence[T], *, size: int) -> list[list[T]]:
    """Return deterministic chunks from a sequence.

    Args:
        values: Sequence to split into chunks.
        size: Maximum number of elements per chunk. Must be positive.

    Returns:
        List of sub-lists, each containing at most ``size`` elements.

    Raises:
        ValidationError: If ``size`` is not positive.

    Side effects:
        None.
    """
    if size <= 0:
        raise ValidationError("size must be greater than zero.", code="INVALID_INPUT")
    res = [list(values[index : index + size]) for index in range(0, len(values), size)]
    logger.info("Implemented splitting sequence to chunks")
    return res


def parameter_combinations(
    grid: Mapping[str, Sequence[object]],
) -> list[dict[str, object]]:
    """Return deterministic parameter combinations from a parameter grid.

    Args:
        grid: Mapping of parameter names to their candidate value sequences.
            Each sequence must be non-empty.

    Returns:
        List of dicts, each representing one parameter combination. Returns
        ``[{}]`` when the grid is empty.

    Raises:
        ValidationError: If any parameter sequence is empty or not a sequence.

    Side effects:
        None.
    """
    if not grid:
        logger.info("Implemented parameter combinations generation")
        return [{}]
    keys = list(grid)
    values: list[Sequence[object]] = []
    for key in keys:
        options = grid[key]
        if not isinstance(options, Sequence) or isinstance(options, str) or not options:
            message = f"parameter options for {key} must be a non-empty sequence."
            raise ValidationError(message, code="INVALID_INPUT")
        values.append(options)
    res = [dict(zip(keys, combo, strict=True)) for combo in product(*values)]
    logger.info("Implemented parameter combinations generation")
    return res


def compare_dataframes(
    left: object,
    right: object,
    *,
    columns: Sequence[str] | None = None,
    tolerance: float = 0.0,
) -> dict[str, object]:
    """Compare two dataframes with deterministic index alignment.

    Args:
        left: Left pandas DataFrame.
        right: Right pandas DataFrame.
        columns: Optional subset of columns to compare. Defaults to all.
        tolerance: Absolute numeric tolerance for float comparisons.
            Defaults to 0.0 (exact equality).

    Returns:
        Mapping with ``equal`` flag, ``row_count``, ``column_count``, and
        a bounded ``differences`` list of ``{index, column, left, right}``
        records.

    Raises:
        ValidationError: If inputs are not DataFrames, indexes don't align,
            columns are missing, or ``tolerance`` is negative.

    Side effects:
        None.
    """
    if tolerance < 0:
        raise ValidationError("tolerance must be non-negative.", code="INVALID_INPUT")
    left_frame = _require_dataframe(left, "left")
    right_frame = _require_dataframe(right, "right")
    if not left_frame.index.equals(right_frame.index):
        raise ValidationError("dataframe indexes do not align.", code="INVALID_INPUT")
    selected = list(columns) if columns is not None else list(left_frame.columns)
    _validate_columns(left_frame, selected)
    _validate_columns(right_frame, selected)
    differences: list[dict[str, object]] = []
    for row_index in left_frame.index:
        for column in selected:
            left_value = left_frame.at[row_index, column]
            right_value = right_frame.at[row_index, column]
            if _values_differ(left_value, right_value, tolerance=tolerance):
                differences.append(
                    {
                        "index": _json_safe(row_index),
                        "column": column,
                        "left": _json_safe(left_value),
                        "right": _json_safe(right_value),
                    },
                )
    logger.info("Implemented dataframes comparison")
    return {
        "equal": not differences,
        "row_count": len(left_frame),
        "column_count": len(selected),
        "differences": differences,
    }


def _values_differ(left: object, right: object, *, tolerance: float) -> bool:
    """Return whether scalar values differ beyond tolerance."""
    if isinstance(left, int | float) and isinstance(right, int | float):
        if any(math.isnan(float(value)) for value in (left, right)):
            res = not (math.isnan(float(left)) and math.isnan(float(right)))
        else:
            res = abs(float(left) - float(right)) > tolerance
    else:
        res = left != right
    logger.debug("Implemented values difference check")
    return res


def compare_ohlc(
    left: object,
    right: object,
    *,
    tolerance: float = 0.0,
) -> dict[str, object]:
    """Compare OHLC columns between two aligned dataframes."""
    res = compare_dataframes(left, right, columns=OHLC_COLUMNS, tolerance=tolerance)
    logger.info("Implemented OHLC comparison")
    return res


def compare_ohlcv(
    left: object,
    right: object,
    *,
    tolerance: float = 0.0,
) -> dict[str, object]:
    """Compare OHLCV columns between two aligned dataframes."""
    res = compare_dataframes(left, right, columns=OHLCV_COLUMNS, tolerance=tolerance)
    logger.info("Implemented OHLCV comparison")
    return res


def dataframe_columns(dataframe: object) -> list[str]:
    """Return dataframe columns as native strings."""
    frame = _require_dataframe(dataframe)
    res = [str(column) for column in frame.columns]
    logger.info("Implemented retrieving dataframe columns")
    return res


def iter_dataframe_records(dataframe: object) -> Iterable[dict[str, object]]:
    """Yield JSON-safe dataframe records without mutating the input."""
    logger.info("Implemented iterating dataframe records")
    yield from serialize_dataframe_records(dataframe)


# ── Contract aliases (required public names) ──────────────────────────────────
align_dataframe_time_index = align_dataframe_datetime
chunk_sequence = chunked
generate_parameter_combinations = parameter_combinations
