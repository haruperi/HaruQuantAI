"""Executable Simulation journal usage example.

Demonstrates creating, writing, finalizing, and replaying Simulation event journals.
"""

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator import (
    JournalEvent,
    JournalWriter,
    replay_journal,
    resolve_idempotent_run,
)
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

NOW = datetime(2025, 1, 1, tzinfo=UTC)


def fr_sim_013() -> None:
    """Demonstrate FR-SIM-013.

    Responsibility:
        The system shall expose an immutable versioned journal event containing run,
        sequence, UTC time, event type, redacted payload, previous hash, event hash,
        correlation, and causation identities.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        event: JournalEvent = JournalWriter(
            store, "run-usage", "req-usage", "cor-usage"
        ).append(
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        print(f"JournalEvent sequence: {event.sequence}")


def fr_sim_014() -> None:
    """Demonstrate FR-SIM-014.

    Responsibility:
        The system shall append one event with the next monotonic sequence and
        hash-chain link before the corresponding governed state transition is considered
        durable.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        event = JournalWriter(store, "run-usage", "req-usage", "cor-usage").append(
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        print(f"Appended event hash: {event.event_hash[:16]}...")


def fr_sim_015() -> None:
    """Demonstrate FR-SIM-015.

    Responsibility:
        The system shall finalize a completed journal atomically and return its checksum
        without publishing incomplete temporary artifacts.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        writer = JournalWriter(store, "run-usage", "req-usage", "cor-usage")
        writer.append(
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        print(f"Finalized checksum: {writer.finalize()[:16]}...")


def fr_sim_016() -> None:
    """Demonstrate FR-SIM-016.

    Responsibility:
        The system shall validate schema, sequence, hash chain, config/data/engine
        identities, and invariants while reconstructing state through an injected
        deterministic reducer.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        writer = JournalWriter(store, "run-usage", "req-usage", "cor-usage")
        writer.append(
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        writer.finalize()
        path = tmp_path / "artifacts" / "run-usage" / "journal.jsonl"
        state = replay_journal(path, lambda _state, event: {"sequence": event.sequence})
        print(f"Replayed sequence: {state['sequence']}")


def fr_sim_017() -> None:
    """Demonstrate FR-SIM-017.

    Responsibility:
        The system shall return the existing completed run for the same request ID and
        hash, and reject the same request ID with a different hash.
    """
    run_id = resolve_idempotent_run(
        "req-usage",
        "a" * 64,
        lambda request_id: {
            "request_hash": "a" * 64,
            "run_id": request_id.replace("req", "run"),
            "status": "completed",
        },
    )
    print(f"Resolved run ID: {run_id}")


def example_journal() -> None:
    """Demonstrate journal writer, finalization, replay, and idempotency."""
    print("=" * 80)
    print("Simulator Example 6: Event Journaling and Replay")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "state.db", tmp_path / "artifacts"
        )
        writer = JournalWriter(store, "run-usage", "req-usage", "cor-usage")

        # 1. Append journal event
        event = writer.append(
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            NOW,
        )
        print(
            f"Appended JournalEvent type: {event.event_type}, "
            f"sequence: {event.sequence}"
        )

        # 2. Finalize journal
        digest = writer.finalize()
        print(f"Finalized journal digest SHA256: {digest[:16]}...")

        # 3. Replay journal
        path = tmp_path / "artifacts" / "run-usage" / "journal.jsonl"
        replayed = replay_journal(path, lambda _state, evt: {"sequence": evt.sequence})
        print(f"Replayed journal state sequence: {replayed['sequence']}")

    # 4. Resolve idempotent run
    run_id = resolve_idempotent_run(
        "req-usage",
        "a" * 64,
        lambda request_id: {
            "request_hash": "a" * 64,
            "run_id": request_id.replace("req", "run"),
            "status": "completed",
        },
    )
    print(f"Resolved idempotent run ID: {run_id}")


def main() -> None:
    """Run Simulator journal usage example."""
    fr_sim_013()
    fr_sim_014()
    fr_sim_015()
    fr_sim_016()
    fr_sim_017()


if __name__ == "__main__":
    main()
