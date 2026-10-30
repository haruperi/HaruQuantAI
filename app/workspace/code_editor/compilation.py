"""Host-managed editor compilation, progress and durable diagnostic delivery.

Description:
    Runs file/package/library or registered-extension compilation in the host I/O
    pool. Cancellation is cooperative between files and after the current import;
    terminal cancellation is reported only when the worker has returned.
Purpose:
    FEAT-CODE-EDITOR-COMMANDS: Own editor compilation snapshots, not host jobs.
Key Capabilities:
    - FR-editor-compilation: Log submission, publication, cancellation and recovery;
      isolated integration tests verify lifecycle and durable diagnostics.
Python API Usage:
    service = CompilationService(manager, store)
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

import hashlib
import logging
import threading
import uuid
from pathlib import Path

from pydantic import ValidationError

from app.core.jobs.manager import JobCancelledError, JobContext, JobManager
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor._common import (
    INCLUDE_DIR,
    CodeEditorError,
    resolve_safe_path,
)
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.command_models import (
    CompilationRequest,
    CompilationSnapshot,
)
from app.workspace.code_editor.registry import registry

logger = logging.getLogger(__name__)
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}


class CompilationService:
    """Serialize editor jobs; retain per-job and latest diagnostics through host storage."""

    def __init__(self, manager: JobManager, store: StateStore) -> None:
        logger.debug("FR-editor-compilation: initialized")
        self.manager = manager
        self.store = store
        if store.gateway.ensure_jobs_schema()["success"] is not True:
            logger.error("FR-editor-compilation: host schema unavailable")
            raise CodeEditorError(
                "Host job storage is unavailable or incompatible",
                code=ErrorCode.UNAVAILABLE,
            )
        self._lock = threading.RLock()
        self._active: str | None = None

    def _write(self, snapshot: CompilationSnapshot) -> None:
        with self._lock:
            self.store.write(
                "compilation:" + snapshot.job_id, snapshot.model_dump(mode="json")
            )
            self.store.write("compilation:latest", snapshot.model_dump(mode="json"))

    def start(self, request: CompilationRequest) -> CompilationSnapshot:
        """Capture the requested file set and reject concurrent editor jobs."""
        logger.debug("FR-editor-compilation: submission invoked")
        if request.scope == "file":
            if request.file_path is None:
                raise CodeEditorError("File compilation requires a path")
            paths = [resolve_safe_path(request.file_path)]
        elif request.scope == "registered":
            paths = [Path(p) for p in sorted(registry.blocks)]
        else:
            if request.scope == "package" and request.file_path is None:
                raise CodeEditorError("Package compilation requires a directory path")
            root = (
                resolve_safe_path(request.file_path)
                if request.scope == "package" and request.file_path
                else INCLUDE_DIR
            )
            if not root.is_dir() or not root.is_relative_to(INCLUDE_DIR.resolve()):
                raise CodeEditorError(
                    "Package compilation requires an include directory"
                )
            paths = sorted(root.rglob("*.py"))
        paths = [
            p
            for p in paths
            if not p.is_symlink()
            and p.resolve().is_relative_to(INCLUDE_DIR.resolve())
            and not any(
                part.startswith(".") or part == "__pycache__" for part in p.parts
            )
        ]
        if not paths and request.scope in ("file", "package"):
            raise CodeEditorError("No Python files selected for compilation")
        with self._lock:
            if self._active is not None:
                raise CodeEditorError(
                    "An editor compilation is already running", code=ErrorCode.CONFLICT
                )
            job_id = "editor-" + uuid.uuid4().hex
            snapshot = CompilationSnapshot(job_id=job_id, status="QUEUED", progress=0)
            self._write(snapshot)
            self._active = job_id
            try:
                self.manager.submit_job(
                    self._run,
                    request,
                    paths,
                    job_id=job_id,
                    owner="code_editor",
                    kind="editor_compilation",
                    executor_kind="thread",
                    pass_context=True,
                )
            except Exception:
                self._active = None
                self._write(
                    snapshot.model_copy(
                        update={
                            "status": "FAILED",
                            "message": "Compilation submission failed",
                        }
                    )
                )
                logger.error("FR-editor-compilation: submission failed")
                raise CodeEditorError(
                    "Compilation unavailable", code=ErrorCode.UNAVAILABLE
                ) from None
        logger.info("FR-editor-compilation: submitted")
        return snapshot

    def _run(
        self, ctx: JobContext, request: CompilationRequest, paths: list[Path]
    ) -> None:
        from app.workspace.code_editor.routes import CodeEditor

        snapshot = CompilationSnapshot(job_id=ctx.job_id, status="RUNNING", progress=0)
        editor = CodeEditor()
        try:
            for index, path in enumerate(paths):
                ctx.raise_if_cancelled()
                ctx.report_progress(100 * index / len(paths), "Compiling Python source")
                if not path.is_file():
                    registry.unregister(str(path))
                try:
                    content = (
                        request.content
                        if request.scope == "file" and request.content is not None
                        else path.read_text(encoding="utf-8")
                    )
                except OSError, UnicodeError:
                    content = None
                result = editor.compile_file(str(path), content)
                if content is not None:
                    snapshot.source_hashes[result["file"]] = hashlib.sha256(
                        content.encode("utf-8")
                    ).hexdigest()
                if request.scope == "registered" and not result["success"]:
                    registry.unregister(str(path))
                snapshot.results.append(result)
                snapshot.progress = 100 * (index + 1) / len(paths)
                snapshot.cancellation_requested = ctx.is_cancelled()
                self._write(snapshot)
                ctx.raise_if_cancelled()
            snapshot.status = "COMPLETED"
            snapshot.progress = 100
            snapshot.message = (
                "Compilation completed"
                if all(r["success"] for r in snapshot.results)
                else "Compilation completed with diagnostics"
            )
        except JobCancelledError:
            snapshot.status = "CANCELLED"
            snapshot.cancellation_requested = True
            snapshot.message = "Cancelled; completed imports may already be registered"
        except Exception:
            snapshot.status = "FAILED"
            snapshot.message = "Compilation failed; inspect source diagnostics"
            logger.error("FR-editor-compilation: execution failed")
        finally:
            with self._lock:
                try:
                    if ctx.is_cancelled():
                        snapshot.status = "CANCELLED"
                        snapshot.cancellation_requested = True
                        snapshot.message = (
                            "Cancelled; completed imports may already be registered"
                        )
                    self._write(snapshot)
                    logger.info("FR-editor-compilation: terminal snapshot published")
                finally:
                    self._active = None

    def get(self, job_id: str | None = None) -> CompilationSnapshot | None:
        """Restore diagnostics and mark orphan editor snapshots interrupted."""
        logger.debug("FR-editor-compilation: read invoked")
        with self._lock:
            return self._read_snapshot(job_id)

    def _read_snapshot(self, job_id: str | None) -> CompilationSnapshot | None:
        raw = self.store.read("compilation:" + (job_id or "latest"))
        if raw is None:
            return None
        try:
            snapshot = CompilationSnapshot.model_validate(raw)
        except ValidationError:
            logger.error("FR-editor-compilation: invalid persisted snapshot")
            raise CodeEditorError(
                "Invalid stored compilation state", code=ErrorCode.INTERNAL
            ) from None
        record = self.manager.get_job(snapshot.job_id)
        if (
            snapshot.status not in TERMINAL
            and record is not None
            and record.status in TERMINAL
        ):
            snapshot.status = CompilationSnapshot.model_validate(
                {**snapshot.model_dump(), "status": record.status}
            ).status
            snapshot.message = "Host compilation job ended"
            self._write(snapshot)
            self._active = None
        if snapshot.status not in TERMINAL and snapshot.job_id != self._active:
            snapshot.status = "INTERRUPTED"
            snapshot.message = "Compilation interrupted by host restart"
            self._write(snapshot)
            logger.warning("FR-editor-compilation: interrupted snapshot restored")
        return snapshot

    def cancel(self, job_id: str) -> CompilationSnapshot:
        """Request cooperative cancellation; do not invent terminal success."""
        with self._lock:
            snapshot = self.get(job_id)
            if snapshot is None:
                raise CodeEditorError(
                    "Compilation job not found", code=ErrorCode.NOT_FOUND
                )
            if snapshot.status not in TERMINAL:
                self.manager.cancel_job(job_id)
                snapshot.cancellation_requested = True
                snapshot.message = (
                    "Cancellation requested; waiting for current import to return"
                )
                self._write(snapshot)
        logger.info("FR-editor-compilation: cancellation requested")
        return snapshot
