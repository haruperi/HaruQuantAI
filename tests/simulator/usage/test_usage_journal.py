"""Runnable usage examples for Simulation journals."""

from datetime import UTC, datetime
from pathlib import Path

from app.services.simulator.journal import (
    JournalEvent,
    JournalWriter,
    replay_journal,
    resolve_idempotent_run,
)
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def _writer(tmp_path: Path) -> JournalWriter:
    """Build a usage journal writer."""
    return JournalWriter(
        SqliteSimulationStateStore(tmp_path / "state.db", tmp_path / "artifacts"),
        "run-usage",
        "req-usage",
        "cor-usage",
    )


def test_usage_journal_event(tmp_path: Path) -> None:
    """Receive the immutable event created by the writer."""
    event = _writer(tmp_path).append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert isinstance(event, JournalEvent)


def test_usage_journal_append(tmp_path: Path) -> None:
    """Append the next canonical event through JournalWriter."""
    event = _writer(tmp_path).append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert event.sequence == 0


def test_usage_journal_finalize(tmp_path: Path) -> None:
    """Atomically finalize a non-empty journal."""
    writer = _writer(tmp_path)
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert len(writer.finalize()) == 64


def test_usage_replay_journal(tmp_path: Path) -> None:
    """Replay a completed journal through a deterministic reducer."""
    writer = _writer(tmp_path)
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        datetime(2025, 1, 1, tzinfo=UTC),
    )
    writer.finalize()
    path = tmp_path / "artifacts" / "run-usage" / "journal.jsonl"
    result = replay_journal(path, lambda _state, event: {"sequence": event.sequence})
    assert result["sequence"] == 0


def test_usage_resolve_idempotent_run() -> None:
    """Resolve an existing completed matching request."""
    result = resolve_idempotent_run(
        "req-usage",
        "a" * 64,
        lambda request_id: {
            "request_hash": "a" * 64,
            "run_id": request_id.replace("req", "run"),
            "status": "completed",
        },
    )
    assert result == "run-usage"
