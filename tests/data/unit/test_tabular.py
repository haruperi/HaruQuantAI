"""Unit tests for private tabular processing functions."""

from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
import pytest
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.records import OHLCVRecord
from app.services.data.processing.tabular import (
    align_dataframe_datetime,
    bars_to_records,
    compare_dataframes,
    compare_ohlc,
    compare_ohlcv,
    serialize_dataframe_records,
)


def test_align_dataframe_datetime_success() -> None:
    """Test successful datetime alignment to aware UTC."""
    timestamps = [
        datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        datetime(2026, 7, 1, 12, 1, tzinfo=UTC),
    ]
    df = pd.DataFrame({"open": [1.0, 2.0]}, index=timestamps)
    aligned = align_dataframe_datetime(df)
    assert isinstance(aligned.index, pd.DatetimeIndex)
    assert aligned.index[0] == timestamps[0]
    assert aligned.index.tz == UTC


def test_align_dataframe_datetime_naive() -> None:
    """Reject a naive datetime index instead of guessing a timezone."""
    timestamps = [
        datetime(2026, 7, 1, 12, 0),  # noqa: DTZ001
        datetime(2026, 7, 1, 12, 1),  # noqa: DTZ001
    ]
    df = pd.DataFrame({"open": [1.0, 2.0]}, index=timestamps)
    with pytest.raises(DataError) as captured:
        align_dataframe_datetime(df)
    assert captured.value.code == "VALIDATION_FAILED"


def test_serialize_dataframe_rejects_unsafe_values() -> None:
    """Reject naive timestamps, non-finite numerics, and arbitrary objects."""
    naive = pd.DataFrame(
        {"value": [1]},
        index=[datetime(2026, 7, 1, 12, 0)],  # noqa: DTZ001
    )
    with pytest.raises(DataError):
        serialize_dataframe_records(naive)

    timestamp = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    non_finite = pd.DataFrame({"value": [float("nan")]}, index=[timestamp])
    with pytest.raises(DataError):
        serialize_dataframe_records(non_finite)

    arbitrary = pd.DataFrame({"value": [object()]}, index=[timestamp])
    with pytest.raises(DataError):
        serialize_dataframe_records(arbitrary)


def test_align_dataframe_datetime_missing_column() -> None:
    """Test validation failure when a specific column is missing."""
    df = pd.DataFrame({"open": [1.0, 2.0]})
    with pytest.raises(DataError) as exc_info:
        align_dataframe_datetime(df, datetime_col="missing_col")
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_bars_to_records() -> None:
    """Test converting OHLCVRecords to records dicts."""
    records = [
        OHLCVRecord(
            timestamp=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
            source="test",
            source_symbol="BTC/USD",
            source_revision="v1",
            available_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
            open=Decimal("100.0"),
            high=Decimal("105.0"),
            low=Decimal("95.0"),
            close=Decimal("102.0"),
            volume=Decimal("10.0"),
            price_unit="USD",
            volume_unit="Units",
        )
    ]
    dicts = bars_to_records(records)
    assert len(dicts) == 1
    assert dicts[0]["open"] == "100.0"


def test_serialize_dataframe_records() -> None:
    """Test serialization of DataFrame rows to JSON-safe records."""
    timestamps = [datetime(2026, 7, 1, 12, 0, tzinfo=UTC)]
    df = pd.DataFrame({"open": [Decimal("100.0")], "val": [123]}, index=timestamps)
    dicts = serialize_dataframe_records(df)
    assert len(dicts) == 1
    assert dicts[0]["open"] == "100.0"
    assert dicts[0]["val"] == 123
    assert "timestamp" in dicts[0]


def test_compare_dataframes_match() -> None:
    """Test comparison of matching dataframes."""
    idx = [
        datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        datetime(2026, 7, 1, 12, 1, tzinfo=UTC),
    ]
    df1 = pd.DataFrame({"open": [1.0, 2.0]}, index=idx)
    df2 = df1.copy()
    assert compare_dataframes(df1, df2) is True


def test_compare_dataframes_mismatch() -> None:
    """Test failure when dataframes do not match."""
    idx = [
        datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        datetime(2026, 7, 1, 12, 1, tzinfo=UTC),
    ]
    df1 = pd.DataFrame({"open": [1.0, 2.0]}, index=idx)
    df2 = pd.DataFrame({"open": [1.0, 3.0]}, index=idx)
    with pytest.raises(DataError) as exc_info:
        compare_dataframes(df1, df2)
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_compare_dataframes_shapes_mismatch() -> None:
    """Test failure when shapes mismatch."""
    idx1 = [datetime(2026, 7, 1, 12, 0, tzinfo=UTC)]
    idx2 = [
        datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        datetime(2026, 7, 1, 12, 1, tzinfo=UTC),
    ]
    df1 = pd.DataFrame({"open": [1.0]}, index=idx1)
    df2 = pd.DataFrame({"open": [1.0, 2.0]}, index=idx2)
    with pytest.raises(DataError) as exc_info:
        compare_dataframes(df1, df2)
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_compare_dataframes_columns_mismatch() -> None:
    """Test failure when columns mismatch."""
    idx = [datetime(2026, 7, 1, 12, 0, tzinfo=UTC)]
    df1 = pd.DataFrame({"open": [1.0]}, index=idx)
    df2 = pd.DataFrame({"close": [1.0]}, index=idx)
    with pytest.raises(DataError) as exc_info:
        compare_dataframes(df1, df2)
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_compare_ohlc_success() -> None:
    """Test successful comparison of OHLC columns."""
    df1 = pd.DataFrame(
        {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [10.0]},
        index=[datetime(2026, 7, 1, 12, 0, tzinfo=UTC)],
    )
    df2 = df1.copy()
    assert compare_ohlc(df1, df2) is True


def test_compare_ohlc_missing_col() -> None:
    """Test failure when an OHLC column is missing."""
    df1 = pd.DataFrame(
        {"open": [1.0], "high": [2.0], "low": [0.5]},
        index=[datetime(2026, 7, 1, 12, 0, tzinfo=UTC)],
    )
    df2 = df1.copy()
    with pytest.raises(DataError) as exc_info:
        compare_ohlc(df1, df2)
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_compare_ohlcv_success() -> None:
    """Test successful comparison of OHLCV columns."""
    df1 = pd.DataFrame(
        {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [10.0]},
        index=[datetime(2026, 7, 1, 12, 0, tzinfo=UTC)],
    )
    df2 = df1.copy()
    assert compare_ohlcv(df1, df2) is True


def test_compare_ohlcv_missing_col() -> None:
    """Test failure when an OHLCV column is missing."""
    df1 = pd.DataFrame(
        {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5]},
        index=[datetime(2026, 7, 1, 12, 0, tzinfo=UTC)],
    )
    df2 = df1.copy()
    with pytest.raises(DataError) as exc_info:
        compare_ohlcv(df1, df2)
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_compare_dataframes_limit_exceeded() -> None:
    """Test comparison raises LIMIT_EXCEEDED when dataframe exceeds row limit."""
    df1 = pd.DataFrame({"open": [1.0] * 100005})
    df2 = pd.DataFrame({"open": [1.0] * 100005})
    with pytest.raises(DataError) as exc_info:
        compare_dataframes(df1, df2)
    assert exc_info.value.args[0] == "LIMIT_EXCEEDED"


def test_align_dataframe_datetime_failure() -> None:
    """Test alignment failure raising DataError."""
    # Let's pass a dataframe with strings that cannot be parsed as datetimes
    df = pd.DataFrame({"open": [1.0]}, index=["not-a-datetime"])
    with pytest.raises(DataError) as exc_info:
        align_dataframe_datetime(df)
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_align_dataframe_datetime_nat() -> None:
    """Test alignment raises DataError on NaT in datetime field."""
    idx = [datetime(2026, 7, 1, 12, 0, tzinfo=UTC), pd.NaT]
    df = pd.DataFrame({"open": [1.0, 2.0]}, index=idx)
    with pytest.raises(DataError) as exc_info:
        align_dataframe_datetime(df)
    assert exc_info.value.args[0] == "VALIDATION_FAILED"
