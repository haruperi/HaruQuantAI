"""Executable bounded Strategy-local checkpoint example."""

import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import hashlib
import json
from datetime import UTC, datetime

from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_data_migrations,
)
from app.services.strategy import (
    commit_strategy_runtime_state,
    create_strategy_checkpoint,
    create_strategy_checkpoint_value,
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    initialize_strategy_runtime_state,
    list_strategy_checkpoints,
    load_strategy_runtime_state,
    validate_strategy_checkpoint,
)
from tests.strategy.unit.test_models import make_auth

_HASH = "d" * 64
_REQUEST = "req-77777777-7777-4777-8777-777777777777"
_WORKFLOW = "wf-88888888-8888-4888-8888-888888888888"
_CORRELATION = "cor-99999999-9999-4999-8999-999999999999"
_AUTHORIZATION = "checkpoint-auth"


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
        policy_version="usage-v1",
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = create_validated_strategy_config(
        strategy_id="usage-replay-strategy",
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"fast_ma_period": 20, "slow_ma_period": 50},
        config_hash=_HASH,
        policy_version="usage-v1",
        request_id=_REQUEST,
    )
    return ref, config


def _auth() -> Any:
    """Build caller context authorized for checkpoint operations."""
    return make_auth(checkpoint=True)


def fr_str_028() -> None:
    """FR-STR-028: Stage 1 — Checkpoint contract creation."""
    _header("Stage 1: Checkpoint Contract Creation (FR-STR-028)")
    ref, config = _binding()
    state = {"bars_seen": 25, "last_signal": "BUY"}
    state_bytes = json.dumps(state, sort_keys=True).encode("utf-8")
    result = create_strategy_checkpoint_value(
        checkpoint_id="chk-00000000-0000-4000-8000-000000000001",
        strategy_id=ref.manifest.strategy_id,
        strategy_version=ref.manifest.strategy_version,
        config_hash=config.config_hash,
        state=state,
        state_checksum=hashlib.sha256(state_bytes).hexdigest(),
        authorization_ref=_AUTHORIZATION,
        created_at=datetime.now(UTC),
        request_id=_REQUEST,
        payload_bytes=len(state_bytes),
        redacted_paths=(),
    )
    print(_format_result(result))
    print(
        f"Data -> checkpoint_id='{result.checkpoint_id}', payload_bytes={result.payload_bytes}"
    )


def fr_str_030() -> None:
    """FR-STR-030: Stage 2 — Checkpoint creation and persistence."""
    _header("Stage 2: Checkpoint Creation & Persistence (FR-STR-030)")
    ref, config = _binding()
    auth = _auth()
    result = create_strategy_checkpoint(
        ref, config, {"bars_seen": 30}, _AUTHORIZATION, auth
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', checkpoint_id='{result.data.checkpoint_id if result.data else None}'"
    )


def fr_str_031() -> None:
    """FR-STR-031: Stage 3 — Read-only checkpoint validation."""
    _header("Stage 3: Read-Only Checkpoint Validation (FR-STR-031)")
    ref, config = _binding()
    auth = _auth()
    created = create_strategy_checkpoint(
        ref, config, {"bars_seen": 31}, _AUTHORIZATION, auth
    )
    if created.data is None:
        raise RuntimeError("Checkpoint creation failed")
    result = validate_strategy_checkpoint(created.data, ref, config, auth)
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', restored_state={dict(result.data) if result.data else None}"
    )


def _demo_checkpoints_persistence() -> None:
    """FR-STR-059 to 062: Stage 4 — Runtime state initialization & optimistic commit."""
    _header("Stage 4: Runtime State Operations & Checkpoint Listing (FR-STR-059..062)")
    config_id = f"usage-replay-strategy@1.0.0#{_HASH}"
    init_res = initialize_strategy_runtime_state(
        config_id, request_id=_REQUEST, correlation_id=_CORRELATION
    )
    print(_format_result(init_res))
    print(
        f"Data -> status='{init_res.status}', evaluation_status='{init_res.data.get('evaluation_status') if init_res.data else None}'"
    )

    loaded_res = load_strategy_runtime_state(config_id)
    print(_format_result(loaded_res))

    commit_res = commit_strategy_runtime_state(
        config_id,
        expected_state_version=0,
        evaluation_status="ready",
        bars_processed=10,
        local_state={"bars_seen": 35},
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    print(_format_result(commit_res))
    print(
        f"Data -> status='{commit_res.status}', new_version={commit_res.data.get('state_version') if commit_res.data else None}"
    )

    checkpoints_res = list_strategy_checkpoints(config_id)
    print(_format_result(checkpoints_res))
    print(
        f"Data -> checkpoints count={len(checkpoints_res.data) if checkpoints_res.data else 0}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-06 — checkpoints/ — Bounded Persisted Local State\n\n"
        "Purpose: Create and validate bounded strategy-local checkpoints for stateful execution.\n\n"
        "Module flow:\n"
        "-> Candidate local state + validated ref & config\n"
        "-> Bounded size check & persistence\n"
        "-> Validated StrategyCheckpoint"
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

            # 1. Stage 1: Checkpoint contract creation
            fr_str_028()

            # 2. Stage 2: Checkpoint creation & persistence
            fr_str_030()

            # 3. Stage 3: Read-only checkpoint validation
            fr_str_031()

            # 4. Stage 4: Runtime state & Checkpoint listing
            _demo_checkpoints_persistence()


if __name__ == "__main__":
    main()
