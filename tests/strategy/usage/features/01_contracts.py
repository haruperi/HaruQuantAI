"""Executable examples of every package-root Strategy contract."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
)
from app.services.strategy import (
    create_strategy_config,
    create_strategy_decision,
    create_strategy_event,
    create_strategy_execution_context,
    create_strategy_execution_result,
    create_strategy_manifest,
    create_strategy_mutation_result,
    create_strategy_parameter_update_request,
    create_strategy_ref,
    create_strategy_registration_request,
    create_strategy_replay_manifest,
    create_strategy_signal,
    create_strategy_signal_evidence,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    export_strategy_diagnostics,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)

_HASH = "a" * 64
_REQUEST = "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_CORRELATION = "cor-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_WORKFLOW = "wf-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


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


def _sample_manifest() -> Any:
    """Construct a sample strategy manifest with all required fields."""
    return create_strategy_manifest(
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        module_path="app.services.strategy.evaluators.naive_ma_trend",
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:H1",),
        required_indicators=("sma",),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        permitted_environments=(get_strategy_environment("RESEARCH"),),
        source_hash=_HASH,
        artifact_hash=_HASH,
        dependency_hash=_HASH,
        provenance_refs=("approval-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=1_000,
        max_diagnostic_bytes=16_384,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )


def fr_str_001() -> None:
    """FR-STR-001: Stage 1 — Enumerate supported Strategy environment."""
    _header("Stage 1: Enumerate Strategy Environment (FR-STR-001)")
    result = get_strategy_environment("RESEARCH")
    print(_format_result(result))
    print(f"Data -> environment='{result.value}'")


def fr_str_002() -> None:
    """FR-STR-002: Stage 1 — Identify explicit decision timing policy."""
    _header("Stage 1: Identify Timing Policy (FR-STR-002)")
    result = get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE")
    print(_format_result(result))
    print(f"Data -> timing_policy='{result.value}'")


def fr_str_003() -> None:
    """FR-STR-003: Stage 1 — Represent immutable lifecycle eligibility state."""
    _header("Stage 1: Represent Lifecycle Status (FR-STR-003)")
    result = get_strategy_lifecycle_status("APPROVED")
    print(_format_result(result))
    print(f"Data -> lifecycle_status='{result.value}'")


def fr_str_035() -> None:
    """FR-STR-035: Stage 1 — Define explicit host validation policy."""
    _header("Stage 1: Define Host Validation Policy (FR-STR-035)")
    result = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=16_384,
        max_config_nesting_depth=8,
        max_config_string_length=512,
        max_config_collection_items=128,
    )
    print(_format_result(result))
    print(
        f"Data -> policy_version='{result.policy_version}', max_bytes={result.max_config_payload_bytes}"
    )


def fr_str_008() -> None:
    """FR-STR-008: Stage 1 — Define applicability-aware Strategy manifest."""
    _header("Stage 1: Define Strategy Manifest (FR-STR-008)")
    result = _sample_manifest()
    print(_format_result(result))
    print(
        f"Data -> strategy_id='{result.strategy_id}', module_path='{result.module_path}'"
    )


def fr_str_004() -> None:
    """FR-STR-004: Stage 2 — Construct exact Strategy reference."""
    _header("Stage 2: Construct Strategy Reference (FR-STR-004)")
    result = create_strategy_ref(
        strategy_id="naive-ma-trend",
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    print(_format_result(result))
    print(
        f"Data -> strategy_id='{result.strategy_id}', exact_version='{result.exact_version}'"
    )


def fr_str_005() -> None:
    """FR-STR-005: Stage 2 — Expose validated Strategy reference."""
    _header("Stage 2: Expose Validated Strategy Reference (FR-STR-005)")
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=16_384,
        max_config_nesting_depth=8,
        max_config_string_length=512,
        max_config_collection_items=128,
    )
    manifest = _sample_manifest()
    result = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    print(_format_result(result))
    print(
        f"Data -> record_hash='{result.registry_record_hash[:16]}...', lifecycle='{result.lifecycle_status.value}'"
    )


def fr_str_006() -> None:
    """FR-STR-006: Stage 2 — Represent declarative Strategy configuration."""
    _header("Stage 2: Represent Strategy Configuration (FR-STR-006)")
    result = create_strategy_config(
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        request_id=_REQUEST,
    )
    print(_format_result(result))
    print(f"Data -> parameters={dict(result.parameters)}")


def fr_str_007() -> None:
    """FR-STR-007: Stage 2 — Expose validated configuration identity."""
    _header("Stage 2: Expose Validated Configuration (FR-STR-007)")
    result = create_validated_strategy_config(
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        config_hash=_HASH,
        policy_version="usage-v1",
        request_id=_REQUEST,
    )
    print(_format_result(result))
    print(
        f"Data -> config_hash='{result.config_hash[:16]}...', params={dict(result.normalized_parameters)}"
    )


def fr_str_009() -> None:
    """FR-STR-009: Stage 2 — Define Strategy registration request command."""
    _header("Stage 2: Define Registration Request (FR-STR-009)")
    manifest = _sample_manifest()
    result = create_strategy_registration_request(
        command_id="usage-command-register",
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        module_path=manifest.module_path,
        manifest=manifest,
        config_schema=manifest.config_schema,
        source_hash=manifest.source_hash,
        artifact_hash=manifest.artifact_hash,
        dependency_hash=manifest.dependency_hash,
        provenance_refs=manifest.provenance_refs,
        principal_id="usage-principal",
        reason="usage example registration",
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        authorization_ref="approval-1",
        requested_at=datetime.now(UTC),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    print(_format_result(result))
    print(f"Data -> command_id='{result.command_id}', schema_id='{result.schema_id}'")


def fr_str_010() -> None:
    """FR-STR-010: Stage 2 — Define parameter update request command."""
    _header("Stage 2: Define Parameter Update Request (FR-STR-010)")
    ref = create_strategy_ref(
        strategy_id="naive-ma-trend",
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = create_strategy_config(
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        request_id=_REQUEST,
    )
    result = create_strategy_parameter_update_request(
        command_id="usage-command-config",
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        parameters=config.parameters,
        principal_id="usage-principal",
        reason="usage example parameter update",
        ref=ref,
        config=config,
        authorization_ref="approval-2",
        requested_at=datetime.now(UTC),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    print(_format_result(result))
    print(f"Data -> command_id='{result.command_id}', schema_id='{result.schema_id}'")


def fr_str_011() -> None:
    """FR-STR-011: Stage 2 — Fix execution context for evaluation."""
    _header("Stage 2: Fix Execution Context (FR-STR-011)")
    result = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=datetime.now(UTC),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=7,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=16_384,
    )
    print(_format_result(result))
    print(f"Data -> request_id='{result.request_id}', seed={result.seed}")


def fr_str_012() -> None:
    """FR-STR-012: Stage 2 — Represent typed Strategy event."""
    _header("Stage 2: Represent Strategy Event (FR-STR-012)")
    result = create_strategy_event(
        event_type="BAR_CLOSED",
        hook="on_bar",
        occurred_at=datetime.now(UTC),
        sequence=0,
        source_owner="data",
        source_contract_version="v1",
        source_schema_id="data.market_dataset.v1",
        source_snapshot_ref="live-market-read",
        source_checksum=_HASH,
        source_as_of=datetime.now(UTC),
        facts={"symbol": "EURUSD"},
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
    )
    print(_format_result(result))
    print(f"Data -> event_type='{result.event_type}', hook='{result.hook}'")


def fr_str_013() -> None:
    """FR-STR-013: Stage 2 — Represent Strategy decision."""
    _header("Stage 2: Represent Strategy Decision (FR-STR-013)")
    now = datetime.now(UTC)
    result = create_strategy_decision(
        decision_id="usage-decision-1",
        sequence=0,
        action="PROPOSE",
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        requested_sizing_mode="quantity",
        quantity_hint=Decimal("0.01"),
        valid_from=now,
        expires_at=now + timedelta(minutes=5),
        allow_partial_fills=False,
        rationale_refs=("usage-rationale",),
        diagnostic_facts={"example": "contract construction only"},
        lineage={
            "strategy_id": "naive-ma-trend",
            "strategy_version": "1.0.0",
            "config_hash": _HASH,
        },
    )
    print(_format_result(result))
    print(
        f"Data -> decision_id='{result.decision_id}', action='{result.action}', side='{result.side}'"
    )


def fr_str_014() -> None:
    """FR-STR-014: Stage 3 — Return atomic execution result."""
    _header("Stage 3: Return Execution Result (FR-STR-014)")
    now = datetime.now(UTC)
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=now,
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=7,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=16_384,
    )
    manifest = _sample_manifest()
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=16_384,
        max_config_nesting_depth=8,
        max_config_string_length=512,
        max_config_collection_items=128,
    )
    validated_ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    validated_config = create_validated_strategy_config(
        strategy_id=manifest.strategy_id,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=_REQUEST,
    )
    diagnostics = export_strategy_diagnostics(context, {"example": "contracts"}).data
    replay = create_strategy_replay_manifest(
        validated_ref, validated_config, context, _HASH, _HASH
    ).data
    result = create_strategy_execution_result(
        decisions=(),
        intents=(),
        diagnostics=diagnostics,
        replay_manifest=replay,
        local_state_update=None,
        result_hash=_HASH,
    )
    print(_format_result(result))
    print(
        f"Data -> result_hash='{result.result_hash[:16]}...', intents_count={len(result.intents)}"
    )


def fr_str_015() -> None:
    """FR-STR-015: Stage 3 — Demonstrate structured Strategy errors."""
    _header("Stage 3: Demonstrate Strategy Errors (FR-STR-015)")
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=datetime.now(UTC),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=7,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=16_384,
    )
    result = export_strategy_diagnostics(context, {"error_context": "testing"})
    print(_format_result(result))
    print(f"Data -> status='{result.status}', has_data={result.data is not None}")


def fr_str_016() -> None:
    """FR-STR-016: Stage 3 — Standard response wrapper outcome."""
    _header("Stage 3: Standard Response Outcomes (FR-STR-016)")
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=datetime.now(UTC),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=7,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=16_384,
    )
    result = export_strategy_diagnostics(context, {"status": "success"})
    print(_format_result(result))
    print(f"Data -> response_status='{result.status}'")


def fr_str_017() -> None:
    """FR-STR-017: Stage 3 — Immutable mutation truth result."""
    _header("Stage 3: Immutable Mutation Result (FR-STR-017)")
    now = datetime.now(UTC)
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=16_384,
        max_config_nesting_depth=8,
        max_config_string_length=512,
        max_config_collection_items=128,
    )
    manifest = _sample_manifest()
    validated_ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    result = create_strategy_mutation_result(
        mutation_id="usage-mutation-1",
        mutation_type="REGISTER_VERSION",
        status="ACCEPTED",
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        validated_ref=validated_ref,
        record_ref=f"{manifest.strategy_id}@{manifest.strategy_version}",
        record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
        workflow_id=_WORKFLOW,
        completed_at=now,
    )
    print(_format_result(result))
    print(
        f"Data -> mutation_id='{result.mutation_id}', status='{result.status}', record_ref='{result.record_ref}'"
    )


def fr_str_038() -> None:
    """FR-STR-038: Stage 3 — Immutable concrete signal output."""
    _header("Stage 3: Concrete Signal Output (FR-STR-038)")
    result = create_strategy_signal(
        signal_id=_HASH,
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        symbol="EURUSD",
        timestamp=datetime.now(UTC),
        signal_name="fast_crosses_above_slow",
        side="BUY",
        active=False,
        facts={"fast": "1.1005"},
        lineage={"config_hash": _HASH},
    )
    print(_format_result(result))
    print(
        f"Data -> signal_name='{result.signal_name}', side='{result.side}', active={result.active}"
    )


def fr_str_039() -> None:
    """FR-STR-039: Stage 3 — Immutable point-in-time signal evidence."""
    _header("Stage 3: Point-in-Time Signal Evidence (FR-STR-039)")
    now = datetime.now(UTC)
    market_record = build_ohlcv_record(
        timestamp=now - timedelta(hours=1),
        open="1.1000",
        high="1.1010",
        low="1.0990",
        close="1.1005",
        volume=100,
        source="usage",
        source_symbol="EURUSD",
        available_at=now - timedelta(hours=1),
        price_unit="USD",
        volume_unit="units",
    )
    market = build_market_dataset(
        symbol="EURUSD",
        data_kind="bars",
        records=(market_record,),
        normalization_version="v1",
        timeframe="H1",
        start=market_record.timestamp,
        end=market_record.timestamp,
        available_at=market_record.available_at,
        record_count=1,
        quality_report=build_data_quality_report(
            quality_status="passed",
            quality_score=Decimal(1),
            record_count=1,
            checked_count=1,
            truncated=False,
            sample_limit=1,
            schema_version="v1",
            generated_at=market_record.available_at,
        ),
        source_metadata={"provider": "usage"},
        license_metadata={"license": "usage"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST,
    )
    result = create_strategy_signal_evidence(
        evidence_id="strategy-contract-usage",
        primary_market=market,
        related_markets={},
        point_size=Decimal("0.0001"),
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )
    print(_format_result(result))
    print(
        f"Data -> evidence_id='{result.evidence_id}', symbol='{result.primary_market.symbol}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-01 — contracts/ — Versioned Strategy Contracts\n\n"
        "Purpose: Define the typed, versioned, serialization-safe contracts shared by all Strategy features.\n\n"
        "Module flow:\n"
        "-> untrusted boundary payload\n"
        "-> typed model schema validation\n"
        "-> Utils StandardResponse[T] structured success/error representation -> consuming Strategy feature"
    )

    # 1. Stage 1: Enums, policies & manifest
    fr_str_001()
    fr_str_002()
    fr_str_003()
    fr_str_035()
    fr_str_008()

    # 2. Stage 2: References, configuration, requests & context
    fr_str_004()
    fr_str_005()
    fr_str_006()
    fr_str_007()
    fr_str_009()
    fr_str_010()
    fr_str_011()
    fr_str_012()
    fr_str_013()

    # 3. Stage 3: Outputs, results & evidence
    fr_str_014()
    fr_str_015()
    fr_str_016()
    fr_str_017()
    fr_str_038()
    fr_str_039()


if __name__ == "__main__":
    main()
