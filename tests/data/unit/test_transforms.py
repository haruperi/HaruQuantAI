"""Unit tests for public transforms processing functions."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.market import (
    DataQualityReport,
    MarketDataset,
)
from app.services.data.contracts.records import OHLCVRecord, SpreadRecord, TickRecord
from app.services.data.processing.transforms import (
    aggregate_ticks,
    align_datasets,
    resample_dataset,
)


def _create_mock_quality_report(count: int) -> DataQualityReport:
    return DataQualityReport(
        quality_status="passed",
        quality_score=Decimal("1.0"),
        issues=(),
        warnings=(),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=datetime.now(UTC),
    )


def test_resample_dataset_is_deterministic() -> None:
    """Test resampling from M1 to M5 is deterministic and correct."""
    start_time = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    records = []
    for i in range(10):
        records.append(
            OHLCVRecord(
                timestamp=start_time + timedelta(minutes=i),
                source="test",
                source_symbol="BTC/USD",
                source_revision="v1",
                available_at=start_time + timedelta(minutes=i),
                open=Decimal("100.0") + i,
                high=Decimal("105.0") + i,
                low=Decimal("95.0") + i,
                close=Decimal("101.0") + i,
                volume=Decimal("10.0"),
                price_unit="USD",
                volume_unit="Units",
                spread=Decimal(2 + i),
                spread_unit="points",
            )
        )

    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="BTC/USD",
        timeframe="M1",
        records=tuple(records),
        start=start_time,
        end=start_time + timedelta(minutes=9),
        available_at=start_time + timedelta(minutes=9),
        record_count=10,
        quality_report=_create_mock_quality_report(10),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )

    resampled = resample_dataset(dataset, "M5")
    assert resampled.timeframe == "M5"
    assert len(resampled.records) == 2
    # Verify first M5 bar: opens at 12:00, close at 12:04 close (101.0 + 4 = 105.0)
    assert resampled.records[0].timestamp == start_time
    assert resampled.records[0].open == Decimal("100.0")
    assert resampled.records[0].close == Decimal("105.0")
    assert resampled.records[0].volume == Decimal("50.0")
    assert resampled.records[0].spread == Decimal(6)
    assert resampled.records[0].spread_unit == "points"


def test_resample_dataset_empty() -> None:
    """Test resampling empty dataset."""
    start_time = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="BTC/USD",
        timeframe="M1",
        records=(),
        start=start_time,
        end=start_time,
        available_at=start_time,
        record_count=0,
        quality_report=_create_mock_quality_report(0),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )
    resampled = resample_dataset(dataset, "M5")
    assert resampled.record_count == 0
    assert len(resampled.records) == 0


def test_resample_dataset_invalid_kind() -> None:
    """Test resampling raises error if data_kind is not bars."""
    start_time = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="BTC/USD",
        timeframe=None,
        records=(),
        start=start_time,
        end=start_time,
        available_at=start_time,
        record_count=0,
        quality_report=_create_mock_quality_report(0),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )
    with pytest.raises(DataError) as exc_info:
        resample_dataset(dataset, "M5")
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_resample_dataset_invalid_direction() -> None:
    """Test resampling raises error if target timeframe is not higher rank."""
    start_time = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="BTC/USD",
        timeframe="M15",
        records=(),
        start=start_time,
        end=start_time,
        available_at=start_time,
        record_count=0,
        quality_report=_create_mock_quality_report(0),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )
    with pytest.raises(DataError) as exc_info:
        resample_dataset(dataset, "M5")
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_align_datasets_prevents_lookahead() -> None:
    """Test align_datasets alignment check and lookahead prevention."""
    t1 = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    t2 = datetime(2026, 7, 1, 12, 1, tzinfo=UTC)

    # Dataset A: record exists at 12:00, available at 12:00
    r_a = OHLCVRecord(
        timestamp=t1,
        source="test",
        source_symbol="A",
        source_revision="v1",
        available_at=t1,
        open=Decimal("1.0"),
        high=Decimal("1.1"),
        low=Decimal("0.9"),
        close=Decimal("1.0"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="Units",
    )
    ds_a = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="A",
        timeframe="M1",
        records=(r_a,),
        start=t1,
        end=t1,
        available_at=t1,
        record_count=1,
        quality_report=_create_mock_quality_report(1),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )

    # Dataset B: record at 12:00, but only available at 12:02.
    # Aligning at 12:01 would constitute a lookahead violation.
    r_b = OHLCVRecord(
        timestamp=t1,
        source="test",
        source_symbol="B",
        source_revision="v1",
        available_at=t1 + timedelta(minutes=2),
        open=Decimal("2.0"),
        high=Decimal("2.1"),
        low=Decimal("1.9"),
        close=Decimal("2.0"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="Units",
    )
    ds_b = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="B",
        timeframe="M1",
        records=(r_b,),
        start=t1,
        end=t1,
        available_at=t1 + timedelta(minutes=2),
        record_count=1,
        quality_report=_create_mock_quality_report(1),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )

    datasets = {"A": ds_a, "B": ds_b}
    target = [t1, t2]

    # Aligning at t2 (12:01) should raise since B's record is not available until 12:02
    with pytest.raises(DataError) as exc_info:
        align_datasets(datasets, target)
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_align_datasets_ticks_and_spreads() -> None:
    """Test align_datasets with TickRecord and SpreadRecord types."""
    t1 = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    t2 = datetime(2026, 7, 1, 12, 1, tzinfo=UTC)

    # Dataset A: Ticks
    r_a = TickRecord(
        timestamp=t1,
        source="test",
        source_symbol="A",
        source_revision="v1",
        available_at=t1,
        bid=Decimal("1.0"),
        ask=Decimal("1.1"),
        last=Decimal("1.05"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="Units",
    )
    ds_a = MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="A",
        timeframe=None,
        records=(r_a,),
        start=t1,
        end=t1,
        available_at=t1,
        record_count=1,
        quality_report=_create_mock_quality_report(1),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )

    # Dataset B: Spreads
    r_b = SpreadRecord(
        timestamp=t1,
        source="test",
        source_symbol="B",
        source_revision="v1",
        available_at=t1,
        spread=Decimal("0.1"),
        unit="USD",
        scale=1,
    )
    ds_b = MarketDataset(
        normalization_version="v1",
        data_kind="spreads",
        symbol="B",
        timeframe=None,
        records=(r_b,),
        start=t1,
        end=t1,
        available_at=t1,
        record_count=1,
        quality_report=_create_mock_quality_report(1),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )

    datasets = {"A": ds_a, "B": ds_b}
    target = [t1, t2]

    aligned = align_datasets(datasets, target)
    assert "A" in aligned
    assert "B" in aligned
    assert isinstance(aligned["A"].records[0], TickRecord)
    assert isinstance(aligned["B"].records[0], SpreadRecord)


def test_aggregate_ticks_rejects_disordered_input() -> None:
    """Test tick aggregation works and rejects incorrect input types/policy."""
    t1 = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)

    # Empty tick dataset validation
    ds_empty = MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="BTC/USD",
        timeframe=None,
        records=(),
        start=t1,
        end=t1,
        available_at=t1,
        record_count=0,
        quality_report=_create_mock_quality_report(0),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )

    with pytest.raises(DataError) as exc_info:
        aggregate_ticks(ds_empty, "M1", "last")
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_aggregate_ticks_preserves_closing_quote_spread() -> None:
    """Tick aggregation keeps the final genuine bid/ask spread in each bar."""
    first = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)
    second = first + timedelta(seconds=10)
    records = (
        TickRecord(
            timestamp=first,
            source="test",
            source_symbol="EURUSD",
            source_revision="v1",
            available_at=first,
            bid=Decimal("1.1000"),
            ask=Decimal("1.1001"),
            last=Decimal("1.10005"),
            volume=Decimal(10),
            price_unit="USD",
            volume_unit="Units",
        ),
        TickRecord(
            timestamp=second,
            source="test",
            source_symbol="EURUSD",
            source_revision="v1",
            available_at=second,
            bid=Decimal("1.1001"),
            ask=Decimal("1.1003"),
            last=Decimal("1.1002"),
            volume=Decimal(20),
            price_unit="USD",
            volume_unit="Units",
        ),
    )
    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe=None,
        records=records,
        start=first,
        end=second,
        available_at=second,
        record_count=2,
        quality_report=_create_mock_quality_report(2),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id=(
            "req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74"
        ),
    )

    aggregated = aggregate_ticks(dataset, "M1", "last")

    assert aggregated.records[0].spread == Decimal("0.0002")
    assert aggregated.records[0].spread_unit == "USD"


def test_aggregate_ticks_invalid_policy() -> None:
    """Test tick aggregation rejects invalid policy."""
    t1 = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)
    r = TickRecord(
        timestamp=t1,
        source="test",
        source_symbol="BTC/USD",
        source_revision="v1",
        available_at=t1,
        bid=Decimal("1.0"),
        ask=Decimal("1.1"),
        last=Decimal("1.05"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="Units",
    )
    ds = MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="BTC/USD",
        timeframe=None,
        records=(r,),
        start=t1,
        end=t1,
        available_at=t1,
        record_count=1,
        quality_report=_create_mock_quality_report(1),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )
    with pytest.raises(DataError) as exc_info:
        aggregate_ticks(ds, "M1", "invalid_policy")
    assert exc_info.value.args[0] == "VALIDATION_FAILED"


def test_aggregate_ticks_mismatched_units() -> None:
    """Test tick aggregation rejects ticks with mismatched units."""
    t1 = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)
    t2 = datetime(2026, 7, 1, 12, 0, 10, tzinfo=UTC)
    r1 = TickRecord(
        timestamp=t1,
        source="test",
        source_symbol="BTC/USD",
        source_revision="v1",
        available_at=t1,
        bid=Decimal("1.0"),
        ask=Decimal("1.1"),
        last=Decimal("1.05"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="Units",
    )
    r2 = TickRecord(
        timestamp=t2,
        source="test",
        source_symbol="BTC/USD",
        source_revision="v1",
        available_at=t2,
        bid=Decimal("1.0"),
        ask=Decimal("1.1"),
        last=Decimal("1.05"),
        volume=Decimal(100),
        price_unit="EUR",  # Mismatched price unit!
        volume_unit="Units",
    )
    ds = MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="BTC/USD",
        timeframe=None,
        records=(r1, r2),
        start=t1,
        end=t2,
        available_at=t2,
        record_count=2,
        quality_report=_create_mock_quality_report(2),
        source_metadata={},
        license_metadata={},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-4e4af1e8fe818e12e32bac7236e1082513dd86fee61e894491067d5ee91ada74",
    )
    with pytest.raises(DataError) as exc_info:
        aggregate_ticks(ds, "M1", "last")
    assert exc_info.value.args[0] == "VALIDATION_FAILED"
