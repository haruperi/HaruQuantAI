"""Unit tests verifying 100% SQX parity for DataManagerSessions.

Description:
    Tests comprehensive StrategyQuant X parity for Data Manager sessions,
    covering REST endpoints for session CRUD, clone, mass deletion,
    NinjaTrader 8 template scanning/import with stats, and Sessions.xml
    export/import with conflict resolution.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Manage exchange trading hours, clocks, and
    holiday calendars in the Data Manager workspace.

Key Capabilities:
    - FR-DATA-SESSIONS-DEFAULTS: Seed baseline sessions idempotently.
    - FR-DATA-SESSIONS-CLONE: Clone sessions with broker profile association.
    - FR-DATA-SESSIONS-PERSISTENCE-CRUD: Batch deletion and broker filtering.
    - FR-DATA-SESSIONS-XML-TRANSFER: Sessions.xml interchange.
    - FR-DATA-SESSIONS-IMPORT: NinjaTrader 8 template scanning and import.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/workspace/test_data_manager_session_parity.py -v --no-cov`

CLI Usage:
    `pytest tests/unit/workspace/test_data_manager_session_parity.py`
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.host.persistence import DatabaseManager
from app.host.resources import ResourceManager
from app.workspace.data_manager.routes import create_data_router
from app.workspace.data_manager.sessions import SessionService
from fastapi import FastAPI
from fastapi.testclient import TestClient

SAMPLE_NT_XML = """<?xml version="1.0" encoding="utf-8"?>
<NinjaTrader>
  <TradingHours>
    <Name>Test NT Session</Name>
    <Description>Test NT Trading Hours</Description>
    <TimeZone>Eastern Standard Time</TimeZone>
    <Sessions>
      <Session>
        <DayOfWeek>Monday</DayOfWeek>
        <StartTime>09:30:00</StartTime>
        <EndTime>16:00:00</EndTime>
        <Type>Regular</Type>
      </Session>
    </Sessions>
    <Holidays>
      <Holiday>
        <Date>2026-12-25</Date>
        <Description>Christmas</Description>
      </Holiday>
    </Holidays>
    <PartialHolidays>
      <PartialHoliday>
        <Date>2026-11-27</Date>
        <EndTime>13:00:00</EndTime>
        <Description>Thanksgiving Early Close</Description>
      </PartialHoliday>
    </PartialHolidays>
  </TradingHours>
</NinjaTrader>
"""


@pytest.fixture
def test_client(tmp_path: Path) -> TestClient:
    """Fixture providing FastAPI test client backed by isolated database."""
    db_file = tmp_path / "test_session_parity.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()
    SessionService(db).ensure_defaults()

    res_dir = tmp_path / "resources"
    res_dir.mkdir()
    res_mgr = ResourceManager(root_dir=res_dir)

    router = create_data_router(db_manager=db, resource_manager=res_mgr)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_api_list_sessions_and_filters(test_client: TestClient) -> None:
    """Verify GET /data/sessions with broker and search query parameters."""
    res = test_client.get("/data/sessions")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert len(body["data"]) >= 5

    # Filter by search
    res_search = test_client.get("/data/sessions?search=Forex")
    assert res_search.status_code == 200
    search_data = res_search.json()["data"]
    assert len(search_data) >= 2
    assert all("Forex" in s["name"] for s in search_data)


def test_api_clone_session(test_client: TestClient) -> None:
    """Verify POST /data/sessions/clone creates session with postfix and broker."""
    payload = {
        "source_name": "US Equities RTH",
        "new_name": "US_Eq_Test",
        "broker_id": 3,
        "broker_postfix": "_IB",
    }
    res = test_client.post("/data/sessions/clone", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "success"
    assert body["data"]["name"] == "US_Eq_Test_IB"
    assert body["data"]["broker_id"] == 3

    # Check that it appears in listing
    get_res = test_client.get("/data/sessions/US_Eq_Test_IB")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "US_Eq_Test_IB"

    # Duplicate clone should fail with 400
    res_dup = test_client.post("/data/sessions/clone", json=payload)
    assert res_dup.status_code == 400


def test_api_mass_delete_sessions(test_client: TestClient) -> None:
    """Verify POST /data/sessions/mass-delete removes targeted sessions."""
    # Create two temporary sessions
    test_client.post(
        "/data/sessions",
        json={"name": "Del_1", "timezone": "UTC", "windows": []},
    )
    test_client.post(
        "/data/sessions",
        json={"name": "Del_2", "timezone": "UTC", "windows": []},
    )

    del_res = test_client.post(
        "/data/sessions/mass-delete",
        json={"names": ["Del_1", "Del_2", "NonExistent"]},
    )
    assert del_res.status_code == 200
    body = del_res.json()
    assert body["data"]["deleted_count"] == 2

    # Verify they no longer exist
    assert test_client.get("/data/sessions/Del_1").status_code == 404
    assert test_client.get("/data/sessions/Del_2").status_code == 404


def test_api_nt_template_scanner_and_import(
    test_client: TestClient, tmp_path: Path
) -> None:
    """Verify scanning NT templates and importing with SQX parity stats."""
    template_dir = tmp_path / "NT_Templates"
    template_dir.mkdir()
    (template_dir / "NT_Hours.xml").write_text(SAMPLE_NT_XML, encoding="utf-8")

    # 1. Scan templates
    scan_res = test_client.get(
        f"/data/sessions/nt-templates?folder_path={template_dir}"
    )
    assert scan_res.status_code == 200
    scan_body = scan_res.json()["data"]
    assert scan_body["exists"] is True
    assert scan_body["count"] == 1
    assert "NT_Hours.xml" in scan_body["templates"]

    # 2. Import from folder
    import_res = test_client.post(
        "/data/sessions/import-nt",
        json={"folder_path": str(template_dir), "conflict_policy": "overwrite"},
    )
    assert import_res.status_code == 201
    import_body = import_res.json()["data"]
    assert "Test NT Session" in import_body["imported"]
    assert import_body["dropped_holidays"] == 1
    assert import_body["dropped_partial_holidays"] == 1
    assert "SQX has no equivalent" in import_body["success"]


def test_api_sqx_xml_transfer(test_client: TestClient) -> None:
    """Verify exporting and importing StrategyQuant X Sessions.xml."""
    # Export GET
    get_export = test_client.get("/data/sessions/export-xml?names=24/7 Forex")
    assert get_export.status_code == 200
    assert "application/xml" in get_export.headers.get("content-type", "")
    xml_content = get_export.text
    assert "<Sessions>" in xml_content
    assert 'name="24/7 Forex"' in xml_content

    # Export POST
    post_export = test_client.post(
        "/data/sessions/export-xml", json={"names": ["US Equities RTH"]}
    )
    assert post_export.status_code == 200
    assert 'name="US Equities RTH"' in post_export.text

    # Modify and import
    xml_mod = xml_content.replace("24/7 Forex", "SQX_Imported_Forex")
    import_res = test_client.post(
        "/data/sessions/import-xml",
        json={"xml_content": xml_mod, "policy": "overwrite"},
    )
    assert import_res.status_code == 201
    import_data = import_res.json()["data"]
    assert len(import_data["imported"]) == 1
    assert import_data["imported"][0]["name"] == "SQX_Imported_Forex"

    # Verify session was persisted
    get_res = test_client.get("/data/sessions/SQX_Imported_Forex")
    assert get_res.status_code == 200
