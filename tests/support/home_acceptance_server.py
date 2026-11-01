"""Isolated real-backend Home acceptance server.

Description:
    Reuses the Home test host schema in marked temporary roots and serves actual
    native projects, catalog bars and Core backtests without API interception.
Purpose:
    FEAT-HOME-BROWSER-ACCEPTANCE: Qualify actual browser-to-result workflows.
Key Capabilities:
    - FR-home-acceptance-isolation: Refuse unmarked existing stores; browser tests
      verify persisted identities and log actual project execution.
Python API Usage:
    gateway = seed_environment(temporary_root)
CLI Usage:
    uv run python -m tests.support.home_acceptance_server --root TEMP_ROOT --port 4180
"""

# Bootstrap must precede workspace imports to isolate default test stores.
# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import os
import tempfile
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from app.core.host import persistence as persistence_module

# Optional pytest bootstrap: redirect default constructors before importing any
# workspace modules. This changes only this test process, never application code
# or an existing user database.
_isolation_value = os.environ.get("HARU_PYTEST_ISOLATION_ROOT")
_isolation_root = Path(_isolation_value).resolve() if _isolation_value else None
if _isolation_root is not None:
    if not _isolation_root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise ValueError("Suite isolation root must be below the temporary directory")
    if not (_isolation_root / ".home-acceptance").is_file():
        raise ValueError("Suite isolation root must be explicitly test-owned")
    persistence_module._DEFAULT_PATH = _isolation_root / "host_test.db"

import uvicorn
from app.core.data.catalog import DataCatalog
from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.core.host.session import SessionManager
from app.core.jobs.manager import JobContext
from app.core.trading.project.envelope import (
    ProjectEnvelope,
    read_project_envelope,
    write_project_envelope,
)
from app.core.trading.project.store import ProjectStore
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.main import create_app
from app.workspace.home.execution import ProjectExecutor
from tests.workspace.home.test_execution_acceptance import (
    market,
    project,
    strategy_payload,
)

logger = get_logger(__name__)


def pytest_configure() -> None:
    """Initialize the optional full-suite default store in a marked temp root."""
    if _isolation_root is not None:
        make_gateway(_isolation_root)
        logger.info("FR-home-acceptance-isolation: redirected test-only default store")


def make_gateway(tmp_path: Path) -> HostPersistence:
    """Create isolated Home test schemas, or reopen the same test database."""
    db_path = tmp_path / "host_test.db"
    if db_path.exists():
        return HostPersistence(db_path)
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


def seed_environment(root: Path) -> HostPersistence:
    """Create test data in an empty root; restart only previously marked roots."""
    root = root.resolve()
    marker = root / ".home-acceptance"
    if root.exists() and not marker.is_file() and any(root.iterdir()):
        raise ValueError("Acceptance root must be empty or previously marked")
    root.mkdir(parents=True, exist_ok=True)
    marker.touch()
    fresh = not (root / "host_test.db").exists()
    gateway = make_gateway(root)
    if not fresh:
        return gateway
    gateway.create_records(
        "host_settings",
        {
            "scope": "application",
            "key": "app_general",
            "value_json": json.dumps({"theme": "dark", "zoom": 1.0, "language": "en"}),
            "updated_at_utc": "unchanged",
            "schema_version": 1,
        },
    )
    market(root, gateway)
    results = ResultStore(gateway)
    results.save_result(
        "bank",
        RunResult(
            "source", "bank", "known", "Known", strategy_payload=strategy_payload()
        ),
    )
    executor = ProjectExecutor(DataCatalog(gateway), results)
    executor.run(
        JobContext("seed-run", root / "scratch" / "seed", min_available_ram_pct=0),
        executor.prepare(project(), "task", 1),
    )
    projects = root / "projects"
    projects.mkdir()
    for workspace, mode in (
        ("builder", "RANDOM"),
        ("retester", "RETEST"),
        ("optimizer", "GRID"),
    ):
        settings = (
            {
                "parameter_ranges": [
                    {"name": "threshold", "start": 10, "end": 12, "step": 1}
                ]
            }
            if mode == "GRID"
            else {}
        )
        doc = project(mode, **settings)
        doc = replace(
            doc,
            manifest=replace(
                doc.manifest,
                project_id=f"acceptance-{workspace}",
                name=f"Acceptance {workspace}",
            ),
        )
        path = projects / f"{doc.manifest.project_id}.haru"
        ProjectStore().save_project(path, doc)
        envelope = read_project_envelope(path)
        write_project_envelope(
            path,
            ProjectEnvelope(
                envelope.manifest,
                {**envelope.project, "target_workspace": workspace},
                envelope.tasks,
            ),
        )
    logger.info("FR-home-acceptance-isolation: seeded actual isolated backtests")
    return gateway


def main() -> None:
    """Serve the real application with isolated project/data/database/job roots."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=4180)
    args = parser.parse_args()
    gateway = seed_environment(args.root)
    application = create_app(
        gateway, projects_dir=args.root / "projects", scratch_root=args.root / "scratch"
    )
    uvicorn.run(application, host="127.0.0.1", port=args.port, log_config=None)


if __name__ == "__main__":
    main()
