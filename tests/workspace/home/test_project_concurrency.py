"""Independent-process revision races and native envelope preservation.

Description:
    Exercises simultaneous writers, lock timeouts, process termination and
    native extension preservation against isolated project files.
Purpose:
    FEAT-HOME-PROJECT-ACCEPTANCE: Verify actual transaction exclusion.
Key Capabilities:
    - FR-home-project-preservation: Verify retained fields and explicit save logs.
    - FR-home-project-lock: Verify competing-process exclusion and crash recovery.
Python API Usage:
    pytest tests/workspace/home/test_project_concurrency.py
CLI Usage:
    uv run python -m pytest tests/workspace/home/test_project_concurrency.py --no-cov
"""

from __future__ import annotations

import multiprocessing
from pathlib import Path
from typing import Any

import pytest
from app.core.host.persistence import HostPersistence
from app.core.lib.errors import DomainError
from app.core.trading.project.contracts import ProjectDocument, ProjectManifest
from app.core.trading.project.envelope import (
    ProjectEnvelope,
    read_project_envelope,
    write_project_envelope,
)
from app.workspace.home.project_repository import (
    HomeProjectRepository,
    _project_file_lock,
)
from app.workspace.home.service import HomeService


def _service(root: Path, name: str = "test") -> HomeService:
    return HomeService(
        persistence=HostPersistence(root / f"{name}.db"), projects_dir=root
    )


def _writer(root: str, barrier: Any, replies: Any, name: str) -> None:
    service = _service(Path(root), name)
    barrier.wait(timeout=20)
    try:
        result = service.save_project_notes("project", name, 1)
        replies.put(("saved", result["revision"]))
    except DomainError as error:
        replies.put((error.code, None))


def _holder(path: str, acquired: Any) -> None:
    with _project_file_lock(Path(path)):
        acquired.set()
        multiprocessing.Event().wait(timeout=30)


def _seed(root: Path) -> Path:
    path = root / "project.haru"
    HomeProjectRepository().save_project(
        path,
        ProjectDocument(
            ProjectManifest("project", "Project"), metadata={"revision": 1}
        ),
    )
    return path


def test_competing_processes_commit_one_revision(tmp_path: Path) -> None:
    """Two independent services race; exactly one commits revision two."""
    path = _seed(tmp_path)
    context = multiprocessing.get_context("spawn")
    replies = context.Queue()
    barrier = context.Barrier(2)
    writers = [
        context.Process(target=_writer, args=(str(tmp_path), barrier, replies, t))
        for t in ("first", "second")
    ]
    try:
        for writer in writers:
            writer.start()
        results = [replies.get(timeout=30) for _ in writers]
        for writer in writers:
            writer.join(timeout=10)
            assert writer.exitcode == 0
        assert sorted(results) == [("CONFLICT", None), ("saved", 2)]
        metadata = read_project_envelope(path).project["metadata"]
        assert metadata["revision"] == 2
        assert metadata["notes"] in {"first", "second"}
    finally:
        for writer in writers:
            if writer.is_alive():
                writer.terminate()
                writer.join(timeout=5)
        replies.close()


def test_timeout_and_process_failure_preserve_content(tmp_path: Path) -> None:
    """Timeout preserves bytes; killing the holder makes its OS lock recoverable."""
    path = _seed(tmp_path)
    before = path.read_bytes()
    context = multiprocessing.get_context("spawn")
    acquired = context.Event()
    holder = context.Process(target=_holder, args=(str(path), acquired))
    holder.start()
    try:
        assert acquired.wait(timeout=20)
        with pytest.raises(DomainError, match="Timeout") as caught:
            with _project_file_lock(path, timeout=0.1):
                pytest.fail("Writer must be excluded")
        assert caught.value.code == "PROJECT_LOCK_TIMEOUT"
        assert path.read_bytes() == before
    finally:
        holder.terminate()
        holder.join(timeout=5)
    service = _service(tmp_path)
    assert service.save_project_notes("project", "recovered", 1)["revision"] == 2
    after = path.read_bytes()
    with pytest.raises(DomainError, match="revision mismatch"):
        service.save_project_notes("project", "stale", 1)
    assert path.read_bytes() == after


def test_preserves_native_extensions(tmp_path: Path, caplog: Any) -> None:
    """Home edits preserve native fields outside the typed Core model."""
    path = _seed(tmp_path)
    old = read_project_envelope(path)
    write_project_envelope(
        path,
        ProjectEnvelope(
            {**old.manifest, "vendor": "native"},
            {**old.project, "target_workspace": "retester", "custom": {"x": 1}},
            {
                "tasks/task.json": {
                    "task_id": "task",
                    "task_type": "retest",
                    "extension": "retained",
                }
            },
        ),
    )
    notes = "Unicode: \u65e5\u672c\u8a9e \U0001f331\n<script>"
    with caplog.at_level("INFO"):
        _service(tmp_path).save_project_notes("project", notes, 1)
    saved = read_project_envelope(path)
    assert saved.manifest["vendor"] == "native"
    assert saved.project["target_workspace"] == "retester"
    assert saved.project["custom"] == {"x": 1}
    assert saved.project["metadata"]["notes"] == notes
    assert saved.tasks["tasks/task.json"]["extension"] == "retained"
    assert "FR-home-project-preservation" in caplog.text
