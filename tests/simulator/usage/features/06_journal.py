"""Executable Simulation journal usage example.

Demonstrates FEAT-SIM-06 creating, writing, finalizing, replaying, and resolving idempotent event journals.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    create_simulation_handle,
    execute_simulation_handle_operation,
    get_simulation_value_field,
    replay_journal,
    resolve_idempotent_run,
    unwrap_simulation_response,
)
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

NOW = datetime(2025, 1, 1, tzinfo=UTC)


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
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.journal")


def fr_sim_013() -> None:
    """
    FR-SIM-013: Stage 3 — Expose immutable versioned journal event structure.

    The system shall expose an immutable versioned journal event containing run, sequence, UTC time, event type, redacted payload, previous hash, event hash, correlation, and causation identities.
    """
    _header("Stage 3: Event Contract - Expose Journal Event (FR-SIM-013)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        resp = execute_simulation_handle_operation(
            create_simulation_handle(
                "JournalWriter", store, "run-usage", "req-usage", "cor-usage"
            ),
            "append",
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        event = _value(resp)
        print(_format_result(resp))
        print(
            f"Data -> event_type='{get_simulation_value_field(event, 'event_type')}', sequence={get_simulation_value_field(event, 'sequence')}"
        )


def fr_sim_014() -> None:
    """
    FR-SIM-014: Stage 3 — Append event with hash-chain integrity verification.

    The system shall append one event with the next monotonic sequence and hash-chain link before the corresponding governed state transition is considered durable.
    """
    _header("Stage 3: Hash Chaining - Append Hash-Chained Event (FR-SIM-014)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        resp = execute_simulation_handle_operation(
            create_simulation_handle(
                "JournalWriter", store, "run-usage", "req-usage", "cor-usage"
            ),
            "append",
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        event = _value(resp)
        print(_format_result(resp))
        print(f"Data -> event_hash='{get_simulation_value_field(event, 'event_hash')}'")


def fr_sim_015() -> None:
    """
    FR-SIM-015: Stage 3 — Finalize completed journal atomically and return SHA-256 checksum.

    The system shall finalize a completed journal atomically and return its checksum without publishing incomplete temporary artifacts.
    """
    _header("Stage 3: Finalization - Finalize Event Journal (FR-SIM-015)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        writer = create_simulation_handle(
            "JournalWriter", store, "run-usage", "req-usage", "cor-usage"
        )
        execute_simulation_handle_operation(
            writer,
            "append",
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        resp = execute_simulation_handle_operation(writer, "finalize")
        checksum = _value(resp)
        print(_format_result(resp))
        print(f"Data -> journal_checksum='{checksum}'")


def fr_sim_016() -> None:
    """
    FR-SIM-016: Stage 3 — Replay journal event stream through deterministic reducer.

    The system shall validate schema, sequence, hash chain, config/data/engine identities, and invariants while reconstructing state through an injected deterministic reducer.
    """
    _header("Stage 3: Journal Replay - Replay Event Journal (FR-SIM-016)")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        writer = create_simulation_handle(
            "JournalWriter", store, "run-usage", "req-usage", "cor-usage"
        )
        execute_simulation_handle_operation(
            writer,
            "append",
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        execute_simulation_handle_operation(writer, "finalize")
        path = tmp_path / "artifacts" / "run-usage" / "journal.jsonl"
        resp = replay_journal(
            path,
            lambda _state, event: {
                "sequence": get_simulation_value_field(event, "sequence")
            },
        )
        state = _value(resp)
        print(_format_result(resp))
        print(
            f"Data -> replayed_sequence={state.get('sequence') if isinstance(state, dict) else state}"
        )


def fr_sim_017() -> None:
    """
    FR-SIM-017: Stage 2 — Resolve idempotent run or reject hash mismatches.

    The system shall return the existing completed run for the same request ID and hash, and reject the same request ID with a different hash.
    """
    _header("Stage 2: Idempotency Resolution - Resolve Idempotent Run (FR-SIM-017)")
    resp = resolve_idempotent_run(
        "req-usage",
        "a" * 64,
        lambda request_id: {
            "request_hash": "a" * 64,
            "run_id": request_id.replace("req", "run"),
            "status": "completed",
        },
    )
    run_id = _value(resp)
    print(_format_result(resp))
    print(f"Data -> resolved_run_id='{run_id}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-06 — journal/ — Immutable Journal and Replay\n\n"
        "Purpose: Append immutable hash-chained event journals, finalize completed runs atomically, replay journals, and resolve run idempotency.\n\n"
        "Module flow:\n"
        "-> Stage 1: JournalWriter and state store initialization\n"
        "-> Stage 2: Monotonic sequence tracking and idempotency hash checking\n"
        "-> Stage 3: Event append, hash-chain calculation, journal finalization, and state replay"
    )

    # Stage 2: Idempotency resolution
    fr_sim_017()

    # Stage 3: Event appending, finalization, & replay
    fr_sim_013()
    fr_sim_014()
    fr_sim_015()
    fr_sim_016()


if __name__ == "__main__":
    main()
