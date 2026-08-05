"""Executable Simulation timeline usage example.

Demonstrates FEAT-SIM-03 tick creation, dataset timeline construction, and intent timing validation.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_tick_record,
)
from app.services.simulator import (
    build_tick_timeline,
    create_simulation_value,
    unwrap_simulation_response,
    validate_intent_timing,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
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


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.timeline")


def _dataset() -> object:
    """Build one valid Data-owned tick dataset."""
    instant = datetime(2025, 1, 2, 12, tzinfo=UTC)
    record = build_tick_record(
        timestamp=instant,
        source="fixture",
        source_symbol="EURUSD",
        available_at=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        last=Decimal("1.10001"),
        volume=Decimal(2),
        price_unit="quote",
        volume_unit="lot",
        source_bar_time=instant,
        tick_index_in_bar=0,
        bar_phase=1,
    )
    quality = build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=1,
        schema_version="v1",
        generated_at=instant,
    )
    return build_market_dataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe="M1",
        records=(record,),
        start=instant,
        end=instant,
        available_at=instant,
        record_count=1,
        quality_report=quality,
        source_metadata={"tick_generation_model": "real"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-11111111-1111-4111-8111-111111111111",
    )


def fr_sim_004() -> None:
    """
    FR-SIM-004: Stage 1 — Construct immutable Simulation UTC tick contract.

    The system shall expose an immutable UTC tick containing symbol, timestamp, bid, ask, source identity, sequence, and availability metadata with finite positive prices and `ask >= bid`.
    """
    _header("Stage 1: Tick Contract - Create Canonical Tick (FR-SIM-004)")
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    tick = create_simulation_value(
        "Tick",
        symbol="EURUSD",
        timestamp=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        source_id="provider",
        sequence=0,
        available_at=instant,
    )
    print(_format_result(tick))
    print(f"Data -> symbol='{tick.symbol}', bid={tick.bid}, ask={tick.ask}")


def fr_sim_005() -> None:
    """
    FR-SIM-005: Stage 2 — Convert MarketDataset into ordered canonical Tick tuple.

    The system shall convert one Data-owned tick `MarketDataset` into a strictly ordered immutable `Tick` tuple, validating UTC monotonicity, positive finite prices, `ask >= bid`, and the presence of intra-bar phase evidence. Tick derivation itself belongs to Data (`FR-DATA-087`-`FR-DATA-090`); Simulation constructs no ticks, applies no spread model, and consumes no seed.
    """
    _header("Stage 2: Timeline Construction - Build Tick Timeline (FR-SIM-005)")
    resp = build_tick_timeline(_dataset())
    ticks = _value(resp)
    print(_format_result(resp))
    print(f"Data -> tick_count={len(ticks if isinstance(ticks, tuple) else ())}")


def fr_sim_006() -> None:
    """
    FR-SIM-006: Stage 2 — Validate intent timing and no-lookahead enforcement.

    The system shall reject a strategy intent whose evidence became available after its execution time and enforce previous-closed-bar visibility by default.
    """
    _header("Stage 2: Timing Validation - Validate Intent Timing (FR-SIM-006)")
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    resp = validate_intent_timing(instant, instant)
    _value(resp)
    print(_format_result(resp))
    print(f"Data -> timing_status='{resp.status}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-03 — timeline/ — Canonical Tick Timeline\n\n"
        "Purpose: Construct Tick contracts, convert MarketDatasets into ordered tick timelines, and validate intent timing.\n\n"
        "Module flow:\n"
        "-> Stage 1: Individual Tick contract construction and field validation\n"
        "-> Stage 2: Monotonic tick timeline assembly and intent timestamp non-lookahead verification"
    )

    # Stage 1: Tick Contract
    fr_sim_004()

    # Stage 2: Timeline & Timing
    fr_sim_005()
    fr_sim_006()


if __name__ == "__main__":
    main()
