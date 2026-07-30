"""Demonstrate FEAT-DATA-08 transformation, resampling, and alignment operations."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    aggregate_ticks_to_bars,
    align_multitimeframe_data,
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
    build_tick_record,
    resample_ohlcv,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.utils import generate_id

_START = datetime(2026, 6, 22, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _sample_m1_dataset() -> Any:
    """Return a sample M1 MarketDataset fixture."""
    records = tuple(
        build_ohlcv_record(
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
    report = build_data_quality_report(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return build_market_dataset(
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


def fr_data_036() -> None:
    """FR-DATA-036: Stage 1 — Resample ordered canonical OHLCV to a supported higher timeframe using deterministic aggregation."""
    _header("Stage 1: OHLCV Resampling - Resample OHLCV (FR-DATA-036)")
    ds = _sample_m1_dataset()
    res1 = resample_ohlcv(ds, target_timeframe="M5")
    print(_format_result(res1))
    if res1.status == "success" and res1.data is not None:
        resampled = res1.data
        print(
            f"Data -> MarketDataset(symbol={resampled.symbol}, timeframe={resampled.timeframe}, count={resampled.record_count})"
        )


def fr_data_037_080() -> None:
    """FR-DATA-037, FR-DATA-080: Stage 2 — Backward-align multiple datasets using only values available by each target timestamp without lookahead."""
    _header(
        "Stage 2: Multi-Timeframe Alignment - Align Multitimeframe Data (FR-DATA-037, FR-DATA-080)"
    )
    m1_ds = _sample_m1_dataset()
    m5_res = resample_ohlcv(m1_ds, target_timeframe="M5")
    if m5_res.status == "success" and m5_res.data is not None:
        m5_ds = m5_res.data
        targets = [m1_ds.records[-1].available_at]
        res2 = align_multitimeframe_data(
            {"M1": m1_ds, "M5": m5_ds}, target_timestamps=targets
        )
        print(_format_result(res2))
        if res2.status == "success" and res2.data is not None:
            print(f"Data -> dict(keys={list(res2.data.keys())})")


def fr_data_038() -> None:
    """FR-DATA-038: Stage 3 — Aggregate sorted canonical ticks into OHLCV bars with explicit timeframe and price-side policy."""
    _header("Stage 3: Tick Aggregation to OHLCV Bars - Aggregate Ticks (FR-DATA-038)")
    ticks = tuple(
        build_tick_record(
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
    res3 = aggregate_ticks_to_bars(tick_dataset, "M1", "last")
    print(_format_result(res3))
    if res3.status == "success" and res3.data is not None:
        bars = res3.data
        print(
            f"Data -> MarketDataset(symbol={bars.symbol}, timeframe={bars.timeframe}, count={bars.record_count})"
        )


def fr_data_081_082_083_085_086() -> None:
    """FR-DATA-081, FR-DATA-082, FR-DATA-083, FR-DATA-085, FR-DATA-086: Stage 4 — Project bar/tick datasets to detached analytical DataFrames with UTC timestamp indices."""
    _header(
        "Stage 4: DataFrame Projection & Comparison - Analytical DataFrame (FR-DATA-081, FR-DATA-082, FR-DATA-083, FR-DATA-085, FR-DATA-086)"
    )
    ds = _sample_m1_dataset()
    df_res = to_ohlcv_dataframe(ds)
    print(_format_result(df_res))
    if df_res.status == "success" and df_res.data is not None:
        df = df_res.data
        print(f"Data -> DataFrame(shape={df.shape})")

    ticks = tuple(
        build_tick_record(
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
        for i in range(5)
    )
    tick_ds = ds.model_copy(
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
    tick_df_res = to_tick_dataframe(tick_ds)
    print(_format_result(tick_df_res))
    if tick_df_res.status == "success" and tick_df_res.data is not None:
        tdf = tick_df_res.data
        print(f"Data -> DataFrame(shape={tdf.shape})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
    print("=" * 80)
    print("FEATURE: FEAT-DATA-08 - Data Transformation and Resampling")
    print(
        "PURPOSE: Resample OHLCV, align multi-timeframe datasets, aggregate ticks to bars, and project to DataFrames"
    )
    print(
        "MODULE FLOW: Stage 1 (OHLCV Resampling) -> Stage 2 (Multi-Timeframe Alignment) -> Stage 3 (Tick Aggregation) -> Stage 4 (DataFrame Projection & Comparison)"
    )
    print("=" * 80)

    fr_data_036()
    fr_data_037_080()
    fr_data_038()
    fr_data_081_082_083_085_086()


if __name__ == "__main__":
    main()
