"""Executable governed Strategy registry lifecycle example."""

import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from datetime import UTC, datetime

from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_data_migrations,
)
from app.services.strategy import (
    bootstrap_builtin_strategies,
    build_development_strategy_validation_policy,
    create_strategy_config,
    create_strategy_manifest,
    create_strategy_parameter_update_request,
    create_strategy_ref,
    create_strategy_registration_request,
    create_strategy_validation_policy,
    get_strategy_definition,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    list_builtin_strategy_descriptors,
    list_strategy_configs,
    list_strategy_definitions,
    list_strategy_versions,
    register_strategy_version,
    resolve_strategy_config,
    update_strategy_parameters,
    validate_strategy_config,
    validate_strategy_ref,
)
from tests.strategy.unit.test_models import make_auth

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
        permitted_environments=("RESEARCH",),
        source_hash=_HASH,
        artifact_hash=_HASH,
        dependency_hash=_HASH,
        provenance_refs=("build-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=10000,
        max_diagnostic_bytes=8192,
        max_checkpoint_bytes=8192,
        max_local_state_bytes=4096,
        decision_timeout_seconds=5.0,
    )


def fr_str_020() -> None:
    """Demonstrate FR-STR-020: Strategy version registration."""
    _header("Demonstrating FR-STR-020: Strategy version registration")
    m = _manifest()
    req = create_strategy_registration_request(
        command_id="cmd-reg-001",
        strategy_id=m.strategy_id,
        strategy_version=m.strategy_version,
        module_path=m.module_path,
        manifest=m,
        config_schema=m.config_schema,
        source_hash=m.source_hash,
        artifact_hash=m.artifact_hash,
        dependency_hash=m.dependency_hash,
        provenance_refs=m.provenance_refs,
        principal_id="caller-reg-001",
        reason="registration usage demonstration",
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        authorization_ref="bootstrap-approval",
        requested_at=datetime.now(UTC),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    auth = make_auth(permissions=("strategy:register",))
    result = register_strategy_version(req, auth, _policy())
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', mutation_id='{result.data.mutation_id if result.data else None}'"
    )


def fr_str_021() -> None:
    """Demonstrate FR-STR-021: Parameter update creation."""
    _header("Demonstrating FR-STR-021: Parameter update creation")
    config = create_strategy_config(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"fast_ma_period": 10, "slow_ma_period": 30},
        request_id=_REQUEST,
    )
    ref = create_strategy_ref(
        strategy_id=_STRATEGY,
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    req = create_strategy_parameter_update_request(
        command_id="cmd-param-001",
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        parameters={"fast_ma_period": 10, "slow_ma_period": 30},
        principal_id="caller-param-001",
        reason="update usage demonstration",
        ref=ref,
        config=config,
        authorization_ref="bootstrap-approval",
        requested_at=datetime.now(UTC),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    auth = make_auth(permissions=("strategy:update",))
    result = update_strategy_parameters(req, auth)
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', mutation_id='{result.data.mutation_id if result.data else None}'"
    )


def fr_str_022() -> None:
    """Demonstrate FR-STR-022: Version listing."""
    _header("Demonstrating FR-STR-022: Version listing")
    result = list_strategy_versions()
    print(_format_result(result))
    print(f"Data -> count={len(result.data) if result.data else 0}")


def fr_str_023() -> None:
    """Demonstrate FR-STR-023: Strategy reference validation."""
    _header("Demonstrating FR-STR-023: Strategy reference validation")
    ref = create_strategy_ref(
        strategy_id=_STRATEGY,
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    result = validate_strategy_ref(ref, _policy())
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', strategy_id='{result.data.manifest.strategy_id if result.data else None}'"
    )


def fr_str_024() -> None:
    """Demonstrate FR-STR-024: Configuration validation."""
    _header("Demonstrating FR-STR-024: Configuration validation")
    ref = create_strategy_ref(
        strategy_id=_STRATEGY,
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    resolved = validate_strategy_ref(ref, _policy())
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
    if result.data:
        cfg_id = f"{result.data.strategy_id}@{result.data.strategy_version}#{result.data.config_hash}"
        resolved_cfg = resolve_strategy_config(cfg_id)
        print(_format_result(resolved_cfg))
    print(
        f"Data -> status='{result.status}', config_hash='{result.data.config_hash[:16] if result.data else None}...'"
    )


def _demo_catalogue_and_bootstrap() -> None:
    """Demonstrate FR-STR-054 through FR-STR-058: Catalogue and Bootstrap operations."""
    _header("Demonstrating FR-STR-054 to 058: Catalogue & Bootstrap Operations")
    descriptors_res = list_builtin_strategy_descriptors()
    print(_format_result(descriptors_res))
    print(
        f"Data -> built-in descriptors count={len(descriptors_res.data) if descriptors_res.data else 0}"
    )

    auth = make_auth(permissions=("strategy:register", "strategy:update"))
    bootstrap_res = bootstrap_builtin_strategies(auth, _policy())
    print(_format_result(bootstrap_res))
    print(
        f"Data -> bootstrap_status='{bootstrap_res.data.get('bootstrap_status') if bootstrap_res.data else None}'"
    )

    defs_res = list_strategy_definitions()
    print(_format_result(defs_res))
    print(
        f"Data -> strategy definitions count={len(defs_res.data) if defs_res.data else 0}"
    )

    def_res = get_strategy_definition("naive-ma-trend")
    print(_format_result(def_res))

    configs_res = list_strategy_configs("naive-ma-trend", "1.0.0")
    print(_format_result(configs_res))
    print(
        f"Data -> strategy configs count={len(configs_res.data) if configs_res.data else 0}"
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

            # 4. Stage 4: Catalogue & Bootstrap operations (FR-STR-054..058)
            _demo_catalogue_and_bootstrap()


if __name__ == "__main__":
    main()
