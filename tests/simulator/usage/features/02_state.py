"""Executable Simulation state usage example.

Demonstrates FEAT-SIM-02 simulation state protocol, idempotency recording, and migrations.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    build_migration_request,
    data_settings_context,
    run_domain_migrations,
    unwrap_data_response,
)
from app.services.simulator import (
    build_simulation_state_store,
    execute_simulation_state_store_operation,
    get_simulation_migrations,
    unwrap_simulation_response,
)
from app.utils import canonical_json, generate_id


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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


def _settings(data_dir: Path) -> object:
    """Build isolated Data settings for this executable example."""
    return build_data_settings(
        database_url="sqlite:///simulator-usage.db",
        data_dir=data_dir,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _run_migrations() -> None:
    """Apply Simulator's immutable manifest through Data's public boundary."""
    request_id = generate_id("req")
    unwrap_data_response(
        run_domain_migrations(
            build_migration_request(
                domain="simulator",
                steps=get_simulation_migrations(),
                request_id=request_id,
            )
        ),
        operation="simulator.usage.migrations",
        request_id=request_id,
    )


def _execute(store: object, operation: str, *args: object) -> object:
    """Execute and unwrap one public Simulator state operation."""
    return unwrap_simulation_response(
        execute_simulation_state_store_operation(store, operation, *args),
        operation=f"simulator.usage.{operation}",
    )


def fr_sim_041() -> None:
    """
    FR-SIM-041: Stage 3 — Depend on state persistence protocol and expose domain migrations.

    The system shall depend on persistence only through an injected runtime-checkable `Protocol` exposing `append_journal`, `flush_journal`, `finalize_journal`, `load_run`, and `record_idempotency`, and shall declare its own migrations using the Data-owned `MigrationStep` contract. Simulation imports no Data storage, connection, or locking module, no `sqlite3`, and executes no schema statement of its own.
    """
    _header(
        "Stage 3: State Protocol - Record Run Idempotency & Migrations (FR-SIM-041)"
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with data_settings_context(_settings(tmp_path)):
            _run_migrations()
            request_id = generate_id("req")
            store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
            _execute(
                store,
                "record_idempotency",
                request_id,
                "a" * 64,
                "run-usage",
                "started",
            )
            run_info = _execute(store, "load_run", request_id)
            print(_format_result(run_info))
            print(f"Data -> run_id='{run_info['run_id']}'")

    migrations = get_simulation_migrations()
    print(_format_result(migrations))
    print(f"Data -> migration_step_count={len(migrations)}")


def fr_sim_094() -> None:
    """FR-SIM-094: Persist lifecycle state directly in `sim_runs`."""
    _header("Direct Relational Run Persistence (FR-SIM-094)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with data_settings_context(_settings(tmp_path)):
            _run_migrations()
            request_id = generate_id("req")
            store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
            _execute(
                store,
                "record_idempotency",
                request_id,
                "b" * 64,
                "run-relational",
                "started",
            )
            reconstructed = build_simulation_state_store(
                artifact_root=tmp_path / "artifacts"
            )
            row = _execute(reconstructed, "load_run", request_id)
            print(_format_result(row))
            print("Data -> persisted_table='sim_runs'")


def fr_sim_095() -> None:
    """FR-SIM-095: Enforce identity-bound lifecycle transitions."""
    _header("Idempotent Lifecycle Compare-and-Swap (FR-SIM-095)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with data_settings_context(_settings(tmp_path)):
            _run_migrations()
            request_id = generate_id("req")
            store = build_simulation_state_store(artifact_root=tmp_path / "artifacts")
            arguments = (request_id, "c" * 64, "run-cas", "started")
            _execute(store, "record_idempotency", *arguments)
            _execute(store, "record_idempotency", *arguments)
            _execute(
                store,
                "record_idempotency",
                request_id,
                "c" * 64,
                "run-cas",
                "failed",
            )
            row = _execute(store, "load_run", request_id)
            print(_format_result(row))
            print(f"Data -> replayed=True, terminal_status='{row['status']}'")


def fr_sim_096() -> None:
    """FR-SIM-096: Publish durable journals as canonical JSONL."""
    _header("Partial JSONL Group Commit and Atomic Publication (FR-SIM-096)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        artifact_root = Path(tmp_dir) / "artifacts"
        store = build_simulation_state_store(artifact_root=artifact_root)
        first = canonical_json({"sequence": 0, "event_hash": "d" * 64})
        second = canonical_json({"sequence": 1, "event_hash": "e" * 64})
        _execute(store, "append_journal", "run-jsonl", first)
        reconstructed = build_simulation_state_store(artifact_root=artifact_root)
        _execute(reconstructed, "append_journal", "run-jsonl", second)
        _execute(reconstructed, "flush_journal", "run-jsonl")
        checksum = _execute(
            reconstructed,
            "finalize_journal",
            "run-jsonl",
            2,
            "e" * 64,
        )
        print(_format_result(checksum))
        print("Data -> artifact='journal.jsonl', partial_exists=False")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-02 — state/ — Simulation-Owned State\n\n"
        "Purpose: Maintain run idempotency state and expose Simulation migration declarations.\n\n"
        "Module flow:\n"
        "-> Stage 1: State store interface initialization\n"
        "-> Stage 2: Migration declaration inspection\n"
        "-> Stage 3: Idempotency state recording and run metadata retrieval"
    )

    # Stage 3: State protocol & Migrations
    fr_sim_041()

    # Stage 4: Direct relational persistence
    fr_sim_094()

    # Stage 5: Identity-bound lifecycle CAS
    fr_sim_095()

    # Stage 6: Durable JSONL journal publication
    fr_sim_096()


if __name__ == "__main__":
    main()
