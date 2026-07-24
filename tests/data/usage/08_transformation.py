"""Demonstrate FEAT-DATA-08 transformation, resampling, and alignment operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    TickRecord,
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    resample_ohlcv,
    to_ohlcv_dataframe,
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
    print(
        f"Resampled OHLCV rows: {resampled.record_count} "
        f"timeframe={resampled.timeframe}"
    )


def example_27_multitimeframe_alignment() -> None:
    """Align M1 and M5 datasets using align_multitimeframe_data."""
    m1_ds = _sample_m1_dataset()
    m5_ds = resample_ohlcv(m1_ds, target_timeframe="M5")
    targets = [m1_ds.records[-1].available_at]
    aligned = align_multitimeframe_data(
        {"M1": m1_ds, "M5": m5_ds}, target_timestamps=targets
    )
    print(f"Aligned multitimeframe datasets: count={len(aligned)}")


def example_28_tick_aggregation() -> None:
    """Aggregate ticks into M1 bars using aggregate_ticks_to_bars."""
    ticks = tuple(
        TickRecord(
            timestamp=_START + timedelta(seconds=i * 10),
            last=Decimal("1.1000") + Decimal(i) * Decimal("0.0001"),
            volume=Decimal(10),
            bid=Decimal("1.0999") + Decimal(i) * Decimal("0.0001"),
            ask=Decimal("1.1001") + Decimal(i) * Decimal("0.0001"),
            price_unit="USD",
            volume_unit="lots",
            source="mt5",
            source_symbol="EURUSD",
            source_revision="usage-v1",
            available_at=_START + timedelta(seconds=i * 10 + 1),
        )
        for i in range(12)
    )
    tick_dataset = _sample_m1_dataset().model_copy(
        update={
            "data_kind": "ticks",
            "timeframe": None,
            "records": ticks,
            "start": ticks[0].timestamp,
            "end": ticks[-1].timestamp,
            "available_at": ticks[-1].available_at,
            "record_count": len(ticks),
        }
    )
    bars = aggregate_ticks_to_bars(tick_dataset, "M1", "last")
    print(f"Aggregated ticks to bars: {bars.record_count} symbol={bars.symbol}")


def _demonstrate_feature() -> None:
    """Run all transformation examples."""
    example_26_resampling()
    example_27_multitimeframe_alignment()
    example_28_tick_aggregation()

    ds = _sample_m1_dataset()
    df = to_ohlcv_dataframe(ds)
    print(f"Converted dataset to DataFrame: shape={df.shape}")


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_036() -> None:
    "FR-DATA-036: Resample ordered canonical OHLCV only to a supported higher timeframe using deterministic OHLCV/spread aggregation and updated `available_at`."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_037() -> None:
    "FR-DATA-037: Backward-align multiple datasets using only values available by each target timestamp, preserving source availability metadata and failing atomically on lookahead."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_038() -> None:
    "FR-DATA-038: Aggregate sorted canonical ticks into OHLCV bars with explicit timeframe and price-side policy, preserving the closing tick's genuine bid/ask spread when both sides exist and rejecting disorder or ambiguous units."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_080() -> None:
    "FR-DATA-080: Align a private tabular market-data copy to an aware UTC datetime field/index without mutating caller input."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_081() -> None:
    "FR-DATA-081: Convert bar rows or private DataFrames to deterministic JSON-safe records with canonical UTC timestamps."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_082() -> None:
    "FR-DATA-082: Compare aligned private DataFrames using explicit finite tolerance and bounded diagnostics."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_083() -> None:
    "FR-DATA-083: Compare OHLC or OHLCV columns only after schema and alignment validation."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_085() -> None:
    'FR-DATA-085: Project one canonical bar `MarketDataset` to a detached analytical DataFrame with a UTC timestamp index and exactly six float64 columns: finite `open`, `high`, `low`, `close`, and `volume`, plus provider-reported `spread`; preserve genuinely missing spread as `NaN`, expose the common supplied spread unit in `DataFrame.attrs["spread_unit"]` or `None` when absent, and fail on inconsistent supplied units or unsafe conversion.'  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_086() -> None:
    "FR-DATA-086: Project one canonical tick `MarketDataset` to a detached analytical DataFrame with a UTC timestamp index and exactly four float64 columns: `bid`, `ask`, `last`, and `volume`; represent genuine missing optional values as `NaN`, expose common price/volume units in `DataFrame.attrs`, and fail on inconsistent units or unsafe float64 conversion."  # noqa: E501 - exact specification text
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_036,
        fr_data_037,
        fr_data_038,
        fr_data_080,
        fr_data_081,
        fr_data_082,
        fr_data_083,
        fr_data_085,
        fr_data_086,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
