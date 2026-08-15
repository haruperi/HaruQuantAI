"""Executable Simulation validation usage example.

Demonstrates FEAT-SIM-01 run input validation, phase-one scope validation, and market data quality gates.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
    build_tick_record,
)
from app.services.simulator import (
    create_simulation_value,
    dump_simulation_value,
    unwrap_simulation_response,
    validate_market_data,
    validate_market_evidence_lineage,
    validate_phase_one_scope,
    validate_run_inputs,
)
from app.utils import canonical_json


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
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.validation")


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


def _context(dataset: object) -> object:
    """Build matching validation context."""
    digest = sha256(
        canonical_json(dataset.model_dump(mode="python", warnings=False)).encode(
            "utf-8"
        )
    ).hexdigest()
    return create_simulation_value(
        "MarketDataValidationContext",
        expected_data_hash=digest,
        requested_start=dataset.start,
        requested_end=dataset.end,
        evaluated_at=dataset.available_at,
        maximum_staleness=timedelta(0),
        allowed_tick_models=("real",),
    )


def _source_dataset() -> object:
    """Build one valid Data-owned source-bar dataset."""
    instant = datetime(2025, 1, 2, 12, tzinfo=UTC)
    available = instant + timedelta(minutes=1)
    record = build_ohlcv_record(
        timestamp=instant,
        source="fixture",
        source_symbol="EURUSD",
        available_at=available,
        open=Decimal("1.10000"),
        high=Decimal("1.10100"),
        low=Decimal("1.09900"),
        close=Decimal("1.10050"),
        volume=Decimal(10),
        price_unit="quote",
        volume_unit="ticks",
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
        generated_at=available,
    )
    return build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M1",
        records=(record,),
        start=instant,
        end=instant,
        available_at=available,
        record_count=1,
        quality_report=quality,
        source_metadata={"source": "fixture"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-22222222-2222-4222-8222-222222222222",
    )


def fr_sim_001() -> None:
    """
    FR-SIM-001: Stage 2 — Validate run request structure and strategy references.

    The system shall validate authentication-relevant request structure, registered strategy references, Data references, broker-profile references, trace identifiers, and deterministic serialization before any import or execution.
    """
    _header("Stage 2: Input Validation - Validate Request & Context (FR-SIM-001)")
    payload = {
        "request_id": "req-simulator-usage",
        "workflow_id": "wf-simulator-usage",
        "correlation_id": "cor-simulator-usage",
        "strategy_id": "registered-strategy",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": "market-data",
        "data_version": "v1",
        "data_hash": "b" * 64,
        "execution_profile_ref": "execution-profile",
        "execution_profile_version": "v1",
        "execution_profile_hash": "c" * 64,
        "risk_policy_ref": "sim-policy",
        "risk_policy_version": "v1",
        "risk_policy_hash": "d" * 64,
        "symbol": "EURUSD",
        "config_hash": "e" * 64,
    }
    resp = validate_run_inputs(payload)
    _value(resp)
    print(_format_result(resp))
    print(f"Data -> validated_status='{resp.status}', symbol='EURUSD'")


def fr_sim_003() -> None:
    """
    FR-SIM-003: Stage 2 — Validate phase-one FX scope requirements.

    The system shall permit only approved FX scope or explicit `FAST_RESEARCH`, rejecting unsupported assets, features, service mode, and canonical claims from approximation.
    """
    _header("Stage 2: Scope Validation - Validate Phase-One FX Scope (FR-SIM-003)")
    resp = validate_phase_one_scope(
        {
            "asset_class": "FX",
            "runtime_profile": "simulation",
            "execution_route": "sim",
        }
    )
    _value(resp)
    print(_format_result(resp))
    print(f"Data -> scope_status='{resp.status}'")


def fr_sim_002() -> None:
    """
    FR-SIM-002: Stage 3 — Validate market dataset checksum and quality gate.

    The system shall verify manifest checksum, required schema, UTC monotonic timestamps, uniqueness, OHLC consistency, bid/ask spread, staleness, availability metadata, and requested coverage, blocking severe failures before execution, and shall return immutable validated evidence.
    """
    _header("Stage 3: Data Quality Gate - Validate Market Dataset (FR-SIM-002)")
    dataset = _dataset()
    resp = validate_market_data(dataset, _context(dataset))
    evidence = _value(resp)
    print(_format_result(resp))
    print(f"Data -> validated_evidence={dump_simulation_value(evidence)}")


def fr_sim_136() -> None:
    """FR-SIM-136: Validate source and tick integrity with separate hashes."""
    ticks = _dataset()
    decision = ticks.available_at + timedelta(minutes=1)
    response = validate_market_evidence_lineage(
        _source_dataset(),
        ticks,
        decision_instant=decision,
        runtime_profile="simulation",
        path_sensitive=True,
        required_clock_edges=("availability", "decision"),
        clock_edges={"availability": ticks.available_at, "decision": decision},
    )
    evidence = _value(response)
    print(_format_result(response))
    print(
        f"Data -> source_hash={evidence.source_lineage_hash}, tick_hash={evidence.tick_lineage_hash}"
    )


def fr_sim_209() -> None:
    """FR-SIM-209: Bind evidence class and explicit clock-edge eligibility."""
    ticks = _dataset()
    decision = ticks.available_at + timedelta(minutes=1)
    response = validate_market_evidence_lineage(
        _source_dataset(),
        ticks,
        decision_instant=decision,
        runtime_profile="simulation",
        path_sensitive=True,
        required_clock_edges=("acknowledgement", "availability", "decision"),
        clock_edges={
            "acknowledgement": None,
            "availability": ticks.available_at,
            "decision": decision,
        },
    )
    evidence = _value(response)
    print(_format_result(response))
    print(
        f"Data -> class={evidence.market_evidence_class}, eligible={evidence.parity_eligible}, missing={evidence.missing_clock_edges}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-01 — validation/ — Boundary and Quality Validation\n\n"
        "Purpose: Validate inbound backtest requests, phase-one FX asset scope, and market data quality gates.\n\n"
        "Module flow:\n"
        "-> Stage 1: Inbound payload and dataset context mapping\n"
        "-> Stage 2: Fail-closed request, strategy reference, and scope validation\n"
        "-> Stage 3: Market data checksum verification and immutable quality evidence construction"
    )

    # Stage 2: Request & Scope Validation
    fr_sim_001()
    fr_sim_003()

    # Stage 3: Data Quality Gate Evidence
    fr_sim_002()
    fr_sim_136()
    fr_sim_209()


if __name__ == "__main__":
    main()
