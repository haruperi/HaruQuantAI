"""Executable deterministic Strategy replay-manifest example."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_replay_manifest,
    create_strategy_replay_manifest_value,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)

_HASH = "d" * 64
_REQUEST = "req-77777777-7777-4777-8777-777777777777"
_WORKFLOW = "wf-88888888-8888-4888-8888-888888888888"
_CORRELATION = "cor-99999999-9999-4999-8999-999999999999"


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


def _binding() -> tuple[Any, Any]:
    """Build the validated reference and configuration pair."""
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    manifest = create_strategy_manifest(
        strategy_id="usage-replay-strategy",
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
        provenance_refs=("usage-approval-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=1_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = create_validated_strategy_config(
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        config_schema_version="v1",
        normalized_parameters={"fast_ma_period": 20},
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=_REQUEST,
    )
    return ref, config


def fr_str_027() -> None:
    """FR-STR-027: Stage 1 — Replay manifest contract creation."""
    _header("Stage 1: Replay Manifest Contract Creation (FR-STR-027)")
    ref, config = _binding()
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=datetime.now(UTC),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=13,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=8_192,
    )
    res = create_strategy_replay_manifest(ref, config, context, _HASH, _HASH)
    if res.data is None:
        raise RuntimeError("Replay manifest creation failed")
    result = create_strategy_replay_manifest_value(**res.data.model_dump())
    print(_format_result(result))
    print(
        f"Data -> strategy_id='{result.strategy_id}', manifest_hash='{result.manifest_hash[:16]}...'"
    )


def fr_str_029() -> None:
    """FR-STR-029: Stage 2 & 3 — Deterministic replay manifest creation."""
    _header("Stage 2 & 3: Deterministic Replay Manifest Creation (FR-STR-029)")
    ref, config = _binding()
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=datetime.now(UTC),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=13,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=8_192,
    )
    result = create_strategy_replay_manifest(
        ref, config, context, data_checksum=_HASH, indicator_manifest_hash=_HASH
    )
    print(_format_result(result))
    if result.data is None:
        raise RuntimeError("Replay manifest generation failed")
    print(
        f"Data -> status='{result.status}', manifest_hash='{result.data.manifest_hash[:16]}...'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-05 — replay/ — Deterministic Replay Manifests\n\n"
        "Purpose: Create immutable replay manifests for exact deterministic evaluation replay.\n\n"
        "Module flow:\n"
        "-> Validated reference & config + context\n"
        "-> Input hash binding & manifest construction\n"
        "-> StrategyReplayManifest"
    )

    # 1. Stage 1: Replay manifest contract creation
    fr_str_027()

    # 2. Stage 2 & 3: Deterministic replay manifest creation
    fr_str_029()


if __name__ == "__main__":
    main()
