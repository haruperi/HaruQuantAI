"""Unit and integration tests for connected market data REST router workflows.

Description:
    Tests the complete FastAPI REST router for the market data subsystem
    (`app.plugins.data.integration`). Validates dataset imports and availability,
    instrument lifecycle CRUD, trading session management and NinjaTrader XML
    imports, stock group / basket definitions and synthetic calculation, provider
    matrix queries and downloads, COT mappings and observations, data quality
    audits, and timeframe resampling / format exports.

Purpose:
    FEAT-DATA-INTEGRATION: Connected Data Manager REST endpoints and workflows.

Key Capabilities:
    - FR-DATA-INTEGRATION-DATASETS: End-to-end dataset listing, lookup, and ingestion.
    - FR-DATA-INTEGRATION-INSTRUMENTS: Instrument specification creation and updates.
    - FR-DATA-INTEGRATION-SESSIONS: Session management and NinjaTrader XML parsing.
    - FR-DATA-INTEGRATION-BASKETS: Stock group baskets and composite series math.
    - FR-DATA-INTEGRATION-PROVIDERS: Provider capability matrix and data downloads.
    - FR-DATA-INTEGRATION-COT: CFTC COT report updates and observation queries.
    - FR-DATA-INTEGRATION-QUALITY: Automated data quality inspection and scoring.
    - FR-DATA-INTEGRATION-TRANSFORMS: Timeframe resampling and CSV/MT4/MT5 export.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_integration.py -v --no-cov`

CLI Usage:
    `uv run pytest tests/unit/v2/phase_02/test_integration.py -v --no-cov`
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from app.host.bootstrap import HostRuntime, HostSettings, create_host_app
from app.host.persistence import DatabaseManager
from app.host.resources import ResourceManager
from fastapi.testclient import TestClient

SAMPLE_CSV_CONTENT = (
    "Date,Time,Open,High,Low,Close,Volume\n"
    "2026.10.01,00:00:00,1.08000,1.08050,1.07980,1.08020,100\n"
    "2026.10.01,00:01:00,1.08020,1.08070,1.08010,1.08060,150\n"
    "2026.10.01,00:02:00,1.08060,1.08100,1.08040,1.08090,200\n"
    "2026.10.01,00:03:00,1.08090,1.08120,1.08080,1.08110,120\n"
    "2026.10.01,00:04:00,1.08110,1.08150,1.08100,1.08140,180\n"
)

SAMPLE_NT_XML = """<?xml version="1.0" encoding="utf-8"?>
<NinjaTrader>
  <TradingHours>
    <Name>Test_Integration_Session</Name>
    <TimeZone>Eastern Standard Time</TimeZone>
    <Sessions>
      <Session>
        <DayOfWeek>Monday</DayOfWeek>
        <StartTime>09:30:00</StartTime>
        <EndTime>16:00:00</EndTime>
      </Session>
    </Sessions>
  </TradingHours>
</NinjaTrader>
"""


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Fixture creating an isolated FastAPI TestClient with mounted data router."""
    db_file = tmp_path / "test_integration.db"
    db = DatabaseManager(database_path=db_file)
    db.initialize()

    res_dir = tmp_path / "resources"
    res_dir.mkdir(parents=True, exist_ok=True)
    res_mgr = ResourceManager(root_dir=res_dir)

    settings = HostSettings(data_dir=tmp_path)
    runtime = HostRuntime(settings)
    runtime.db_manager = db
    runtime.resource_manager = res_mgr

    app = create_host_app(settings, runtime=runtime)
    return TestClient(app)


def test_integration_datasets_workflow(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Validate full dataset import, query, availability, and deletion endpoints."""
    caplog.set_level(logging.DEBUG)

    # 1. Initial list empty
    resp = client.get("/api/v1/data/datasets")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"] == []

    # 2. Check availability before import -> UNAVAILABLE
    avail_resp = client.get("/api/v1/data/datasets/EURUSD/M1/availability")
    assert avail_resp.status_code == 200
    avail_body = avail_resp.json()
    assert avail_body["data"]["status"] == "UNAVAILABLE"
    assert avail_body["data"]["is_available"] is False

    # 3. Import dataset from inline CSV
    import_resp = client.post(
        "/api/v1/data/datasets/import",
        json={
            "symbol": "EURUSD",
            "timeframe": "M1",
            "content": SAMPLE_CSV_CONTENT,
            "broker": "default",
            "timezone": "UTC",
        },
    )
    assert import_resp.status_code == 201
    import_data = import_resp.json()["data"]
    dataset_id = import_data["dataset_id"]
    assert import_data["bar_count"] == 5

    # 4. Query specific dataset
    get_resp = client.get(f"/api/v1/data/datasets/{dataset_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["symbol"] == "EURUSD"

    # 5. Check availability after import -> AVAILABLE
    avail_after = client.get("/api/v1/data/datasets/EURUSD/M1/availability")
    assert avail_after.status_code == 200
    assert avail_after.json()["data"]["status"] == "AVAILABLE"
    assert avail_after.json()["data"]["is_available"] is True

    # 6. Delete dataset
    del_resp = client.delete(f"/api/v1/data/datasets/{dataset_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["deleted"] is True

    # 7. Confirm 404 after deletion
    del_check = client.get(f"/api/v1/data/datasets/{dataset_id}")
    assert del_check.status_code == 404


def test_integration_instruments_workflow(client: TestClient) -> None:
    """Validate instrument CRUD operations via REST endpoints."""
    # 1. Initial listing
    resp = client.get("/api/v1/data/instruments")
    assert resp.status_code == 200
    assert resp.json()["data"] == []

    # 2. Create instrument
    inst_payload = {
        "symbol": "GBPUSD",
        "connection": "Direct",
        "broker_id": 1,
        "description": "British Pound vs US Dollar",
        "point_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.0001,
        "digits": 4,
        "data_type": "Forex",
    }
    create_resp = client.post("/api/v1/data/instruments", json=inst_payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["data"]["symbol"] == "GBPUSD"

    # 3. Retrieve instrument
    get_resp = client.get("/api/v1/data/instruments/GBPUSD")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["description"] == "British Pound vs US Dollar"

    # 4. Update instrument
    update_resp = client.put(
        "/api/v1/data/instruments/GBPUSD",
        json={"description": "Updated GBPUSD Description"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["updated"] is True

    # 5. Verify update persisted
    verify_resp = client.get("/api/v1/data/instruments/GBPUSD")
    assert verify_resp.json()["data"]["description"] == "Updated GBPUSD Description"

    # 6. Delete instrument
    del_resp = client.delete("/api/v1/data/instruments/GBPUSD")
    assert del_resp.status_code == 200

    # 7. Check 404 on deleted instrument
    assert client.get("/api/v1/data/instruments/GBPUSD").status_code == 404


def test_integration_sessions_workflow(client: TestClient) -> None:
    """Validate trading session creation, listing, deletion, and NT XML import."""
    # 1. Create session
    session_payload = {
        "name": "London_Standard",
        "timezone": "Europe/London",
        "description": "London regular equity trading session",
        "windows": [
            {
                "day_of_week": 0,
                "start_time": "08:00:00",
                "end_time": "16:30:00",
            }
        ],
        "holidays": [],
    }
    create_resp = client.post("/api/v1/data/sessions", json=session_payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["data"]["name"] == "London_Standard"

    # 2. Retrieve session
    get_resp = client.get("/api/v1/data/sessions/London_Standard")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["timezone"] == "Europe/London"

    # 3. Import NinjaTrader XML session template
    nt_resp = client.post(
        "/api/v1/data/sessions/import-nt",
        json={"xml_content": SAMPLE_NT_XML, "conflict_policy": "overwrite"},
    )
    assert nt_resp.status_code == 201
    imported = nt_resp.json()["data"]
    assert len(imported) == 1
    assert imported[0]["name"] == "Test_Integration_Session"

    # 4. List all sessions
    list_resp = client.get("/api/v1/data/sessions")
    assert list_resp.status_code == 200
    names = [s["name"] for s in list_resp.json()["data"]]
    assert "London_Standard" in names
    assert "Test_Integration_Session" in names

    # 5. Delete session
    del_resp = client.delete("/api/v1/data/sessions/London_Standard")
    assert del_resp.status_code == 200
    assert client.get("/api/v1/data/sessions/London_Standard").status_code == 404


def test_integration_baskets_workflow(client: TestClient) -> None:
    """Validate basket lifecycle and composite series computation."""
    # 1. Create basket definition
    basket_payload = {
        "name": "FX_Majors",
        "description": "Major currency basket",
        "items": [
            {"symbol": "EURUSD", "weight": 0.6},
            {"symbol": "GBPUSD", "weight": 0.4},
        ],
    }
    save_resp = client.post("/api/v1/data/baskets", json=basket_payload)
    assert save_resp.status_code == 201
    assert save_resp.json()["data"]["name"] == "FX_Majors"

    # 2. Retrieve basket
    get_resp = client.get("/api/v1/data/baskets/FX_Majors")
    assert get_resp.status_code == 200
    assert len(get_resp.json()["data"]["items"]) == 2

    # 3. Compute synthetic composite basket
    eur_bars = [
        {
            "timestamp_utc": "2026-10-01T00:00:00Z",
            "open": 1.1000,
            "high": 1.1050,
            "low": 1.0950,
            "close": 1.1020,
            "volume": 100.0,
        },
        {
            "timestamp_utc": "2026-10-01T00:01:00Z",
            "open": 1.1020,
            "high": 1.1080,
            "low": 1.1000,
            "close": 1.1050,
            "volume": 120.0,
        },
    ]
    gbp_bars = [
        {
            "timestamp_utc": "2026-10-01T00:00:00Z",
            "open": 1.3000,
            "high": 1.3050,
            "low": 1.2950,
            "close": 1.3020,
            "volume": 200.0,
        },
        {
            "timestamp_utc": "2026-10-01T00:01:00Z",
            "open": 1.3020,
            "high": 1.3070,
            "low": 1.2990,
            "close": 1.3040,
            "volume": 180.0,
        },
    ]
    compute_resp = client.post(
        "/api/v1/data/baskets/compute",
        json={
            "basket": basket_payload,
            "series": {"EURUSD": eur_bars, "GBPUSD": gbp_bars},
            "alignment_mode": "intersection",
        },
    )
    assert compute_resp.status_code == 200
    synthetic_bars = compute_resp.json()["data"]
    assert len(synthetic_bars) == 2
    # 0.6 * 1.1000 + 0.4 * 1.3000 = 0.66 + 0.52 = 1.1800
    assert pytest.approx(synthetic_bars[0]["open"], rel=1e-4) == 1.1800

    # 4. Delete basket
    del_resp = client.delete("/api/v1/data/baskets/FX_Majors")
    assert del_resp.status_code == 200
    assert client.get("/api/v1/data/baskets/FX_Majors").status_code == 404


def test_integration_providers_and_cot_workflow(client: TestClient) -> None:
    """Validate provider capability enumeration and COT mapping & updates."""
    # 1. Provider matrix query
    prov_resp = client.get("/api/v1/data/providers")
    assert prov_resp.status_code == 200
    providers = prov_resp.json()["data"]
    assert len(providers) >= 10
    names = [p["name"] for p in providers]
    assert "Dukascopy" in names
    assert "Binance" in names
    assert "Yahoo" in names

    # 2. COT symbol mappings
    cot_resp = client.get("/api/v1/data/cot/mappings")
    assert cot_resp.status_code == 200
    mappings = cot_resp.json()["data"]
    assert len(mappings) >= 5
    symbols = [m["symbol"] for m in mappings]
    assert "EURUSD" in symbols or "CL" in symbols or "GC" in symbols

    # 3. COT report update
    update_resp = client.post(
        "/api/v1/data/cot/EURUSD/update",
        json={"reports": [], "lookback_weeks": 26},
    )
    assert update_resp.status_code == 200
    obs = update_resp.json()["data"]
    assert len(obs) > 0
    assert "cpihedg" in obs[0]
    assert "ctihedg" in obs[0]

    # 4. COT observation query
    get_obs_resp = client.get("/api/v1/data/cot/EURUSD")
    assert get_obs_resp.status_code == 200
    assert len(get_obs_resp.json()["data"]) == len(obs)


def test_integration_quality_and_transforms_workflow(client: TestClient) -> None:
    """Validate data quality auditing, M1 resampling, and format exports."""
    # 5 contiguous M1 bars
    bars = [
        {
            "timestamp_utc": f"2026-10-01T00:0{i}:00Z",
            "open": 1.0800 + i * 0.0001,
            "high": 1.0805 + i * 0.0001,
            "low": 1.0798 + i * 0.0001,
            "close": 1.0802 + i * 0.0001,
            "volume": 100.0,
        }
        for i in range(5)
    ]

    # 1. Quality audit endpoint
    audit_resp = client.post(
        "/api/v1/data/quality/audit",
        json={"bars": bars, "timeframe": "M1", "strict": False},
    )
    assert audit_resp.status_code == 200
    report = audit_resp.json()["data"]
    assert report["total_bars"] == 5
    assert report["valid_bars"] == 5
    assert report["quality_score"] == 1.0

    # 2. Resampling M1 -> M5 endpoint
    resample_resp = client.post(
        "/api/v1/data/transforms/resample",
        json={"bars": bars, "target_timeframe": "M5"},
    )
    assert resample_resp.status_code == 200
    resampled = resample_resp.json()["data"]
    assert len(resampled) == 1
    assert pytest.approx(resampled[0]["open"], rel=1e-5) == 1.0800
    assert pytest.approx(resampled[0]["close"], rel=1e-5) == 1.0806

    # 3. CSV export endpoint
    export_csv_resp = client.post(
        "/api/v1/data/export",
        json={
            "bars": bars,
            "format": "csv",
            "symbol": "EURUSD",
            "timeframe": "M1",
            "digits": 5,
        },
    )
    assert export_csv_resp.status_code == 200
    csv_data = export_csv_resp.json()["data"]
    assert "Date,Time,Open,High,Low,Close,Volume" in csv_data["content"]
    assert csv_data["line_count"] == 6

    # 4. MT4 export endpoint
    export_mt4_resp = client.post(
        "/api/v1/data/export",
        json={
            "bars": bars,
            "format": "mt4",
            "symbol": "EURUSD",
            "timeframe": "M1",
            "digits": 5,
        },
    )
    assert export_mt4_resp.status_code == 200
    assert export_mt4_resp.json()["data"]["format"] == "mt4"


def test_integration_error_handling(client: TestClient) -> None:
    """Validate standard error response schemas and HTTP error codes."""
    # 404 for missing dataset
    resp = client.get("/api/v1/data/datasets/non_existent_dataset_id")
    assert resp.status_code == 404
    body = resp.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "DATASET_NOT_FOUND"

    # 400 for dataset import without content or file_path
    bad_import = client.post(
        "/api/v1/data/datasets/import",
        json={"symbol": "EURUSD", "timeframe": "M1"},
    )
    assert bad_import.status_code == 400
    assert bad_import.json()["status"] == "error"

    # Also verify route reachable at root /data prefix
    root_resp = client.get("/data/datasets")
    assert root_resp.status_code == 200
