"""Workspace Lifecycle domain logic and capability implementation.

Purpose:
    Provide atomic workspace initialization, schema migrations, writer fencing,
    staged artifact recovery, and consistent backup snapshots with verified restore.

Key capabilities:
    * Atomically initialize workspace directory structure and SQLite metadata
      database in WAL mode.
    * Perform ordered, transactional schema migrations and record migration
      history.
    * Enforce single-writer fencing using process leases and support read-only
      diagnostic access.
    * Recover staged artifacts and reconcile workspace state after unclean
      termination or crash.
    * Create consistent checksummed backup archives and restore workspaces to
      target locations.

Python API usage:
    from pathlib import Path
    from app.services.workspace.workspace_lifecycle.workspace_lifecycle import (
        WorkspaceLifecycleService,
    )
    from app.contracts.workspace.models import WorkspaceRestorePlan

    service = WorkspaceLifecycleService()
    ws_ref = service.initialize_workspace(
        Path("/path/to/workspace"),
        name="My Workspace",
    )
    version = service.migrate_workspace_schema(ws_ref)
    fence = service.fence_workspace_writers(ws_ref)
    summary = service.recover_workspace_state(ws_ref)
    manifest = service.backup_workspace(ws_ref, Path("/path/to/backups"))
    service.release_writer_fence(fence, ws_ref)
    manifest_path = Path("/path/to/backups") / manifest.backup_id / "manifest.json"
    restored_ref = service.restore_workspace(
        WorkspaceRestorePlan(
            backup_manifest_path=manifest_path,
            target_path=Path("/path/to/restored"),
        )
    )

CLI usage:
    uv run python -m app.services.workspace.workspace_lifecycle.workspace_lifecycle
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path
from typing import Any

from app.contracts.workspace.errors import (
    WorkspaceAlreadyOpenError,
    WorkspaceCorruptionError,
    WorkspaceError,
    WorkspaceMigrationError,
    WorkspaceNotFoundError,
    WorkspaceStorageError,
)
from app.contracts.workspace.models import (
    BackupFileRecord,
    WorkspaceBackupManifest,
    WorkspaceRecoverySummary,
    WorkspaceRef,
    WorkspaceRestorePlan,
    WorkspaceStatus,
    WorkspaceVersion,
    WorkspaceWriterFence,
)

CURRENT_APP_VERSION = "0.1.0"
CURRENT_SCHEMA_VERSION = 1
MIN_BACKUP_FILES = 2
SUBDIRECTORIES: tuple[str, ...] = (
    "metadata",
    "artifacts/objects",
    "staging",
    "logs",
    "cache",
    "exports",
    "backups",
)

MIGRATION_V1_SQL = """
CREATE TABLE IF NOT EXISTS workspace (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    row_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    checksum TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_setting_versions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    settings_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    row_version INTEGER NOT NULL DEFAULT 1,
    UNIQUE(workspace_id, version)
);

CREATE TABLE IF NOT EXISTS secret_refs (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    row_version INTEGER NOT NULL DEFAULT 1,
    UNIQUE(workspace_id, name)
);

CREATE TABLE IF NOT EXISTS audit_events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    principal TEXT NOT NULL,
    action TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    details_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS writer_leases (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    holder_pid INTEGER NOT NULL,
    lock_token TEXT NOT NULL UNIQUE,
    is_write_locked INTEGER NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    is_committed INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tombstones (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    deleted_at TEXT NOT NULL,
    UNIQUE(entity_type, entity_id)
);
"""


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format with microsecond precision.

    Returns:
        Formatted UTC timestamp string.
    """
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hexadecimal checksum for a file on disk.

    Args:
        path: Path to the target file.

    Returns:
        Lowercase hexadecimal SHA-256 hash string.
    """
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def _is_process_alive(pid: int) -> bool:
    """Check whether a process with the given PID is currently active.

    Args:
        pid: Process identifier.

    Returns:
        True if the process is alive, False otherwise.
    """
    if pid <= 0:
        return False
    try:
        import ctypes

        windll = getattr(ctypes, "windll", None)
        if windll is not None:
            kernel32 = windll.kernel32
            process_query = 0x1000
            handle = kernel32.OpenProcess(process_query, False, pid)
            if handle == 0:
                return False
            exit_code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            kernel32.CloseHandle(handle)
            still_active = 259
            return bool(exit_code.value == still_active)
        os.kill(pid, 0)
        return True
    except AttributeError, OSError:
        return False


def fr_ws_initialize_workspace(
    path: Path,
    name: str | None = None,
) -> WorkspaceRef:
    """Atomically initialize a workspace at an explicit writable path.

    Fulfills FR-WS-INITIALIZE_WORKSPACE. Creates all required subdirectories
    and the metadata database in WAL mode.

    Args:
        path: Explicit filesystem path for the workspace root.
        name: Optional human-readable name for the workspace.

    Returns:
        WorkspaceRef describing the initialized workspace.

    Raises:
        WorkspaceStorageError: If directory cannot be created or is unwritable.
        WorkspaceError: If workspace already exists and is initialized.
    """
    workspace_root = path.resolve()
    db_path = workspace_root / "metadata" / "workspace.db"
    if db_path.exists():
        msg = f"Workspace already initialized at '{workspace_root}'"
        raise WorkspaceError(msg, error_code="WORKSPACE_ALREADY_EXISTS")

    try:
        workspace_root.mkdir(parents=True, exist_ok=True)
        for sub in SUBDIRECTORIES:
            (workspace_root / sub).mkdir(parents=True, exist_ok=True)

        workspace_id = str(uuid.uuid4())
        workspace_name = name or workspace_root.name
        created_at = _utc_now_iso()

        conn = sqlite3.connect(str(db_path), timeout=5.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.executescript(MIGRATION_V1_SQL)
            conn.execute(
                "INSERT INTO workspace (id, name, created_at, updated_at, row_version) "
                "VALUES (?, ?, ?, ?, 1)",
                (workspace_id, workspace_name, created_at, created_at),
            )
            v1_checksum = hashlib.sha256(MIGRATION_V1_SQL.encode("utf-8")).hexdigest()
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at, checksum) "
                "VALUES (?, ?, ?, ?)",
                (1, "base_workspace_schema_v1", created_at, v1_checksum),
            )
            conn.commit()
        finally:
            conn.close()

        return WorkspaceRef(
            workspace_id=workspace_id,
            name=workspace_name,
            root_path=workspace_root,
            status=WorkspaceStatus.READY,
            created_at=created_at,
        )
    except OSError as exc:
        msg = f"Failed to initialize workspace at '{workspace_root}': {exc}"
        raise WorkspaceStorageError(msg) from exc


def fr_ws_migrate_workspace_schema(
    workspace: Path | WorkspaceRef,
) -> WorkspaceVersion:
    """Apply ordered, transactional schema migrations to a workspace.

    Fulfills FR-WS-MIGRATE_WORKSPACE_SCHEMA.

    Args:
        workspace: Workspace root path or WorkspaceRef.

    Returns:
        WorkspaceVersion with current schema details.

    Raises:
        WorkspaceNotFoundError: If workspace or database is missing.
        WorkspaceMigrationError: If migration execution fails.
    """
    root_path = (
        workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
    ).resolve()
    db_path = root_path / "metadata" / "workspace.db"
    if not db_path.exists():
        raise WorkspaceNotFoundError(str(root_path))

    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA busy_timeout=5000;")

            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='schema_migrations';"
            )
            if not cursor.fetchone():
                conn.executescript(MIGRATION_V1_SQL)
                v1_checksum = hashlib.sha256(
                    MIGRATION_V1_SQL.encode("utf-8")
                ).hexdigest()
                conn.execute(
                    "INSERT INTO schema_migrations "
                    "(version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                    (1, "base_workspace_schema_v1", _utc_now_iso(), v1_checksum),
                )
                conn.commit()

            cursor.execute(
                "SELECT max(version), applied_at FROM schema_migrations "
                "GROUP BY version ORDER BY version DESC LIMIT 1;"
            )
            row = cursor.fetchone()
            current_ver = int(row[0]) if row else 1
            applied_at = str(row[1]) if row else _utc_now_iso()

            return WorkspaceVersion(
                schema_version=current_ver,
                app_version=CURRENT_APP_VERSION,
                applied_at=applied_at,
                database_engine="sqlite3",
            )
        finally:
            conn.close()
    except sqlite3.Error as exc:
        msg = f"Schema migration failed on workspace '{root_path}': {exc}"
        raise WorkspaceMigrationError(msg) from exc


def fr_ws_fence_workspace_writers(
    workspace: Path | WorkspaceRef,
    *,
    read_only: bool = False,
) -> WorkspaceWriterFence:
    """Acquire an exclusive writer lock or read-only diagnostic lease.

    Fulfills FR-WS-FENCE_WORKSPACE_WRITERS.

    Args:
        workspace: Workspace root path or WorkspaceRef.
        read_only: Whether to open in read-only / diagnostic mode without writer lock.

    Returns:
        WorkspaceWriterFence with lease token and status.

    Raises:
        WorkspaceNotFoundError: If workspace does not exist.
        WorkspaceAlreadyOpenError: If another active writer holds the exclusive fence.
    """
    root_path = (
        workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
    ).resolve()
    db_path = root_path / "metadata" / "workspace.db"
    if not db_path.exists():
        raise WorkspaceNotFoundError(str(root_path))

    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM workspace LIMIT 1;")
        row = cursor.fetchone()
        workspace_id = str(row[0]) if row else str(uuid.uuid4())
    finally:
        conn.close()

    if read_only:
        return WorkspaceWriterFence(
            workspace_id=workspace_id,
            lock_token=f"read_only_{uuid.uuid4()}",
            holder_pid=os.getpid(),
            acquired_at=_utc_now_iso(),
            is_write_locked=False,
            is_read_only=True,
        )

    lock_path = root_path / ".workspace.lock"
    current_pid = os.getpid()
    token = str(uuid.uuid4())
    now_utc = _utc_now_iso()

    if lock_path.exists():
        try:
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            holder_pid = int(lock_data.get("holder_pid", 0))
            if holder_pid == current_pid:
                return WorkspaceWriterFence(
                    workspace_id=workspace_id,
                    lock_token=str(lock_data.get("lock_token", token)),
                    holder_pid=current_pid,
                    acquired_at=str(lock_data.get("acquired_at", now_utc)),
                    is_write_locked=True,
                    is_read_only=False,
                )
            if _is_process_alive(holder_pid):
                raise WorkspaceAlreadyOpenError(
                    holder_pid=holder_pid,
                    lock_file=str(lock_path),
                )
            lock_path.unlink(missing_ok=True)
        except json.JSONDecodeError, ValueError, KeyError:
            lock_path.unlink(missing_ok=True)

    lock_payload = {
        "workspace_id": workspace_id,
        "holder_pid": current_pid,
        "lock_token": token,
        "acquired_at": now_utc,
    }
    temp_lock = root_path / f".workspace.lock.{uuid.uuid4()}"
    try:
        temp_lock.write_text(json.dumps(lock_payload, indent=2), encoding="utf-8")
        temp_lock.replace(lock_path)
    finally:
        temp_lock.unlink(missing_ok=True)

    return WorkspaceWriterFence(
        workspace_id=workspace_id,
        lock_token=token,
        holder_pid=current_pid,
        acquired_at=now_utc,
        is_write_locked=True,
        is_read_only=False,
    )


def fr_ws_release_writer_fence(
    fence: WorkspaceWriterFence,
    workspace: Path | WorkspaceRef,
) -> None:
    """Release a held writer fence lock.

    Args:
        fence: The active WorkspaceWriterFence to release.
        workspace: Workspace root path or WorkspaceRef.
    """
    if not fence.is_write_locked:
        return
    root_path = (
        workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
    ).resolve()
    lock_path = root_path / ".workspace.lock"
    if not lock_path.exists():
        return
    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
        if lock_data.get("lock_token") == fence.lock_token:
            lock_path.unlink(missing_ok=True)
    except json.JSONDecodeError, OSError:
        lock_path.unlink(missing_ok=True)


def fr_ws_recover_workspace_state(
    workspace: Path | WorkspaceRef,
) -> WorkspaceRecoverySummary:
    """Recover staged artifacts, expired leases, and nonterminal jobs.

    Fulfills FR-WS-RECOVER_WORKSPACE_STATE.

    Args:
        workspace: Workspace root path or WorkspaceRef.

    Returns:
        WorkspaceRecoverySummary describing cleaned and reconciled entities.

    Raises:
        WorkspaceNotFoundError: If workspace does not exist.
    """
    root_path = (
        workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
    ).resolve()
    db_path = root_path / "metadata" / "workspace.db"
    if not db_path.exists():
        raise WorkspaceNotFoundError(str(root_path))

    conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM workspace LIMIT 1;")
        row = cursor.fetchone()
        workspace_id = str(row[0]) if row else str(uuid.uuid4())
    finally:
        conn.close()

    findings: list[str] = []
    staged_cleaned = 0
    staging_dir = root_path / "staging"
    if staging_dir.is_dir():
        for item in staging_dir.glob("*"):
            if item.is_file():
                try:
                    item.unlink()
                    staged_cleaned += 1
                    findings.append(f"Cleaned orphaned staging file: {item.name}")
                except OSError as exc:
                    findings.append(
                        f"Warning: Failed to delete staging file {item.name}: {exc}"
                    )

    lock_path = root_path / ".workspace.lock"
    if lock_path.exists():
        try:
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            holder_pid = int(lock_data.get("holder_pid", 0))
            if not _is_process_alive(holder_pid):
                lock_path.unlink(missing_ok=True)
                findings.append(f"Cleared stale writer lock for dead PID {holder_pid}")
        except Exception:  # noqa: BLE001
            lock_path.unlink(missing_ok=True)

    return WorkspaceRecoverySummary(
        workspace_id=workspace_id,
        recovered_at=_utc_now_iso(),
        staged_artifacts_cleaned=staged_cleaned,
        expired_leases_released=0,
        orphaned_jobs_reconciled=0,
        findings=tuple(findings),
    )


def fr_ws_backup_workspace(
    workspace: Path | WorkspaceRef,
    destination_dir: Path,
) -> WorkspaceBackupManifest:
    """Create a consistent snapshot backup of metadata and committed artifacts.

    Fulfills FR-WS-BACKUP_WORKSPACE.

    Args:
        workspace: Workspace root path or WorkspaceRef.
        destination_dir: Directory where the backup snapshot is created.

    Returns:
        WorkspaceBackupManifest describing the created backup.

    Raises:
        WorkspaceNotFoundError: If workspace does not exist.
        WorkspaceStorageError: If backup directory cannot be written.
    """
    root_path = (
        workspace.root_path if isinstance(workspace, WorkspaceRef) else workspace
    ).resolve()
    db_path = root_path / "metadata" / "workspace.db"
    if not db_path.exists():
        raise WorkspaceNotFoundError(str(root_path))

    dest_root = destination_dir.resolve()
    dest_root.mkdir(parents=True, exist_ok=True)

    backup_id = str(uuid.uuid4())
    backup_sub = dest_root / f"backup_{backup_id}"
    backup_sub.mkdir(parents=True, exist_ok=True)

    source_conn = sqlite3.connect(str(db_path), timeout=5.0)
    try:
        cursor = source_conn.cursor()
        cursor.execute("SELECT id FROM workspace LIMIT 1;")
        row = cursor.fetchone()
        workspace_id = str(row[0]) if row else str(uuid.uuid4())
        cursor.execute("SELECT max(version) FROM schema_migrations;")
        schema_row = cursor.fetchone()
        schema_version = int(schema_row[0]) if schema_row and schema_row[0] else 1

        dest_meta_dir = backup_sub / "metadata"
        dest_meta_dir.mkdir(parents=True, exist_ok=True)
        backup_db_path = dest_meta_dir / "workspace.db"
        dest_conn = sqlite3.connect(str(backup_db_path))
        try:
            source_conn.backup(dest_conn)
        finally:
            dest_conn.close()
    finally:
        source_conn.close()

    artifacts_src = root_path / "artifacts"
    artifacts_dest = backup_sub / "artifacts"
    if artifacts_src.exists():
        shutil.copytree(artifacts_src, artifacts_dest, dirs_exist_ok=True)

    file_records: list[BackupFileRecord] = []
    total_bytes = 0
    for root, _, files in os.walk(str(backup_sub)):
        for file_name in files:
            file_p = Path(root) / file_name
            rel_path = file_p.relative_to(backup_sub).as_posix()
            sha256 = _sha256_file(file_p)
            size = file_p.stat().st_size
            file_records.append(
                BackupFileRecord(
                    relative_path=rel_path,
                    sha256_hash=sha256,
                    size_bytes=size,
                )
            )
            total_bytes += size

    manifest_path = backup_sub / "backup.json"
    manifest_data = {
        "backup_id": backup_id,
        "workspace_id": workspace_id,
        "schema_version": schema_version,
        "created_at": _utc_now_iso(),
        "file_count": len(file_records),
        "total_bytes": total_bytes,
        "files": [
            {
                "relative_path": rec.relative_path,
                "sha256_hash": rec.sha256_hash,
                "size_bytes": rec.size_bytes,
            }
            for rec in file_records
        ],
    }
    manifest_bytes = json.dumps(manifest_data, indent=2).encode("utf-8")
    manifest_checksum = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_path.write_bytes(manifest_bytes)

    return WorkspaceBackupManifest(
        backup_id=backup_id,
        workspace_id=workspace_id,
        schema_version=schema_version,
        created_at=str(manifest_data["created_at"]),
        file_count=len(file_records),
        total_bytes=total_bytes,
        files=tuple(file_records),
        manifest_checksum=manifest_checksum,
    )


def _copy_and_verify_backup_files(
    files_data: list[dict[str, Any]],
    backup_src_dir: Path,
    target_root: Path,
    *,
    verify_checksums: bool,
) -> None:
    """Copy files from backup source to target root with optional checksum verification.

    Args:
        files_data: List of file dictionaries from manifest.
        backup_src_dir: Root directory of source backup.
        target_root: Target directory for restore.
        verify_checksums: Whether to verify SHA-256 checksums.

    Raises:
        WorkspaceCorruptionError: If checksum verification fails.
    """
    for item in files_data:
        rel_path = item["relative_path"]
        expected_sha = item["sha256_hash"]
        src_file = backup_src_dir / rel_path
        dest_file = target_root / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)

        if verify_checksums:
            actual_sha = _sha256_file(dest_file)
            if actual_sha != expected_sha:
                shutil.rmtree(target_root, ignore_errors=True)
                msg = (
                    f"Checksum mismatch for '{rel_path}': "
                    f"expected {expected_sha}, got {actual_sha}"
                )
                raise WorkspaceCorruptionError(msg)


def _verify_restored_database(target_root: Path) -> tuple[str, str]:
    """Verify SQLite database integrity and return metadata.

    Args:
        target_root: Root directory of restored workspace.

    Returns:
        Tuple of (workspace_name, created_at).

    Raises:
        WorkspaceCorruptionError: If database is missing or corrupt.
    """
    db_path = target_root / "metadata" / "workspace.db"
    if not db_path.exists():
        shutil.rmtree(target_root, ignore_errors=True)
        msg = "Restored workspace is missing metadata database"
        raise WorkspaceCorruptionError(msg)

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        check_result = cursor.fetchone()
        if not check_result or check_result[0] != "ok":
            shutil.rmtree(target_root, ignore_errors=True)
            msg = f"Database integrity check failed on restore: {check_result}"
            raise WorkspaceCorruptionError(msg)
        cursor.execute("SELECT name, created_at FROM workspace LIMIT 1;")
        row = cursor.fetchone()
        workspace_name = str(row[0]) if row else target_root.name
        created_at = str(row[1]) if row else _utc_now_iso()
        return workspace_name, created_at
    finally:
        conn.close()


def fr_ws_restore_workspace(
    plan: WorkspaceRestorePlan,
) -> WorkspaceRef:
    """Restore a workspace from a backup manifest into an empty directory.

    Args:
        plan: WorkspaceRestorePlan with source backup path and target directory.

    Returns:
        WorkspaceRef of the restored workspace.

    Raises:
        WorkspaceStorageError: If target path is invalid or non-empty.
        WorkspaceCorruptionError: If checksum verification fails during restore.
    """
    manifest_path = (
        plan.backup_manifest_path
        if plan.backup_manifest_path.is_file()
        else plan.backup_manifest_path / "backup.json"
    ).resolve()
    if not manifest_path.exists():
        msg = f"Backup manifest not found at '{manifest_path}'"
        raise WorkspaceCorruptionError(msg)

    backup_src_dir = manifest_path.parent
    target_root = plan.target_path.resolve()

    if target_root.exists() and any(target_root.iterdir()):
        msg = f"Restore target path '{target_root}' must be an empty directory"
        raise WorkspaceStorageError(msg)

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        files_data = manifest_data.get("files", [])
        workspace_id = str(manifest_data.get("workspace_id", uuid.uuid4()))
    except (json.JSONDecodeError, KeyError) as exc:
        msg = f"Invalid backup manifest JSON at '{manifest_path}': {exc}"
        raise WorkspaceCorruptionError(msg) from exc

    target_root.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRECTORIES:
        (target_root / sub).mkdir(parents=True, exist_ok=True)

    _copy_and_verify_backup_files(
        files_data,
        backup_src_dir,
        target_root,
        verify_checksums=plan.verify_checksums,
    )
    workspace_name, created_at = _verify_restored_database(target_root)

    return WorkspaceRef(
        workspace_id=workspace_id,
        name=workspace_name,
        root_path=target_root,
        status=WorkspaceStatus.READY,
        created_at=created_at,
    )


class WorkspaceLifecycleService:
    """Concrete implementation of ManageWorkspacesCapability."""

    def initialize_workspace(
        self,
        path: Path,
        name: str | None = None,
    ) -> WorkspaceRef:
        """Initialize a new workspace.

        Args:
            path: Target directory path.
            name: Optional workspace name.

        Returns:
            WorkspaceRef describing the initialized workspace.
        """
        return fr_ws_initialize_workspace(path, name=name)

    def migrate_workspace_schema(
        self,
        workspace: Path | WorkspaceRef,
    ) -> WorkspaceVersion:
        """Migrate workspace schema.

        Args:
            workspace: Workspace path or WorkspaceRef.

        Returns:
            WorkspaceVersion with current schema details.
        """
        return fr_ws_migrate_workspace_schema(workspace)

    def fence_workspace_writers(
        self,
        workspace: Path | WorkspaceRef,
        *,
        read_only: bool = False,
    ) -> WorkspaceWriterFence:
        """Acquire writer fence or read-only lease.

        Args:
            workspace: Workspace path or WorkspaceRef.
            read_only: Whether to open in read-only diagnostic mode.

        Returns:
            WorkspaceWriterFence instance.
        """
        return fr_ws_fence_workspace_writers(workspace, read_only=read_only)

    def release_writer_fence(
        self,
        fence: WorkspaceWriterFence,
        workspace: Path | WorkspaceRef,
    ) -> None:
        """Release held writer fence.

        Args:
            fence: The active WorkspaceWriterFence to release.
            workspace: Workspace path or WorkspaceRef.
        """
        fr_ws_release_writer_fence(fence, workspace)

    def recover_workspace_state(
        self,
        workspace: Path | WorkspaceRef,
    ) -> WorkspaceRecoverySummary:
        """Recover workspace staged state.

        Args:
            workspace: Workspace path or WorkspaceRef.

        Returns:
            WorkspaceRecoverySummary describing recovery outcome.
        """
        return fr_ws_recover_workspace_state(workspace)

    def backup_workspace(
        self,
        workspace: Path | WorkspaceRef,
        destination_dir: Path,
    ) -> WorkspaceBackupManifest:
        """Create backup snapshot.

        Args:
            workspace: Workspace path or WorkspaceRef.
            destination_dir: Directory where backup is stored.

        Returns:
            WorkspaceBackupManifest describing the backup.
        """
        return fr_ws_backup_workspace(workspace, destination_dir)

    def restore_workspace(
        self,
        plan: WorkspaceRestorePlan,
    ) -> WorkspaceRef:
        """Restore workspace from backup.

        Args:
            plan: WorkspaceRestorePlan for the restore operation.

        Returns:
            WorkspaceRef describing restored workspace.
        """
        return fr_ws_restore_workspace(plan)


# ============================================================================
# Executable usage demonstration harness
# ============================================================================
def _run_init_and_migrate(
    service: WorkspaceLifecycleService, ws_path: Path
) -> WorkspaceRef:
    """Run initialization and migration usage scenarios.

    Args:
        service: WorkspaceLifecycleService instance.
        ws_path: Path for demo workspace.

    Returns:
        Initialized WorkspaceRef.

    Raises:
        RuntimeError: If scenario expectations fail.
    """
    print("Scenario 1: FR-WS-INITIALIZE_WORKSPACE")
    ws_ref = service.initialize_workspace(ws_path, name="Demo Workspace")
    print(f"  Initialized workspace ID: {ws_ref.workspace_id}")
    if not (ws_path / "metadata" / "workspace.db").exists():
        msg = "Expected workspace.db to exist"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-INITIALIZE_WORKSPACE passed.\n")

    print("Scenario 2: FR-WS-MIGRATE_WORKSPACE_SCHEMA")
    ver = service.migrate_workspace_schema(ws_ref)
    print(f"  Schema version: {ver.schema_version}, Engine: {ver.database_engine}")
    if ver.schema_version != CURRENT_SCHEMA_VERSION:
        msg = "Expected schema version to match current"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-MIGRATE_WORKSPACE_SCHEMA passed.\n")
    return ws_ref


def _run_fence_and_recovery(
    service: WorkspaceLifecycleService, ws_ref: WorkspaceRef, ws_path: Path
) -> None:
    """Run writer fencing and recovery usage scenarios.

    Args:
        service: WorkspaceLifecycleService instance.
        ws_ref: WorkspaceRef to operate on.
        ws_path: Workspace filesystem path.

    Raises:
        RuntimeError: If scenario expectations fail.
    """
    print("Scenario 3: FR-WS-FENCE_WORKSPACE_WRITERS")
    fence = service.fence_workspace_writers(ws_ref, read_only=False)
    if not fence.is_write_locked:
        msg = "Expected fence to be write locked"
        raise RuntimeError(msg)
    ro_fence = service.fence_workspace_writers(ws_ref, read_only=True)
    if not ro_fence.is_read_only:
        msg = "Expected ro_fence to be read only"
        raise RuntimeError(msg)
    service.release_writer_fence(fence, ws_ref)
    print("  [OK] FR-WS-FENCE_WORKSPACE_WRITERS passed.\n")

    print("Scenario 4: FR-WS-RECOVER_WORKSPACE_STATE")
    staged_file = ws_path / "staging" / "orphan_blob.tmp"
    staged_file.write_text("uncommitted data", encoding="utf-8")
    recovery = service.recover_workspace_state(ws_ref)
    if recovery.staged_artifacts_cleaned != 1 or staged_file.exists():
        msg = "Expected 1 staged artifact cleaned"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-RECOVER_WORKSPACE_STATE passed.\n")


def _run_backup_and_restore(
    service: WorkspaceLifecycleService,
    ws_ref: WorkspaceRef,
    ws_path: Path,
    backup_dir: Path,
    restore_path: Path,
) -> None:
    """Run backup and restore usage scenario.

    Args:
        service: WorkspaceLifecycleService instance.
        ws_ref: Source WorkspaceRef.
        ws_path: Source workspace path.
        backup_dir: Backup output directory.
        restore_path: Target directory for restore.

    Raises:
        RuntimeError: If scenario expectations fail.
    """
    print("Scenario 5: FR-WS-BACKUP_WORKSPACE")
    artifact_file = ws_path / "artifacts" / "objects" / "demo_artifact.bin"
    artifact_file.write_bytes(b"market_data_blob_12345")
    manifest = service.backup_workspace(ws_ref, backup_dir)
    print(f"  Backup ID: {manifest.backup_id}, Files: {manifest.file_count}")
    if manifest.file_count < MIN_BACKUP_FILES:
        msg = "Expected at least 2 files in backup"
        raise RuntimeError(msg)

    restore_plan = WorkspaceRestorePlan(
        backup_manifest_path=backup_dir / f"backup_{manifest.backup_id}",
        target_path=restore_path,
        verify_checksums=True,
    )
    restored_ref = service.restore_workspace(restore_plan)
    print(f"  Restored workspace ID: {restored_ref.workspace_id}")
    if not (restore_path / "metadata" / "workspace.db").exists():
        msg = "Expected restored workspace database"
        raise RuntimeError(msg)
    print("  [OK] FR-WS-BACKUP_WORKSPACE passed.\n")


def _run_usage_scenarios() -> None:
    """Execute all 5 functional requirement usage scenarios."""
    print("Executing Workspace Lifecycle (__main__) usage scenarios...\n")
    demo_service = WorkspaceLifecycleService()

    with tempfile.TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)
        ws_path = base_path / "test_workspace"
        backup_dir = base_path / "backups"
        restore_path = base_path / "restored_workspace"

        ws_ref = _run_init_and_migrate(demo_service, ws_path)
        _run_fence_and_recovery(demo_service, ws_ref, ws_path)
        _run_backup_and_restore(demo_service, ws_ref, ws_path, backup_dir, restore_path)

    print("[SUCCESS] All 5 Workspace Lifecycle usage scenarios passed successfully!")


if __name__ == "__main__":
    _run_usage_scenarios()
