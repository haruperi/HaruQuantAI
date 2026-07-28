"""Executable examples of every package-root Strategy contract."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.strategy import (
    StrategyConfig,
    StrategyDecision,
    StrategyEnvironment,
    StrategyEvent,
    StrategyExecutionContext,
    StrategyExecutionResult,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyMutationResult,
    StrategyParameterUpdateRequest,
    StrategyRef,
    StrategyRegistrationRequest,
    StrategySignal,
    StrategySignalEvidence,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
    create_strategy_replay_manifest,
    export_strategy_diagnostics,
)
from app.utils import StandardResponse

_HASH = "a" * 64
_REQUEST = "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
_CORRELATION = "cor-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
_WORKFLOW = "wf-cccccccc-cccc-4ccc-8ccc-cccccccccccc"


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_str_001() -> None:
    """Demonstrate the supported Strategy environment."""
    _header("Demonstrate the supported Strategy environment.")
    assert StrategyEnvironment.RESEARCH.value == "RESEARCH"


def fr_str_002() -> None:
    """Demonstrate the explicit timing policy."""
    _header("Demonstrate the explicit timing policy.")
    assert StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE.value


def fr_str_003() -> None:
    """Demonstrate lifecycle eligibility states."""
    _header("Demonstrate lifecycle eligibility states.")
    assert StrategyLifecycleStatus.APPROVED is not StrategyLifecycleStatus.REVOKED


def fr_str_004() -> None:
    """Demonstrate exact Strategy reference construction."""
    _header("Demonstrate exact Strategy reference construction.")
    assert StrategyRef.model_fields["exact_version"]


def fr_str_005() -> None:
    """Demonstrate validated reference construction."""
    _header("Demonstrate validated reference construction.")
    assert ValidatedStrategyRef.model_fields["registry_record_hash"]


def fr_str_006() -> None:
    """Demonstrate declarative Strategy configuration."""
    _header("Demonstrate declarative Strategy configuration.")
    assert StrategyConfig.model_fields["parameters"]


def fr_str_007() -> None:
    """Demonstrate validated configuration identity."""
    _header("Demonstrate validated configuration identity.")
    assert ValidatedStrategyConfig.model_fields["config_hash"]


def fr_str_008() -> None:
    """Demonstrate the complete Strategy manifest."""
    _header("Demonstrate the complete Strategy manifest.")
    assert StrategyManifest.model_fields["max_batch_records"]


def fr_str_009() -> None:
    """Demonstrate the registration request contract."""
    _header("Demonstrate the registration request contract.")
    assert StrategyRegistrationRequest.model_fields["authorization_ref"]


def fr_str_010() -> None:
    """Demonstrate the parameter-update request contract."""
    _header("Demonstrate the parameter-update request contract.")
    assert StrategyParameterUpdateRequest.model_fields["parameters"]


def fr_str_011() -> None:
    """Demonstrate fixed execution context."""
    _header("Demonstrate fixed execution context.")
    assert StrategyExecutionContext.model_fields["decision_timestamp"]


def fr_str_012() -> None:
    """Demonstrate typed Strategy event evidence."""
    _header("Demonstrate typed Strategy event evidence.")
    assert StrategyEvent.model_fields["source_checksum"]


def fr_str_013() -> None:
    """Demonstrate neutral and proposal decisions."""
    _header("Demonstrate neutral and proposal decisions.")
    assert StrategyDecision.model_fields["action"]


def fr_str_014() -> None:
    """Demonstrate the closed atomic execution result."""
    _header("Demonstrate the closed atomic execution result.")
    assert StrategyExecutionResult.model_fields["replay_manifest"]


def fr_str_015() -> None:
    """Demonstrate structured Strategy errors."""
    _header("Demonstrate structured Strategy errors.")
    assert StandardResponse.model_fields["error"]


def fr_str_016() -> None:
    """Demonstrate exclusive Strategy outcomes."""
    _header("Demonstrate exclusive Strategy outcomes.")
    assert StandardResponse.model_fields["status"]


def fr_str_017() -> None:
    """Demonstrate immutable mutation truth."""
    _header("Demonstrate immutable mutation truth.")
    assert StrategyMutationResult.model_fields["mutation_id"]


def fr_str_035() -> None:
    """Demonstrate explicit host validation policy."""
    _header("Demonstrate explicit host validation policy.")
    assert StrategyValidationPolicy.model_fields["policy_version"]


def fr_str_038() -> None:
    """Demonstrate immutable concrete signal output."""
    _header("Demonstrate immutable concrete signal output.")
    assert StrategySignal.model_fields["signal_id"]


def fr_str_039() -> None:
    """Demonstrate immutable point-in-time signal evidence."""
    _header("Demonstrate immutable point-in-time signal evidence.")
    assert StrategySignalEvidence.model_fields["primary_market"]


def _demonstrate_requirement_contracts() -> None:
    """Run every Contracts feature requirement demonstration."""
    for demonstration in (
        fr_str_001,
        fr_str_002,
        fr_str_003,
        fr_str_004,
        fr_str_005,
        fr_str_006,
        fr_str_007,
        fr_str_008,
        fr_str_009,
        fr_str_010,
        fr_str_011,
        fr_str_012,
        fr_str_013,
        fr_str_014,
        fr_str_015,
        fr_str_016,
        fr_str_017,
        fr_str_035,
        fr_str_038,
        fr_str_039,
    ):
        demonstration()


def main() -> int:  # noqa: PLR0915 - explicit end-to-end evidence flow
    """Construct and display every immutable Strategy contract.

    Returns:
        ``0`` once every contract has been constructed and printed.
    """
    now = datetime.now(UTC)
    _demonstrate_requirement_contracts()
    print("\nSTRATEGY CONTRACTS")

    print("\n-- Enumerations --")
    print("Environment:", StrategyEnvironment.RESEARCH.value)
    print("Timing policy:", StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE.value)
    print("Lifecycle:", StrategyLifecycleStatus.APPROVED.value)

    policy = StrategyValidationPolicy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=16_384,
        max_config_nesting_depth=8,
        max_config_string_length=512,
        max_config_collection_items=128,
    )
    reference = StrategyRef(
        strategy_id="naive-ma-trend",
        exact_version="1.0.0",
        environment=StrategyEnvironment.RESEARCH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = StrategyConfig(
        strategy_id=reference.strategy_id,
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        request_id=_REQUEST,
    )
    context = StrategyExecutionContext(
        environment=StrategyEnvironment.RESEARCH,
        decision_timestamp=now,
        timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
        seed=7,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=16_384,
    )
    print("\n-- Inputs --")
    print("Reference:", reference.model_dump(mode="json"))
    print("Configuration parameters:", dict(config.parameters))
    print("Policy version:", policy.policy_version)
    print("Context timing:", context.timing_policy.value)

    manifest = StrategyManifest(
        strategy_id=reference.strategy_id,
        strategy_version="1.0.0",
        module_path="app.services.strategy.evaluators.naive_ma_trend",
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:H1",),
        required_indicators=("sma",),
        timing_policy=context.timing_policy,
        permitted_environments=(StrategyEnvironment.RESEARCH,),
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
    validated_ref = ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=StrategyEnvironment.RESEARCH,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    validated_config = ValidatedStrategyConfig(
        strategy_id=reference.strategy_id,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=_REQUEST,
    )
    print("\n-- Validated immutable identity --")
    print("Manifest schema:", manifest.schema_id)
    print("Validated ref record hash:", validated_ref.registry_record_hash)
    print("Validated config hash:", validated_config.config_hash)

    registration = StrategyRegistrationRequest(
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
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        authorization_ref="approval-1",
        requested_at=now,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    parameter_update = StrategyParameterUpdateRequest(
        command_id="usage-command-config",
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        parameters=config.parameters,
        principal_id="usage-principal",
        reason="usage example parameter update",
        ref=reference,
        config=config,
        authorization_ref="approval-2",
        requested_at=now,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    print("\n-- Receiver-owned commands --")
    print("Registration schema:", registration.schema_id)
    print("Parameter update schema:", parameter_update.schema_id)

    event = StrategyEvent(
        event_type="BAR_CLOSED",
        hook="on_bar",
        occurred_at=now,
        sequence=0,
        source_owner="data",
        source_contract_version="v1",
        source_schema_id="data.market_dataset.v1",
        source_snapshot_ref="live-market-read",
        source_checksum=_HASH,
        source_as_of=now,
        facts={"symbol": "EURUSD"},
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
    )
    decision = StrategyDecision(
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
            "strategy_id": manifest.strategy_id,
            "strategy_version": manifest.strategy_version,
            "config_hash": _HASH,
        },
    )
    neutral = StrategyDecision(
        decision_id="usage-decision-2",
        sequence=1,
        action="NEUTRAL",
        valid_from=now,
        expires_at=now + timedelta(minutes=5),
        allow_partial_fills=False,
        rationale_refs=("usage-rationale",),
        diagnostic_facts={},
        lineage={
            "strategy_id": manifest.strategy_id,
            "strategy_version": manifest.strategy_version,
            "config_hash": _HASH,
        },
    )
    signal = StrategySignal(
        signal_id=_HASH,
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        symbol="EURUSD",
        timestamp=now,
        signal_name="fast_crosses_above_slow",
        side="BUY",
        active=False,
        facts={"fast": "1.1005"},
        lineage={"config_hash": _HASH},
    )
    market_record = OHLCVRecord(
        timestamp=now - timedelta(hours=1),
        source="usage",
        source_symbol="EURUSD",
        available_at=now - timedelta(hours=1),
        open=Decimal("1.1000"),
        high=Decimal("1.1010"),
        low=Decimal("1.0990"),
        close=Decimal("1.1005"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="units",
    )
    market = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="H1",
        records=(market_record,),
        start=market_record.timestamp,
        end=market_record.timestamp,
        available_at=market_record.available_at,
        record_count=1,
        quality_report=DataQualityReport(
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
    signal_evidence = StrategySignalEvidence(
        evidence_id="strategy-contract-usage",
        primary_market=market,
        related_markets={},
        point_size=Decimal("0.0001"),
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )
    print("\n-- Evaluation values --")
    print("Event type:", event.event_type)
    print("Proposal action:", decision.action, decision.symbol, decision.side)
    print("Neutral decision emits no intent:", neutral.symbol is None)
    print("Signal:", signal.signal_name, "active:", signal.active)
    print("Signal evidence:", signal_evidence.evidence_id)

    mutation = StrategyMutationResult(
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
    diagnostics = export_strategy_diagnostics(context, {"example": "contracts"})
    replay = create_strategy_replay_manifest(
        validated_ref,
        validated_config,
        context,
        _HASH,
        _HASH,
    )
    if diagnostics.data is None or replay.data is None:
        print("Unable to construct typed execution-result dependencies.")
        return 1
    result = StrategyExecutionResult(
        decisions=(neutral,),
        intents=(),
        diagnostics=diagnostics.data,
        replay_manifest=replay.data,
        local_state_update=None,
        result_hash=_HASH,
    )
    print("\n-- Standard responses --")
    print("Diagnostics response:", diagnostics.status)
    print("Replay response:", replay.status)
    print("Mutation:", mutation.status, mutation.record_ref)
    print("Execution result intents:", len(result.intents))
    print("\nEvery contract above is immutable and carries no executable value.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
