"""Focused branch coverage for durable Simulation playback sessions."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.services.simulator.errors import SimulationError
from app.services.simulator.state import sessions


def _row(**overrides: object) -> dict[str, object]:
    """Return one valid persisted playback-session row."""
    value: dict[str, object] = {
        "session_id": "session-one",
        "run_id": "run-one",
        "status": "active",
        "cursor": -1,
        "created_at": "2026-01-01T00:00:00.000000Z",
        "expires_at": "2027-01-01T00:00:00.000000Z",
    }
    value.update(overrides)
    return value


def test_session_create_validates_and_normalizes_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Creation rejects bad identity, missing runs, and persistence failures."""
    with pytest.raises(SimulationError, match="Session identity is invalid"):
        sessions.create_simulation_session(" run-one", request_id="request")
    monkeypatch.setattr(sessions, "read_completed_run_record", lambda *_: None)
    with pytest.raises(SimulationError) as missing:
        sessions.create_simulation_session("run-one", request_id="request")
    assert missing.value.code == "SIM_SESSION_NOT_FOUND"
    monkeypatch.setattr(
        sessions,
        "read_completed_run_record",
        lambda *_: (_ for _ in ()).throw(ValueError("broken")),
    )
    with pytest.raises(SimulationError) as failed_lookup:
        sessions.create_simulation_session("run-one", request_id="request")
    assert failed_lookup.value.code == "SIM_PERSISTENCE_FAILED"


def test_session_create_returns_immutable_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A completed run creates one immutable active session projection."""
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        sessions, "read_completed_run_record", lambda *_: {"run_id": "run-one"}
    )
    monkeypatch.setattr(
        sessions,
        "create_session_record",
        lambda _store, value, **_kwargs: captured.update(value),
    )
    result = sessions.create_simulation_session("run-one", request_id="request")
    assert result["status"] == "active"
    assert captured["cursor"] == -1
    with pytest.raises(TypeError):
        result["status"] = "completed"  # type: ignore[index]


def test_session_read_materializes_expiry_and_rejects_bad_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reads return absence, materialize expiry, and normalize malformed rows."""
    with pytest.raises(SimulationError, match="Session identity is invalid"):
        sessions.read_simulation_session("")
    monkeypatch.setattr(sessions, "read_session_record", lambda *_: None)
    assert sessions.read_simulation_session("session-one") is None
    expired = datetime.now(UTC) - timedelta(seconds=1)
    monkeypatch.setattr(
        sessions,
        "read_session_record",
        lambda *_: _row(expires_at=sessions.format_utc_timestamp(expired)),
    )
    assert sessions.read_simulation_session("session-one")["status"] == "expired"
    monkeypatch.setattr(sessions, "read_session_record", lambda *_: {})
    with pytest.raises(SimulationError) as malformed:
        sessions.read_simulation_session("session-one")
    assert malformed.value.code == "SIM_PERSISTENCE_FAILED"


def test_journal_path_validates_dependencies(tmp_path: Path) -> None:
    """Playback journal paths remain inside an explicit artifact root."""
    with pytest.raises(SimulationError, match="dependencies are unavailable"):
        sessions._journal_path(object(), "run-one")
    path = sessions._journal_path(SimpleNamespace(artifact_root=tmp_path), "run-one")
    assert path == (tmp_path / "run-one" / "journal.jsonl").resolve()


def test_stream_rejects_missing_expired_and_cursor_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Streaming fails closed for missing, expired, and unpersisted cursor state."""

    async def collect() -> list[object]:
        return [
            event
            async for event in sessions.stream_simulation_session_frames(
                "session-one",
                resume_after=None,
                dependencies=SimpleNamespace(artifact_root=tmp_path),
            )
        ]

    monkeypatch.setattr(sessions, "read_simulation_session", lambda _: None)
    with pytest.raises(SimulationError) as missing:
        asyncio.run(collect())
    assert missing.value.code == "SIM_SESSION_NOT_FOUND"

    monkeypatch.setattr(
        sessions,
        "read_simulation_session",
        lambda _: _row(status="expired"),
    )
    monkeypatch.setattr(
        sessions, "update_session_record", lambda *_args, **_kwargs: True
    )
    with pytest.raises(SimulationError) as expired:
        asyncio.run(collect())
    assert expired.value.code == "SIM_SESSION_EXPIRED"

    async def events(*_args: object, **_kwargs: object):
        yield SimpleNamespace(sequence=0)

    monkeypatch.setattr(sessions, "read_simulation_session", lambda _: _row())
    monkeypatch.setattr(sessions, "stream_journal_events", events)
    monkeypatch.setattr(
        sessions, "update_session_record", lambda *_args, **_kwargs: False
    )
    with pytest.raises(SimulationError) as cursor:
        asyncio.run(collect())
    assert cursor.value.code == "SIM_PERSISTENCE_FAILED"


def test_stream_completes_and_persists_final_cursor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Streaming advances each cursor and records terminal completion."""
    updates: list[tuple[str, int]] = []

    async def events(*_args: object, **_kwargs: object):
        yield SimpleNamespace(sequence=0)
        yield SimpleNamespace(sequence=1)

    def update(*_args: object, status: str, cursor: int, **_kwargs: object) -> bool:
        updates.append((status, cursor))
        return True

    monkeypatch.setattr(sessions, "read_simulation_session", lambda _: _row())
    monkeypatch.setattr(sessions, "stream_journal_events", events)
    monkeypatch.setattr(sessions, "update_session_record", update)

    async def collect() -> list[object]:
        return [
            event
            async for event in sessions.stream_simulation_session_frames(
                "session-one",
                resume_after=-1,
                dependencies=SimpleNamespace(artifact_root=tmp_path),
            )
        ]

    assert len(asyncio.run(collect())) == 2
    assert updates == [("active", 0), ("active", 1), ("completed", 1)]
