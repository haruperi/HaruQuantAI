"""Unit tests for immutable Simulation journal events."""

from datetime import UTC, datetime

import pytest
from app.services.simulator.journal import JournalEvent
from app.utils import canonical_digest, canonical_json


def test_journal_event_rejects_secret_payload() -> None:
    """Reject sensitive-key evidence at the journal boundary."""
    with pytest.raises(ValueError, match="sensitive"):
        JournalEvent(
            run_id="run-test",
            sequence=0,
            occurred_at=datetime(2025, 1, 1, tzinfo=UTC),
            event_type="run_started",
            payload={"access_token": "unsafe"},
            previous_hash="0" * 64,
            event_hash="1" * 64,
            correlation_id="cor-test",
            causation_id=None,
        )


def test_stream_journal_events_success_and_errors(tmp_path: object) -> None:
    """Validate streaming playback over finalized journals and cursor validation error paths."""
    from pathlib import Path

    import anyio
    from app.services.simulator.errors import SimulationError
    from app.services.simulator.journal import (
        replay_journal,
        stream_journal_events,
    )

    async def _runner() -> None:
        journal_dir = Path(str(tmp_path))
        file_path = journal_dir / "test.jsonl"
        now = datetime(2025, 1, 1, tzinfo=UTC)

        event0 = JournalEvent(
            run_id="run-pb-1",
            sequence=0,
            occurred_at=now,
            event_type="run_started",
            payload={
                "config_hash": "a" * 64,
                "data_hash": "b" * 64,
                "engine_version": "v1",
            },
            previous_hash="0" * 64,
            event_hash="0" * 64,
            correlation_id="cor-1",
            causation_id=None,
        )
        dump0 = event0.model_dump(mode="python", exclude={"event_hash"}, warnings=False)
        hash0 = canonical_digest(dump0)
        event0 = event0.model_copy(update={"event_hash": hash0})

        event1 = JournalEvent(
            run_id="run-pb-1",
            sequence=1,
            occurred_at=now,
            event_type="order_submitted",
            payload={"order_id": "ord-1"},
            previous_hash=hash0,
            event_hash="0" * 64,
            correlation_id="cor-1",
            causation_id=None,
        )
        dump1 = event1.model_dump(mode="python", exclude={"event_hash"}, warnings=False)
        hash1 = canonical_digest(dump1)
        event1 = event1.model_copy(update={"event_hash": hash1})

        line0 = canonical_json(event0.model_dump(mode="python", warnings=False))
        line1 = canonical_json(event1.model_dump(mode="python", warnings=False))
        file_path.write_text(f"{line0}\n{line1}\n", encoding="utf-8")

        # Test playback streaming
        events = [
            ev
            async for ev in stream_journal_events(
                file_path, "run-pb-1", resume_after=-1
            )
        ]
        assert len(events) == 2
        assert events[0].event_type == "run_started"
        assert events[1].event_type == "order_submitted"

        # Test resume_after cursor
        resumed = [
            ev
            async for ev in stream_journal_events(file_path, "run-pb-1", resume_after=0)
        ]
        assert len(resumed) == 1
        assert resumed[0].sequence == 1

        # Test invalid resume_after cursors
        with pytest.raises(SimulationError, match="cursor is invalid"):
            [
                ev
                async for ev in stream_journal_events(
                    file_path, "run-pb-1", resume_after=-2
                )
            ]

        with pytest.raises(SimulationError, match="exceeds the journal"):
            [
                ev
                async for ev in stream_journal_events(
                    file_path, "run-pb-1", resume_after=10
                )
            ]

        # Test wrong run_id
        with pytest.raises(SimulationError, match=r"Journal event is invalid|broken"):
            [
                ev
                async for ev in stream_journal_events(
                    file_path, "run-wrong", resume_after=-1
                )
            ]

        # Test empty journal error
        empty_file = journal_dir / "empty.jsonl"
        empty_file.write_text("", encoding="utf-8")
        with pytest.raises(SimulationError, match="Journal is empty"):
            [
                ev
                async for ev in stream_journal_events(
                    empty_file, "run-empty", resume_after=-1
                )
            ]
        with pytest.raises(SimulationError, match="Journal is empty"):
            replay_journal(empty_file, lambda s, _e: s)

        # Test non-existent file error
        bad_path = journal_dir / "nonexistent.jsonl"
        with pytest.raises(SimulationError, match="cannot be read"):
            [
                ev
                async for ev in stream_journal_events(
                    bad_path, "run-none", resume_after=-1
                )
            ]
        with pytest.raises(SimulationError, match="cannot be read"):
            replay_journal(bad_path, lambda s, _e: s)

    anyio.run(_runner)
