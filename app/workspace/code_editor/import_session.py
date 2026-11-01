"""Interactive extension import conflict-resolution sessions and archive hardening.

Description:
    Implements the donor-faithful interactive import/export session workflow
    (WO-CE-IMPORT-SESSION) with per-file conflict resolution (overwrite,
    overwriteAlways, skip, skipAlways, cancel), 60-second decision timeout,
    builtin collision protection ("already exists in Builtin"), Python-only
    .zip/.sxp validation, and post-import reload reporting.
Purpose:
    FEAT-CODE-EDITOR-IMPORT-SESSION: Provide stateful conflict-by-conflict
    extension archive import and hardened package validation.
Key Capabilities:
    - FR-code-editor-import-session-list: List user-owned exportable snippets
      with case-insensitive stem filtering while excluding protected builtins.
    - FR-code-editor-import-session-start: Validate archive size, entry count,
      compression ratio, traversal, and Java bytecode rejection before starting
      an interactive import session.
    - FR-code-editor-import-session-resolve: Apply overwrite, overwrite_always,
      skip, skip_always, and cancel actions with 60-second timeout enforcement.
Python API Usage:
    from app.workspace.code_editor.import_session import ImportSessionService
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor/test_import_session.py --no-cov
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from app.core.lib.responses import ErrorCode
from app.workspace.code_editor._common import (
    EXTEND_DIR,
    PROJECT_ROOT,
    CodeEditorError,
    resolve_safe_path,
    writable_snippet_path,
)
from app.workspace.code_editor._storage import StateStore, atomic_write_batch
from app.workspace.code_editor.command_models import (
    ImportSessionActionRequest,
    ImportSessionSnapshot,
    ImportSessionStartRequest,
    SkippedImportItem,
)
from app.workspace.code_editor.path_policy import inspect_path
from app.workspace.code_editor.results import CompileResult, NavigatorItem
from app.workspace.code_editor.routes import CodeEditor

logger = logging.getLogger(__name__)

MODE_DEFAULT = 0
MODE_OVERWRITE = 1
MODE_OVERWRITE_ALWAYS = 2
MODE_SKIP = 3
MODE_SKIP_ALWAYS = 4
MODE_CANCEL = 5

MAX_PACKAGE_BYTES = 10 * 1024 * 1024
MAX_PACKAGE_UNCOMPRESSED_BYTES = 25 * 1024 * 1024
MAX_PACKAGE_ENTRIES = 500
MAX_PACKAGE_COMPRESSION_RATIO = 100.0


@dataclass(slots=True)
class PendingArchiveEntry:
    """Validated entry queued for interactive import processing."""

    archive_name: str
    rel_path: str
    dest_path: Path | None
    payload: bytes
    skip_reason: str | None = None


@dataclass(slots=True)
class ActiveImportSession:
    """In-memory state for a running or paused interactive import session."""

    session_id: str
    entries: list[PendingArchiveEntry]
    timeout_seconds: float
    cursor: int = 0
    decision_mode: int = MODE_DEFAULT
    status: str = "RUNNING"
    paused_at: float | None = None
    approved_writes: dict[Path, bytes] = field(default_factory=dict)
    new_files: list[str] = field(default_factory=list)
    not_imported_files: list[SkippedImportItem] = field(default_factory=list)
    reload_results: list[CompileResult] = field(default_factory=list)
    message: str = ""


def list_exportable_tree(filter_text: str = "") -> NavigatorItem:
    """Return the user-owned snippet hierarchy filtered by case-insensitive text."""
    logger.debug("FR-code-editor-import-session-list: invoked")
    editor = CodeEditor()
    return editor.navigator(ownership="user", filter_text=filter_text)


def normalize_archive_entry_path(raw_name: str) -> Path:
    """Normalize an archive entry path to a destination inside app/extend."""
    posix = PurePosixPath(raw_name.replace("\\", "/"))
    if posix.is_absolute() or ".." in posix.parts:
        raise CodeEditorError(f"Unsafe archive entry path: {raw_name}")
    parts = posix.parts
    if not parts:
        raise CodeEditorError("Empty archive entry path")
    if (
        len(parts) >= 2
        and parts[0] == "app"
        and (parts[1] == "extend" or parts[1] == "include")
    ):
        target = PROJECT_ROOT.joinpath(*parts)
    else:
        target = EXTEND_DIR.joinpath(*parts)
    return resolve_safe_path(target)


def validate_and_extract_archive(archive_path: str | Path) -> list[PendingArchiveEntry]:
    """Validate package bounds and prepare entries with collision/Java diagnostics."""
    src = Path(archive_path).resolve()
    if not src.is_file():
        raise CodeEditorError(f"Archive not found: {archive_path}")
    if src.suffix.lower() not in {".zip", ".sxp"}:
        raise CodeEditorError("Extension packages must use .zip or .sxp extension")
    archive_size = src.stat().st_size
    if archive_size > MAX_PACKAGE_BYTES:
        raise CodeEditorError("Extension package exceeds maximum size limit (10 MB)")

    entries: list[PendingArchiveEntry] = []
    seen_destinations: set[Path] = set()
    total_uncompressed = 0
    try:
        with zipfile.ZipFile(src, "r") as zf:
            infos = [
                i
                for i in zf.infolist()
                if not i.is_dir() and i.filename != "manifest.json"
            ]
            if not infos:
                raise CodeEditorError("Extension package contains no importable files")
            if len(infos) > MAX_PACKAGE_ENTRIES:
                raise CodeEditorError("Extension package exceeds maximum entry count")
            for info in infos:
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_PACKAGE_UNCOMPRESSED_BYTES:
                    raise CodeEditorError(
                        "Extension package uncompressed size exceeds 25 MB limit"
                    )
                compressed = max(info.compress_size, 1)
                if (
                    info.file_size > 65536
                    and (info.file_size / compressed) > MAX_PACKAGE_COMPRESSION_RATIO
                ):
                    raise CodeEditorError(
                        "Extension package compression ratio exceeds safety limit"
                    )
                dest = normalize_archive_entry_path(info.filename)
                rel_p = dest.relative_to(PROJECT_ROOT).as_posix()
                if dest in seen_destinations:
                    raise CodeEditorError(
                        f"Archive contains duplicate destination path: {rel_p}"
                    )
                seen_destinations.add(dest)
                suffix = dest.suffix.lower()
                if suffix in {".java", ".class", ".jar"}:
                    entries.append(
                        PendingArchiveEntry(
                            archive_name=src.name,
                            rel_path=rel_p,
                            dest_path=None,
                            payload=b"",
                            skip_reason=(
                                "Unsupported Java extension entry; "
                                "only Python (.py) snippets are supported"
                            ),
                        )
                    )
                    continue
                if suffix != ".py":
                    entries.append(
                        PendingArchiveEntry(
                            archive_name=src.name,
                            rel_path=rel_p,
                            dest_path=None,
                            payload=b"",
                            skip_reason="Unsupported file extension; only .py allowed",
                        )
                    )
                    continue
                path_info = inspect_path(dest)
                if path_info.protected or path_info.ownership == "builtin":
                    entries.append(
                        PendingArchiveEntry(
                            archive_name=src.name,
                            rel_path=rel_p,
                            dest_path=None,
                            payload=b"",
                            skip_reason="already exists in Builtin",
                        )
                    )
                    continue
                writable_dest = writable_snippet_path(dest)
                payload = zf.read(info)
                try:
                    compile(payload.decode("utf-8"), str(writable_dest), "exec")
                except (UnicodeError, SyntaxError) as exc:
                    entries.append(
                        PendingArchiveEntry(
                            archive_name=src.name,
                            rel_path=rel_p,
                            dest_path=None,
                            payload=b"",
                            skip_reason=f"Invalid Python syntax: {type(exc).__name__}",
                        )
                    )
                    continue
                entries.append(
                    PendingArchiveEntry(
                        archive_name=src.name,
                        rel_path=rel_p,
                        dest_path=writable_dest,
                        payload=payload,
                        skip_reason=None,
                    )
                )
    except zipfile.BadZipFile as exc:
        raise CodeEditorError("Corrupted or invalid ZIP/.sxp archive") from exc
    return entries


class ImportSessionService:
    """Coordinate interactive extension import sessions and conflict decisions."""

    def __init__(self, store: StateStore | None = None) -> None:
        logger.debug("FR-code-editor-import-session-start: service initialized")
        self.store = store or StateStore()
        self._lock = threading.RLock()
        self._sessions: dict[str, ActiveImportSession] = {}

    def start_session(self, req: ImportSessionStartRequest) -> ImportSessionSnapshot:
        """Start an interactive import session across one or more archives."""
        logger.debug("FR-code-editor-import-session-start: invoked")
        all_entries: list[PendingArchiveEntry] = []
        for archive_path in req.archive_paths:
            all_entries.extend(validate_and_extract_archive(archive_path))

        session_id = "import-" + uuid.uuid4().hex
        session = ActiveImportSession(
            session_id=session_id,
            entries=all_entries,
            timeout_seconds=req.timeout_seconds,
        )
        with self._lock:
            self._sessions[session_id] = session
            snapshot = self._advance(session)
            self._persist(snapshot)
            return snapshot

    def apply_action(self, req: ImportSessionActionRequest) -> ImportSessionSnapshot:
        """Apply overwrite, overwrite_always, skip, skip_always, or cancel."""
        logger.debug("FR-code-editor-import-session-resolve: action=%s", req.action)
        with self._lock:
            session = self._sessions.get(req.session_id)
            if session is None:
                raise CodeEditorError(
                    f"Import session not found: {req.session_id}",
                    code=ErrorCode.NOT_FOUND,
                )
            if session.status in {"COMPLETED", "CANCELLED", "TIMED_OUT", "FAILED"}:
                raise CodeEditorError(
                    f"Import session is already in terminal state: {session.status}",
                    code=ErrorCode.CONFLICT,
                )
            if session.status != "AWAITING_DECISION":
                raise CodeEditorError(
                    "Import session is not awaiting a conflict decision",
                    code=ErrorCode.CONFLICT,
                )
            if (
                session.paused_at is not None
                and (time.monotonic() - session.paused_at) > session.timeout_seconds
            ):
                session.decision_mode = MODE_CANCEL
                session.status = "TIMED_OUT"
                session.paused_at = None
                self._record_remaining_cancelled(
                    session, reason="Timed out waiting for conflict decision"
                )
                self._publish_approved(session)
                session.message = "Import session timed out waiting for user decision"
                snapshot = self._to_snapshot(session)
                self._persist(snapshot)
                return snapshot

            entry = session.entries[session.cursor]
            session.paused_at = None
            session.status = "RUNNING"

            if req.action == "cancel":
                session.decision_mode = MODE_CANCEL
                session.status = "CANCELLED"
                self._record_remaining_cancelled(session, reason="Cancelled by user")
                self._publish_approved(session)
                session.message = "Import cancelled by user"
                snapshot = self._to_snapshot(session)
                self._persist(snapshot)
                return snapshot

            if req.action == "overwrite":
                session.decision_mode = MODE_OVERWRITE
                self._approve_entry(session, entry)
                session.cursor += 1
                session.decision_mode = MODE_DEFAULT
            elif req.action == "overwrite_always":
                session.decision_mode = MODE_OVERWRITE_ALWAYS
                self._approve_entry(session, entry)
                session.cursor += 1
            elif req.action == "skip":
                session.decision_mode = MODE_SKIP
                session.not_imported_files.append(
                    SkippedImportItem(name=entry.rel_path, reason="Skipped by user")
                )
                session.cursor += 1
                session.decision_mode = MODE_DEFAULT
            elif req.action == "skip_always":
                session.decision_mode = MODE_SKIP_ALWAYS
                session.not_imported_files.append(
                    SkippedImportItem(
                        name=entry.rel_path, reason="Skipped by user (Skip Always)"
                    )
                )
                session.cursor += 1

            snapshot = self._advance(session)
            self._persist(snapshot)
            return snapshot

    def get_session(self, session_id: str | None = None) -> ImportSessionSnapshot:
        """Return the current or latest persisted import session snapshot."""
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._to_snapshot(self._sessions[session_id])
            key = (
                f"import_session:{session_id}"
                if session_id
                else "import_session:latest"
            )
            raw = self.store.read(key)
            if raw is None:
                raise CodeEditorError(
                    "Import session not found", code=ErrorCode.NOT_FOUND
                )
            return ImportSessionSnapshot.model_validate(raw)

    def _advance(self, session: ActiveImportSession) -> ImportSessionSnapshot:
        while session.cursor < len(session.entries):
            entry = session.entries[session.cursor]
            if entry.skip_reason is not None or entry.dest_path is None:
                session.not_imported_files.append(
                    SkippedImportItem(
                        name=entry.rel_path,
                        reason=entry.skip_reason or "Skipped",
                    )
                )
                session.cursor += 1
                continue

            has_conflict = (
                entry.dest_path.exists() or entry.dest_path in session.approved_writes
            )
            if not has_conflict:
                self._approve_entry(session, entry)
                session.cursor += 1
                continue

            if session.decision_mode == MODE_OVERWRITE_ALWAYS:
                self._approve_entry(session, entry)
                session.cursor += 1
                continue

            if session.decision_mode == MODE_SKIP_ALWAYS:
                session.not_imported_files.append(
                    SkippedImportItem(
                        name=entry.rel_path, reason="Skipped by user (Skip Always)"
                    )
                )
                session.cursor += 1
                continue

            session.status = "AWAITING_DECISION"
            session.paused_at = time.monotonic()
            session.message = f"File '{entry.rel_path}' already exists"
            return self._to_snapshot(session)

        self._publish_approved(session)
        session.status = "COMPLETED"
        session.message = (
            f"Imported {len(session.new_files)} file(s), "
            f"skipped {len(session.not_imported_files)} file(s)"
        )
        return self._to_snapshot(session)

    def _approve_entry(
        self, session: ActiveImportSession, entry: PendingArchiveEntry
    ) -> None:
        assert entry.dest_path is not None
        session.approved_writes[entry.dest_path] = entry.payload
        if entry.rel_path not in session.new_files:
            session.new_files.append(entry.rel_path)

    def _record_remaining_cancelled(
        self, session: ActiveImportSession, *, reason: str
    ) -> None:
        while session.cursor < len(session.entries):
            entry = session.entries[session.cursor]
            session.not_imported_files.append(
                SkippedImportItem(
                    name=entry.rel_path,
                    reason=entry.skip_reason or reason,
                )
            )
            session.cursor += 1

    def _publish_approved(self, session: ActiveImportSession) -> None:
        if not session.approved_writes:
            return
        atomic_write_batch(session.approved_writes)
        compiler = CodeEditor()
        session.reload_results = [
            compiler.compile_file(str(dest)) for dest in session.approved_writes
        ]

    def _to_snapshot(self, session: ActiveImportSession) -> ImportSessionSnapshot:
        conflict_rel: str | None = None
        archive_name: str | None = None
        if session.status == "AWAITING_DECISION" and session.cursor < len(
            session.entries
        ):
            current = session.entries[session.cursor]
            conflict_rel = current.rel_path
            archive_name = current.archive_name
        return ImportSessionSnapshot(
            session_id=session.session_id,
            status=session.status,  # type: ignore[arg-type]
            decision_mode=session.decision_mode,  # type: ignore[arg-type]
            current_conflict=conflict_rel,
            current_archive=archive_name,
            processed_entries=session.cursor,
            total_entries=len(session.entries),
            new_files=list(session.new_files),
            not_imported_files=list(session.not_imported_files),
            reload_results=list(session.reload_results),
            message=session.message,
        )

    def _persist(self, snapshot: ImportSessionSnapshot) -> None:
        payload = snapshot.model_dump(mode="json")
        self.store.write(f"import_session:{snapshot.session_id}", payload)
        self.store.write("import_session:latest", payload)
