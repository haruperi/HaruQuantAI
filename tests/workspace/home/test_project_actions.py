"""Unit and service integration tests for Home workspace project actions.

Description:
    Tests HomeService project persistence, optimistic concurrency locking,
    task configuration updates, notes saving, template application, and resource resolution.

Purpose:
    FEAT-HOME-PROJECT-ACTIONS: Direct service tests for shared project workflows.

Key Capabilities:
    - FR-home-project-persistence: Verify loading and atomic saving of .haru projects.
    - FR-home-notes-persistence: Verify project notes updating with conflict prevention.
    - FR-home-template-manager: Verify template configuration merge and validation.
    - FR-home-resource-resolver: Verify symbol mapping resolution into project metadata.

Python API Usage:
    pytest tests/workspace/home/test_project_actions.py

CLI Usage:
    uv run python -m pytest tests/workspace/home/test_project_actions.py -q
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from app.core.data.catalog import DataCatalog
from app.core.host.persistence import HostPersistence
from app.core.lib.errors import DomainError
from app.core.trading.project.contracts import (
    ProjectDocument,
    ProjectManifest,
    TaskDocument,
)
from app.core.trading.project.store import ProjectStore
from app.workspace.home.service import HomeService


@pytest.fixture
def service_env(tmp_path: Path) -> dict[str, Any]:
    """Set up HomeService with isolated temporary project directory."""
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "test.db"
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.close()
    gateway = HostPersistence(db_path)
    gateway.ensure_datasets_schema()
    gateway.create_records(
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
    catalog = DataCatalog(gateway)
    store = ProjectStore()

    # Create two test projects with different timestamps
    p1 = ProjectDocument(
        manifest=ProjectManifest(
            project_id="proj-old",
            name="Older Project",
            schema_version=1,
            updated_at="2026-10-20T10:00:00Z",
        ),
        pipeline=("t1",),
        databanks={"Results": "Results"},
        tasks={"t1": TaskDocument(task_id="t1", task_type="build")},
        metadata={"notes": "Old notes", "revision": 1},
    )
    store.save_project(projects_dir / "proj-old.haru", p1)

    p2 = ProjectDocument(
        manifest=ProjectManifest(
            project_id="proj-new",
            name="Newer Project",
            schema_version=1,
            updated_at="2026-10-30T10:00:00Z",
        ),
        pipeline=("t2",),
        databanks={"Results": "Results"},
        tasks={"t2": TaskDocument(task_id="t2", task_type="retest")},
        metadata={
            "notes": "New notes",
            "revision": 1,
            "resources": {"EURUSD_RAW": "", "GBPUSD_RAW": "", "UNKNOWN": ""},
        },
    )
    store.save_project(projects_dir / "proj-new.haru", p2)

    service = HomeService(
        persistence=gateway,
        project_store=store,
        projects_dir=projects_dir,
        data_catalog=catalog,
        settings_manager=Mock(
            get_scope=Mock(
                return_value={
                    "Simple": {
                        "task_type": "retest",
                        "settings": {"engine": "MetaTrader4"},
                    }
                }
            )
        ),
    )
    return {"service": service, "projects_dir": projects_dir, "store": store}


def test_recent_projects_ordering(service_env: dict[str, Any]) -> None:
    """FR-home-project-persistence: verify recent projects ordering."""
    service: HomeService = service_env["service"]
    recent = service.get_recent_projects()
    assert len(recent) == 2
    assert recent[0]["id"] == "proj-new"
    assert recent[1]["id"] == "proj-old"


def test_load_project_success_and_missing(service_env: dict[str, Any]) -> None:
    """FR-home-project-persistence: verify project loading and missing."""
    service: HomeService = service_env["service"]
    doc = service.load_project("proj-new")
    assert doc["manifest"]["project_id"] == "proj-new"
    assert "t2" in doc["tasks"]

    with pytest.raises(DomainError) as exc_info:
        service.load_project("does-not-exist")
    assert exc_info.value.code == "PROJECT_FILE_NOT_FOUND"


def test_save_project_settings_concurrency(service_env: dict[str, Any]) -> None:
    """FR-home-project-persistence: verify optimistic concurrency."""
    service: HomeService = service_env["service"]

    # First update with correct expected revision
    result = service.save_project_settings(
        project_id="proj-new",
        task_id="t2",
        settings={"timeframe": "H1", "spread": 2.0},
        expected_revision=1,
    )
    assert result["revision"] == 2
    assert result["status"] == "saved"

    # Verify updated settings persist to disk and schema_version remains unchanged
    reloaded = service.load_project("proj-new")
    assert reloaded["tasks"]["t2"]["settings"]["timeframe"] == "H1"
    assert reloaded["tasks"]["t2"]["settings"]["spread"] == 2.0
    assert reloaded["manifest"]["schema_version"] == 1
    assert reloaded["metadata"]["revision"] == 2

    # Second update with stale revision 1 raises CONFLICT
    with pytest.raises(DomainError) as exc_info:
        service.save_project_settings(
            project_id="proj-new",
            task_id="t2",
            settings={"spread": 3.0},
            expected_revision=1,
        )
    assert exc_info.value.code == "CONFLICT"


def test_save_project_notes_concurrency(service_env: dict[str, Any]) -> None:
    """FR-home-notes-persistence: verify notes persistence and revision."""
    service: HomeService = service_env["service"]

    # Save notes with expected_revision=1
    res = service.save_project_notes(
        project_id="proj-old",
        notes="Updated detailed research notes with Unicode: €1000 & é",
        expected_revision=1,
    )
    assert res["revision"] == 2

    reloaded = service.load_project("proj-old")
    assert (
        reloaded["metadata"]["notes"]
        == "Updated detailed research notes with Unicode: €1000 & é"
    )
    assert reloaded["manifest"]["schema_version"] == 1
    assert reloaded["metadata"]["revision"] == 2

    # Stale revision conflict
    with pytest.raises(DomainError) as exc_info:
        service.save_project_notes(
            project_id="proj-old",
            notes="Conflicting concurrent note",
            expected_revision=1,
        )
    assert exc_info.value.code == "CONFLICT"


def test_apply_template_success_and_validation(service_env: dict[str, Any]) -> None:
    """FR-home-template-manager: verify template application."""
    service: HomeService = service_env["service"]

    # Valid template Simple
    res = service.apply_template("proj-new", "t2", "Simple", expected_revision=1)
    assert res["template"] == "Simple"
    assert res["revision"] == 2

    reloaded = service.load_project("proj-new")
    assert reloaded["tasks"]["t2"]["settings"]["engine"] == "MetaTrader4"
    assert reloaded["tasks"]["t2"]["settings"]["template"] == "Simple"
    assert reloaded["manifest"]["schema_version"] == 1
    assert reloaded["metadata"]["revision"] == 2

    # Unsupported template raises INVALID_TEMPLATE
    with pytest.raises(DomainError) as exc_info:
        service.apply_template("proj-new", "t2", "InvalidTemplate", expected_revision=2)
    assert exc_info.value.code == "INVALID_TEMPLATE"


def test_resolve_resources(service_env: dict[str, Any]) -> None:
    """FR-home-resource-resolver: verify symbol and dataset resolution."""
    service: HomeService = service_env["service"]
    res = service.resolve_resources(
        "proj-new",
        {"EURUSD_RAW": "EURUSD", "GBPUSD_RAW": "GBPUSD"},
        expected_revision=1,
    )
    assert res["resolved_count"] == 2
    assert res["revision"] == 2

    reloaded = service.load_project("proj-new")
    assert reloaded["metadata"]["resources"]["EURUSD_RAW"] == "EURUSD"
    assert reloaded["metadata"]["resources"]["GBPUSD_RAW"] == "GBPUSD"
    assert reloaded["manifest"]["schema_version"] == 1
    assert reloaded["metadata"]["revision"] == 2

    # Missing dataset symbol raises DATASET_NOT_FOUND
    with pytest.raises(DomainError) as exc_info:
        service.resolve_resources(
            "proj-new",
            {"UNKNOWN": "NONEXISTENT_SYMBOL"},
            expected_revision=2,
        )
    assert exc_info.value.code == "DATASET_NOT_FOUND"


@pytest.mark.parametrize(
    "names",
    [
        [""],
        ["   "],
        ["Duplicate", "Duplicate"],
        ["x" * 81],
        [str(i) for i in range(33)],
    ],
)
def test_invalid_analysis_definitions_preserve_native_file(
    service_env: dict[str, Any], names: list[str]
) -> None:
    """Invalid names cannot partially alter the native project or revision."""
    service: HomeService = service_env["service"]
    path = service_env["projects_dir"] / "proj-new.haru"
    before = path.read_bytes()
    with pytest.raises(DomainError) as caught:
        service.save_project_analysis("proj-new", names, 1)
    assert caught.value.code == "INVALID_ANALYSIS"
    assert path.read_bytes() == before


def test_analysis_acknowledgment_conflict_and_clear(
    service_env: dict[str, Any], caplog: Any
) -> None:
    """Names persist exactly; stale edits preserve bytes and clearing is revisioned."""
    service: HomeService = service_env["service"]
    path = service_env["projects_dir"] / "proj-new.haru"
    names = ["日本語 review", "Risk <plain text>"]
    with caplog.at_level("INFO"):
        response = service.save_project_analysis("proj-new", names, 1)
    assert response == {
        "project_id": "proj-new",
        "analysis_tabs": names,
        "revision": 2,
        "status": "saved",
    }
    assert (
        "FR-home-analysis-persistence: acknowledged saved analysis revision 2"
        in caplog.text
    )
    metadata = service.load_project("proj-new")["metadata"]
    assert metadata["analysis_tabs"] == names
    assert metadata["notes"] == "New notes"
    committed = path.read_bytes()
    with pytest.raises(DomainError) as caught:
        service.save_project_analysis("proj-new", ["Stale draft"], 1)
    assert caught.value.code == "CONFLICT"
    assert path.read_bytes() == committed
    assert service.save_project_analysis("proj-new", [], 2)["revision"] == 3
    assert service.load_project("proj-new")["metadata"]["analysis_tabs"] == []
