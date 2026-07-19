"""Unit tests for Simulation journal replay and idempotency."""
# ruff: noqa: INP001

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.journal import (
    JournalEvent,
    JournalWriter,
    replay_journal,
    resolve_idempotent_run,
)
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def _journal(tmp_path: Path) -> Path:
    """Create one finalized valid journal."""
    store = SqliteSimulationStateStore(tmp_path / "state.db", tmp_path / "artifacts")
    writer = JournalWriter(store, "run-test", "req-test", "cor-test")
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    writer.finalize()
    return tmp_path / "artifacts" / "run-test" / "journal.jsonl"


def _reducer(state: object, event: JournalEvent) -> dict[str, object]:
    """Count replayed events deterministically."""
    del state
    return {"events": event.sequence + 1}


def test_replay_rejects_hash_break(tmp_path: Path) -> None:
    """Reject journal bytes whose hash chain was modified."""
    path = _journal(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8").replace('"v1"', '"v2"', 1), encoding="utf-8"
    )
    with pytest.raises(SimulationError) as captured:
        replay_journal(path, _reducer)
    assert captured.value.code == "SIM_CHECKPOINT_INCOMPATIBLE"


def test_replay_reconstructs_state(tmp_path: Path) -> None:
    """Reduce a valid journal deterministically."""
    assert replay_journal(_journal(tmp_path), _reducer)["events"] == 1


def test_request_id_conflict_fails_closed() -> None:
    """Reject reuse of a request identifier with different material."""
    with pytest.raises(SimulationError) as captured:
        resolve_idempotent_run(
            "req-test",
            "a" * 64,
            lambda request_id: {"request_hash": "b" * 64, "run_id": request_id},
        )
    assert captured.value.code == "SIM_RUN_ID_CONFLICT"
