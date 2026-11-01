"""Comprehensive integration test suite for AppHome REST endpoints.

Description:
    Tests authenticated API routes for landing, about, update feeds,
    diagnostics, project settings persistence, notes, template management,
    resource resolution, engine lifecycle controls, and dashboard leaderboard.

Purpose:
    FEAT-HOME-ROUTES-TESTS: Verification of HTTP transport contracts and security boundaries.

Key Capabilities:
    - FR-home-routes-landing: Verify authenticated recent projects response.
    - FR-home-routes-about: Verify host environment and unconfigured license state.
    - FR-home-routes-updates: Verify safe update feed checks.
    - FR-home-routes-diagnostics: Verify database, memory, and directory reporting.
    - FR-home-routes-project: Verify settings persistence and revision conflict detection.
    - FR-home-routes-notes: Verify notes persistence with conflict checks.
    - FR-home-routes-template: Verify strategy template application.
    - FR-home-routes-resources: Verify symbol and dataset resource resolution.
    - FR-home-routes-engine: Verify engine lifecycle actions and telemetry.
    - FR-home-routes-dashboard: Verify candidate ranking leaderboard.

Python API Usage:
    pytest tests/workspace/home/test_routes.py

CLI Usage:
    uv run python -m pytest tests/workspace/home/test_routes.py -q
"""

from __future__ import annotations

import json
from collections.abc import Generator
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from app.core.host.persistence import HostPersistence
from app.core.host.session import SessionManager
from app.core.trading.project.contracts import (
    ProjectDocument,
    ProjectManifest,
    TaskDocument,
)
from app.core.trading.project.store import ProjectStore
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.main import create_app
from fastapi.testclient import TestClient
from tests.workspace.home.test_execution_acceptance import market, project


@pytest.fixture
def gateway(tmp_path: Path) -> HostPersistence:
    """Initialize HostPersistence with session and host settings schemas."""
    db_path = tmp_path / "host_test.db"
    import sqlite3

    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS host_session (
                session_id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL UNIQUE,
                username TEXT NOT NULL,
                peer_id TEXT NOT NULL,
                created_at_utc TEXT NOT NULL,
                expires_at_utc TEXT NOT NULL,
                revoked_at_utc TEXT,
                status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS host_settings (
                scope TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                updated_at_utc TEXT NOT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY(scope, key)
            );
            CREATE TABLE IF NOT EXISTS host_entities (
                entity_id TEXT NOT NULL, entity_type TEXT NOT NULL,
                status TEXT NOT NULL, lineage_json TEXT NOT NULL,
                manifest_json TEXT NOT NULL, payload_ref TEXT NOT NULL,
                created_at_utc TEXT NOT NULL, updated_at_utc TEXT NOT NULL,
                PRIMARY KEY(entity_id,entity_type));
        """)

    gw = HostPersistence(db_path)
    gw.ensure_jobs_schema()
    gw.ensure_datasets_schema()
    gw.create_records(
        "datamgr_datasets",
        [
            {
                "id": "default:EURUSD:M1",
                "source": "default",
                "symbol": "EURUSD",
                "underlying": "EURUSD",
                "timeframe": "M1",
                "broker": "DefaultBroker",
                "timezone": "UTC",
                "category": "Forex",
                "date_from": "2020-01-01",
                "date_to": "2026-01-01",
                "bars": 1000,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
            {
                "id": "default:GBPUSD:M1",
                "source": "default",
                "symbol": "GBPUSD",
                "underlying": "GBPUSD",
                "timeframe": "M1",
                "broker": "DefaultBroker",
                "timezone": "UTC",
                "category": "Forex",
                "date_from": "2020-01-01",
                "date_to": "2026-01-01",
                "bars": 1000,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
        ],
    )
    gw.create_records(
        "host_settings",
        [
            {
                "scope": "application",
                "key": "user_access",
                "value_json": json.dumps(
                    {
                        "username": "tester",
                        "password_hash": SessionManager.hash_password("password"),
                    }
                ),
                "updated_at_utc": "unchanged",
                "schema_version": 1,
            },
            {
                "scope": "_system",
                "key": "revision",
                "value_json": "1",
                "updated_at_utc": "unchanged",
                "schema_version": 1,
            },
        ],
    )
    return gw


@pytest.fixture
def test_setup(gateway: HostPersistence, tmp_path: Path) -> Generator[dict[str, Any]]:
    """Set up application with test project directory and sample projects."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    market(tmp_path, gateway)
    gateway.create_records(
        "host_settings",
        [
            {
                "scope": "project_templates",
                "key": name,
                "value_json": json.dumps(
                    {"task_type": "build", "settings": {"engine": "MetaTrader5"}}
                ),
                "updated_at_utc": "unchanged",
                "schema_version": 1,
            }
            for name in ("Simple", "Advanced")
        ],
    )
    # Create a sample .haru project
    store = ProjectStore()
    manifest = ProjectManifest(
        project_id="sample-proj-1",
        name="Alpha Momentum",
        schema_version=1,
    )
    task = TaskDocument(
        task_id="task_01",
        task_type="build",
        name="Builder Task 1",
        settings={
            **dict(project("RANDOM", candidates=1000).tasks["task"].settings),
            "engine": "MetaTrader5",
            "symbol": "EURUSD",
        },
        databank_target="Results",
    )
    doc = ProjectDocument(
        manifest=manifest,
        pipeline=("task_01",),
        databanks={"Results": "Results"},
        tasks={"task_01": task},
        metadata={
            "notes": "Initial research note.",
            "revision": 1,
            "resources": {"EURUSD_M1": "", "GBPUSD_M1": ""},
        },
    )
    store.save_project(projects_dir / "sample-proj-1.haru", doc)

    # Seed ResultStore with candidate results
    gateway.ensure_databanks_schema()
    r_store = ResultStore(gateway)
    r_store.save_result(
        "Results",
        RunResult(
            result_id="res-101",
            strategy_id="strat-alpha",
            strategy_name="Trend Follower A",
            databank_id="Results",
            metrics={
                "net_profit": 15000.0,
                "sharpe_ratio": 2.1,
                "drawdown": 500.0,
                "profit_factor": 1.9,
                "trades_count": 120,
                "win_rate": 62.0,
            },
        ),
    )

    app = create_app(
        gateway, projects_dir=projects_dir, scratch_root=tmp_path / "scratch"
    )
    with TestClient(app) as client:
        # Log in
        resp = client.post("/api/v1/auth/login", json={"password": "password"})
        assert resp.status_code == 200, resp.text
        token = resp.json()["data"]["token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield {
            "client": client,
            "projects_dir": projects_dir,
            "service": app.state.home_service,
            "jobs": app.state.job_manager,
        }


def test_unauthenticated_request_rejected(gateway: HostPersistence) -> None:
    """Verify requests without session token receive HTTP 401."""
    app = create_app(gateway)
    with TestClient(app) as client:
        resp = client.get("/api/v1/home")
        assert resp.status_code == 401
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"]["code"] in ("UNAUTHORIZED", "unauthorized")


def test_home_index_endpoint(test_setup: dict[str, Any]) -> None:
    """FR-home-routes-landing: verify home index returns recent projects list."""
    client = test_setup["client"]
    resp = client.get("/api/v1/home")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert "recent_projects" in data
    assert len(data["recent_projects"]) >= 1
    proj = data["recent_projects"][0]
    assert proj["id"] == "sample-proj-1"
    assert proj["name"] == "Alpha Momentum"


def test_home_about_endpoint(test_setup: dict[str, Any]) -> None:
    """FR-home-routes-about: verify application environment and license metadata."""
    client = test_setup["client"]
    resp = client.get("/api/v1/home/about")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["application"] == "HaruQuantAI"
    assert data["version"] == "unconfigured"
    assert "runtime" in data
    assert data["license"]["state"] == "unconfigured"
    assert "No license configured" in data["license"]["reason"]


def test_home_updates_endpoint(test_setup: dict[str, Any]) -> None:
    """FR-home-routes-updates: verify unconfigured update feed safely returns."""
    client = test_setup["client"]
    resp = client.get("/api/v1/home/updates")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["state"] == "unavailable"
    assert data["update_available"] is None
    assert "No release feed configured" in data["reason"]


def test_home_diagnostics_endpoint(test_setup: dict[str, Any]) -> None:
    """FR-home-routes-diagnostics: verify database and hardware metrics."""
    client = test_setup["client"]
    resp = client.get("/api/v1/home/diagnostics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["status"] == "OK"
    assert data["database"]["exists"] is True
    assert data["hardware"]["ram_total_bytes"] > 0
    assert "projects_dir" in data["directories"]


def test_project_document_endpoints(test_setup: dict[str, Any]) -> None:
    """FR-home-routes-project: verify loading, update, and conflict."""
    client = test_setup["client"]

    # 1. Load project
    resp = client.get("/api/v1/home/project/sample-proj-1")
    assert resp.status_code == 200
    doc = resp.json()["data"]
    assert doc["manifest"]["project_id"] == "sample-proj-1"

    # Missing project returns 404
    missing_resp = client.get("/api/v1/home/project/non-existent")
    assert missing_resp.status_code == 404

    # 2. Save settings successfully
    save_resp = client.post(
        "/api/v1/home/project/sample-proj-1/settings",
        json={
            "task_id": "task_01",
            "settings": {"timeframe": "M30"},
            "expected_revision": 1,
        },
    )
    assert save_resp.status_code == 200
    res = save_resp.json()["data"]
    assert res["revision"] == 2

    # 3. Revision conflict (stale revision 1 passed when current is 2)
    conflict_resp = client.post(
        "/api/v1/home/project/sample-proj-1/settings",
        json={
            "task_id": "task_01",
            "settings": {"timeframe": "H4"},
            "expected_revision": 1,
        },
    )
    assert conflict_resp.status_code == 409
    err = conflict_resp.json()["error"]
    assert err["code"] in ("CONFLICT", "conflict")


def test_project_notes_endpoints(test_setup: dict[str, Any]) -> None:
    """FR-home-routes-notes: verify saving notes and conflict handling."""
    client = test_setup["client"]

    # Save notes with expected_revision=1
    resp = client.post(
        "/api/v1/home/project/sample-proj-1/notes",
        json={
            "notes": "Updated research observations with UTF-8: äöü and emoji 🚀",
            "expected_revision": 1,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["revision"] == 2

    # Conflict check (stale revision 1 when current is now 2)
    conflict_resp = client.post(
        "/api/v1/home/project/sample-proj-1/notes",
        json={"notes": "Stale draft", "expected_revision": 1},
    )
    assert conflict_resp.status_code == 409


def test_template_and_resource_endpoints(test_setup: dict[str, Any]) -> None:
    """FR-home-routes-template & FR-home-routes-resources: verify template and symbol mapping."""
    client = test_setup["client"]

    # Apply valid template
    tpl_resp = client.post(
        "/api/v1/home/project/sample-proj-1/template",
        json={
            "task_id": "task_01",
            "strategy_type": "Advanced",
            "expected_revision": 1,
        },
    )
    assert tpl_resp.status_code == 200
    assert tpl_resp.json()["data"]["template"] == "Advanced"

    # Apply invalid template -> 422
    inv_resp = client.post(
        "/api/v1/home/project/sample-proj-1/template",
        json={
            "task_id": "task_01",
            "strategy_type": "UnsupportedType",
            "expected_revision": 2,
        },
    )
    assert inv_resp.status_code == 422

    # Resolve resources
    res_resp = client.post(
        "/api/v1/home/project/sample-proj-1/resources/resolve",
        json={
            "resolutions": {"EURUSD_M1": "EURUSD", "GBPUSD_M1": "GBPUSD"},
            "expected_revision": 2,
        },
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["data"]["resolved_count"] == 2


def test_engine_lifecycle_and_dashboard_endpoints(
    test_setup: dict[str, Any],
) -> None:
    """FR-home-routes-engine & FR-home-routes-dashboard: verify engine controls and leaderboard."""
    client = test_setup["client"]
    proj_id = "sample-proj-1"

    # 1. Initial engine status is IDLE
    status_resp = client.get(f"/api/v1/home/engine/{proj_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["status"] == "IDLE"

    # 2. Start engine
    start_resp = client.post(
        f"/api/v1/home/engine/{proj_id}/start",
        json={"task_id": "task_01", "expected_revision": 1},
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["data"]["status"] == "RUNNING"

    job_id = start_resp.json()["data"]["job_id"]
    # Start again -> 409 conflict
    start_again = client.post(
        f"/api/v1/home/engine/{proj_id}/start",
        json={"task_id": "task_01", "expected_revision": 1},
    )
    assert start_again.status_code == 409

    # 3. Pause engine
    pause_resp = client.post(
        f"/api/v1/home/engine/{proj_id}/pause", json={"job_id": job_id}
    )
    assert pause_resp.status_code == 200
    assert pause_resp.json()["data"]["status"] == "PAUSED"

    # 4. Resume engine
    resume_resp = client.post(
        f"/api/v1/home/engine/{proj_id}/resume", json={"job_id": job_id}
    )
    assert resume_resp.status_code == 200
    assert resume_resp.json()["data"]["status"] == "RUNNING"

    # 5. Stop engine
    stop_resp = client.post(
        f"/api/v1/home/engine/{proj_id}/stop", json={"job_id": job_id}
    )
    assert stop_resp.status_code == 200
    assert test_setup["jobs"].wait_for_job(job_id, timeout=10).status == "CANCELLED"

    # 6. Dashboard results leaderboard
    dash_resp = client.get(
        f"/api/v1/home/dashboard/results?project_id={proj_id}&metric=net_profit&limit=5"
    )
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()["data"]
    assert dash_data["metric"] == "net_profit"
    assert len(dash_data["strategies"]) >= 1
    top_strat = dash_data["strategies"][0]
    assert top_strat["name"] == "Trend Follower A"
    assert top_strat["net_profit"] == 15000.0


def test_routes_lazy_service_construction(gateway: HostPersistence) -> None:
    """Verify _get_service lazily creates HomeService from app state."""
    app = create_app(gateway)
    with TestClient(app) as client:
        resp = client.post("/api/v1/auth/login", json={"password": "password"})
        assert resp.status_code == 200
        token = resp.json()["data"]["token"]
        client.headers["Authorization"] = f"Bearer {token}"
        app.state.home_service = None
        r = client.get("/api/v1/home")
        assert r.status_code == 200
        assert app.state.home_service is not None


def test_routes_error_mappings(test_setup: dict[str, Any]) -> None:
    """Verify error branch mappings across all routes."""
    client = test_setup["client"]

    # Invalid project IDs and missing projects
    assert client.get("/api/v1/home/project/bad@id").status_code == 422
    assert (
        client.post(
            "/api/v1/home/project/bad@id/settings",
            json={"task_id": "t", "expected_revision": 1},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/home/project/nonexistent/settings",
            json={"task_id": "t", "expected_revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/home/project/bad@id/notes",
            json={"notes": "n", "expected_revision": 1},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/home/project/nonexistent/notes",
            json={"notes": "n", "expected_revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/home/project/bad@id/template",
            json={"task_id": "t", "strategy_type": "Simple", "expected_revision": 1},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/home/project/nonexistent/template",
            json={"task_id": "t", "strategy_type": "Simple", "expected_revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/home/project/bad@id/resources/resolve",
            json={"resolutions": {}, "expected_revision": 1},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/home/project/nonexistent/resources/resolve",
            json={"resolutions": {}, "expected_revision": 1},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/v1/home/project/sample-proj-1/resources/resolve",
            json={"resolutions": {"SYM": "NONEXISTENT"}, "expected_revision": 1},
        ).status_code
        == 422
    )
    assert client.post("/api/v1/home/engine/bad@id/start", json={}).status_code == 422
    assert (
        client.post("/api/v1/home/engine/nonexistent/start", json={}).status_code == 404
    )
    assert (
        client.post(
            "/api/v1/home/engine/sample-proj-1/invalid_action", json={}
        ).status_code
        == 422
    )
    assert client.get("/api/v1/home/engine/bad@id/status").status_code == 422
    assert client.get("/api/v1/home/engine/nonexistent/status").status_code == 404
    assert (
        client.get("/api/v1/home/dashboard/results?project_id=bad@id").status_code
        == 422
    )
    assert (
        client.get("/api/v1/home/dashboard/results?project_id=nonexistent").status_code
        == 404
    )
    assert (
        client.get(
            "/api/v1/home/dashboard/results?project_id=sample-proj-1&databank_id=NonexistentDatabank"
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/api/v1/home/dashboard/results?project_id=sample-proj-1&metric=invalid"
        ).status_code
        == 422
    )
    assert (
        client.get(
            "/api/v1/home/dashboard/results?project_id=sample-proj-1&sample_type=invalid"
        ).status_code
        == 422
    )
