"""Executable Simulation state usage example.

Demonstrates simulation state store idempotency recording and migration definitions.
"""

import sys
import tempfile
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator import get_simulation_migrations
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_sim_041() -> None:
    """Demonstrate FR-SIM-041.

    Responsibility:
        The system shall depend on persistence only through an injected
        runtime-checkable `Protocol` exposing `append_journal`, `flush_journal`,
        `finalize_journal`, `load_run`, and `record_idempotency`, and shall declare its
        own migrations using the Data-owned `MigrationStep` contract. Simulation imports
        no Data storage, connection, or locking module, no `sqlite3`, and executes no
        schema statement of its own.
    """
    _header(
        "Demonstrate FR-SIM-041. Responsibility: The system shall depend on persistence only through an injected runtime-checkable `Protocol` exposing `append_journal`, `flush_journal`, `finalize_journal`, `load_run`, and `record_idempotency`, and shall declare its own migrations using the Data-owned `MigrationStep` contract. Simulation imports no Data storage, connection, or locking module, no `sqlite3`, and executes no schema statement of its own."
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store = SqliteSimulationStateStore(
            tmp_path / "simulation.db", tmp_path / "artifacts"
        )
        store.record_idempotency("req-usage", "a" * 64, "run-usage", "started")
        run_info = store.load_run("req-usage")
        print("Persisted idempotency row:", run_info)
        migrations = get_simulation_migrations()
        print(
            "Simulation migration manifest:",
            tuple(
                step.model_dump(mode="python", warnings=False) for step in migrations
            ),
        )


def main() -> None:
    """Run Simulator state usage example."""
    fr_sim_041()


if __name__ == "__main__":
    main()
