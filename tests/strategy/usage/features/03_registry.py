"""Executable governed Strategy registry lifecycle example."""

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_data_migrations,
)
from app.services.strategy import (
    build_development_strategy_validation_policy,
    create_strategy_config,
    create_strategy_manifest,
    create_strategy_parameter_update_request,
    create_strategy_ref,
    create_strategy_registration_request,
    create_strategy_validation_policy,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    list_strategy_versions,
    register_strategy_version,
    update_strategy_parameters,
    validate_strategy_config,
    validate_strategy_ref,
)
from app.utils import create_auth_context

_HASH = "c" * 64
_REQUEST = "req-44444444-4444-4444-8444-444444444444"
_WORKFLOW = "wf-55555555-5555-4555-8555-555555555555"
_CORRELATION = "cor-66666666-6666-4666-8666-666666666666"
_STRATEGY = "usage-naive-ma-trend"


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


def _policy() -> Any:
    """Build the explicit host-owned validation policy."""
    return create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )


def _manifest() -> Any:
    """Build the immutable registration manifest."""
    return create_strategy_manifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path="app.services.strategy.evaluators.naive_ma_trend",
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={
            "type": "object",
            "properties": {
                "fast_ma_period": {"type": "integer", "minimum": 1},
                "slow_ma_period": {"type": "integer", "minimum": 1},
            },
            "required": ("fast_ma_period", "slow_ma_period"),
            "additionalProperties": False,
        },
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


def fr_str_020() -> None:
    """FR-STR-020: Stage 1 — Immutable version registration."""
    _header("Stage 1: Register Immutable Version (FR-STR-020)")
    now = datetime.now(UTC)
    policy = _policy()
    manifest = _manifest()
    auth = create_auth_context(
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
    request = create_strategy_registration_request(
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
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        authorization_ref="usage-approval-1",
        requested_at=now,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    result = register_strategy_version(request, auth, policy)
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', record_ref='{result.data.record_ref if result.data else None}'"
    )


def fr_str_021() -> None:
    """FR-STR-021: Stage 2 — Record immutable parameter version."""
    _header("Stage 2: Record Parameter Version (FR-STR-021)")
    now = datetime.now(UTC)
    auth = create_auth_context(
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
    ref = create_strategy_ref(
        strategy_id=_STRATEGY,
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = create_strategy_config(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        request_id=_REQUEST,
    )
    update = create_strategy_parameter_update_request(
        command_id=f"usage-config-{now.isoformat()}",
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        parameters=config.parameters,
        principal_id=auth.principal_id,
        reason="usage example parameter update",
        ref=ref,
        config=config,
        authorization_ref="usage-approval-1",
        requested_at=now,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    result = update_strategy_parameters(update, auth)
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', record_hash='{result.data.record_hash[:16] if result.data else None}...'"
    )


def fr_str_022() -> None:
    """FR-STR-022: Stage 2 — Deterministic registry listing."""
    _header("Stage 2: Deterministic Registry Listing (FR-STR-022)")
    result = list_strategy_versions()
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', total_versions={len(result.data) if result.data else 0}"
    )


def fr_str_023() -> None:
    """FR-STR-023: Stage 3 — Resolve exact registry reference."""
    _header("Stage 3: Resolve Exact Strategy Reference (FR-STR-023)")
    policy = _policy()
    ref = create_strategy_ref(
        strategy_id=_STRATEGY,
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    result = validate_strategy_ref(ref, policy)
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', strategy_id='{result.data.manifest.strategy_id if result.data else None}'"
    )


def fr_str_024() -> None:
    """FR-STR-024: Stage 3 — Validate declarative configuration."""
    _header("Stage 3: Validate Configuration Identity (FR-STR-024)")
    policy = _policy()
    ref = create_strategy_ref(
        strategy_id=_STRATEGY,
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    resolved = validate_strategy_ref(ref, policy)
    if resolved.data is None:
        raise RuntimeError("Reference validation failed")
    config = create_strategy_config(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        request_id=_REQUEST,
    )
    result = validate_strategy_config(resolved.data, config)
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', config_hash='{result.data.config_hash[:16] if result.data else None}...'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-03 — registry/ — Immutable Registry and Configuration\n\n"
        "Purpose: Register immutable versions, resolve exactly one approved reference, and validate declarative configuration before execution.\n\n"
        "Module flow:\n"
        "-> Registration/Parameter update command\n"
        "-> Fail-closed validation & schema check\n"
        "-> Immutable registry record & canonical hash"
    )
    assert (
        build_development_strategy_validation_policy().policy_version
        == "strategy-development-v1"
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        settings = build_data_settings(
            database_url="sqlite:///strategy.sqlite3",
            data_dir=Path(tmp_dir),
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            run_data_migrations(_REQUEST)

            # 1. Stage 1: Registration of immutable strategy version
            fr_str_020()

            # 2. Stage 2: Parameter version update & registry listing
            fr_str_021()
            fr_str_022()

            # 3. Stage 3: Reference resolution & configuration validation
            fr_str_023()
            fr_str_024()


if __name__ == "__main__":
    main()
