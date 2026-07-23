"""Unit tests for the Simulation-owned persistence boundary."""
# ruff: noqa: INP001

import ast
from pathlib import Path
from typing import Protocol, runtime_checkable

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.state import SIMULATION_MIGRATIONS, SimulationStateStore
from app.utils import canonical_json
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

_PACKAGE_ROOT = Path(__file__).resolve().parents[3] / "app" / "services" / "simulator"


def _imported_modules() -> set[str]:
    """Collect every module name imported anywhere in the Simulation package.

    Returns:
        Set of fully qualified imported module names.
    """
    names: set[str] = set()
    for path in _PACKAGE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                names.add(node.module)
    return names


def test_simulation_imports_no_data_storage_module() -> None:
    """Keep Simulation independent of Data storage internals."""
    assert not any(
        name.startswith("app.services.data.persistence") for name in _imported_modules()
    )
    assert SIMULATION_MIGRATIONS[0].domain == "simulation"


def test_simulation_imports_no_sqlite_module() -> None:
    """Prove Simulation owns no database connection or schema execution."""
    assert "sqlite3" not in _imported_modules()


def test_state_store_is_a_protocol_only() -> None:
    """Prove the persistence boundary is an injected port, not a class."""
    assert issubclass(type(SimulationStateStore), type(Protocol))
    assert isinstance(runtime_checkable(SimulationStateStore), object)
    with pytest.raises(TypeError):
        SimulationStateStore()  # type: ignore[misc]


def test_caller_implementation_satisfies_the_port(tmp_path: Path) -> None:
    """Prove a caller-supplied implementation structurally satisfies the port."""
    store = SqliteSimulationStateStore(tmp_path / "state.db", tmp_path / "artifacts")
    assert isinstance(store, SimulationStateStore)


def test_state_store_records_and_loads_idempotency(tmp_path: Path) -> None:
    """Persist and load immutable completed run evidence."""
    store = SqliteSimulationStateStore(tmp_path / "state.db", tmp_path / "artifacts")
    store.record_idempotency(
        "req-test",
        "a" * 64,
        "run-test",
        "completed",
        {"status": "completed"},
    )
    loaded = store.load_run("req-test")
    assert loaded is not None
    assert loaded["result_payload"] == {"status": "completed"}


def test_state_store_rejects_idempotency_conflict(tmp_path: Path) -> None:
    """Reject one request identifier bound to different material."""
    store = SqliteSimulationStateStore(tmp_path / "state.db", tmp_path / "artifacts")
    store.record_idempotency("req-test", "a" * 64, "run-test", "started")
    with pytest.raises(SimulationError) as captured:
        store.record_idempotency("req-test", "b" * 64, "run-other", "started")
    assert captured.value.code == "SIM_RUN_ID_CONFLICT"


def test_state_store_finalizes_journal_atomically(tmp_path: Path) -> None:
    """Publish only the completed canonical journal name."""
    store = SqliteSimulationStateStore(tmp_path / "state.db", tmp_path / "artifacts")
    event = canonical_json({"sequence": 0, "event_hash": "f" * 64})
    store.append_journal("run-test", event)
    checksum = store.finalize_journal("run-test", 1, "f" * 64)
    assert len(checksum) == 64
    assert (tmp_path / "artifacts" / "run-test" / "journal.jsonl").is_file()
    assert not (tmp_path / "artifacts" / "run-test" / "journal.jsonl.tmp").exists()
