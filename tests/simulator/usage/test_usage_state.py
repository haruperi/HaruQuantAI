"""Runnable usage example for the Simulation state port."""

from pathlib import Path

from app.services.simulator.state import SIMULATION_MIGRATIONS, SimulationStateStore
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def test_usage_state_store_port(tmp_path: Path) -> None:
    """Inject a caller-supplied store and record one idempotent run."""
    store: SimulationStateStore = SqliteSimulationStateStore(
        tmp_path / "simulation.db", tmp_path / "artifacts"
    )
    store.record_idempotency("req-usage", "a" * 64, "run-usage", "started")
    assert store.load_run("req-usage") is not None
    assert SIMULATION_MIGRATIONS[0].domain == "simulation"
