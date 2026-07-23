"""Executable examples of every package-root Strategy contract."""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyConfig,
    StrategyDecision,
    StrategyEnvironment,
    StrategyError,
    StrategyEvent,
    StrategyExecutionContext,
    StrategyExecutionResult,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyMutationResult,
    StrategyOutcome,
    StrategyParameterUpdateRequest,
    StrategyRef,
    StrategyRegistrationRequest,
    StrategySignal,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)

_HASH = "a" * 64
_REQUEST = "strategy-usage-contracts"
_CORRELATION = "strategy-usage-contracts-correlation"
_WORKFLOW = "strategy-usage-contracts-workflow"


def main() -> int:
    """Construct and display every immutable Strategy contract.

    Returns:
        ``0`` once every contract has been constructed and printed.
    """
    now = datetime.now(UTC)
    print("\nSTRATEGY CONTRACTS")
    print("=" * 88)

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
    print("\n-- Evaluation values --")
    print("Event type:", event.event_type)
    print("Proposal action:", decision.action, decision.symbol, decision.side)
    print("Neutral decision emits no intent:", neutral.symbol is None)
    print("Signal:", signal.signal_name, "active:", signal.active)

    error = StrategyError(
        code="STRATEGY_INVALID_CONFIG",
        message="usage example structured failure",
        details={"field": "fast_ma_period"},
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    success_outcome = StrategyOutcome[StrategyConfig](status="success", data=config)
    error_outcome = StrategyOutcome[StrategyConfig](status="error", error=error)
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
    result = StrategyExecutionResult(
        decisions=(neutral,),
        intents=(),
        diagnostics=None,
        replay_manifest=None,
        local_state_update=None,
        result_hash=_HASH,
    )
    print("\n-- Structured outcomes --")
    print("Success outcome:", success_outcome.status)
    print("Error outcome:", error_outcome.status, error.code)
    print("Mutation:", mutation.status, mutation.record_ref)
    print("Execution result intents:", len(result.intents))
    print("\nEvery contract above is immutable and carries no executable value.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
