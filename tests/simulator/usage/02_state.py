"""Executable Simulation state usage example.

Demonstrates simulation state store idempotency recording and migration definitions.
"""

import sys
import tempfile
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator.state import SIMULATION_MIGRATIONS, SimulationStateStore
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def example_state() -> None:
    """Demonstrate state store operations and migrations."""
    print("=" * 80)
    print("Simulator Example 2: State Store Port and Migrations")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        store: SimulationStateStore = SqliteSimulationStateStore(
            tmp_path / "simulation.db", tmp_path / "artifacts"
        )
        store.record_idempotency("req-usage", "a" * 64, "run-usage", "started")
        run_info = store.load_run("req-usage")
        print(f"Recorded run info loaded: {run_info is not None}")
        print(f"First simulation migration domain: {SIMULATION_MIGRATIONS[0].domain}")


def main() -> None:
    """Run Simulator state usage example."""
    example_state()


if __name__ == "__main__":
    main()
