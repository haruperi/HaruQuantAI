"""Unit tests for SessionService and trading session management.

Description:
    Unit tests for SessionService, exchange clocks, DST transitions, and
    NinjaTrader 8 TradingHours XML template import, validating Phase 2 Task 2.2.

Purpose:
    FEAT-DATA-SESSIONS: Manage exchange trading hours, clocks, and holiday calendars.

Key Capabilities:
    FR-DATA-SESSIONS-TIMEZONES: Validates IANA timezone handling and DST resolution.
    FR-DATA-SESSIONS-WINDOWS: Validates daily and overnight trading windows and holidays.
    FR-DATA-SESSIONS-IMPORT: Validates NT8 XML import with overwrite/skip policies.
    FR-DATA-SESSIONS-PERSISTENCE-CRUD: Validates persistence CRUD in datamgr_sessions.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_sessions.py -v --no-cov`
"""

from __future__ import annotations

import logging
import zoneinfo
from datetime import datetime
from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.plugins.data.sessions import (
    SessionService,
    SessionWindow,
    TradingHoliday,
    TradingSessionDefinition,
)

SAMPLE_NT8_XML = """<?xml version="1.0" encoding="utf-8"?>
<NinjaTrader>
  <TradingHours>
    <Name>CME US Index Futures RTH</Name>
    <Description>Chicago Mercantile Exchange Regular Trading Hours</Description>
    <TimeZone>Central Standard Time</TimeZone>
    <Sessions>
      <Session>
        <DayOfWeek>Monday</DayOfWeek>
        <StartTime>08:30:00</StartTime>
        <EndTime>15:15:00</EndTime>
        <Type>Regular</Type>
      </Session>
      <Session>
        <DayOfWeek>Tuesday</DayOfWeek>
        <StartTime>08:30:00</StartTime>
        <EndTime>15:15:00</EndTime>
        <Type>Regular</Type>
      </Session>
      <Session>
        <DayOfWeek>Wednesday</DayOfWeek>
        <StartTime>08:30:00</StartTime>
        <EndTime>15:15:00</EndTime>
        <Type>Regular</Type>
      </Session>
      <Session>
        <DayOfWeek>Thursday</DayOfWeek>
        <StartTime>08:30:00</StartTime>
        <EndTime>15:15:00</EndTime>
        <Type>Regular</Type>
      </Session>
      <Session>
        <DayOfWeek>Friday</DayOfWeek>
        <StartTime>08:30:00</StartTime>
        <EndTime>15:15:00</EndTime>
        <Type>Regular</Type>
      </Session>
    </Sessions>
    <Holidays>
      <Holiday>
        <Date>2026-12-25</Date>
        <Description>Christmas Day</Description>
      </Holiday>
      <Holiday>
        <Date>2026-01-01</Date>
        <Description>New Years Day</Description>
      </Holiday>
    </Holidays>
  </TradingHours>
</NinjaTrader>
"""


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    """Fixture providing an isolated SQLite database."""
    db_file = tmp_path / "test_sessions.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    return db


def test_session_persistence_crud(
    test_db: DatabaseManager, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate full CRUD operations against datamgr_sessions."""
    caplog.set_level(logging.DEBUG)
    service = SessionService(test_db)

    # Initial state contains baseline seeds
    assert len(service.list_sessions()) >= 2
    initial_names = [s.name for s in service.list_sessions()]
    assert "24/7 Forex" in initial_names
    assert "US Equities RTH" in initial_names
    assert service.get_session("US_Equities") is None

    session = TradingSessionDefinition(
        name="US_Equities",
        description="US Regular Trading Hours",
        timezone="America/New_York",
        windows=[
            SessionWindow(
                day_of_week=d,
                start_time="09:30",
                end_time="16:00",
                session_type="Regular",
            )
            for d in range(5)
        ],
        holidays=[
            TradingHoliday(date_str="2026-07-04", description="Independence Day")
        ],
        is_default=True,
    )

    new_id = service.save_session(session)
    assert new_id > 0

    # FR log verification
    assert any(
        "FR-DATA-SESSIONS-PERSISTENCE-CRUD" in rec.message for rec in caplog.records
    )

    # Read back
    retrieved = service.get_session("US_Equities")
    assert retrieved is not None
    assert retrieved.name == "US_Equities"
    assert retrieved.timezone == "America/New_York"
    assert len(retrieved.windows) == 5
    assert len(retrieved.holidays) == 1
    assert retrieved.is_default is True

    # Update
    updated = retrieved.model_copy(update={"description": "Updated US Trading Hours"})
    service.save_session(updated)
    retrieved2 = service.get_session("US_Equities")
    assert retrieved2 is not None
    assert retrieved2.description == "Updated US Trading Hours"

    # List
    all_sessions = service.list_sessions()
    assert any(s.name == "US_Equities" for s in all_sessions)

    # Delete
    assert service.delete_session("US_Equities") is True
    assert service.get_session("US_Equities") is None
    assert service.delete_session("US_Equities") is False


def test_session_timezone_validation(caplog: pytest.LogCaptureFixture) -> None:
    """Validate standard IANA timezone validation and rejection of invalid names."""
    caplog.set_level(logging.DEBUG)

    # Valid timezones
    s1 = TradingSessionDefinition(name="S1", timezone="America/New_York")
    assert s1.timezone == "America/New_York"
    s2 = TradingSessionDefinition(name="S2", timezone="Europe/London")
    assert s2.timezone == "Europe/London"
    s3 = TradingSessionDefinition(name="S3", timezone="Asia/Tokyo")
    assert s3.timezone == "Asia/Tokyo"

    # Invalid timezone
    with pytest.raises(ValueError, match="Invalid standard IANA timezone"):
        TradingSessionDefinition(name="BadTZ", timezone="Invalid/Timezone_Name")

    assert any("FR-DATA-SESSIONS-TIMEZONES" in rec.message for rec in caplog.records)


def test_market_open_evaluation(test_db: DatabaseManager) -> None:
    """Validate market open/closed checks across time windows, DST, and holidays."""
    service = SessionService(test_db)

    # Session: US Equities (09:30 - 16:00 New York, Mon-Fri, 0=Mon, 4=Fri)
    session = TradingSessionDefinition(
        name="NYSE",
        timezone="America/New_York",
        windows=[
            SessionWindow(day_of_week=d, start_time="09:30", end_time="16:00")
            for d in range(5)
        ],
        holidays=[TradingHoliday(date_str="2026-11-26", description="Thanksgiving")],
    )
    service.save_session(session)

    # Wednesday 2026-10-07 14:00:00 UTC -> 10:00:00 EDT (EDT is UTC-4 in October)
    # Market should be OPEN (between 09:30 and 16:00)
    open_dt = datetime(2026, 10, 7, 14, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("NYSE", open_dt) is True

    # Wednesday 2026-10-07 08:00:00 UTC -> 04:00:00 EDT
    # Market should be CLOSED
    pre_dt = datetime(2026, 10, 7, 8, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("NYSE", pre_dt) is False

    # Saturday 2026-10-10 15:00:00 UTC -> Weekend
    # Market should be CLOSED
    weekend_dt = datetime(2026, 10, 10, 15, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("NYSE", weekend_dt) is False

    # Thursday 2026-11-26 15:00:00 UTC -> Thanksgiving Holiday
    # Market should be CLOSED
    holiday_dt = datetime(2026, 11, 26, 15, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("NYSE", holiday_dt) is False

    # Nonexistent session
    assert service.is_market_open("NONEXISTENT", open_dt) is False


def test_overnight_session_window(test_db: DatabaseManager) -> None:
    """Validate overnight sessions that cross midnight (e.g. 18:00 to 05:00)."""
    service = SessionService(test_db)

    session = TradingSessionDefinition(
        name="Crypto_Overnight",
        timezone="UTC",
        windows=[
            SessionWindow(day_of_week=0, start_time="18:00", end_time="05:00")  # Mon
        ],
    )
    service.save_session(session)

    # Monday 19:00 UTC -> within window
    dt1 = datetime(2026, 10, 5, 19, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("Crypto_Overnight", dt1) is True

    # Monday 04:00 UTC -> within window
    dt2 = datetime(2026, 10, 5, 4, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("Crypto_Overnight", dt2) is True

    # Monday 12:00 UTC -> outside window
    dt3 = datetime(2026, 10, 5, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("Crypto_Overnight", dt3) is False


def test_import_ninjatrader_xml(
    test_db: DatabaseManager, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate importing NinjaTrader 8 TradingHours XML templates."""
    caplog.set_level(logging.DEBUG)
    service = SessionService(test_db)

    # 1. Import from XML string
    imported = service.import_ninjatrader_xml(SAMPLE_NT8_XML, policy="overwrite")
    assert len(imported) == 1
    session = imported[0]
    assert session.name == "CME US Index Futures RTH"
    assert session.timezone == "America/Chicago"  # CST normalized
    assert len(session.windows) == 5
    assert len(session.holidays) == 2

    # Check persistence
    retrieved = service.get_session("CME US Index Futures RTH")
    assert retrieved is not None
    assert retrieved.name == session.name

    # 2. Test 'skip' policy on duplicate
    caplog.clear()
    skipped_import = service.import_ninjatrader_xml(SAMPLE_NT8_XML, policy="skip")
    assert len(skipped_import) == 0
    assert any("FR-DATA-SESSIONS-IMPORT" in rec.message for rec in caplog.records)

    # 3. Import from file path
    xml_file = tmp_path / "TradingHours.xml"
    xml_file.write_text(SAMPLE_NT8_XML, encoding="utf-8")
    re_imported = service.import_ninjatrader_xml(xml_file, policy="overwrite")
    assert len(re_imported) == 1
    assert re_imported[0].name == "CME US Index Futures RTH"

    # Nonexistent file error
    with pytest.raises(FileNotFoundError):
        service.import_ninjatrader_xml(tmp_path / "missing.xml")
