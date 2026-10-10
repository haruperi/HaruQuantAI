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
from app.workspace.data_manager.instruments import InstrumentService
from app.workspace.data_manager.sessions import (
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
    InstrumentService(db).ensure_defaults()
    SessionService(db).ensure_defaults()
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


def test_session_clone(test_db: DatabaseManager) -> None:
    """Validate cloning sessions with broker association and postfix handling."""
    service = SessionService(test_db)

    # Missing source error
    with pytest.raises(ValueError, match="doesn't exist"):
        service.clone_session("NonExistent", "NewClone")

    # Valid clone
    cloned = service.clone_session(
        source_name="US Equities RTH",
        new_name="US_Eq_Oanda",
        broker_id=2,
        broker_postfix="_OAN",
    )
    assert cloned.name == "US_Eq_Oanda_OAN"
    assert cloned.broker_id == 2
    assert cloned.broker_name == "Broker 2"
    assert len(cloned.windows) == 5

    # Check persistence
    retrieved = service.get_session("US_Eq_Oanda_OAN")
    assert retrieved is not None
    assert retrieved.broker_id == 2

    # Duplicate target error
    with pytest.raises(ValueError, match="already exists"):
        service.clone_session(
            source_name="US Equities RTH",
            new_name="US_Eq_Oanda_OAN",
            broker_id=2,
        )


def test_batch_delete_sessions(test_db: DatabaseManager) -> None:
    """Validate mass delete of session records."""
    service = SessionService(test_db)
    service.save_session(TradingSessionDefinition(name="Batch_1", timezone="UTC"))
    service.save_session(TradingSessionDefinition(name="Batch_2", timezone="UTC"))

    deleted_count = service.delete_sessions(["Batch_1", "Batch_2", "NonExistent"])
    assert deleted_count == 2
    assert service.get_session("Batch_1") is None
    assert service.get_session("Batch_2") is None


def test_generate_mon_fri(test_db: DatabaseManager) -> None:
    """Validate generating Tuesday-Friday elements from Monday definition."""
    service = SessionService(test_db)

    # Empty list error
    with pytest.raises(ValueError, match="No session defined"):
        service.generate_mon_fri([])

    # Missing Monday error
    with pytest.raises(ValueError, match="Monday session"):
        service.generate_mon_fri(
            [
                SessionWindow(
                    day_from="Tue", day_to="Tue", start_time="09:00", end_time="17:00"
                )
            ]
        )

    monday = SessionWindow(
        day_from="Mon", day_to="Tue", start_time="17:00", end_time="16:00", eod=True
    )
    weekend = SessionWindow(
        day_from="Sun", day_to="Sun", start_time="17:00", end_time="23:59", eod=False
    )
    generated = service.generate_mon_fri([monday, weekend])

    # 5 weekdays + 1 weekend
    assert len(generated) == 6
    assert [w.day_from for w in generated[:5]] == ["Mon", "Tue", "Wed", "Thu", "Fri"]
    assert [w.day_to for w in generated[:5]] == ["Tue", "Wed", "Thu", "Fri", "Sat"]
    assert generated[5].day_from == "Sun"


def test_sqx_xml_export_and_import(test_db: DatabaseManager) -> None:
    """Validate exporting and importing native SQX Sessions.xml."""
    service = SessionService(test_db)

    session = TradingSessionDefinition(
        name="SQX_Test_Session",
        broker_id=5,
        description="SQX XML Export Test",
        timezone="America/New_York",
        windows=[
            SessionWindow(
                day_from="Mon",
                day_to="Mon",
                start_time="09:30",
                end_time="16:00",
                eod=True,
            )
        ],
    )
    service.save_session(session)

    xml_str = service.export_sqx_xml(["SQX_Test_Session"])
    assert "<Sessions>" in xml_str
    assert 'name="SQX_Test_Session"' in xml_str
    assert 'broker="5"' in xml_str
    assert 'startDay="Mon"' in xml_str

    # Modify and re-import under new name
    xml_modified = xml_str.replace("SQX_Test_Session", "SQX_Imported_Session")
    imported, skipped = service.import_sqx_xml(xml_modified, policy="overwrite")
    assert len(imported) == 1
    assert imported[0].name == "SQX_Imported_Session"
    assert imported[0].broker_id == 5
    assert len(imported[0].windows) == 1
    assert imported[0].windows[0].start_time == "09:30"

    # Test skip policy
    imported2, skipped2 = service.import_sqx_xml(xml_modified, policy="skip")
    assert len(imported2) == 0
    assert "SQX_Imported_Session" in skipped2


def test_import_ninjatrader_full_stats(
    test_db: DatabaseManager, tmp_path: Path
) -> None:
    """Validate import_ninjatrader_full directory scanning and statistics."""
    service = SessionService(test_db)

    nt_dir = tmp_path / "NT_Templates"
    nt_dir.mkdir()
    xml_path = nt_dir / "Futures.xml"
    xml_path.write_text(SAMPLE_NT8_XML, encoding="utf-8")

    # List templates
    info = service.list_ninjatrader_templates(nt_dir)
    assert info["exists"] is True
    assert info["count"] == 1
    assert info["templates"] == ["Futures.xml"]

    # Full import with dropped holiday statistics
    res = service.import_ninjatrader_full(nt_dir, policy="overwrite")
    assert len(res["imported"]) == 1
    assert res["imported"][0] == "CME US Index Futures RTH"
    assert res["dropped_holidays"] == 2
    assert "SQX has no equivalent" in res["success"]


def test_multiday_cross_midnight_open(test_db: DatabaseManager) -> None:
    """Validate multi-day session open check (e.g. Sunday to Monday)."""
    service = SessionService(test_db)

    session = TradingSessionDefinition(
        name="Sunday_To_Monday",
        timezone="UTC",
        windows=[
            SessionWindow(
                day_from="Sun", day_to="Mon", start_time="17:00", end_time="16:00"
            )
        ],
    )
    service.save_session(session)

    # Sunday 18:00 UTC -> open
    sun_open = datetime(2026, 10, 4, 18, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("Sunday_To_Monday", sun_open) is True

    # Monday 10:00 UTC -> open
    mon_open = datetime(2026, 10, 5, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("Sunday_To_Monday", mon_open) is True

    # Monday 17:00 UTC -> closed
    mon_closed = datetime(2026, 10, 5, 17, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("Sunday_To_Monday", mon_closed) is False

    # Tuesday 10:00 UTC -> closed
    tue_closed = datetime(2026, 10, 6, 10, 0, 0, tzinfo=zoneinfo.ZoneInfo("UTC"))
    assert service.is_market_open("Sunday_To_Monday", tue_closed) is False


def test_list_sessions_filters(test_db: DatabaseManager) -> None:
    """Validate listing sessions with broker_id and search filters."""
    service = SessionService(test_db)
    service.save_session(
        TradingSessionDefinition(name="Broker1_EURUSD", broker_id=1, timezone="UTC")
    )
    service.save_session(
        TradingSessionDefinition(name="Broker2_EURUSD", broker_id=2, timezone="UTC")
    )

    # Filter by broker
    b1_sessions = service.list_sessions(broker_id=1)
    assert any(s.name == "Broker1_EURUSD" for s in b1_sessions)
    assert not any(s.name == "Broker2_EURUSD" for s in b1_sessions)

    # Filter by search text
    searched = service.list_sessions(search="Broker2")
    assert len(searched) == 1
    assert searched[0].name == "Broker2_EURUSD"


def test_session_window_sqx_tuples() -> None:
    """Validate SQX 5-field tuple conversion and parsing."""
    w = SessionWindow(
        day_from="Mon",
        day_to="Tue",
        start_time="09:30",
        end_time="16:00",
        eod=True,
    )
    assert w.time_from == "09:30"
    assert w.time_to == "16:00"
    assert w.seoc is True
    assert w.int_start_time() == 930
    assert w.int_end_time() == 1600
    tup = w.to_sqx_tuple()
    assert tup == "Mon,09:30,Tue,16:00,Yes"

    parsed = SessionWindow.from_sqx_tuple("Wed,08:00,Wed,17:00,No")
    assert parsed.day_from == "Wed"
    assert parsed.day_to == "Wed"
    assert parsed.start_time == "08:00"
    assert parsed.end_time == "17:00"
    assert parsed.eod is False

    # Test camelCase and SQX aliases
    w_alias = SessionWindow.model_validate(
        {
            "dayFrom": "Fri",
            "dayTo": "Sat",
            "timeFrom": "18:00",
            "timeTo": "04:00",
            "seoc": "true",
        }
    )
    assert w_alias.day_from == "Fri"
    assert w_alias.day_to == "Sat"
    assert w_alias.start_time == "18:00"
    assert w_alias.eod is True

    # Test session aliases
    sess_alias = TradingSessionDefinition.model_validate(
        {
            "name": "Alias_Sess",
            "broker": "3",
            "elements": [w_alias],
        }
    )
    assert sess_alias.broker_id == 3
    assert len(sess_alias.elements) == 1


def test_session_cli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate CLI main() functionality."""
    import sys

    from app.workspace.data_manager import sessions

    # 1. Test --list
    monkeypatch.setattr(sys, "argv", ["sessions.py", "--list"])
    rc = sessions.main()
    assert rc == 0
    out, _ = capsys.readouterr()
    assert "Configured sessions" in out

    # 2. Test --check
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sessions.py",
            "--check",
            "24/7 Forex",
            "--time",
            "2026-10-05T12:00:00+00:00",
        ],
    )
    rc_check = sessions.main()
    assert rc_check == 0
    out2, _ = capsys.readouterr()
    assert "open=True" in out2

    # 3. Test --import-nt
    xml_path = tmp_path / "cli_nt.xml"
    xml_path.write_text(SAMPLE_NT8_XML, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["sessions.py", "--import-nt", str(xml_path)])
    rc_import = sessions.main()
    assert rc_import == 0
    out3, _ = capsys.readouterr()
    assert "Imported" in out3
