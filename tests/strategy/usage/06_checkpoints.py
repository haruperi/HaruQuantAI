"""Executable bounded Strategy-local checkpoint example."""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyCheckpoint,
    StrategyEnvironment,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
    create_strategy_checkpoint,
    validate_strategy_checkpoint,
)
from app.utils import AuthContext

_UNAVAILABLE = 3
_HASH = "d" * 64
_REQUEST = "req-77777777-7777-4777-8777-777777777777"
_WORKFLOW = "wf-88888888-8888-4888-8888-888888888888"
_CORRELATION = "cor-99999999-9999-4999-8999-999999999999"
_AUTHORIZATION = "usage-checkpoint-auth"


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
    """Persist, restore, and reject bounded Strategy-local state.

    Returns:
        ``0`` on success, or ``3`` when the configured Strategy store is closed.
    """
    print("\nSTRATEGY LOCAL CHECKPOINTS")
    print("=" * 88)
    print("Contract:", StrategyCheckpoint.__name__)
    if os.getenv("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        print(
            "Set RUN_STRATEGY_STATEFUL_USAGE=1 to persist through the "
            "configured Data-owned Strategy store."
        )
        return _UNAVAILABLE

    ref, config = _binding()
    auth = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="usage-principal",
        principal_type="USER",
        roles=("strategy-admin",),
        permissions=("strategy:checkpoint",),
        scopes=(_AUTHORIZATION,),
        tenant_or_environment="research",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        issued_at=datetime.now(UTC),
    )
    created = create_strategy_checkpoint(
        ref, config, {"bars_seen": 42}, _AUTHORIZATION, auth
    )
    if created.data is None:
        print("Checkpoint creation failed:", created.error)
        return _UNAVAILABLE
    checkpoint = created.data
    print("Checkpoint ID:", checkpoint.checkpoint_id)
    print("State checksum:", checkpoint.state_checksum)
    print("Payload bytes:", checkpoint.payload_bytes)

    restored = validate_strategy_checkpoint(checkpoint, ref, config, auth)
    if restored.data is None:
        print("Checkpoint validation failed:", restored.error)
        return _UNAVAILABLE
    print("Restored local state:", dict(restored.data))

    tampered = checkpoint.model_copy(update={"state_checksum": "e" * 64})
    rejected = validate_strategy_checkpoint(tampered, ref, config, auth)
    print("Tampered checkpoint status:", rejected.status)
    if rejected.error is not None:
        print("Tampered checkpoint code:", rejected.error.code)
    print("\nCheckpoints carry strategy-local state only, never official state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
