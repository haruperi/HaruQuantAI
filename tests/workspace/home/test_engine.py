"""Unit and integration tests for Home engine lifecycle controls and dashboard rankings.

Description:
    Tests HomeService engine execution actions (start, pause, resume, stop),
    state validation, telemetry reporting, and dashboard strategy candidate ranking.

Purpose:
    FEAT-HOME-ENGINE-TESTS: Engine and dashboard service test verification.

Key Capabilities:
    - FR-home-engine-controls: Verify state transitions and conflict prevention.
    - FR-home-dashboard-ranking: Verify strategy sorting by performance metrics.

Python API Usage:
    pytest tests/workspace/home/test_engine.py

CLI Usage:
    uv run python -m pytest tests/workspace/home/test_engine.py -q
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from app.core.host.persistence import HostPersistence
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
from app.workspace.home.service import HomeService
from tests.workspace.home.test_execution_acceptance import market, project


@pytest.fixture
def engine_service(tmp_path: Path) -> Generator[dict[str, Any]]:
    """Set up HomeService with temporary database, JobManager, and candidate results."""
    db_path = tmp_path / "engine_test.db"
    db_path.touch()
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    gateway = HostPersistence(db_path)
    gateway.ensure_datasets_schema()
    market(tmp_path, gateway)
    gateway.ensure_jobs_schema()
    gateway.ensure_databanks_schema()
    r_store = ResultStore(gateway)
    job_mgr = JobManager(persistence=gateway)

    p_store = ProjectStore()
    for pid in ("test-project-1", "test-project-err", "test-proj"):
        p_store.save_project(
            projects_dir / f"{pid}.haru",
            ProjectDocument(
                manifest=ProjectManifest(
                    project_id=pid,
                    name=f"Project {pid}",
                    schema_version=1,
                ),
                pipeline=("t1",),
                databanks={"Results": "Results"},
                tasks={
                    "t1": TaskDocument(
                        task_id="t1",
                        task_type="build",
                        databank_target="Results",
                        settings=dict(
                            project("RANDOM", candidates=1000).tasks["task"].settings
                        ),
                    )
                },
                metadata={"revision": 1},
            ),
        )

    # Seed multiple candidate results to test ranking
    r_store.save_result(
        "Results",
        RunResult(
            result_id="res-1",
            strategy_id="strat-1",
            strategy_name="Strategy Low Profit",
            databank_id="Results",
            metrics={
                "net_profit": 5000.0,
                "sharpe_ratio": 1.2,
                "drawdown": 400.0,
                "trades_count": 50,
            },
        ),
    )
    r_store.save_result(
        "Results",
        RunResult(
            result_id="res-2",
            strategy_id="strat-2",
            strategy_name="Strategy High Profit",
            databank_id="Results",
            metrics={
                "net_profit": 25000.0,
                "sharpe_ratio": 2.8,
                "drawdown": 800.0,
                "trades_count": 180,
            },
        ),
    )
    r_store.save_result(
        "Results",
        RunResult(
            result_id="res-3",
            strategy_id="strat-3",
            strategy_name="Strategy Mid Profit",
            databank_id="Results",
            metrics={
                "net_profit": 12000.0,
                "sharpe_ratio": 3.1,
                "drawdown": 250.0,
                "trades_count": 95,
            },
        ),
    )

    service = HomeService(
        persistence=gateway,
        result_store=r_store,
        project_store=p_store,
        projects_dir=projects_dir,
        job_manager=job_mgr,
    )
    yield {"service": service, "store": r_store, "job_manager": job_mgr}
    job_mgr.shutdown()


def test_engine_state_transitions(engine_service: dict[str, Any]) -> None:
    """FR-home-engine-controls: verify valid lifecycle transitions."""
    service: HomeService = engine_service["service"]
    proj_id = "test-project-1"

    # 1. Initially IDLE
    st = service.get_engine_status(proj_id)
    assert st["status"] == "IDLE"

    # 2. Start
    res = service.engine_action(proj_id, "start", "t1", expected_revision=1)
    job_id = res["job_id"]
    assert res["status"] == "RUNNING"
    st = service.get_engine_status(proj_id)
    assert st["status"] == "RUNNING"

    # 3. Pause
    res = service.engine_action(proj_id, "pause", job_id=job_id)
    assert res["status"] == "PAUSED"
    st = service.get_engine_status(proj_id)
    assert st["status"] == "PAUSED"

    # 4. Resume
    res = service.engine_action(proj_id, "resume", job_id=job_id)
    assert res["status"] == "RUNNING"
    st = service.get_engine_status(proj_id)
    assert st["status"] == "RUNNING"

    # 5. Stop
    res = service.engine_action(proj_id, "stop", job_id=job_id)
    terminal = engine_service["job_manager"].wait_for_job(job_id, timeout=10)
    assert terminal.status == "CANCELLED"
    assert service.get_engine_status(proj_id, job_id)["status"] == "CANCELLED"


def test_engine_invalid_transitions(engine_service: dict[str, Any]) -> None:
    """FR-home-engine-controls: verify illegal transitions raise domain errors."""
    service: HomeService = engine_service["service"]
    proj_id = "test-project-err"

    # Pause when IDLE -> NOT_RUNNING
    with pytest.raises(DomainError) as exc_info:
        service.engine_action(proj_id, "pause")
    assert exc_info.value.code == "JOB_NOT_FOUND"

    # Resume when IDLE -> NOT_PAUSED
    with pytest.raises(DomainError) as exc_info:
        service.engine_action(proj_id, "resume")
    assert exc_info.value.code == "JOB_NOT_FOUND"

    # Stop when IDLE -> NOT_RUNNING
    with pytest.raises(DomainError) as exc_info:
        service.engine_action(proj_id, "stop")
    assert exc_info.value.code == "JOB_NOT_FOUND"

    # Start -> RUNNING
    started = service.engine_action(proj_id, "start", "t1", expected_revision=1)

    # Start when already RUNNING -> ALREADY_RUNNING
    with pytest.raises(DomainError) as exc_info:
        service.engine_action(proj_id, "start", "t1", expected_revision=1)
    assert exc_info.value.code == "ALREADY_RUNNING"

    # Invalid action name -> INVALID_ENGINE_ACTION
    with pytest.raises(DomainError) as exc_info:
        service.engine_action(proj_id, "unknown_action")
    assert exc_info.value.code == "INVALID_ENGINE_ACTION"

    # Clean up
    service.engine_action(proj_id, "stop", job_id=started["job_id"])


def test_dashboard_results_ranking(engine_service: dict[str, Any]) -> None:
    """FR-home-dashboard-ranking: verify candidates ranked by metric."""
    service: HomeService = engine_service["service"]

    # Rank by net_profit descending
    res_profit = service.get_dashboard_results(
        "test-proj", metric="net_profit", limit=10
    )
    strats = res_profit["strategies"]
    assert len(strats) == 3
    assert strats[0]["name"] == "Strategy High Profit"
    assert strats[0]["net_profit"] == 25000.0
    assert strats[1]["name"] == "Strategy Mid Profit"
    assert strats[1]["net_profit"] == 12000.0
    assert strats[2]["name"] == "Strategy Low Profit"
    assert strats[2]["net_profit"] == 5000.0

    # Rank by sharpe_ratio descending
    res_sharpe = service.get_dashboard_results(
        "test-proj", metric="sharpe_ratio", limit=10
    )
    strats_sharpe = res_sharpe["strategies"]
    assert strats_sharpe[0]["name"] == "Strategy Mid Profit"
    assert strats_sharpe[0]["sharpe_ratio"] == 3.1
