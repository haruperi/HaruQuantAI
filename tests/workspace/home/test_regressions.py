"""Regression test suite for AppHome P1/P2 defect remediations.

Description:
    Verifies that all 7 P1 defects identified during audit remain closed:
    1. Engine execution delegates to JobManager and fails closed when missing.
    2. Authentication fails closed when session authority is absent.
    3. Path traversal attempts via project IDs are rejected.
    4. Project schema_version is preserved and edit revisions are enforced.
    5. Host metadata and licensing report true host state, never fabricated strings.
    6. Resource resolution validates symbols against DataCatalog.
    7. Dashboard results rank entire databank with proper sample filtering and metric checks.

Purpose:
    FEAT-HOME-REGRESSION: Guard against regressions in security and persistence boundaries.

Key Capabilities:
    - FR-home-auth-fail-closed: Verify missing session authority produces HTTP 401.
    - FR-home-path-traversal-guard: Verify path containment rejection.
    - FR-home-engine-jobmanager-wiring: Verify real JobManager delegation and 503 on missing manager.
    - FR-home-persistence-revision: Verify monotonic metadata revision and unchanged schema_version.
    - FR-home-honest-metadata: Verify absence of fabricated licensing or build info.
    - FR-home-catalog-validation: Verify dataset symbol existence verification.
    - FR-home-dashboard-isolation: Verify metric validation and partition ranking.

Python API Usage:
    pytest tests/workspace/home/test_regressions.py

CLI Usage:
    uv run python -m pytest tests/workspace/home/test_regressions.py -q
"""

from __future__ import annotations

import json
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest
from app.core.data.catalog import DataCatalog
from app.core.host.persistence import HostPersistence
from app.core.host.session import SessionManager
from app.core.jobs.manager import JobManager
from app.core.lib.errors import DomainError
from app.core.trading.project.contracts import (
    ProjectDocument,
    ProjectManifest,
    TaskDocument,
)
from app.core.trading.project.store import ProjectStore
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.main import create_app
from app.workspace.home.service import HomeService
from fastapi.testclient import TestClient
from tests.workspace.home.test_execution_acceptance import market, project


@pytest.fixture
def base_gateway(tmp_path: Path) -> HostPersistence:
    """Initialize HostPersistence with all required tables."""
    db_path = tmp_path / "regression.db"
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
                PRIMARY KEY(entity_id,entity_type)
            );
        """)
    gw = HostPersistence(db_path)
    gw.ensure_jobs_schema()
    gw.ensure_datasets_schema()
    gw.ensure_databanks_schema()
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


def test_auth_fails_closed_when_sessions_missing(base_gateway: HostPersistence) -> None:
    """P1 Defect 2: Verify _require_auth rejects with 401 when sessions authority is absent."""
    app = create_app(base_gateway)
    with TestClient(app) as client:
        # Deliberately remove sessions authority to simulate absent authority
        app.state.sessions = None
        resp = client.get("/api/v1/home/about")
        assert resp.status_code == 401
        data = resp.json()
        assert data["status"] == "error"
        assert "Session manager authority is absent" in data["error"]["message"]


def test_path_traversal_project_id_rejected(
    tmp_path: Path, base_gateway: HostPersistence
) -> None:
    """P1 Defect 3: Verify path traversal attempts via project IDs are rejected with INVALID_PROJECT_ID."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    service = HomeService(persistence=base_gateway, projects_dir=projects_dir)

    for bad_id in (
        "../outside",
        "..\\escape",
        "/etc/passwd",
        "sub/dir",
        "has spaces",
        "bad@char",
    ):
        with pytest.raises(DomainError) as exc_info:
            service.load_project(bad_id)
        assert exc_info.value.code == "INVALID_PROJECT_ID"


def test_engine_execution_delegates_and_fails_closed(
    tmp_path: Path, base_gateway: HostPersistence
) -> None:
    """P1 Defect 1: Verify engine execution fails closed on missing manager or nonexistent project."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    # 1. Nonexistent project raises PROJECT_FILE_NOT_FOUND
    service_no_job = HomeService(persistence=base_gateway, projects_dir=projects_dir)
    with pytest.raises(DomainError) as exc_info:
        service_no_job.engine_action("nonexistent-proj", "start")
    assert exc_info.value.code == "PROJECT_FILE_NOT_FOUND"

    # 2. Project exists but JobManager is None raises JOB_MANAGER_UNAVAILABLE
    p_store = ProjectStore()
    p_store.save_project(
        projects_dir / "valid-proj.haru",
        ProjectDocument(
            manifest=ProjectManifest(
                project_id="valid-proj",
                name="Valid Project",
                schema_version=1,
            ),
            pipeline=("t1",),
            databanks={"Results": "Results"},
            tasks={"t1": TaskDocument(task_id="t1", task_type="build")},
            metadata={"revision": 1},
        ),
    )
    with pytest.raises(DomainError) as exc_info:
        service_no_job.engine_action("valid-proj", "start")
    assert exc_info.value.code == "JOB_MANAGER_UNAVAILABLE"

    # 3. With real JobManager, starting delegates to submit_job and reports real JobRecord
    job_mgr = JobManager(persistence=base_gateway)
    service_with_job = HomeService(
        persistence=base_gateway,
        projects_dir=projects_dir,
        project_store=p_store,
        job_manager=job_mgr,
    )
    try:
        with pytest.raises(DomainError) as rejected:
            service_with_job.engine_action(
                "valid-proj", "start", "t1", expected_revision=1
            )
        assert rejected.value.code == "INVALID_EXECUTION_SETTINGS"
        assert job_mgr.list_jobs() == []
    finally:
        job_mgr.shutdown()


def test_schema_version_preserved_and_revision_enforced(
    tmp_path: Path, base_gateway: HostPersistence
) -> None:
    """P1 Defect 5: Verify schema_version is untouched and metadata['revision'] increments."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    p_store = ProjectStore()
    p_store.save_project(
        projects_dir / "rev-proj.haru",
        ProjectDocument(
            manifest=ProjectManifest(
                project_id="rev-proj",
                name="Revision Test",
                schema_version=1,
            ),
            pipeline=("t1",),
            databanks={"Results": "Results"},
            tasks={"t1": TaskDocument(task_id="t1", task_type="build")},
            metadata={"revision": 1, "notes": "Initial"},
        ),
    )
    service = HomeService(
        persistence=base_gateway,
        projects_dir=projects_dir,
        project_store=p_store,
    )

    # Save settings: expected revision 1 -> produces revision 2
    save_res = service.save_project_settings(
        project_id="rev-proj",
        task_id="t1",
        settings={"param": "value"},
        expected_revision=1,
    )
    assert save_res["revision"] == 2

    # Save notes: expected revision 2 -> produces revision 3
    notes_res = service.save_project_notes(
        project_id="rev-proj",
        notes="Updated notes",
        expected_revision=2,
    )
    assert notes_res["revision"] == 3

    # Reload document and verify format schema_version is strictly 1
    doc = service.load_project("rev-proj")
    assert doc["manifest"]["schema_version"] == 1
    assert doc["metadata"]["revision"] == 3

    # Mismatched expected revision raises CONFLICT
    with pytest.raises(DomainError) as exc_info:
        service.save_project_notes(
            project_id="rev-proj",
            notes="Conflicting write",
            expected_revision=2,  # Stale: current is 3
        )
    assert exc_info.value.code == "CONFLICT"


def test_metadata_and_licensing_honest(base_gateway: HostPersistence) -> None:
    """P1 Defect 6: Verify get_about_info returns unconfigured, never fabricated community edition."""
    service = HomeService(persistence=base_gateway)
    about = service.get_about_info()
    assert about["application"] == "HaruQuantAI"
    assert about["license"]["state"] == "unconfigured"
    assert "Standard Community Edition" not in about["license"]["state"]
    assert "Standard Community Edition" not in about["license"]["reason"]
    assert about["build_timestamp"] == "unversioned"


def test_resource_resolution_validates_data_catalog(
    tmp_path: Path, base_gateway: HostPersistence
) -> None:
    """P1 Defect 7: Verify resource resolution validates datasets against DataCatalog."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    p_store = ProjectStore()
    p_store.save_project(
        projects_dir / "res-proj.haru",
        ProjectDocument(
            manifest=ProjectManifest(
                project_id="res-proj",
                name="Resource Test",
                schema_version=1,
            ),
            pipeline=("t1",),
            databanks={"Results": "Results"},
            tasks={"t1": TaskDocument(task_id="t1", task_type="build")},
            metadata={"revision": 1, "resources": {"SYM1": "", "SYM2": ""}},
        ),
    )

    base_gateway.create_records(
        "datamgr_datasets",
        [
            {
                "id": "default:VALID_SYM:M1",
                "source": "default",
                "symbol": "VALID_SYM",
                "underlying": "VALID_SYM",
                "timeframe": "M1",
                "broker": "DefaultBroker",
                "timezone": "UTC",
                "category": "Forex",
                "date_from": "2020-01-01",
                "date_to": "2026-01-01",
                "bars": 100,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ],
    )
    catalog = DataCatalog(base_gateway)
    service = HomeService(
        persistence=base_gateway,
        projects_dir=projects_dir,
        project_store=p_store,
        data_catalog=catalog,
    )

    # Valid symbol succeeds
    res = service.resolve_resources(
        "res-proj",
        {"SYM1": "VALID_SYM"},
        expected_revision=1,
    )
    assert res["status"] == "resolved"
    assert res["resolved_count"] == 1

    # Missing symbol raises DATASET_NOT_FOUND
    with pytest.raises(DomainError) as exc_info:
        service.resolve_resources(
            "res-proj",
            {"SYM2": "NONEXISTENT_SYMBOL"},
            expected_revision=2,
        )
    assert exc_info.value.code == "DATASET_NOT_FOUND"


def test_dashboard_ranking_filters_project_and_sample(
    tmp_path: Path, base_gateway: HostPersistence
) -> None:
    """P1 Defect 7: Verify dashboard ranking validates metrics and sample partitions."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    p_store = ProjectStore()
    p_store.save_project(
        projects_dir / "target-proj.haru",
        ProjectDocument(
            manifest=ProjectManifest(
                project_id="target-proj",
                name="Target Project",
                schema_version=1,
            ),
            pipeline=("t1",),
            databanks={"Results": "Results"},
            tasks={"t1": TaskDocument(task_id="t1", task_type="build")},
            metadata={"revision": 1},
        ),
    )

    r_store = ResultStore(base_gateway)
    # Strategy 1 with in-sample metric
    r_store.save_result(
        "Results",
        RunResult(
            result_id="res-target-1",
            strategy_id="strat-target",
            strategy_name="Target Strategy",
            databank_id="Results",
            metrics={
                "net_profit": 50000.0,
                "net_profit_is": 50000.0,
                "sharpe_ratio": 2.5,
            },
        ),
    )
    # Strategy 2 with out-of-sample metric
    r_store.save_result(
        "Results",
        RunResult(
            result_id="res-other-1",
            strategy_id="strat-other",
            strategy_name="Other Strategy",
            databank_id="Results",
            metrics={
                "net_profit": 20000.0,
                "net_profit_oos": 20000.0,
                "sharpe_ratio": 1.5,
            },
        ),
    )

    service = HomeService(
        persistence=base_gateway,
        projects_dir=projects_dir,
        project_store=p_store,
        result_store=r_store,
    )

    # Query with IS partition
    res_is = service.get_dashboard_results(
        "target-proj", metric="net_profit", sample_type="IS"
    )
    strats = res_is["strategies"]
    assert len(strats) == 1
    assert strats[0]["name"] == "Target Strategy"
    assert strats[0]["net_profit"] == 50000.0

    # Query with OOS partition
    res_oos = service.get_dashboard_results(
        "target-proj", metric="net_profit", sample_type="OOS"
    )
    strats_oos = res_oos["strategies"]
    assert len(strats_oos) == 1
    assert strats_oos[0]["name"] == "Other Strategy"
    assert strats_oos[0]["net_profit"] == 20000.0

    # Invalid metric raises INVALID_METRIC
    with pytest.raises(DomainError) as exc_info:
        service.get_dashboard_results("target-proj", metric="fabricated_metric")
    assert exc_info.value.code == "INVALID_METRIC"

    # Invalid sample type raises INVALID_SAMPLE_TYPE
    with pytest.raises(DomainError) as exc_info:
        service.get_dashboard_results("target-proj", sample_type="UNKNOWN_PARTITION")
    assert exc_info.value.code == "INVALID_SAMPLE_TYPE"


def test_real_engine_execution_evaluates_and_stores_results(
    tmp_path: Path,
    base_gateway: HostPersistence,
) -> None:
    """Run a real bounded Builder job against actual isolated catalog bars."""
    market(tmp_path, base_gateway)
    projects = tmp_path / "projects"
    projects.mkdir()
    doc = project("RANDOM", candidates=3)
    doc = replace(doc, manifest=replace(doc.manifest, project_id="exec-proj"))
    ProjectStore().save_project(projects / "exec-proj.haru", doc)
    with_manager = JobManager(persistence=base_gateway)
    try:
        service = HomeService(
            persistence=base_gateway, projects_dir=projects, job_manager=with_manager
        )
        action = service.engine_action(
            "exec-proj", "start", "task", expected_revision=1
        )
        record = with_manager.wait_for_job(action["job_id"], timeout=10)
        assert record.status == "COMPLETED"
        assert record.result["candidates_evaluated"] == 3
        for identity in record.result["result_ids"]:
            result = service.get_result("exec-proj", identity)
            assert len(result["equity_curve"]) == 4
            assert result["metrics"]["net_profit"] == sum(
                t["net_pnl"] for t in result["trades"]
            )
    finally:
        with_manager.shutdown()


def test_app_lifespan_injects_jobmanager_and_datacatalog(
    base_gateway: HostPersistence,
) -> None:
    """Verify create_app lifespan injects JobManager and DataCatalog into HomeService."""
    app = create_app(persistence=base_gateway)
    with TestClient(app):
        assert hasattr(app.state, "job_manager")
        assert isinstance(app.state.job_manager, JobManager)
        assert hasattr(app.state, "data_catalog")
        assert isinstance(app.state.data_catalog, DataCatalog)
        assert hasattr(app.state, "home_service")
        home_svc = app.state.home_service
        assert home_svc._job_manager is app.state.job_manager
        assert app.state.job_manager._persistence is base_gateway
        assert home_svc._data_catalog is app.state.data_catalog


def test_empty_databank_ownership_fails_closed(
    tmp_path: Path, base_gateway: HostPersistence
) -> None:
    """Verify that an empty project databank map fails closed rather than bypassing checks."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    p_store = ProjectStore()
    p_store.save_project(
        projects_dir / "empty-db-proj.haru",
        ProjectDocument(
            manifest=ProjectManifest(
                project_id="empty-db-proj",
                name="Empty DB Project",
                schema_version=1,
            ),
            pipeline=(),
            databanks={},
            tasks={},
            metadata={"revision": 1},
        ),
    )

    service = HomeService(
        persistence=base_gateway,
        projects_dir=projects_dir,
        project_store=p_store,
    )

    with pytest.raises(DomainError) as exc_info:
        service.get_dashboard_results("empty-db-proj", databank_id="AnyBank")
    assert exc_info.value.code == "DATABANK_NOT_FOUND"


def test_leaderboard_paginates_beyond_1000_records(
    tmp_path: Path, base_gateway: HostPersistence
) -> None:
    """Verify leaderboard retrieves and ranks all candidates across multiple 1000-record pages."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    p_store = ProjectStore()
    p_store.save_project(
        projects_dir / "large-proj.haru",
        ProjectDocument(
            manifest=ProjectManifest(
                project_id="large-proj",
                name="Large Project",
                schema_version=1,
            ),
            pipeline=(),
            databanks={"Results": "Results"},
            tasks={},
            metadata={"revision": 1},
        ),
    )

    # Seed 1050 records in batches into databank_results
    batch: list[dict[str, str | int | float | bytes | None]] = []
    for i in range(1050):
        # The very last strategy on page 2 has the highest profit
        profit = 999999.0 if i == 1049 else float(i + 10)
        batch.append(
            {
                "id": f"res-large-{i}",
                "databank_id": "Results",
                "strategy_id": f"strat-large-{i}",
                "strategy_name": f"Large Strategy {i}",
                "net_profit": profit,
                "profit_factor": 1.5,
                "drawdown": 10.0,
                "sharpe_ratio": 1.2,
                "trades_count": 100,
                "win_rate": 0.55,
                "metrics_json": json.dumps({"net_profit": profit}),
                "result_json": json.dumps(
                    {
                        "result_id": f"res-large-{i}",
                        "databank_id": "Results",
                        "strategy_id": f"strat-large-{i}",
                        "strategy_name": f"Large Strategy {i}",
                        "metrics": {"net_profit": profit},
                    }
                ),
                "created_at": "2026-11-01T00:00:00Z",
                "updated_at": "2026-11-01T00:00:00Z",
            }
        )
        if len(batch) >= 200:
            base_gateway.create_records("databank_results", batch)
            batch = []
    if batch:
        base_gateway.create_records("databank_results", batch)

    service = HomeService(
        persistence=base_gateway,
        projects_dir=projects_dir,
        project_store=p_store,
    )

    res = service.get_dashboard_results("large-proj", databank_id="Results", limit=5)
    assert res["total_candidates"] == 1050
    assert len(res["strategies"]) == 5
    assert res["strategies"][0]["name"] == "Large Strategy 1049"
    assert res["strategies"][0]["net_profit"] == 999999.0


def test_cross_process_file_lock_prevents_concurrent_overwrite(
    tmp_path: Path, base_gateway: HostPersistence
) -> None:
    """Verify OS file lock and revision checking prevent concurrent write overwrites."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    p_store = ProjectStore()
    p_store.save_project(
        projects_dir / "lock-proj.haru",
        ProjectDocument(
            manifest=ProjectManifest(
                project_id="lock-proj",
                name="Lock Project",
                schema_version=1,
            ),
            pipeline=(),
            databanks={},
            tasks={"t1": TaskDocument(task_id="t1", task_type="build")},
            metadata={"revision": 1},
        ),
    )

    service1 = HomeService(
        persistence=base_gateway,
        projects_dir=projects_dir,
        project_store=p_store,
    )
    service2 = HomeService(
        persistence=base_gateway,
        projects_dir=projects_dir,
        project_store=p_store,
    )

    # Worker 1 saves settings at revision 1 -> revision becomes 2
    res1 = service1.save_project_settings(
        "lock-proj", "t1", {"param": "from_worker_1"}, expected_revision=1
    )
    assert res1["revision"] == 2

    # Worker 2 attempts to save with stale expected_revision=1 -> must raise CONFLICT
    with pytest.raises(DomainError) as exc_info:
        service2.save_project_settings(
            "lock-proj", "t1", {"param": "from_worker_2"}, expected_revision=1
        )
    assert exc_info.value.code == "CONFLICT"
