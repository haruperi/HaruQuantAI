"""Unit tests for hash-chained Simulation journal writing."""
# ruff: noqa: INP001

from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.journal import JournalWriter
from app.services.simulator.journal.writer import (
    JOURNAL_FORMAT,
    JOURNAL_FSYNC_INTERVAL,
    JOURNAL_SIDECAR_MODE,
)
from app.services.simulator.state import SIMULATION_MIGRATIONS
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def _writer(tmp_path: Path) -> JournalWriter:
    """Build one isolated journal writer."""
    store = SqliteSimulationStateStore(tmp_path / "state.db", tmp_path / "artifacts")
    return JournalWriter(store, "run-test", "req-test", "cor-test")


def test_append_fails_closed_on_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Surface durable-write failure before advancing writer state."""
    writer = _writer(tmp_path)

    def fail_append(run_id: str, canonical_event: str) -> None:
        """Raise a controlled persistence failure."""
        del run_id, canonical_event
        raise SimulationError("SIM_PERSISTENCE_FAILED", "Injected failure")

    monkeypatch.setattr(writer._store, "append_journal", fail_append)
    with pytest.raises(SimulationError) as captured:
        writer.append(
            "run_started",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            datetime(2025, 1, 1, tzinfo=UTC),
        )
    assert captured.value.code == "SIM_PERSISTENCE_FAILED"


def test_finalize_is_atomic(tmp_path: Path) -> None:
    """Finalize to the canonical filename with a stable checksum."""
    writer = _writer(tmp_path)
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    checksum = writer.finalize()
    assert len(checksum) == 64
    assert (tmp_path / "artifacts" / "run-test" / "journal.jsonl").is_file()
    assert not (tmp_path / "artifacts" / "run-test" / "journal.jsonl.partial").exists()


def test_journal_durability_settings_are_declared() -> None:
    """Expose the documented journal format and group-commit settings."""
    assert JOURNAL_FORMAT == "jsonl-v1"
    assert JOURNAL_FSYNC_INTERVAL == 100
    assert JOURNAL_SIDECAR_MODE == "disabled"


def test_append_group_commits_on_the_fsync_interval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Flush exactly once per `JOURNAL_FSYNC_INTERVAL` appended events."""
    writer = _writer(tmp_path)
    flushes: list[str] = []
    original = writer._store.flush_journal

    def counting_flush(run_id: str) -> None:
        """Record each durability boundary."""
        flushes.append(run_id)
        original(run_id)

    monkeypatch.setattr(writer._store, "flush_journal", counting_flush)
    for index in range(JOURNAL_FSYNC_INTERVAL):
        writer.append(
            "run_started" if index == 0 else "tick_observed",
            {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
            datetime(2025, 1, 1, tzinfo=UTC),
        )
    assert len(flushes) == 1
    writer.append(
        "tick_observed",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert len(flushes) == 1
    writer.finalize()
    assert len(flushes) == 2


def test_no_sqlite_journal_sidecar_is_created(tmp_path: Path) -> None:
    """Keep the canonical journal JSONL-only, per the Phase 1 exclusion."""
    writer = _writer(tmp_path)
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    writer.finalize()
    statements = " ".join(
        statement
        for migration in SIMULATION_MIGRATIONS
        for statement in migration.statements
    )
    assert "simulation_journal" not in statements
