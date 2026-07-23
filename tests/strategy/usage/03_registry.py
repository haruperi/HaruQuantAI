"""Executable governed Strategy registry lifecycle example."""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.strategy import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategyParameterUpdateRequest,
    StrategyRef,
    StrategyRegistrationRequest,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    list_strategy_versions,
    register_strategy_version,
    update_strategy_parameters,
    validate_strategy_config,
    validate_strategy_ref,
)
from app.utils import AuthContext

_UNAVAILABLE = 3
_HASH = "c" * 64
_REQUEST = "req-44444444-4444-4444-8444-444444444444"
_WORKFLOW = "wf-55555555-5555-4555-8555-555555555555"
_CORRELATION = "cor-66666666-6666-4666-8666-666666666666"
_STRATEGY = "usage-naive-ma-trend"


def _policy() -> StrategyValidationPolicy:
    """Build the explicit host-owned validation policy.

    Returns:
        A complete immutable validation policy.
    """
    return StrategyValidationPolicy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )


def _manifest() -> StrategyManifest:
    """Build the immutable registration manifest.

    Returns:
        A complete immutable strategy manifest.
    """
    return StrategyManifest(
        strategy_id=_STRATEGY,
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
        supported_hooks=(),
        requires_account_snapshot=False,
        max_batch_records=1_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )


def main() -> int:  # noqa: PLR0911
    """Register, resolve, validate, and re-version one immutable strategy.

    Returns:
        ``0`` on success, or ``3`` when the configured Strategy store is closed.
    """
    print("\nGOVERNED STRATEGY REGISTRY LIFECYCLE")
    print("=" * 88)
    if os.getenv("RUN_STRATEGY_STATEFUL_USAGE") != "1":
        print(
            "Set RUN_STRATEGY_STATEFUL_USAGE=1 to open the configured "
            "Data-owned Strategy store."
        )
        return _UNAVAILABLE

    now = datetime.now(UTC)
    policy = _policy()
    manifest = _manifest()
    auth = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="usage-principal",
        principal_type="USER",
        roles=("strategy-admin",),
        permissions=("strategy:register", "strategy:update"),
        scopes=("usage-approval-1",),
        tenant_or_environment="research",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        issued_at=now,
    )
    registration = StrategyRegistrationRequest(
        command_id=f"usage-register-{now.isoformat()}",
        strategy_id=manifest.strategy_id,
        strategy_version=manifest.strategy_version,
        module_path=manifest.module_path,
        manifest=manifest,
        config_schema=manifest.config_schema,
        source_hash=manifest.source_hash,
        artifact_hash=manifest.artifact_hash,
        dependency_hash=manifest.dependency_hash,
        provenance_refs=manifest.provenance_refs,
        principal_id=auth.principal_id,
        reason="usage example registration",
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        authorization_ref="usage-approval-1",
        requested_at=now,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )

    print("\n-- Register immutable version (WF-STR-008) --")
    registered = register_strategy_version(registration, auth, policy)
    if registered.data is None:
        print("Registration failed:", registered.error)
        return _UNAVAILABLE
    print("Mutation status:", registered.data.status)
    print("Record ref:", registered.data.record_ref)

    print("\n-- Resolve exactly one approved version (WF-STR-001) --")
    reference = StrategyRef(
        strategy_id=_STRATEGY,
        exact_version="1.0.0",
        environment=StrategyEnvironment.RESEARCH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    resolved = validate_strategy_ref(reference, policy)
    if resolved.data is None:
        print("Reference validation failed:", resolved.error)
        return _UNAVAILABLE
    print("Resolved:", resolved.data.manifest.strategy_id, resolved.data.environment)

    print("\n-- Validate declarative configuration --")
    config = StrategyConfig(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        request_id=_REQUEST,
    )
    validated = validate_strategy_config(resolved.data, config)
    if validated.data is None:
        print("Configuration validation failed:", validated.error)
        return _UNAVAILABLE
    print("Canonical config hash:", validated.data.config_hash)

    print("\n-- Record a new immutable parameter version --")
    update = StrategyParameterUpdateRequest(
        command_id=f"usage-config-{now.isoformat()}",
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        parameters=config.parameters,
        principal_id=auth.principal_id,
        reason="usage example parameter update",
        ref=reference,
        config=config,
        authorization_ref="usage-approval-1",
        requested_at=now,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    updated = update_strategy_parameters(update, auth)
    if updated.data is None:
        print("Parameter update failed:", updated.error)
        return _UNAVAILABLE
    print("Mutation status:", updated.data.status)
    print("New configuration hash:", updated.data.record_hash)

    print("\n-- Deterministic registry listing --")
    listed = list_strategy_versions()
    if listed.data is None:
        print("Registry unavailable:", listed.error)
        return _UNAVAILABLE
    for entry in listed.data:
        print(
            " ",
            entry.manifest.strategy_id,
            entry.manifest.strategy_version,
            entry.lifecycle_status.value,
        )
    print("\nRegistration proves technical validity only, never Risk eligibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
