"""Tests for FEAT-DATA-SESSIONS (app/services/data/sessions.py)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.contracts.data import (
    InvalidSessionWindowError,
    SessionDefinition,
    SessionWindow,
)
from app.services.data.sessions import (
    SessionConfig,
    SessionServiceImpl,
    _parse_time_str,
)
from app.services.persistence.data import (
    DataPersistenceConfig,
    DataPersistenceServiceImpl,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseServiceImpl,
)


async def _setup_sessions(tmp_path: Path) -> SessionServiceImpl:
    db_file = tmp_path / "test_sessions.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = DataPersistenceServiceImpl(
        db, DataPersistenceConfig(preseed_defaults=True)
    )
    await persist.initialize_schema()
    return SessionServiceImpl(persist, SessionConfig())


def test_session_open_closed_hours(tmp_path: Path) -> None:
    """Verify session schedule window checks."""

    async def _test() -> None:
        svc = await _setup_sessions(tmp_path)
        session = SessionDefinition(
            name="NYSE RTH",
            timezone="America/New_York",
            windows=[
                SessionWindow(
                    day_of_week=0, open_time="09:30:00", close_time="16:00:00"
                )
            ],
            holidays=[],
        )

        # Monday 2026-06-01 10:00:00 NY time (14:00:00 UTC) -> IN SESSION
        in_sess_dt = datetime(2026, 6, 1, 14, 0, 0, tzinfo=UTC)
        assert svc.is_in_session(in_sess_dt, session) is True

        # Monday 2026-06-01 09:00:00 NY time (13:00:00 UTC) -> OUT OF SESSION
        pre_mkt_dt = datetime(2026, 6, 1, 13, 0, 0, tzinfo=UTC)
        assert svc.is_in_session(pre_mkt_dt, session) is False

        # Sunday 2026-05-31 (Weekend) -> OUT OF SESSION
        weekend_dt = datetime(2026, 5, 31, 15, 0, 0, tzinfo=UTC)
        assert svc.is_in_session(weekend_dt, session) is False

    asyncio.run(_test())


def test_holiday_exclusion(tmp_path: Path) -> None:
    """Verify holidays override active session windows."""

    async def _test() -> None:
        svc = await _setup_sessions(tmp_path)
        session = SessionDefinition(
            name="US Holiday Test",
            timezone="America/New_York",
            windows=[
                SessionWindow(
                    day_of_week=4, open_time="09:30:00", close_time="16:00:00"
                )
            ],
            holidays=["2026-07-03"],  # Friday July 3 holiday
        )

        # Friday July 3 at 11:00 NY time -> HOLIDAY -> Closed
        dt = datetime(2026, 7, 3, 15, 0, 0, tzinfo=UTC)
        assert svc.is_in_session(dt, session) is False

    asyncio.run(_test())


def test_timezone_conversion(tmp_path: Path) -> None:
    """Verify deterministic timezone translation."""

    async def _test() -> None:
        svc = await _setup_sessions(tmp_path)
        utc_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

        ny_time = svc.convert_timezone(utc_time, "UTC", "America/New_York")
        assert ny_time.hour == 7  # UTC-5 in winter

        tokyo_time = svc.convert_timezone(utc_time, "UTC", "Asia/Tokyo")
        assert tokyo_time.hour == 21  # UTC+9

    asyncio.run(_test())


def test_default_session(tmp_path: Path) -> None:
    """Verify default session retrieval."""

    async def _test() -> None:
        svc = await _setup_sessions(tmp_path)
        default_sess = await svc.get_default_session()
        assert default_sess.is_default is True
        assert "Forex" in default_sess.name

    asyncio.run(_test())


def test_strict_session_window_parsing() -> None:
    """Verify malformed and out-of-bounds time strings raise InvalidSessionWindowError."""
    # Valid
    t1 = _parse_time_str("09:30")
    assert t1.hour == 9
    assert t1.minute == 30
    assert t1.second == 0

    t2 = _parse_time_str("23:59:59")
    assert t2.hour == 23
    assert t2.minute == 59
    assert t2.second == 59

    # Invalid hour
    with pytest.raises(InvalidSessionWindowError, match="Invalid session time values"):
        _parse_time_str("24:00")

    # Invalid minute
    with pytest.raises(InvalidSessionWindowError, match="Invalid session time values"):
        _parse_time_str("12:60")

    # Invalid second
    with pytest.raises(InvalidSessionWindowError, match="Invalid session time values"):
        _parse_time_str("12:00:60")

    # Malformed string
    with pytest.raises(
        InvalidSessionWindowError, match="Malformed session time string"
    ):
        _parse_time_str("not_a_time")
