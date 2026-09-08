"""Bounded, checksummed workspace backup and staged restore."""

# TRY301 is intentionally local to the cleanup transaction: validation failures
# must pass through the same staging-directory rollback path.
# ruff: noqa: TRY301

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import uuid
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any

from app.contracts.workspace.errors import (
    WorkspaceCorruptionError,
    WorkspaceStorageError,
)
from app.contracts.workspace.models import (
    BackupFileRecord,
    WorkspaceBackupManifest,
    WorkspaceRef,
    WorkspaceStatus,
)

if TYPE_CHECKING:
    from app.services.workspace.manage_workspaces.config import ManageWorkspacesConfig

SHA256_HEX_LENGTH = 64


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a regular file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise WorkspaceCorruptionError("Manifest relative_path must be non-empty")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "\\" in value or ":" in value:
        message = f"Unsafe manifest path: {value!r}"
        raise WorkspaceCorruptionError(message)
    normalized = pure.as_posix()
    if normalized != value or normalized == "backup.json":
        message = f"Non-canonical manifest path: {value!r}"
        raise WorkspaceCorruptionError(message)
    return normalized


def _assert_regular_within(path: Path, root: Path) -> Path:
    if path.is_symlink() or not path.is_file():
        message = f"Backup member is not a regular file: {path}"
        raise WorkspaceCorruptionError(message)
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        message = f"Backup member escapes its root: {path}"
        raise WorkspaceCorruptionError(message) from error
    return resolved


def _resolve_db(root: Path) -> Path:
    """Return the canonical database path for the workspace.

    Args:
        root: Workspace root directory or database path.

    Returns:
        Canonical database path.
    """
    if root.suffix == ".db":
        return root
    central_db = root / "database" / "haruquantai.db"
    if central_db.exists():
        return central_db
    if (root / "haruquantai.db").exists():
        return root / "haruquantai.db"
    if (root / "data" / "database" / "haruquantai.db").exists():
        return root / "data" / "database" / "haruquantai.db"
    return central_db


def create_backup(  # noqa: C901, PLR0915 - one atomic staged publication.
    *,
    root: Path,
    workspace_id: str,
    schema_version: int,
    destination: Path,
    artifacts: tuple[tuple[str, str, int], ...],
    timestamp: str,
    config: ManageWorkspacesConfig,
) -> WorkspaceBackupManifest:
    """Create and atomically promote one consistent backup directory.

    Returns:
        The immutable backup manifest.

    Raises:
        WorkspaceCorruptionError: If catalogued bytes differ from their record.
        WorkspaceStorageError: If configured bounds or storage operations fail.
    """
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    backup_id = str(uuid.uuid4())
    staging = destination / f".backup-{backup_id}.staging"
    final = destination / f"backup_{backup_id}"
    if staging.exists() or final.exists():
        raise WorkspaceStorageError("Backup destination identity collision")
    staging.mkdir()
    try:
        database_dir = staging / "database"
        database_dir.mkdir(parents=True, exist_ok=True)
        source_db = _resolve_db(root)
        target_db = database_dir / "haruquantai.db"
        source_connection = sqlite3.connect(
            str(source_db), timeout=config.busy_timeout_seconds
        )
        target_connection = sqlite3.connect(str(target_db))
        try:
            source_connection.backup(target_connection)
        finally:
            target_connection.close()
            source_connection.close()

        sources: list[tuple[str, Path, str | None, int | None]] = [
            ("database/haruquantai.db", target_db, None, None)
        ]
        for artifact_hash, artifact_path, artifact_size in artifacts:
            safe = _safe_relative_path(artifact_path)
            if not safe.startswith("artifacts/objects/"):
                message = (
                    "Catalogued artifact path is outside immutable custody: " + safe
                )
                raise WorkspaceCorruptionError(message)
            source = _assert_regular_within(root / PurePosixPath(safe), root)
            sources.append((safe, source, artifact_hash, artifact_size))
        if len(sources) > config.max_manifest_files:
            raise WorkspaceStorageError("Backup exceeds max_manifest_files")

        records: list[BackupFileRecord] = []
        total_bytes = 0
        for relative_path, source, expected_hash, expected_size in sources:
            target = staging / PurePosixPath(relative_path)
            if source != target:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            actual_hash = sha256_file(target)
            actual_size = target.stat().st_size
            if expected_hash is not None and actual_hash != expected_hash:
                message = (
                    "Catalogued hash differs from artifact bytes: " + relative_path
                )
                raise WorkspaceCorruptionError(message)
            if expected_size is not None and actual_size != expected_size:
                message = (
                    "Catalogued size differs from artifact bytes: " + relative_path
                )
                raise WorkspaceCorruptionError(message)
            total_bytes += actual_size
            if total_bytes > config.max_backup_bytes:
                raise WorkspaceStorageError("Backup exceeds max_backup_bytes")
            records.append(BackupFileRecord(relative_path, actual_hash, actual_size))

        body: dict[str, Any] = {
            "backup_id": backup_id,
            "workspace_id": workspace_id,
            "schema_version": schema_version,
            "created_at": timestamp,
            "file_count": len(records),
            "total_bytes": total_bytes,
            "files": [
                {
                    "relative_path": record.relative_path,
                    "sha256_hash": record.sha256_hash,
                    "size_bytes": record.size_bytes,
                }
                for record in records
            ],
        }
        manifest_checksum = hashlib.sha256(_canonical_json(body)).hexdigest()
        manifest_document = {**body, "manifest_checksum": manifest_checksum}
        (staging / "backup.json").write_bytes(_canonical_json(manifest_document))
        Path(staging).replace(final)
        return WorkspaceBackupManifest(
            backup_id=backup_id,
            workspace_id=workspace_id,
            schema_version=schema_version,
            created_at=timestamp,
            file_count=len(records),
            total_bytes=total_bytes,
            files=tuple(records),
            manifest_checksum=manifest_checksum,
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _load_manifest(path: Path, config: ManageWorkspacesConfig) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        message = f"Invalid backup manifest: {error}"
        raise WorkspaceCorruptionError(message) from error
    if not isinstance(document, dict):
        raise WorkspaceCorruptionError("Backup manifest must be an object")
    checksum = document.pop("manifest_checksum", None)
    if not isinstance(checksum, str) or len(checksum) != SHA256_HEX_LENGTH:
        raise WorkspaceCorruptionError("Backup manifest checksum is missing or invalid")
    if hashlib.sha256(_canonical_json(document)).hexdigest() != checksum:
        raise WorkspaceCorruptionError("Backup manifest checksum mismatch")
    files = document.get("files")
    if not isinstance(files, list) or not files:
        raise WorkspaceCorruptionError("Backup manifest files must be non-empty")
    if len(files) > config.max_manifest_files:
        raise WorkspaceCorruptionError("Backup manifest exceeds max_manifest_files")
    if document.get("file_count") != len(files):
        raise WorkspaceCorruptionError("Backup manifest file_count mismatch")
    return {**document, "manifest_checksum": checksum}


def restore_backup(  # noqa: C901, PLR0912, PLR0915 - staged validation pipeline.
    *,
    manifest_path: Path,
    target: Path,
    verify_checksums: bool,
    config: ManageWorkspacesConfig,
    expected_workspace_id: str | None = None,
    expected_account_id: str | None = None,
) -> WorkspaceRef:
    """Verify a backup in isolated staging before atomically exposing it.

    ``verify_checksums`` is retained for API compatibility; integrity checks are
    mandatory and can no longer be disabled.

    Returns:
        The restored workspace reference after atomic promotion.

    Raises:
        WorkspaceCorruptionError: If manifest, bytes, database, or scope is invalid.
        WorkspaceStorageError: If the target is not empty or promotion fails.
    """
    _ = verify_checksums
    manifest_path = (
        manifest_path if manifest_path.is_file() else manifest_path / "backup.json"
    ).resolve()
    document = _load_manifest(manifest_path, config)
    source_root = manifest_path.parent
    target = target.resolve()
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        message = f"Restore target must be an empty directory: {target}"
        raise WorkspaceStorageError(message)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.parent / f".{target.name}.restore-{uuid.uuid4()}.staging"
    staging.mkdir()
    try:
        seen: set[str] = set()
        records: dict[str, tuple[str, int]] = {}
        total_bytes = 0
        for item in document["files"]:
            if not isinstance(item, dict):
                raise WorkspaceCorruptionError("Backup file record must be an object")
            relative = _safe_relative_path(item.get("relative_path"))
            if relative in seen:
                message = f"Duplicate backup path: {relative}"
                raise WorkspaceCorruptionError(message)
            seen.add(relative)
            expected_hash = item.get("sha256_hash")
            expected_size = item.get("size_bytes")
            if (
                not isinstance(expected_hash, str)
                or len(expected_hash) != SHA256_HEX_LENGTH
            ):
                message = f"Invalid hash for {relative}"
                raise WorkspaceCorruptionError(message)
            if not isinstance(expected_size, int) or expected_size < 0:
                message = f"Invalid size for {relative}"
                raise WorkspaceCorruptionError(message)
            total_bytes += expected_size
            if total_bytes > config.max_backup_bytes:
                raise WorkspaceCorruptionError("Backup exceeds max_backup_bytes")
            source = _assert_regular_within(
                source_root / PurePosixPath(relative), source_root
            )
            if source.stat().st_size != expected_size:
                message = f"Size mismatch for {relative}"
                raise WorkspaceCorruptionError(message)
            if sha256_file(source) != expected_hash:
                message = f"Checksum mismatch for {relative}"
                raise WorkspaceCorruptionError(message)
            destination = staging / PurePosixPath(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            records[relative] = (expected_hash, expected_size)
        if total_bytes != document.get("total_bytes"):
            raise WorkspaceCorruptionError("Backup manifest total_bytes mismatch")
        db_path = _resolve_db(staging)
        if not db_path.is_file():
            raise WorkspaceCorruptionError("Restored workspace database is missing")
        connection = sqlite3.connect(str(db_path))
        connection.row_factory = sqlite3.Row
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if integrity is None or integrity[0] != "ok":
                raise WorkspaceCorruptionError("Restored workspace database is corrupt")
            identity = connection.execute(
                "SELECT id, name, created_at, account_id FROM workspace LIMIT 1"
            ).fetchone()
            if identity is None or identity["id"] != document.get("workspace_id"):
                raise WorkspaceCorruptionError("Restored workspace identity mismatch")
            if (
                expected_workspace_id is not None
                and identity["id"] != expected_workspace_id
            ):
                raise WorkspaceCorruptionError("Restore request workspace ID mismatch")
            if (
                expected_account_id is not None
                and identity["account_id"] != expected_account_id
            ):
                raise WorkspaceCorruptionError("Restore request account scope mismatch")
            artifacts = connection.execute(
                "SELECT content_hash, relative_path, size_bytes FROM artifacts "
                "WHERE is_committed = 1"
            ).fetchall()
            for artifact in artifacts:
                record = records.get(str(artifact["relative_path"]))
                if record != (
                    str(artifact["content_hash"]),
                    int(artifact["size_bytes"]),
                ):
                    raise WorkspaceCorruptionError(
                        "Restored artifact catalogue does not match manifest"
                    )
        finally:
            connection.close()
        if target.exists():
            target.rmdir()
        Path(staging).replace(target)
        return WorkspaceRef(
            workspace_id=str(identity["id"]),
            name=str(identity["name"]),
            root_path=target,
            status=WorkspaceStatus.READY,
            created_at=str(identity["created_at"]),
        )
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
