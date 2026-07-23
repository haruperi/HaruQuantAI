"""Demonstrate FEAT-DATA-07 data quality validation and anomaly detection."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.data.quality import (
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


def _sample_dataset() -> MarketDataset:
    """Return a test MarketDataset fixture."""
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
        for i in range(5)
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


def example_25_quality_validation() -> None:
    """Validate OHLCV quality using inspect_data_quality and inspect_dataset_quality."""
    ds = _sample_dataset()
    report = inspect_data_quality(ds.records, timeframe="M1")
    print(f"Data Quality status: {report.quality_status} score={report.quality_score}")

    full_report = inspect_dataset_quality(ds)
    print(f"Dataset Quality score: {full_report.quality_score} checked={full_report.checked_count}")

    policy = get_quality_policy()
    print(f"Quality policy: {policy.policy_id}")

    remediation = summarize_quality_remediation(report)
    print(f"Quality remediation summary: {remediation}")


def example_anomaly_detectors() -> None:
    """Exercise individual anomaly detector functions."""
    ds = _sample_dataset()
    gaps = detect_timestamp_gaps(ds.records, timeframe="M1")
    jumps = detect_price_jumps(ds.records, max_jump_pct=Decimal("0.05"))
    flatlines = detect_flatline_periods(ds.records, max_consecutive=3)
    zero_vols = detect_zero_volume_bars(ds.records)
    spreads = detect_extreme_spread_widening(ds.records, max_spread=Decimal("0.01"))
    print(f"Anomaly detection: gaps={len(gaps)} jumps={len(jumps)} flatlines={len(flatlines)} zero_vol={len(zero_vols)} spreads={len(spreads)}")


def main() -> None:
    """Run all quality validation examples."""
    example_25_quality_validation()
    example_anomaly_detectors()


if __name__ == "__main__":
    main()
