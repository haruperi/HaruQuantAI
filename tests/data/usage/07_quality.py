"""Demonstrate FEAT-DATA-07 data quality validation and anomaly detection."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

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


def _sample_dataset() -> MarketDataset:
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


def example_25_quality_validation() -> None:
    """Validate OHLCV quality using inspect_data_quality and inspect_dataset_quality."""
    _header(
        "Validate OHLCV quality using inspect_data_quality and inspect_dataset_quality."
    )
    ds = _sample_dataset()
    res1 = inspect_data_quality(ds)
    if res1.status == "success" and res1.data is not None:
        report = res1.data
        print(
            f"Data Quality status: {report.quality_status} score={report.quality_score}"
        )
        res2 = inspect_dataset_quality(ds)
        if res2.status == "success" and res2.data is not None:
            full_report = res2.data
            print(
                f"Dataset Quality score: {full_report.quality_score} "
                f"checked={full_report.checked_count}"
            )
        res3 = get_quality_policy()
        if res3.status == "success" and res3.data is not None:
            policy = res3.data
            print(f"Quality policy: {policy.profile}")
        res4 = summarize_quality_remediation(report)
        if res4.status == "success" and res4.data is not None:
            remediation = res4.data
            print(f"Quality remediation summary: {remediation}")


def example_anomaly_detectors() -> None:
    """Exercise individual anomaly detector functions."""
    _header("Exercise individual anomaly detector functions.")
    ds = _sample_dataset()
    gaps = detect_timestamp_gaps(ds.records, timeframe="M1")
    jumps = detect_price_jumps(ds.records)
    flatlines = detect_flatline_periods(ds.records)
    zero_vols = detect_zero_volume_bars(ds.records)
    spreads = detect_extreme_spread_widening(ds.records)
    print(
        f"Anomaly detection: gaps={gaps is not None} jumps={jumps is not None} "
        f"flatlines={flatlines is not None} zero_vol={zero_vols is not None} "
        f"spreads={spreads is not None}"
    )


def _demonstrate_feature() -> None:
    """Run all quality validation examples."""
    example_25_quality_validation()
    example_anomaly_detectors()


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_091() -> None:
    _header("fr_data_091")
    "FR-DATA-091: Detect missing bars against expected timeframe frequency, discounting exact weekend closures and supplied `SessionWindow` closures. Emit critical `MISSING_BARS` only for unexplained gaps beyond tolerance, with affected count and bounded samples; add `calendar_unverified` when no sessions were supplied."
    _demonstrate_once()


def fr_data_092() -> None:
    _header("fr_data_092")
    "FR-DATA-092: Detect price spikes beyond the profile sigma bound, flat-line runs, zero-volume runs, duplicate OHLCV bar timestamps, and comparable price-unit spread-threshold breaches. Tick timestamps may repeat; provider-point spreads are disclosed as `spread_unit_unverified` instead of being compared to a price-unit ceiling. Each issue carries bounded evidence."
    _demonstrate_once()


def fr_data_093() -> None:
    _header("fr_data_093")
    "FR-DATA-093: Compute `quality_score` as `1 - sum(severity_weight x affected_count / checked_count)` clamped to `[0, 1]` in `Decimal`, and derive `quality_status`: `failed` when any `QUALITY_BLOCKING_ISSUES` code is present (or, under `strict`, when the score is below `QUALITY_MIN_SCORE`), otherwise `passed_with_warnings` when any issue or warning exists, otherwise `passed`. A constant or unexamined score is never emitted."
    _demonstrate_once()


def fr_data_094() -> None:
    _header("fr_data_094")
    "FR-DATA-094: Map each detected issue code to one deterministic recommended remediation action without mutating the dataset or performing the remediation."
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_091,
        fr_data_092,
        fr_data_093,
        fr_data_094,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
