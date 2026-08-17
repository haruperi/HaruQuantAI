"""Unit evidence for the safe file-backed session activity stream."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from app.services.api.workstation.trading import activity


class _Request:
    """Minimal disconnect-aware request double."""

    def __init__(self) -> None:
        self._calls = 0

    async def is_disconnected(self) -> bool:
        """Disconnect after one bounded file scan."""
        self._calls += 1
        return self._calls > 1


def test_activity_stream_filters_to_session_and_does_not_persist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only matching redacted file lines leave the stream boundary."""
    log_path = tmp_path / "app.log"
    log_path.write_text(
        "INFO session-one started\nERROR session-two credential=[REDACTED]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(activity, "_active_log_path", lambda: log_path)

    async def _no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(activity.asyncio, "sleep", _no_sleep)

    frames = asyncio.run(
        _collect(
            activity._events(_Request(), session_id="session-one", request_id="req-1")
        )
    )

    assert len(frames) == 1
    assert b"session-one started" in frames[0]
    assert b"session-two" not in frames[0]


async def _collect(events: AsyncIterator[bytes]) -> list[bytes]:
    """Collect a bounded async iterator for assertion."""
    return [frame async for frame in events]
