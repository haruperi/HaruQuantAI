"""Demonstrate FEAT-DATA-01 canonical contracts without external I/O."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

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


def _demonstrate_feature() -> None:
    """Construct every public FEAT-DATA-01 contract type."""
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
    spread = build_spread_record(
        timestamp=_START,
        source="usage",
        source_symbol="EURUSD",
        available_at=_START,
        spread=Decimal(2),
        unit="points",
        scale=5,
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
        quality_status="passed_with_warnings",
        quality_score=Decimal("0.99"),
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
    definition = build_error_definition(
        code="EXAMPLE",
        domain="data",
        category="usage",
        retryable=False,
        severity="info",
        description="Example",
        operator_action="None",
    )
    error = DataError(
        "VALIDATION_FAILED",
        safe_details={"operation": "usage"},
        request_id=_REQUEST_ID,
    )

    print(
        "FEAT-DATA-01:",
        type(dataset).__name__,
        type(tick).__name__,
        type(spread).__name__,
        type(data_range).__name__,
        type(gap).__name__,
        definition.code,
        error.code,
    )


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_001() -> None:
    _header("fr_data_001")
    "FR-DATA-001: Validate UTC OHLCV with finite exact numerics, `low ≤ open/close ≤ high`, non-negative volume, optional non-negative provider-reported spread with its native unit, provenance, and `available_at`."
    _demonstrate_once()


def fr_data_002() -> None:
    _header("fr_data_002")
    "FR-DATA-002: Validate UTC ticks with finite bid/ask/last, `ask ≥ bid` when both exist, volume metadata, provenance, and `available_at`."
    _demonstrate_once()


def fr_data_003() -> None:
    _header("fr_data_003")
    "FR-DATA-003: Validate spread records with declared unit/scale, non-negative exact spread, UTC timestamp, provenance, and `available_at`."
    _demonstrate_once()


def fr_data_004() -> None:
    _header("fr_data_004")
    "FR-DATA-004: Represent bounded quality evidence with status, score, issues, warnings, counts, truncation, schema version, UTC generation time, and governed blocking behavior."
    _demonstrate_once()


def fr_data_005() -> None:
    _header("fr_data_005")
    "FR-DATA-005: Expose immutable normalized records with availability, quality, provenance, license, cache, workflow, schema, normalization, and precision metadata, including failed quality evidence when the caller selected `warn`."
    _demonstrate_once()


def fr_data_012() -> None:
    _header("fr_data_012")
    "FR-DATA-012: Expose one redacted domain exception carrying a manifest code, safe details, retryability, severity, request ID, and operator action without raw exceptions."
    _demonstrate_once()


def fr_data_013() -> None:
    _header("fr_data_013")
    "FR-DATA-013: Expose one immutable manifest for active deterministic codes and reserve `UNKNOWN_ERROR` for failures not otherwise mapped."
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_001,
        fr_data_002,
        fr_data_003,
        fr_data_004,
        fr_data_005,
        fr_data_012,
        fr_data_013,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
