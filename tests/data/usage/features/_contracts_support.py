"""Demonstrate FEAT-DATA-01 canonical contracts without external I/O."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_error,
    build_data_gap,
    build_data_quality_report,
    build_data_range,
    build_error_definition,
    build_market_dataset,
    build_ohlcv_record,
    build_quality_issue,
    build_spread_record,
    build_tick_record,
)

DataError = build_data_error


_START = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
_END = _START + timedelta(minutes=1)
_REQUEST_ID = "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


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


def fr_data_001() -> None:
    """FR-DATA-001: Stage 1 — Validate UTC OHLCV with finite exact numerics, `low ≤ open/close ≤ high`, non-negative volume, optional non-negative provider-reported spread with its native unit, provenance, and `available_at`."""
    _header(
        "Stage 1: OHLCV Record Validation - Validate UTC OHLCV Record (FR-DATA-001)"
    )
    bar = build_ohlcv_record(
        timestamp=_START,
        source="usage",
        source_symbol="EURUSD",
        available_at=_START,
        open=Decimal("1.1000"),
        high=Decimal("1.1020"),
        low=Decimal("1.0990"),
        close=Decimal("1.1010"),
        volume=Decimal(100),
        price_unit="quote",
        volume_unit="ticks",
        spread=Decimal("0.0002"),
        spread_unit="price",
    )
    print(_format_result(bar))
    print(
        f"Data -> OHLCVRecord(symbol={bar.source_symbol}, close={bar.close}, volume={bar.volume})"
    )


def fr_data_002() -> None:
    """FR-DATA-002: Stage 2 — Validate UTC ticks with finite bid/ask/last, `ask ≥ bid` when both exist, volume metadata, provenance, and `available_at`."""
    _header("Stage 2: Tick Record Validation - Validate UTC Ticks (FR-DATA-002)")
    tick = build_tick_record(
        timestamp=_START,
        source="usage",
        source_symbol="EURUSD",
        available_at=_START,
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        volume=Decimal(1),
        price_unit="quote",
        volume_unit="ticks",
    )
    print(_format_result(tick))
    print(
        f"Data -> TickRecord(symbol={tick.source_symbol}, bid={tick.bid}, ask={tick.ask})"
    )


def fr_data_003() -> None:
    """FR-DATA-003: Stage 3 — Validate spread records with declared unit/scale, non-negative exact spread, UTC timestamp, provenance, and `available_at`."""
    _header("Stage 3: Spread Record Validation - Validate Spread Records (FR-DATA-003)")
    spread = build_spread_record(
        timestamp=_START,
        source="usage",
        source_symbol="EURUSD",
        available_at=_START,
        spread=Decimal(2),
        unit="points",
        scale=5,
    )
    print(_format_result(spread))
    print(
        f"Data -> SpreadRecord(symbol={spread.source_symbol}, spread={spread.spread}, unit={spread.unit})"
    )


def fr_data_004() -> None:
    """FR-DATA-004: Stage 4 — Represent bounded quality evidence with status, score, issues, warnings, counts, truncation, schema version, UTC generation time, and governed blocking behavior."""
    _header(
        "Stage 4: Quality Evidence Representation - Bounded Quality Evidence (FR-DATA-004)"
    )
    issue = build_quality_issue(
        code="MISSING_BARS",
        severity="warning",
        message="One bounded example issue",
        affected_count=1,
        samples=("2026-07-01T12:01:00Z",),
        blocking_workflows=(),
    )
    report = build_data_quality_report(
        quality_status="excellent",
        quality_decision="rejected",
        quality_score=Decimal("99.00"),
        issues=(issue,),
        warnings=(),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=_END,
    )
    print(_format_result(report))
    print(
        f"Data -> DataQualityReport(status={report.quality_status}, score={report.quality_score}, issues={len(report.issues)})"
    )


def fr_data_005() -> None:
    """FR-DATA-005: Stage 5 — Expose immutable normalized records with availability, quality, provenance, license, cache, workflow, schema, normalization, and precision metadata, including failed quality evidence when the caller selected `warn`."""
    _header(
        "Stage 5: Market Dataset Construction - Expose Immutable Normalized Records (FR-DATA-005)"
    )
    bar = build_ohlcv_record(
        timestamp=_START,
        source="usage",
        source_symbol="EURUSD",
        available_at=_START,
        open=Decimal("1.1000"),
        high=Decimal("1.1020"),
        low=Decimal("1.0990"),
        close=Decimal("1.1010"),
        volume=Decimal(100),
        price_unit="quote",
        volume_unit="ticks",
    )
    issue = build_quality_issue(
        code="MISSING_BARS",
        severity="warning",
        message="One bounded example issue",
        affected_count=1,
        samples=("2026-07-01T12:01:00Z",),
        blocking_workflows=(),
    )
    report = build_data_quality_report(
        quality_status="excellent",
        quality_decision="rejected",
        quality_score=Decimal("99.00"),
        issues=(issue,),
        warnings=(),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=10,
        schema_version="v1",
        generated_at=_END,
    )
    dataset = build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M1",
        records=(bar,),
        start=_START,
        end=_START,
        available_at=_START,
        record_count=1,
        quality_report=report,
        source_metadata={"source": "usage"},
        license_metadata={"license": "fixture-only"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )
    data_range = build_data_range(start=_START, end=_END)
    gap = build_data_gap(start=_START, end=_END)
    print(_format_result(dataset))
    print(
        f"Data -> MarketDataset(symbol={dataset.symbol}, kind={dataset.data_kind}, records={dataset.record_count}, range={data_range.start}..{data_range.end}, gap={gap.start}..{gap.end})"
    )


def fr_data_012() -> None:
    """FR-DATA-012: Stage 6 — Expose one redacted domain exception carrying a manifest code, safe details, retryability, severity, request ID, and operator action without raw exceptions."""
    _header(
        "Stage 6: Exception Representation - Redacted Domain Exception (FR-DATA-012)"
    )
    error = DataError(
        "VALIDATION_FAILED",
        safe_details={"operation": "usage"},
        request_id=_REQUEST_ID,
    )
    print(_format_result(error))
    print(f"Data -> DataError(code={error.code}, safe_details={error.safe_details})")


def fr_data_013() -> None:
    """FR-DATA-013: Stage 7 — Expose one immutable manifest for active deterministic codes and reserve `UNKNOWN_ERROR` for failures not otherwise mapped."""
    _header(
        "Stage 7: Error Code Manifest Validation - Active Deterministic Codes (FR-DATA-013)"
    )
    definition = build_error_definition(
        code="EXAMPLE",
        domain="data",
        category="usage",
        retryable=False,
        severity="info",
        description="Example",
        operator_action="None",
    )
    print(_format_result(definition))
    print(
        f"Data -> ErrorDefinition(code={definition.code}, domain={definition.domain}, category={definition.category})"
    )


def main() -> None:
    """Execute every functional-requirement demonstration."""
    print("=" * 80)
    print("FEATURE: FEAT-DATA-01 - Canonical Data Contracts")
    print(
        "PURPOSE: Contract bases, canonical records, dataset/range/quality vocabulary, stable errors, and request validation"
    )
    print(
        "MODULE FLOW: Stage 1 (OHLCV Validation) -> Stage 2 (Tick Validation) -> Stage 3 (Spread Validation) -> Stage 4 (Quality Evidence) -> Stage 5 (Market Dataset) -> Stage 6 (Redacted Domain Exception) -> Stage 7 (Error Manifest Validation)"
    )
    print("=" * 80)

    fr_data_001()
    fr_data_002()
    fr_data_003()
    fr_data_004()
    fr_data_005()
    fr_data_012()
    fr_data_013()
    print("SUCCESS: FEAT-DATA-01 completed")


if __name__ == "__main__":
    main()
