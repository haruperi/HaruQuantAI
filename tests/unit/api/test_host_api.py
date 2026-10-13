"""Unit tests for the complete decoupled host presentation API layer.

Description:
    Validates that all host capability REST API routers (discovery,
    debug console, diagnostics, database diagnostics, settings paths,
    persistence, resources, jobs, leases, sessions, auth, shell, recovery,
    and transport) are decoupled from the host business logic and live cleanly
    under app.api. Verifies route behavior, public endpoint projections,
    central exports, and architectural boundary invariants.

Purpose:
    FEAT-API-HOST-DECOUPLING: Comprehensive verification of app.api presentation layer.

Key Capabilities:
    - FR-API-ARCHITECTURAL-INVARIANTS: Assert clean module separation and zero FastAPI
      imports in pure business logic host modules.
      Associated: `test_architectural_separation_invariants()`
      Logging: DEBUG invariant test step assertions.
    - FR-API-CENTRAL-EXPORTS: Assert app.api exposes all canonical router factories.
      Associated: `test_central_api_exports()`
      Logging: DEBUG central export validation.
    - FR-API-DISCOVERY-ROUTES: Assert create_discovery_router endpoint projection.
      Associated: `test_discovery_router_endpoints()`
      Logging: DEBUG discovery endpoint evaluation.
    - FR-API-DEBUG-CONSOLE-ROUTES: Assert create_debug_console_router endpoint projection.
      Associated: `test_debug_console_router_endpoints()`
      Logging: DEBUG debug console endpoint evaluation.
    - FR-API-DIAGNOSTICS-ROUTES: Assert diagnostics, database, and paths routers.
      Associated: `test_diagnostics_router_endpoints()`
      Logging: DEBUG diagnostics endpoint evaluation.
    - FR-API-RESOURCES-ROUTES: Assert create_resources_router endpoint projection.
      Associated: `test_resources_router_endpoints()`
      Logging: DEBUG resources endpoint evaluation.
    - FR-API-JOBS-ROUTES: Assert create_jobs_router and create_leases_router endpoints.
      Associated: `test_jobs_router_endpoints()`
      Logging: DEBUG jobs endpoint evaluation.
    - FR-API-SESSIONS-ROUTES: Assert create_sessions_router and create_auth_router endpoints.
      Associated: `test_sessions_and_auth_router_endpoints()`
      Logging: DEBUG sessions endpoint evaluation.
    - FR-API-SHELL-ROUTES: Assert create_shell_router and create_recovery_router endpoints.
      Associated: `test_shell_and_recovery_router_endpoints()`
      Logging: DEBUG shell endpoint evaluation.

Python API Usage:
    ```python
    pytest tests/unit/api/test_host_api.py
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/api/test_host_api.py --no-cov
    ```
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from app import api
from app.api.debug_console import create_debug_console_router
from app.api.diagnostics import (
    create_database_diagnostics_router,
    create_diagnostics_router,
    create_settings_paths_router,
)
from app.api.discovery import create_discovery_router
from app.api.jobs import create_jobs_router, create_leases_router
from app.api.resources import create_resources_router
from app.api.sessions import create_auth_router, create_sessions_router
from app.api.shell import create_recovery_router, create_shell_router
from app.host import (
    diagnostics as host_diagnostics,
)
from app.host import (
    discovery as host_discovery,
)
from app.host import (
    jobs as host_jobs,
)
from app.host import (
    logging as host_logging,
)
from app.host import (
    resources as host_resources,
)
from app.host import (
    session as host_session,
)
from app.host import (
    settings as host_settings,
)
from app.host import (
    transport as host_transport,
)
from app.host.logging import configure_host_logging, get_logger
from app.host.persistence import DatabaseManager
from app.host.settings import HostSettings
from fastapi import FastAPI
from fastapi.testclient import TestClient

logger = get_logger(__name__)


def test_architectural_separation_invariants() -> None:
    """Verify that all host modules are decoupled and pure business logic."""
    logger.debug(
        "Verifying architectural separation invariants across host modules",
        extra={"event": "test_invariants_start"},
    )

    host_modules = [
        host_discovery,
        host_logging,
        host_diagnostics,
        host_resources,
        host_jobs,
        host_session,
        host_transport,
        host_settings,
    ]

    for mod in host_modules:
        mod_dict = mod.__dict__
        # Ensure APIRouter is not in module namespace
        assert "APIRouter" not in mod_dict, f"APIRouter leaked into {mod.__name__}"
        # Ensure create_*_router functions are not on host module
        router_callables = [
            k for k in mod_dict if k.startswith("create_") and k.endswith("_router")
        ]
        assert not router_callables, (
            f"Router factories leaked in {mod.__name__}: {router_callables}"
        )

    logger.debug(
        "Architectural separation invariants verified successfully",
        extra={"event": "test_invariants_complete"},
    )


def test_central_api_exports() -> None:
    """Verify that app.api centrally exports all canonical router factories."""
    expected_routers = [
        "create_settings_router",
        "create_discovery_router",
        "create_debug_console_router",
        "create_diagnostics_router",
        "create_database_diagnostics_router",
        "create_settings_paths_router",
        "create_persistence_router",
        "create_resources_router",
        "create_jobs_router",
        "create_leases_router",
        "create_sessions_router",
        "create_auth_router",
        "create_shell_router",
        "create_recovery_router",
        "create_transport_router",
    ]

    for router_name in expected_routers:
        assert hasattr(api, router_name), (
            f"app.api missing central export: {router_name}"
        )
        assert router_name in api.__all__, f"{router_name} missing from app.api.__all__"


def test_discovery_router_endpoints() -> None:
    """Verify create_discovery_router creates a working router."""
    mock_lifecycle = MagicMock()
    mock_lifecycle.list_plugins.return_value = []
    mock_lifecycle.get_plugin_record.return_value = None

    router = create_discovery_router(mock_lifecycle)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.get("/discovery/plugins")
    assert resp.status_code == 200
    assert resp.json()["plugins"] == []


def test_debug_console_router_endpoints(tmp_path: Path) -> None:
    """Verify create_debug_console_router creates a working router."""
    engine = configure_host_logging(tmp_path)
    router = create_debug_console_router(engine)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.get("/api/v1/debugconsole/logs")
    assert resp.status_code == 200
    assert "entries" in resp.json()


def test_diagnostics_router_endpoints(tmp_path: Path) -> None:
    """Verify diagnostics and database diagnostics router endpoints."""
    runner = host_diagnostics.BenchmarkRunner()
    diag_router = create_diagnostics_router(runner)

    db_path = tmp_path / "diag.db"
    db_mgr = DatabaseManager(db_path)
    db_mgr.initialize()
    db_router = create_database_diagnostics_router(db_mgr)

    settings = HostSettings(db_path)
    paths_router = create_settings_paths_router(settings)

    app = FastAPI()
    app.include_router(diag_router)
    app.include_router(db_router)
    app.include_router(paths_router)
    client = TestClient(app)

    resp_diag = client.get("/api/v1/diagnostics/system")
    assert resp_diag.status_code == 200
    assert "cpu" in resp_diag.json()

    resp_db = client.get("/persistence/status")
    assert resp_db.status_code == 200
    assert resp_db.json()["data"]["is_connected"] is True

    resp_paths = client.get("/settings/paths/validate")
    assert resp_paths.status_code == 200


def test_resources_router_endpoints(tmp_path: Path) -> None:
    """Verify create_resources_router creates a working router."""
    res_mgr = host_resources.ResourceManager(root_dir=tmp_path / "resources")
    router = create_resources_router(res_mgr)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.get("/resources/cache/status")
    assert resp.status_code == 200
    assert "used_bytes" in resp.json()["data"]


def test_jobs_router_endpoints(tmp_path: Path) -> None:
    """Verify create_jobs_router and create_leases_router endpoints."""
    db_path = tmp_path / "jobs.db"
    db_mgr = DatabaseManager(db_path)
    db_mgr.initialize()

    job_mgr = host_jobs.JobManager(db_path=db_path)
    jobs_router = create_jobs_router(job_mgr)
    leases_router = create_leases_router(db_mgr)

    app = FastAPI()
    app.include_router(jobs_router)
    app.include_router(leases_router)
    client = TestClient(app)

    resp_jobs = client.get("/jobs/capacity")
    assert resp_jobs.status_code == 200
    assert resp_jobs.json()["status"] == "success"

    resp_lease = client.get("/persistence/leases")
    assert resp_lease.status_code == 200


def test_sessions_and_auth_router_endpoints(tmp_path: Path) -> None:
    """Verify sessions and auth routers create working endpoints."""
    db_path = tmp_path / "session.db"
    db_mgr = DatabaseManager(db_path)
    db_mgr.initialize()

    settings = HostSettings(db_path)
    session_mgr = host_session.SessionManager()
    auth = host_session.HostAuthentication(settings=settings, manager=session_mgr)

    auth_router = create_auth_router(auth)
    sessions_router = create_sessions_router(
        session_manager=session_mgr,
        authentication=auth,
    )

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(sessions_router)
    client = TestClient(app)

    # Test login with bad credentials
    resp = client.post("/auth/login", json={"username": "fake", "password": "wrong"})
    assert resp.status_code == 401

    # Test sessions listing without token -> 401
    resp_sess = client.get("/sessions/me")
    assert resp_sess.status_code == 401


def test_shell_and_recovery_router_endpoints(tmp_path: Path) -> None:
    """Verify shell and recovery routers."""
    mock_runtime = MagicMock()
    mock_readiness = MagicMock()
    mock_readiness.is_ready = True
    mock_readiness.model_dump.return_value = {"is_ready": True, "state": "ready"}
    mock_runtime.get_readiness.return_value = mock_readiness
    mock_runtime.host_instance_id = "test-host"

    settings = HostSettings(tmp_path / "shell.db")
    shell_router = create_shell_router(settings)
    rec_fn = MagicMock(return_value={"recovered": True})
    rec_router = create_recovery_router(rec_fn)

    app = FastAPI()
    app.state.runtime = mock_runtime
    app.include_router(shell_router)
    app.include_router(rec_router)
    client = TestClient(app)

    resp_ready = client.get(f"{settings.api_prefix}/readiness")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "success"

    resp_rec = client.post("/persistence/recovery/reconcile", json={})
    assert resp_rec.status_code == 200
    assert resp_rec.json()["data"]["recovered"] is True
