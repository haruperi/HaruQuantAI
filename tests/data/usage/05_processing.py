"""Run deterministic market-data processing and private tabular examples."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    generate_synthetic_bars,
    resample_ohlcv,
)
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    SyntheticRequest,
    TickRecord,
)
from app.services.data.processing.tabular import (
    align_dataframe_datetime,
    bars_to_records,
    compare_dataframes,
    compare_ohlcv,
    serialize_dataframe_records,
)
from app.utils import generate_id, logger

_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _quality(count: int, generated_at: datetime) -> DataQualityReport:
    """Build clean bounded quality evidence for processing examples."""
    logger.info("Building processing quality evidence for %d records", count)
    return DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        issues=(),
        warnings=(),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=100,
        schema_version="v1",
        generated_at=generated_at,
    )


def _minute_bars(symbol: str = "BTCUSD") -> MarketDataset:
    """Build five canonical M1 bars with truthful availability times."""
    logger.info("Building five canonical M1 bars for %s", symbol)
    records = tuple(
        OHLCVRecord(
            timestamp=_START + timedelta(minutes=index),
            source="binance",
            source_symbol=symbol,
            source_revision="adapter-v1",
            available_at=_START + timedelta(minutes=index, seconds=1),
            open=Decimal(100) + index,
            high=Decimal(101) + index,
            low=Decimal(99) + index,
            close=Decimal("100.5") + index,
            volume=Decimal(10) + index,
            price_unit="USDT",
            volume_unit="BTC",
        )
        for index in range(5)
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol=symbol,
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=_quality(len(records), records[-1].available_at),
        source_metadata={"source_id": "binance", "revision": "adapter-v1"},
        license_metadata={"status": "approved"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def _ticks() -> MarketDataset:
    """Build a sorted canonical tick stream for aggregation."""
    logger.info("Building a sorted canonical tick stream")
    records = tuple(
        TickRecord(
            timestamp=_START + timedelta(seconds=index * 10),
            source="binance",
            source_symbol="BTCUSDT",
            source_revision="adapter-v1",
            available_at=_START + timedelta(seconds=index * 10, milliseconds=50),
            bid=Decimal(100) + index,
            ask=Decimal("100.2") + index,
            last=Decimal("100.1") + index,
            volume=Decimal("0.5"),
            price_unit="USDT",
            volume_unit="BTC",
        )
        for index in range(6)
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="BTCUSDT",
        timeframe=None,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=_quality(len(records), records[-1].available_at),
        source_metadata={"source_id": "binance", "revision": "adapter-v1"},
        license_metadata={"status": "approved"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def example_fr_data_036_resample_ohlcv() -> MarketDataset:
    """Roll five M1 bars into one deterministic M5 bar."""
    logger.info("FR-DATA-036: resampling M1 OHLCV to M5")
    result = resample_ohlcv(_minute_bars(), "M5")
    logger.info(
        "M5 open=%s high=%s low=%s close=%s volume=%s",
        result.records[0].open,  # type: ignore[union-attr]
        result.records[0].high,  # type: ignore[union-attr]
        result.records[0].low,  # type: ignore[union-attr]
        result.records[0].close,  # type: ignore[union-attr]
        result.records[0].volume,  # type: ignore[union-attr]
    )
    return result


def example_fr_data_037_no_lookahead_alignment() -> None:
    """Backward-align data using only observations already available."""
    logger.info("FR-DATA-037: aligning datasets without lookahead")
    dataset = _minute_bars()
    targets = tuple(record.available_at for record in dataset.records)
    aligned = align_multitimeframe_data({"M1": dataset}, targets)
    for record, target in zip(aligned["M1"].records, targets, strict=True):
        if record.available_at > target:
            raise AssertionError("alignment exposed future evidence")
    logger.info("Aligned %d target timestamps", len(targets))


def example_fr_data_038_ticks_to_bars() -> MarketDataset:
    """Aggregate a sorted tick stream into canonical M1 OHLCV."""
    logger.info("FR-DATA-038: aggregating ticks into M1 bars")
    result = aggregate_ticks_to_bars(_ticks(), "M1", "last")
    logger.info("Aggregated %d ticks into %d bars", 6, result.record_count)
    return result


def example_fr_data_039_synthetic_bars() -> MarketDataset:
    """Generate a repeatable explicitly synthetic GBM path."""
    logger.info("FR-DATA-039: generating deterministic synthetic H1 bars")
    result = generate_synthetic_bars(
        SyntheticRequest(
            symbol="SYNTHETIC_EURUSD",
            data_kind="bars",
            timeframe="H1",
            start=_START,
            record_count=24,
            method="gbm",
            seed=42,
            parameters={
                "mu": Decimal("0.02"),
                "sigma": Decimal("0.10"),
                "start_val": Decimal("1.10"),
            },
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
    )
    logger.info("Generated %d explicitly synthetic H1 bars", result.record_count)
    return result


def _private_frame() -> pd.DataFrame:
    """Build a private caller-owned tabular copy for conversion examples."""
    logger.info("Building a private tabular market-data copy")
    return pd.DataFrame(
        {
            "timestamp": [_START, _START + timedelta(minutes=1)],
            "open": [100.0, 101.0],
            "high": [101.0, 102.0],
            "low": [99.0, 100.0],
            "close": [100.5, 101.5],
            "volume": [10.0, 11.0],
        }
    )


def example_fr_data_080_align_private_tabular_copy() -> pd.DataFrame:
    """Align a copied DataFrame to an aware UTC index without mutation."""
    logger.info("FR-DATA-080: aligning a private tabular copy")
    original = _private_frame()
    aligned = align_dataframe_datetime(original, "timestamp")
    if "timestamp" not in original.columns:
        raise AssertionError("caller input was mutated")
    logger.info("Aligned private frame rows=%d", len(aligned))
    return aligned


def example_fr_data_081_json_safe_records() -> None:
    """Serialize canonical bars and a private frame deterministically."""
    logger.info("FR-DATA-081: serializing deterministic JSON-safe records")
    dataset = _minute_bars()
    canonical = bars_to_records(dataset.records)  # type: ignore[arg-type]
    tabular = serialize_dataframe_records(
        align_dataframe_datetime(_private_frame(), "timestamp")
    )
    logger.info("Serialized canonical=%d tabular=%d", len(canonical), len(tabular))


def _compare_private_frames() -> None:
    """Compare aligned frames and their OHLCV schema with explicit tolerance."""
    logger.info("FR-DATA-082/083: comparing aligned private OHLCV frames")
    left = align_dataframe_datetime(_private_frame(), "timestamp")
    right = left.copy(deep=True)
    if not compare_dataframes(left, right, tolerance=Decimal("0.000001")):
        raise AssertionError("equal aligned frames did not compare equal")
    if not compare_ohlcv(left, right, tolerance=Decimal("0.000001")):
        raise AssertionError("equal OHLCV frames did not compare equal")
    logger.info("Private tabular comparisons passed")


def example_fr_data_082_compare_dataframes() -> None:
    """Compare aligned private frames with explicit finite tolerance."""
    logger.info("FR-DATA-082: comparing aligned private frames")
    _compare_private_frames()


def example_fr_data_083_compare_ohlcv() -> None:
    """Compare only validated OHLCV columns and alignment."""
    logger.info("FR-DATA-083: comparing validated OHLCV columns")
    _compare_private_frames()


if __name__ == "__main__":
    example_fr_data_036_resample_ohlcv()
    example_fr_data_037_no_lookahead_alignment()
    example_fr_data_038_ticks_to_bars()
    example_fr_data_039_synthetic_bars()
    example_fr_data_080_align_private_tabular_copy()
    example_fr_data_081_json_safe_records()
    example_fr_data_082_compare_dataframes()
    example_fr_data_083_compare_ohlcv()
