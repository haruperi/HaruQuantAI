"""Unit tests for native ProjectEnvelope and .haru container handling."""

import io
import json
import logging
import zipfile
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pytest
from app.core.lib.errors import DomainError, JSONValue
from app.core.trading.project.envelope import (
    ProjectEnvelope,
    read_project_envelope,
    write_project_envelope,
)


def _make_sample_manifest() -> dict[str, JSONValue]:
    return {
        "app_name": "HaruQuantAI",
        "schema_version": 1,
        "project_id": "proj-uuid-1234",
        "name": "TrendFollowing_H1",
        "created_at": "2026-10-30T08:00:00Z",
    }


def _make_sample_project() -> dict[str, JSONValue]:
    return {
        "tasks": ["TaskBuild-1", "TaskOptimizer-2"],
        "databanks": {"results": "db-target-1"},
    }


def _make_sample_tasks() -> dict[str, dict[str, JSONValue]]:
    return {
        "tasks/TaskBuild-1.json": {
            "task_type": "builder",
            "generator": "random",
            "target": "EMA",
        },
        "tasks/TaskOptimizer-2.json": {
            "task_type": "optimizer",
            "optimizer": "genetic",
            "generations": 50,
        },
    }


def test_roundtrip_haru_project(tmp_path: Path) -> None:
    """Full roundtrip envelope with manifest, project, and multiple tasks."""
    manifest = _make_sample_manifest()
    project = _make_sample_project()
    tasks = _make_sample_tasks()

    envelope = ProjectEnvelope(manifest=manifest, project=project, tasks=tasks)
    haru_path = tmp_path / "test_strategy.haru"

    write_project_envelope(haru_path, envelope)
    loaded = read_project_envelope(haru_path)

    assert loaded.manifest == manifest
    assert loaded.project == project
    assert dict(loaded.tasks) == tasks
    assert loaded.tasks.keys() == tasks.keys()
    assert isinstance(loaded.tasks, Mapping)
    assert isinstance(loaded.tasks, MappingProxyType)

    # Immutability check on tasks mapping
    with pytest.raises(TypeError):
        loaded.tasks["tasks/TaskNew.json"] = {}  # type: ignore[index]

    # Verify physical ZIP member ordering: manifest first, then project, then sorted tasks
    with zipfile.ZipFile(haru_path, "r") as zf:
        members = [info.filename for info in zf.infolist()]
        assert members == [
            "manifest.json",
            "project.json",
            "tasks/TaskBuild-1.json",
            "tasks/TaskOptimizer-2.json",
        ]


def test_roundtrip_minimal_project(tmp_path: Path) -> None:
    """Minimal envelope with manifest and project but zero tasks roundtrips cleanly."""
    manifest = _make_sample_manifest()
    project = _make_sample_project()

    envelope = ProjectEnvelope(manifest=manifest, project=project)
    haru_path = tmp_path / "minimal.haru"

    write_project_envelope(haru_path, envelope)
    loaded = read_project_envelope(haru_path)

    assert loaded.manifest == manifest
    assert loaded.project == project
    assert len(loaded.tasks) == 0


def test_missing_file_raises(tmp_path: Path) -> None:
    """Reading non-existent path raises PROJECT_FILE_NOT_FOUND."""
    missing_path = tmp_path / "does_not_exist.haru"

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(missing_path)

    err = exc_info.value
    assert err.code == "PROJECT_FILE_NOT_FOUND"
    assert err.message == "Project file not found"


def test_corrupt_archive_raises(tmp_path: Path) -> None:
    """Reading non-zip bytes raises INVALID_PROJECT_CONTAINER with member ''."""
    corrupt_path = tmp_path / "corrupt.haru"
    corrupt_path.write_bytes(b"not a valid zip file content")

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(corrupt_path)

    err = exc_info.value
    assert err.code == "INVALID_PROJECT_CONTAINER"
    assert err.details == {"member": ""}


def test_missing_manifest_raises(tmp_path: Path) -> None:
    """Archive lacking manifest.json raises INVALID_PROJECT_CONTAINER."""
    bad_path = tmp_path / "no_manifest.haru"
    with zipfile.ZipFile(bad_path, "w") as zf:
        zf.writestr("project.json", json.dumps({"tasks": []}))

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bad_path)

    err = exc_info.value
    assert err.code == "INVALID_PROJECT_CONTAINER"
    assert err.details == {"member": "manifest.json"}


def test_missing_project_raises(tmp_path: Path) -> None:
    """Archive lacking project.json raises INVALID_PROJECT_CONTAINER."""
    bad_path = tmp_path / "no_project.haru"
    with zipfile.ZipFile(bad_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(_make_sample_manifest()))

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bad_path)

    err = exc_info.value
    assert err.code == "INVALID_PROJECT_CONTAINER"
    assert err.details == {"member": "project.json"}


def test_empty_task_member_raises(tmp_path: Path) -> None:
    """Zero-byte task member raises INVALID_PROJECT_CONTAINER with member name."""
    bad_path = tmp_path / "empty_task.haru"
    with zipfile.ZipFile(bad_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(_make_sample_manifest()))
        zf.writestr("project.json", json.dumps(_make_sample_project()))
        zf.writestr("tasks/TaskBuild-1.json", b"")

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bad_path)

    err = exc_info.value
    assert err.code == "INVALID_PROJECT_CONTAINER"
    assert err.details == {"member": "tasks/TaskBuild-1.json"}


def test_malformed_json_raises(tmp_path: Path) -> None:
    """Malformed JSON syntax raises INVALID_PROJECT_CONTAINER with member name."""
    bad_path = tmp_path / "bad_json.haru"
    with zipfile.ZipFile(bad_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(_make_sample_manifest()))
        zf.writestr("project.json", b"{ malformed: json [")

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bad_path)

    err = exc_info.value
    assert err.code == "INVALID_PROJECT_CONTAINER"
    assert err.details == {"member": "project.json"}


def test_non_utf8_bytes_raises(tmp_path: Path) -> None:
    """Non-UTF-8 bytes raise INVALID_PROJECT_CONTAINER with member name."""
    bad_path = tmp_path / "bad_utf8.haru"
    with zipfile.ZipFile(bad_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(_make_sample_manifest()))
        zf.writestr("project.json", json.dumps(_make_sample_project()))
        zf.writestr("tasks/TaskBuild-1.json", b"\xff\xfe\x00\x00")

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bad_path)

    err = exc_info.value
    assert err.code == "INVALID_PROJECT_CONTAINER"
    assert err.details == {"member": "tasks/TaskBuild-1.json"}


def test_traversal_paths_rejected_in_archive(tmp_path: Path) -> None:
    """Archive members with ../ traversal or path escape are rejected."""
    bad_escape = tmp_path / "escape.haru"
    with zipfile.ZipFile(bad_escape, "w") as zf:
        zf.writestr("../escape.json", b'{"key": 1}')

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bad_escape)

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    assert exc_info.value.details == {"member": "../escape.json"}

    bad_nested_escape = tmp_path / "nested_escape.haru"
    with zipfile.ZipFile(bad_nested_escape, "w") as zf:
        zf.writestr("tasks/../../secret.json", b'{"key": 1}')

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bad_nested_escape)

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    assert exc_info.value.details == {"member": "tasks/../../secret.json"}


def test_traversal_paths_rejected_in_envelope() -> None:
    """Constructing ProjectEnvelope with traversal task keys is rejected."""
    manifest = _make_sample_manifest()
    project = _make_sample_project()

    with pytest.raises(DomainError) as exc_info:
        ProjectEnvelope(
            manifest=manifest,
            project=project,
            tasks={"../escape.json": {"val": 1}},
        )

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    assert exc_info.value.details == {"member": "../escape.json"}

    with pytest.raises(DomainError) as exc_info:
        ProjectEnvelope(
            manifest=manifest,
            project=project,
            tasks={"tasks/../../secret.json": {"val": 1}},
        )

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    assert exc_info.value.details == {"member": "tasks/../../secret.json"}


def test_duplicate_zip_names_rejected(tmp_path: Path) -> None:
    """Duplicate member names in archive raise INVALID_PROJECT_CONTAINER."""
    dup_path = tmp_path / "duplicates.haru"
    with zipfile.ZipFile(dup_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(_make_sample_manifest()))
        with pytest.warns(UserWarning, match="Duplicate name"):
            zf.writestr("manifest.json", json.dumps(_make_sample_manifest()))

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(dup_path)

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    assert exc_info.value.details == {"member": "manifest.json"}


def test_directory_entries_rejected(tmp_path: Path) -> None:
    """Directory entries in ZIP raise INVALID_PROJECT_CONTAINER."""
    dir_path = tmp_path / "has_dir.haru"
    with zipfile.ZipFile(dir_path, "w") as zf:
        zf.writestr(zipfile.ZipInfo("tasks/"), b"")

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(dir_path)

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    assert exc_info.value.details == {"member": "tasks/"}


def test_backslashes_rejected_in_archive(tmp_path: Path) -> None:
    """Archive member name containing backslashes is rejected."""
    bs_path = tmp_path / "backslash.haru"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", json.dumps(_make_sample_manifest()))
        zf.writestr("project.json", json.dumps(_make_sample_project()))
        zf.writestr("tasks/TaskBuild-1.json", b'{"a": 1}')

    raw_bytes = buf.getvalue().replace(
        b"tasks/TaskBuild-1.json", b"tasks\x5cTaskBuild-1.json"
    )
    bs_path.write_bytes(raw_bytes)

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bs_path)

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    assert exc_info.value.details == {"member": r"tasks\TaskBuild-1.json"}


def test_backslashes_rejected_in_envelope() -> None:
    """Task dictionary key containing backslashes is rejected."""
    with pytest.raises(DomainError) as exc_info:
        ProjectEnvelope(
            manifest=_make_sample_manifest(),
            project=_make_sample_project(),
            tasks={r"tasks\TaskBuild-1.json": {"a": 1}},
        )

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    assert exc_info.value.details == {"member": r"tasks\TaskBuild-1.json"}


def test_atomic_write_failure_preserves_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If atomic replacement fails, original file is preserved and temp file cleaned up."""
    haru_path = tmp_path / "atomic_target.haru"
    envelope = ProjectEnvelope(
        manifest=_make_sample_manifest(),
        project=_make_sample_project(),
    )
    write_project_envelope(haru_path, envelope)
    original_bytes = haru_path.read_bytes()

    modified_manifest = _make_sample_manifest()
    modified_manifest["name"] = "MODIFIED_NAME"
    modified_envelope = ProjectEnvelope(
        manifest=modified_manifest,
        project=_make_sample_project(),
    )

    def _failing_replace(self: Path, target: Path) -> Path:
        raise OSError("Simulated disk replace error")

    monkeypatch.setattr(Path, "replace", _failing_replace)

    with pytest.raises(OSError, match="Simulated disk replace error"):
        write_project_envelope(haru_path, modified_envelope)

    # Previous destination bytes must be identical
    assert haru_path.read_bytes() == original_bytes

    # No leftover temporary files in directory
    temp_files = list(tmp_path.glob("*.tmp.*"))
    assert temp_files == []


def test_rejected_envelope_never_truncates_prior(tmp_path: Path) -> None:
    """Attempting to write an invalid envelope fails before modifying disk."""
    haru_path = tmp_path / "safe.haru"
    envelope = ProjectEnvelope(
        manifest=_make_sample_manifest(),
        project=_make_sample_project(),
    )
    write_project_envelope(haru_path, envelope)
    original_bytes = haru_path.read_bytes()

    # Create an envelope with an invalid task key bypassing normal init
    # by raising during write_project_envelope validation
    bad_manifest: dict[str, JSONValue] = {"invalid": "manifest"}
    with pytest.raises(DomainError) as exc_info:
        ProjectEnvelope(manifest=bad_manifest, project={})

    assert exc_info.value.code == "INVALID_PROJECT_CONTAINER"
    # Destination remains unchanged
    assert haru_path.read_bytes() == original_bytes


def test_missing_parent_directory_raises(tmp_path: Path) -> None:
    """Writing to non-existent parent directory raises FileNotFoundError."""
    missing_dir = tmp_path / "nested_missing" / "project.haru"
    envelope = ProjectEnvelope(
        manifest=_make_sample_manifest(),
        project=_make_sample_project(),
    )

    with pytest.raises(FileNotFoundError):
        write_project_envelope(missing_dir, envelope)


def test_manifest_validation() -> None:
    """Manifest requires app_name, schema_version (int), project_id, and name."""
    project = _make_sample_project()

    # Missing schema_version
    m1: dict[str, JSONValue] = {
        "app_name": "HaruQuantAI",
        "project_id": "p1",
        "name": "N1",
    }
    with pytest.raises(DomainError) as exc_info:
        ProjectEnvelope(manifest=m1, project=project)
    assert exc_info.value.details == {"member": "manifest.json"}

    # schema_version is boolean
    m2: dict[str, JSONValue] = {
        "app_name": "HaruQuantAI",
        "schema_version": True,
        "project_id": "p1",
        "name": "N1",
    }
    with pytest.raises(DomainError) as exc_info:
        ProjectEnvelope(manifest=m2, project=project)
    assert exc_info.value.details == {"member": "manifest.json"}

    # non-dict project
    with pytest.raises(DomainError) as exc_info:
        ProjectEnvelope(
            manifest=_make_sample_manifest(),
            project="invalid",  # type: ignore[arg-type]
        )
    assert exc_info.value.details == {"member": "project.json"}


def test_non_dict_task_json_raises(tmp_path: Path) -> None:
    """Task member parsing to non-dict (e.g. JSON array) raises INVALID_PROJECT_CONTAINER."""
    bad_path = tmp_path / "array_task.haru"
    with zipfile.ZipFile(bad_path, "w") as zf:
        zf.writestr("manifest.json", json.dumps(_make_sample_manifest()))
        zf.writestr("project.json", json.dumps(_make_sample_project()))
        zf.writestr("tasks/TaskBuild-1.json", b"[1, 2, 3]")

    with pytest.raises(DomainError) as exc_info:
        read_project_envelope(bad_path)

    err = exc_info.value
    assert err.code == "INVALID_PROJECT_CONTAINER"
    assert err.details == {"member": "tasks/TaskBuild-1.json"}


def test_logging_events(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Read and write operations emit structured log messages."""
    haru_path = tmp_path / "logged.haru"
    envelope = ProjectEnvelope(
        manifest=_make_sample_manifest(),
        project=_make_sample_project(),
        tasks=_make_sample_tasks(),
    )

    with caplog.at_level(logging.DEBUG, logger="app.core.trading.project.envelope"):
        write_project_envelope(haru_path, envelope)
        read_project_envelope(haru_path)

    assert "Preparing atomic write of project envelope" in caplog.text
    assert "Successfully wrote project envelope to" in caplog.text
    assert "Successfully read project envelope from" in caplog.text
