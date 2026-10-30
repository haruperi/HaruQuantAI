"""Unit tests for ProjectStore service."""

from pathlib import Path

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.project.contracts import (
    ProjectDocument,
    ProjectManifest,
    TaskDocument,
)
from app.core.trading.project.store import ProjectStore


def _make_sample_project() -> ProjectDocument:
    manifest = ProjectManifest(
        project_id="proj-9999",
        name="MeanReversion_M15",
        description="Stat-arb and mean reversion pipeline",
        created_at="2026-10-30T09:00:00Z",
        updated_at="2026-10-30T09:15:00Z",
    )
    t1 = TaskDocument(
        task_id="TaskBuild-1",
        task_type="builder",
        name="Initial Generator",
        enabled=True,
        databank_target="db-raw",
        dependencies=(),
        settings={"engine": "random", "max_rules": 4},
    )
    t2 = TaskDocument(
        task_id="TaskOptimizer-2",
        task_type="optimizer",
        name="Parameter Optimizer",
        enabled=True,
        databank_target="db-optimized",
        dependencies=("TaskBuild-1",),
        settings={"optimizer": "genetic", "generations": 30},
    )
    return ProjectDocument(
        manifest=manifest,
        pipeline=("TaskBuild-1", "TaskOptimizer-2"),
        databanks={"results": "db-optimized", "incoming": "db-raw"},
        tasks={"TaskBuild-1": t1, "TaskOptimizer-2": t2},
        metadata={"author": "HaruTrader", "notes": "H1/M15 regime"},
    )


def test_project_store_roundtrip(tmp_path: Path) -> None:
    """ProjectStore successfully persists and restores a complete project document."""
    store = ProjectStore()
    project = _make_sample_project()
    haru_path = tmp_path / "mean_reversion.haru"

    store.save_project(haru_path, project)
    loaded = store.load_project(haru_path)

    assert loaded.manifest.project_id == project.manifest.project_id
    assert loaded.manifest.name == project.manifest.name
    assert loaded.manifest.app_name == "HaruQuantAI"
    assert loaded.manifest.schema_version == 1
    assert loaded.manifest.description == project.manifest.description
    assert loaded.pipeline == ("TaskBuild-1", "TaskOptimizer-2")
    assert dict(loaded.databanks) == {"results": "db-optimized", "incoming": "db-raw"}
    assert dict(loaded.metadata) == {"author": "HaruTrader", "notes": "H1/M15 regime"}

    assert len(loaded.tasks) == 2
    assert "TaskBuild-1" in loaded.tasks
    assert "TaskOptimizer-2" in loaded.tasks

    t1 = loaded.tasks["TaskBuild-1"]
    assert t1.task_id == "TaskBuild-1"
    assert t1.task_type == "builder"
    assert t1.databank_target == "db-raw"
    assert t1.settings == {"engine": "random", "max_rules": 4}

    t2 = loaded.tasks["TaskOptimizer-2"]
    assert t2.task_id == "TaskOptimizer-2"
    assert t2.dependencies == ("TaskBuild-1",)
    assert t2.settings == {"optimizer": "genetic", "generations": 30}


def test_project_store_minimal(tmp_path: Path) -> None:
    """ProjectStore roundtrips minimal project without tasks or databanks."""
    store = ProjectStore()
    manifest = ProjectManifest(project_id="min-1", name="Minimal")
    project = ProjectDocument(manifest=manifest)
    haru_path = tmp_path / "minimal.haru"

    store.save_project(haru_path, project)
    loaded = store.load_project(haru_path)

    assert loaded.manifest.project_id == "min-1"
    assert loaded.manifest.name == "Minimal"
    assert len(loaded.tasks) == 0
    assert loaded.pipeline == ()
    assert len(loaded.databanks) == 0


def test_project_store_missing_file_raises(tmp_path: Path) -> None:
    """Loading non-existent file raises PROJECT_FILE_NOT_FOUND."""
    store = ProjectStore()
    missing_path = tmp_path / "does_not_exist.haru"

    with pytest.raises(DomainError) as exc_info:
        store.load_project(missing_path)

    assert exc_info.value.code == "PROJECT_FILE_NOT_FOUND"


def test_project_store_corrupted_file_raises(tmp_path: Path) -> None:
    """Loading corrupted archive raises INVALID_PROJECT_CONTAINER."""
    store = ProjectStore()
    bad_file = tmp_path / "corrupted.haru"
    bad_file.write_bytes(b"not a valid zip file")

    with pytest.raises(DomainError) as exc_info:
        store.load_project(bad_file)

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"


def test_contracts_serialization() -> None:
    """Contracts convert to/from dictionary representations."""
    task = TaskDocument(
        task_id="T1",
        task_type="builder",
        settings={"param": 10},
        name="Task 1",
        dependencies=("T0",),
    )
    t_dict = task.to_dict()
    assert t_dict["task_id"] == "T1"
    restored_task = TaskDocument.from_dict("T1", t_dict)
    assert restored_task == task

    manifest = ProjectManifest(
        project_id="P1",
        name="Proj 1",
        description="Desc",
    )
    m_dict = manifest.to_dict()
    assert m_dict["project_id"] == "P1"
    restored_manifest = ProjectManifest.from_dict(m_dict)
    assert restored_manifest.project_id == "P1"
    assert restored_manifest.name == "Proj 1"
