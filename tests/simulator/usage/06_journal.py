"""Executable Simulation journal usage example.

Demonstrates creating, writing, finalizing, and replaying Simulation event journals.
"""

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator.journal import (
    JournalWriter,
    replay_journal,
    resolve_idempotent_run,
)
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

NOW = datetime(2025, 1, 1, tzinfo=UTC)


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
            f"Appended JournalEvent type: {event.event_type}, sequence: {event.sequence}"
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
    example_journal()


if __name__ == "__main__":
    main()
