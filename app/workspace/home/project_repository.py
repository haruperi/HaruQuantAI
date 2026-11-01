"""Native project preservation and process-safe Home mutation locks.

Description:
    Serializes competing Home writers and preserves native envelope extension fields
    while delegating atomic container replacement to the Core envelope owner.
Purpose:
    FEAT-HOME-PROJECT-TRANSACTIONS: Revision-safe native project edits.
Key Capabilities:
    - FR-home-project-lock: Bound lock acquisition and log release failures;
      competing-process tests verify mutual exclusion and recovery.
    - FR-home-project-preservation: Preserve native extension fields during saves;
      envelope round-trip tests verify the retained values and operation logs.
Python API Usage:
    store = HomeProjectRepository()
CLI Usage:
    uv run python -m pytest tests/workspace/home/test_project_concurrency.py --no-cov
"""

from __future__ import annotations

import sys
import time
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue
from app.core.trading.project.contracts import ProjectDocument
from app.core.trading.project.envelope import (
    ProjectEnvelope,
    read_project_envelope,
    write_project_envelope,
)
from app.core.trading.project.store import ProjectStore

logger = get_logger(__name__)


@contextmanager
def _project_file_lock(
    project_file: Path,
    timeout: float = 10.0,
) -> Generator[None]:
    """Inter-process advisory file lock around project container mutations."""
    lock_path = project_file.with_name(f"{project_file.name}.lock")
    start = time.monotonic()
    lock_file = lock_path.open("a+b")
    try:
        while True:
            try:
                lock_file.seek(0)
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError, PermissionError, OSError:
                if time.monotonic() - start > timeout:
                    msg = f"Timeout waiting for lock: {project_file.name}"
                    raise DomainError(
                        code="PROJECT_LOCK_TIMEOUT",
                        message=msg,
                        details={"project_file": str(project_file)},
                    ) from None
                time.sleep(0.05)
        try:
            yield
        finally:
            try:
                lock_file.seek(0)
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            except OSError:
                logger.warning("FR-home-project-lock: lock release failed")
    finally:
        lock_file.close()


class HomeProjectRepository(ProjectStore):
    """Preserve fields beyond the typed Core document when editing native files."""

    @override
    def save_project(self, path: Path | str, project: ProjectDocument) -> None:
        """Merge typed edits into an existing envelope and replace it atomically.

        Callers hold the project lock across load, revision check, and this save.
        """
        target = Path(path)
        if not target.exists():
            super().save_project(path, project)
            return
        original = read_project_envelope(target)
        manifest = dict(original.manifest)
        manifest.update(project.manifest.to_dict())
        native = dict(original.project)
        native.update(
            {
                "pipeline": list(project.pipeline),
                "databanks": dict(project.databanks),
                "metadata": dict(project.metadata),
            }
        )
        tasks: dict[str, dict[str, JSONValue]] = {}
        for task_id, task in project.tasks.items():
            member = f"tasks/{task_id}.json"
            fields = dict(original.tasks.get(member, {}))
            fields.update(task.to_dict())
            tasks[member] = fields
        write_project_envelope(target, ProjectEnvelope(manifest, native, tasks))
        logger.info("FR-home-project-preservation: saved native project envelope")


def update_project_metadata(
    store: ProjectStore,
    path: Path,
    expected_revision: int,
    changes: Mapping[str, JSONValue],
) -> int:
    """Commit a revision-checked metadata edit inside one process-safe boundary."""
    from app.workspace.home.settings_contracts import require_revision

    require_revision(expected_revision)
    with _project_file_lock(path):
        project = store.load_project(path)
        revision = project.metadata.get("revision", 1)
        if isinstance(revision, bool) or revision != expected_revision:
            raise DomainError(
                code="CONFLICT",
                message="Project revision mismatch; reload current state",
            )
        metadata = {**project.metadata, **changes, "revision": expected_revision + 1}
        store.save_project(
            path,
            replace(
                project,
                metadata=metadata,
                manifest=replace(
                    project.manifest, updated_at=datetime.now(UTC).isoformat()
                ),
            ),
        )
    logger.info(
        "FR-home-project-preservation: committed metadata revision %d",
        expected_revision + 1,
    )
    return expected_revision + 1
