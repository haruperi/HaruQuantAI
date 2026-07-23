"""Executable deterministic Strategy replay-manifest example."""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyReplayManifest,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
    create_strategy_replay_manifest,
)

_HASH = "d" * 64
_REQUEST = "req-77777777-7777-4777-8777-777777777777"
_WORKFLOW = "wf-88888888-8888-4888-8888-888888888888"
_CORRELATION = "cor-99999999-9999-4999-8999-999999999999"


def _binding() -> tuple[ValidatedStrategyRef, ValidatedStrategyConfig]:
    """Build the validated reference and configuration pair.

    Returns:
        The exact validated reference and configuration.
    """
    policy = StrategyValidationPolicy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    manifest = StrategyManifest(
        strategy_id="usage-replay-strategy",
        strategy_version="1.0.0",
        module_path="app.services.strategy.evaluators.naive_ma_trend",
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:H1",),
        required_indicators=("sma",),
        timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
        permitted_environments=(StrategyEnvironment.RESEARCH,),
        source_hash=_HASH,
        artifact_hash=_HASH,
        dependency_hash=_HASH,
        provenance_refs=("usage-approval-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=1_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=StrategyEnvironment.RESEARCH,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = ValidatedStrategyConfig(
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        config_schema_version="v1",
        normalized_parameters={"fast_ma_period": 20},
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=_REQUEST,
    )
    return ref, config


def main() -> int:
    """Create a deterministic replay manifest from exact validated identities.

    Returns:
        ``0`` once manifest creation and hash stability are demonstrated.
    """
    print("\nSTRATEGY REPLAY MANIFEST")
    print("=" * 88)
    print("Contract:", StrategyReplayManifest.__name__)
    ref, config = _binding()
    context = StrategyExecutionContext(
        environment=StrategyEnvironment.RESEARCH,
        decision_timestamp=datetime.now(UTC),
        timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
        seed=13,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=8_192,
    )
    outcome = create_strategy_replay_manifest(
        ref, config, context, data_checksum=_HASH, indicator_manifest_hash=_HASH
    )
    if outcome.data is None:
        print("Replay manifest failed:", outcome.error)
        return 1
    replay = outcome.data
    print("Schema:", replay.schema_id)
    print("Strategy:", replay.strategy_id, replay.strategy_version)
    print("Config hash:", replay.config_hash)
    print("Manifest hash:", replay.manifest_hash)

    repeat = create_strategy_replay_manifest(
        ref, config, context, data_checksum=_HASH, indicator_manifest_hash=_HASH
    )
    same = repeat.data is not None and repeat.data.manifest_hash == replay.manifest_hash
    print("Identical inputs reproduce the identical hash:", same)

    drifted = create_strategy_replay_manifest(
        ref, config, context, data_checksum="a" * 64, indicator_manifest_hash=_HASH
    )
    changed = (
        drifted.data is not None
        and drifted.data.manifest_hash != replay.manifest_hash
    )
    print("Changed data checksum changes the manifest hash:", changed)
    print("\nReplay-manifest construction is pure and persists nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
