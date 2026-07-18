"""Unit tests for private tabular processing functions."""

from datetime import UTC, datetime
from decimal import Decimal

import pandas as pd
import pytest
from app.services.data import to_ohlcv_dataframe, to_tick_dataframe
from app.services.data.contracts import DataQualityReport, MarketDataset
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.records import OHLCVRecord, TickRecord
from app.services.data.processing.tabular import (
    align_dataframe_datetime,
    bars_to_records,
    compare_dataframes,
    compare_ohlc,
    compare_ohlcv,
    serialize_dataframe_records,
)
from app.utils import generate_id


def _bar_dataset(
    *,
    price: Decimal = Decimal(100),
    include_spread: bool = True,
) -> MarketDataset:
    """Return a valid two-row canonical bar dataset."""
    first = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    records = tuple(
        OHLCVRecord(
            timestamp=first.replace(minute=index),
            source="test",
            source_symbol="EURUSD",
            source_revision="v1",
            available_at=first.replace(minute=index + 1),
            open=price + index,
            high=price + index + Decimal(1),
            low=price + index - Decimal(1),
            close=price + index + Decimal("0.5"),
            volume=Decimal(10 + index),
            price_unit="quote_currency",
            volume_unit="lots",
            spread=Decimal(2 + index) if include_spread else None,
            spread_unit="points" if include_spread else None,
        )
        for index in range(2)
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=DataQualityReport(
            quality_status="passed",
            quality_score=Decimal(1),
            record_count=len(records),
            checked_count=len(records),
            truncated=False,
            sample_limit=len(records),
            schema_version="v1",
            generated_at=records[-1].available_at,
        ),
        source_metadata={"source_id": "test"},
        license_metadata={"status": "internal"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def _tick_dataset(
    *,
    price: Decimal = Decimal("1.1"),
    second_price_unit: str = "quote_currency",
    first_volume_unit: str | None = None,
) -> MarketDataset:
    """Return a valid two-row canonical tick dataset."""
    first = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    records = (
        TickRecord(
            timestamp=first,
            source="test",
            source_symbol="EURUSD",
            source_revision="v1",
            available_at=first,
            bid=price,
            ask=price + Decimal("0.0002"),
            volume=Decimal(2) if first_volume_unit is not None else None,
            price_unit="quote_currency",
            volume_unit=first_volume_unit,
        ),
        TickRecord(
            timestamp=first.replace(second=1),
            source="test",
            source_symbol="EURUSD",
            source_revision="v1",
            available_at=first.replace(second=1),
            last=price + Decimal("0.0001"),
            volume=Decimal(3),
            price_unit=second_price_unit,
            volume_unit="lots",
        ),
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=DataQualityReport(
            quality_status="passed",
            quality_score=Decimal(1),
            record_count=len(records),
            checked_count=len(records),
            truncated=False,
            sample_limit=len(records),
            schema_version="v1",
            generated_at=records[-1].available_at,
        ),
        source_metadata={"source_id": "test"},
        license_metadata={"status": "internal"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
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


def test_to_ohlcv_dataframe_returns_float64_analytical_copy() -> None:
    """Project canonical bars to the exact public analytical frame shape."""
    dataset = _bar_dataset()

    frame = to_ohlcv_dataframe(dataset)

    assert list(frame.columns) == [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "spread",
    ]
    assert frame.index.name == "timestamp"
    assert frame.index.tz == UTC
    assert frame.attrs["spread_unit"] == "points"
    assert all(str(dtype) == "float64" for dtype in frame.dtypes)
    assert frame.iloc[0].to_dict() == {
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
        "volume": 10.0,
        "spread": 2.0,
    }

    frame.iloc[0, 0] = 999.0
    assert dataset.records[0].open == Decimal(100)


def test_to_ohlcv_dataframe_rejects_non_bar_dataset() -> None:
    """Reject a dataset whose declared kind is not OHLCV bars."""
    dataset = _bar_dataset().model_copy(
        update={"data_kind": "ticks", "timeframe": None},
    )

    with pytest.raises(DataError) as captured:
        to_ohlcv_dataframe(dataset)

    assert captured.value.code == "VALIDATION_FAILED"


def test_to_ohlcv_dataframe_rejects_float64_overflow() -> None:
    """Reject canonical Decimal values that overflow analytical float64."""
    dataset = _bar_dataset(price=Decimal("1e999"))

    with pytest.raises(DataError) as captured:
        to_ohlcv_dataframe(dataset)

    assert captured.value.code == "PRECISION_MISMATCH"


def test_to_ohlcv_dataframe_rejects_missing_spread_evidence() -> None:
    """Never invent a zero or current quote when historical spread is absent."""
    dataset = _bar_dataset(include_spread=False)

    with pytest.raises(DataError) as captured:
        to_ohlcv_dataframe(dataset)

    assert captured.value.code == "DATA_QUALITY_FAILED"


def test_ohlcv_record_requires_spread_unit_with_spread() -> None:
    """Canonical per-bar spread evidence always carries its native unit."""
    values = _bar_dataset().records[0].model_dump()
    values["spread_unit"] = None

    with pytest.raises(ValueError, match="provided together"):
        OHLCVRecord(**values)


def test_to_tick_dataframe_returns_float64_analytical_copy() -> None:
    """Project canonical ticks while preserving genuine missing values."""
    dataset = _tick_dataset()

    frame = to_tick_dataframe(dataset)

    assert list(frame.columns) == ["bid", "ask", "last", "volume"]
    assert frame.index.name == "timestamp"
    assert frame.index.tz == UTC
    assert frame.attrs == {
        "price_unit": "quote_currency",
        "volume_unit": "lots",
    }
    assert all(str(dtype) == "float64" for dtype in frame.dtypes)
    assert frame.iloc[0]["bid"] == 1.1
    assert frame.iloc[0]["ask"] == 1.1002
    assert pd.isna(frame.iloc[0]["last"])
    assert pd.isna(frame.iloc[0]["volume"])
    assert frame.iloc[1]["last"] == 1.1001
    assert frame.iloc[1]["volume"] == 3.0

    frame.iloc[0, 0] = 999.0
    assert dataset.records[0].bid == Decimal("1.1")


def test_to_tick_dataframe_rejects_non_tick_dataset() -> None:
    """Reject a dataset whose declared kind is not ticks."""
    dataset = _bar_dataset()

    with pytest.raises(DataError) as captured:
        to_tick_dataframe(dataset)

    assert captured.value.code == "VALIDATION_FAILED"


def test_to_tick_dataframe_rejects_inconsistent_price_units() -> None:
    """Reject a frame that would mix incomparable provider price units."""
    dataset = _tick_dataset(second_price_unit="USD")

    with pytest.raises(DataError) as captured:
        to_tick_dataframe(dataset)

    assert captured.value.code == "DATA_QUALITY_FAILED"


def test_to_tick_dataframe_rejects_inconsistent_volume_units() -> None:
    """Reject a frame that would mix incomparable provider volume units."""
    dataset = _tick_dataset(first_volume_unit="contracts")

    with pytest.raises(DataError) as captured:
        to_tick_dataframe(dataset)

    assert captured.value.code == "DATA_QUALITY_FAILED"


def test_to_tick_dataframe_rejects_float64_overflow() -> None:
    """Reject canonical Decimal tick values that overflow analytical float64."""
    dataset = _tick_dataset(price=Decimal("1e999"))

    with pytest.raises(DataError) as captured:
        to_tick_dataframe(dataset)

    assert captured.value.code == "PRECISION_MISMATCH"


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
