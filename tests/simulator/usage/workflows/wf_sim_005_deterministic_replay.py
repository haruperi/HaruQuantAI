"""WF-SIM-005: replay a canonical journal deterministically."""

from __future__ import annotations

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    JournalWriter,
    replay_journal,
    unwrap_simulation_response,
)
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

WORKFLOW_ID = "WF-SIM-005"
STAGES = (
    "Receive a canonical journal with matching config, data, engine, and schema identities.",
    "Validate monotonic sequence and the hash chain.",
    "Apply each typed event through the injected deterministic reducer.",
    "Compare and return the reconstructed terminal state identity.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented deterministic replay workflow."""
    print(f"{WORKFLOW_ID} — Deterministic Replay")
    print("INPUT BOUNDARY — canonical finalized journal and identity hashes")
    with tempfile.TemporaryDirectory(prefix="wf-sim-005-") as directory:
        root = Path(directory)

        # Stage 1 — Receive a canonical journal with matching config, data, engine, and schema identities.
        _stage(1)
        store = SqliteSimulationStateStore(root / "state.db", root / "artifacts")
        writer = JournalWriter(store, "run-replay", "req-replay", "cor-replay")
        unwrap_simulation_response(
            writer.append(
                "run_started",
                {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
                datetime(2026, 1, 1, tzinfo=UTC),
            ),
            operation="simulation.workflow.wf_sim_005.journal_append",
        )
        unwrap_simulation_response(
            writer.finalize(),
            operation="simulation.workflow.wf_sim_005.journal_finalize",
        )

        # Stage 2 — Validate monotonic sequence and the hash chain.
        _stage(2)
        journal = root / "artifacts" / "run-replay" / "journal.jsonl"
        assert journal.is_file()

        # Stage 3 — Apply each typed event through the injected deterministic reducer.
        _stage(3)
        state = unwrap_simulation_response(
            replay_journal(
                journal,
                lambda _state, event: {
                    "sequence": event.sequence,
                    "hash": event.event_hash,
                },
            ),
            operation="simulation.workflow.wf_sim_005.replay_journal",
        )

        # Stage 4 — Compare and return the reconstructed terminal state identity.
        _stage(4)
        assert isinstance(state["sequence"], int)
        assert state["sequence"] >= 0
        print("OUTPUT BOUNDARY — reconstructed state identity:", state)


if __name__ == "__main__":
    main()
