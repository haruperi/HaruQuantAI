"""Executable deterministic market-data processing and synthetic examples."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to path before importing local modules
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    generate_synthetic_bars,
    generate_synthetic_ticks,
    resample_ohlcv,
)
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    SyntheticRequest,
    TickRecord,
)
from app.utils import generate_id

_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print the header for an example section.

    Args:
        title: The title of the section to display.
    """
    print(f"\n\n\n{'=' * 100}")
    print(f"\t\t{title}\t")
    print(f"{'=' * 100}\n")


def _quality(count: int, generated_at: datetime) -> DataQualityReport:
    """Build clean quality evidence."""
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


# Build M1 bars dataset
records_m1 = tuple(
    OHLCVRecord(
        timestamp=_START + timedelta(minutes=index),
        source="binance",
        source_symbol="BTCUSDT",
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
dataset_m1 = MarketDataset(
    normalization_version="v1",
    data_kind="bars",
    symbol="BTCUSDT",
    timeframe="M1",
    records=records_m1,
    start=records_m1[0].timestamp,
    end=records_m1[-1].timestamp,
    available_at=records_m1[-1].available_at,
    record_count=len(records_m1),
    quality_report=_quality(len(records_m1), records_m1[-1].available_at),
    source_metadata={"source_id": "binance", "revision": "adapter-v1"},
    license_metadata={"status": "approved"},
    cache_status="not_used",
    workflow_context="research",
    precision_policy="decimal_string",
    request_id=generate_id("req"),
)

# Build ticks dataset
records_ticks = tuple(
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
dataset_ticks = MarketDataset(
    normalization_version="v1",
    data_kind="ticks",
    symbol="BTCUSDT",
    timeframe=None,
    records=records_ticks,
    start=records_ticks[0].timestamp,
    end=records_ticks[-1].timestamp,
    available_at=records_ticks[-1].available_at,
    record_count=len(records_ticks),
    quality_report=_quality(len(records_ticks), records_ticks[-1].available_at),
    source_metadata={"source_id": "binance", "revision": "adapter-v1"},
    license_metadata={"status": "approved"},
    cache_status="not_used",
    workflow_context="research",
    precision_policy="decimal_string",
    request_id=generate_id("req"),
)


_header("Example 1: Roll up OHLCV records to a larger timeframe.")
resampled = resample_ohlcv(dataset_m1, "M5")
print("Resampled Record Count:", resampled.record_count)
print("Resampled Bar Close:", resampled.records[0].close)

_header("Example 2: Align multiple datasets to a uniform index with forward fill.")
targets = tuple(record.available_at for record in dataset_m1.records)
aligned = align_multitimeframe_data({"M1": dataset_m1}, targets)
print("Aligned Dataset Count:", len(aligned["M1"].records))

_header("Example 3: Generate GBM-based synthetic tick records.")
synthetic_ticks = generate_synthetic_ticks(
    SyntheticRequest(
        symbol="SYN_BTCUSD",
        data_kind="ticks",
        timeframe=None,
        start=_START,
        record_count=10,
        method="gbm",
        seed=42,
        parameters={
            "mu": Decimal("0.02"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal(60000),
        },
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
)
print("Synthetic Ticks Count:", synthetic_ticks.record_count)

_header("Example 4: Generate GBM-based synthetic OHLCV bar records.")
synthetic_bars = generate_synthetic_bars(
    SyntheticRequest(
        symbol="SYN_BTCUSD",
        data_kind="bars",
        timeframe="H1",
        start=_START,
        record_count=10,
        method="gbm",
        seed=42,
        parameters={
            "mu": Decimal("0.02"),
            "sigma": Decimal("0.10"),
            "start_val": Decimal(60000),
        },
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
)
print("Synthetic Bars Count:", synthetic_bars.record_count)

_header("Example 5: Aggregate tick records into custom-timeframe OHLCV bars.")
aggregated = aggregate_ticks_to_bars(dataset_ticks, "M1", "last")
print("Aggregated Bar Count:", aggregated.record_count)
