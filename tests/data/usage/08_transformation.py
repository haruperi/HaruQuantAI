"""Demonstrate FEAT-DATA-08 transformation, resampling, and alignment operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord, TickRecord
from app.services.data.transformation import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    resample_ohlcv,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.utils import generate_id

_START = datetime(2026, 6, 22, tzinfo=UTC)


def _sample_m1_dataset() -> MarketDataset:
    """Return a sample M1 MarketDataset fixture."""
    records = tuple(
        OHLCVRecord(
            timestamp=_START + timedelta(minutes=i),
            open=Decimal(100 + i),
            high=Decimal(101 + i),
            low=Decimal(99 + i),
            close=Decimal("100.5") + i,
            volume=Decimal(100 + i * 10),
            price_unit="USD",
            volume_unit="shares",
            source="mt5",
            source_symbol="EURUSD",
            available_at=_START + timedelta(minutes=i, seconds=1),
        )
        for i in range(10)
    )
    report = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=records[-1].available_at,
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
        quality_report=report,
        source_metadata={"source": "mt5"},
        license_metadata={"license": "fixture"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def example_26_resampling() -> None:
    """Resample M1 bars to M5 using resample_ohlcv."""
    ds = _sample_m1_dataset()
    resampled = resample_ohlcv(ds, target_timeframe="M5")
    print(f"Resampled OHLCV rows: {resampled.record_count} timeframe={resampled.timeframe}")


def example_27_multitimeframe_alignment() -> None:
    """Align M1 and M5 datasets using align_multitimeframe_data."""
    m1_ds = _sample_m1_dataset()
    m5_ds = resample_ohlcv(m1_ds, target_timeframe="M5")
    targets = [r.timestamp for r in m1_ds.records]
    aligned = align_multitimeframe_data({"M1": m1_ds, "M5": m5_ds}, target_timestamps=targets)
    print(f"Aligned multitimeframe datasets: count={len(aligned)}")


def example_28_tick_aggregation() -> None:
    """Aggregate ticks into M1 bars using aggregate_ticks_to_bars."""
    ticks = tuple(
        TickRecord(
            timestamp=_START + timedelta(seconds=i * 10),
            price=Decimal("1.1000") + Decimal(i) * Decimal("0.0001"),
            volume=Decimal(10),
            bid=Decimal("1.0999") + Decimal(i) * Decimal("0.0001"),
            ask=Decimal("1.1001") + Decimal(i) * Decimal("0.0001"),
            source="mt5",
            source_symbol="EURUSD",
            available_at=_START + timedelta(seconds=i * 10 + 1),
        )
        for i in range(12)
    )
    bars = aggregate_ticks_to_bars(ticks, timeframe="M1", policy="last")
    print(f"Aggregated ticks to bars: {bars.record_count} symbol={bars.symbol}")


def main() -> None:
    """Run all transformation examples."""
    example_26_resampling()
    example_27_multitimeframe_alignment()
    example_28_tick_aggregation()

    ds = _sample_m1_dataset()
    df = to_ohlcv_dataframe(ds)
    print(f"Converted dataset to DataFrame: shape={df.shape}")


if __name__ == "__main__":
    main()
