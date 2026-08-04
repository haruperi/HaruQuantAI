"""Unit tests for validated Simulation journal playback."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.journal import JournalWriter, stream_journal_events

from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def _journal(tmp_path: Path) -> Path:
    """Create one finalized three-event journal."""
    store = SqliteSimulationStateStore(tmp_path / "state.db", tmp_path / "artifacts")
    writer = JournalWriter(store, "run-playback", "req-playback", "cor-playback")
    occurred_at = datetime(2026, 8, 4, tzinfo=UTC)
    writer.append(
        "run_started",
        {"config_hash": "a", "data_hash": "b", "engine_version": "v1"},
        occurred_at,
    )
    writer.append("order_accepted", {"order_id": "order-1"}, occurred_at)
    writer.append("run_completed", {"receipt_count": 1}, occurred_at)
    writer.finalize()
    return tmp_path / "artifacts" / "run-playback" / "journal.jsonl"


def test_stream_journal_events_resumes_after_cursor(tmp_path: Path) -> None:
    """Playback emits only validated events after the supplied sequence."""

    async def scenario() -> list[int]:
        return [
            event.sequence
            async for event in stream_journal_events(
                _journal(tmp_path),
                "run-playback",
                resume_after=0,
            )
        ]

    assert asyncio.run(scenario()) == [1, 2]


def test_stream_journal_events_validates_all_bytes_before_yield(tmp_path: Path) -> None:
    """A corrupt tail prevents publication of an otherwise valid first frame."""
    path = _journal(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            '"receipt_count":1', '"receipt_count":2'
        ),
        encoding="utf-8",
    )

    async def scenario() -> None:
        iterator = stream_journal_events(path, "run-playback", resume_after=-1)
        await anext(iterator)

    with pytest.raises(SimulationError) as captured:
        asyncio.run(scenario())
    assert captured.value.code == "SIM_CHECKPOINT_INCOMPATIBLE"


def test_stream_journal_events_rejects_cursor_beyond_tail(tmp_path: Path) -> None:
    """Resume cannot silently skip beyond authoritative journal history."""

    async def scenario() -> None:
        iterator = stream_journal_events(
            _journal(tmp_path),
            "run-playback",
            resume_after=99,
        )
        await anext(iterator)

    with pytest.raises(SimulationError) as captured:
        asyncio.run(scenario())
    assert captured.value.code == "SIM_PLAYBACK_CURSOR_INVALID"
