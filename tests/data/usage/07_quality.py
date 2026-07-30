"""Demonstrate FEAT-DATA-07 data quality validation and anomaly detection."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
    detect_extreme_spread_widening,
    detect_flatline_periods,
    detect_price_jumps,
    detect_timestamp_gaps,
    detect_zero_volume_bars,
    get_quality_policy,
    inspect_data_quality,
    inspect_dataset_quality,
    summarize_quality_remediation,
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


def _sample_dataset() -> Any:
    """Return a test MarketDataset fixture."""
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
        for i in range(5)
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


def fr_data_091() -> None:
    """FR-DATA-091: Stage 1 — Detect missing bars against expected timeframe frequency, discounting exact weekend closures."""
    _header("Stage 1: Gap & Frequency Anomaly Detection - Timestamp Gaps (FR-DATA-091)")
    ds = _sample_dataset()
    gaps_res = detect_timestamp_gaps(ds.records, timeframe="M1")
    print(_format_result(gaps_res))
    print(f"Data -> TimestampGaps(detected={gaps_res is not None})")


def fr_data_092() -> None:
    """FR-DATA-092: Stage 2 — Detect price spikes beyond profile sigma bounds, flatline runs, zero-volume runs, and spread breaches."""
    _header(
        "Stage 2: Price Spike, Flatline & Spread Anomaly Detection - Anomaly Detectors (FR-DATA-092)"
    )
    ds = _sample_dataset()
    jumps_res = detect_price_jumps(ds.records)
    print(_format_result(jumps_res))
    flatlines_res = detect_flatline_periods(ds.records)
    print(_format_result(flatlines_res))
    zero_vols_res = detect_zero_volume_bars(ds.records)
    print(_format_result(zero_vols_res))
    spreads_res = detect_extreme_spread_widening(ds.records)
    print(_format_result(spreads_res))
    print(
        f"Data -> Anomalies(jumps={jumps_res is not None}, flatlines={flatlines_res is not None}, zero_vols={zero_vols_res is not None}, spreads={spreads_res is not None})"
    )


def fr_data_093() -> None:
    """FR-DATA-093: Stage 3 — Compute quality score clamped to [0, 1] in Decimal and resolve quality status."""
    _header(
        "Stage 3: Quality Scoring & Status Resolution - Score & Status (FR-DATA-093)"
    )
    ds = _sample_dataset()
    res1 = inspect_data_quality(ds)
    print(_format_result(res1))
    res2 = inspect_dataset_quality(ds)
    print(_format_result(res2))
    res3 = get_quality_policy()
    print(_format_result(res3))
    if res1.status == "success" and res1.data is not None:
        report = res1.data
        print(
            f"Data -> DataQualityReport(status={report.quality_status}, score={report.quality_score})"
        )


def fr_data_094() -> None:
    """FR-DATA-094: Stage 4 — Map each detected issue code to one deterministic recommended remediation action."""
    _header(
        "Stage 4: Remediation Mapping & Report Synthesis - Remediation Mapping (FR-DATA-094)"
    )
    ds = _sample_dataset()
    res1 = inspect_data_quality(ds)
    if res1.status == "success" and res1.data is not None:
        res4 = summarize_quality_remediation(res1.data)
        print(_format_result(res4))
        if res4.status == "success" and res4.data is not None:
            print(f"Data -> QualityRemediationSummary(remediations={res4.data})")


def main() -> None:
    """Execute every functional-requirement demonstration."""
    print("=" * 80)
    print("FEATURE: FEAT-DATA-07 - Data Quality and Validation")
    print(
        "PURPOSE: Validate data quality, score datasets, and detect anomalies and missing bars"
    )
    print(
        "MODULE FLOW: Stage 1 (Gap & Frequency) -> Stage 2 (Price Spike, Flatline & Spread) -> Stage 3 (Scoring & Status) -> Stage 4 (Remediation Mapping)"
    )
    print("=" * 80)

    fr_data_091()
    fr_data_092()
    fr_data_093()
    fr_data_094()


if __name__ == "__main__":
    main()
