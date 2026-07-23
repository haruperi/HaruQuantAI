"""Immutable approved-root backups, atomic restore, and raw-data retention."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from app.services.data.audit.store import persist_audit_event
from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import (
    BackupEntry,
    BackupManifest,
    BackupTarget,
    RestoreReport,
    StorageManifest,
)
from app.services.data.persistence.dataset_writer import (
    compute_file_hash,
    resolve_approved_storage_path,
    resolve_data_root,
)
from app.services.data.persistence.locking import acquire_write_lock
from app.utils import AuditEvent, derive_stable_id, generate_id, logger, utc_now

if TYPE_CHECKING:
    from collections.abc import Sequence

_BACKUP_ROOT = Path("artifacts/data/backups")
_MANIFEST_NAME = "manifest.json"
_WINDOWS_RENAME_ATTEMPTS = 3
_WINDOWS_RENAME_DELAY_SECONDS = 0.01

type _PreparedRestore = tuple[BackupEntry, Path, Path, Path]


def _error(code: str, request_id: str, operation: str) -> DataError:
    """Build one redacted backup-boundary error.

    Args:
        code: Registered Data error code.
        request_id: Trace identifier for the operation.
        operation: Safe operation label.

    Returns:
        Typed Data-domain error.
    """
    logger.debug("Building a backup boundary error for %s", operation)
    return DataError(
        code,
        safe_details={"operation": operation},
        request_id=request_id,
    )


def _require(
    condition: bool,
    code: str,
    request_id: str,
    operation: str,
) -> None:
    """Raise a typed boundary error when a required condition is false.

    Args:
        condition: Condition that must be true.
        code: Registered Data error code.
        request_id: Trace identifier.
        operation: Safe operation label.

    Raises:
        DataError: When ``condition`` is false.
    """
    logger.debug("Checking a required %s condition", operation)
    if not condition:
        raise _error(code, request_id, operation)


def _manifest_payload(
    manifest_id: str,
    entries: tuple[BackupEntry, ...],
    created_at: datetime,
    request_id: str,
) -> bytes:
    """Return canonical bytes covered by the manifest hash.

    Args:
        manifest_id: Stable backup identity.
        entries: Ordered per-file integrity evidence.
        created_at: UTC creation time.
        request_id: Trace identifier recorded by the manifest.

    Returns:
        Deterministically encoded JSON bytes.
    """
    logger.debug("Encoding canonical backup manifest hash input")
    payload = {
        "created_at": created_at.isoformat(),
        "entries": [
            {
                "byte_count": entry.byte_count,
                "content_hash": entry.content_hash,
                "normalization_version": entry.normalization_version,
                "relative_path": entry.relative_path.as_posix(),
                "schema_version": entry.schema_version,
            }
            for entry in entries
        ],
        "manifest_id": manifest_id,
        "request_id": request_id,
    }
    return json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _manifest_hash(
    manifest_id: str,
    entries: tuple[BackupEntry, ...],
    created_at: datetime,
    request_id: str,
) -> str:
    """Return the SHA256 identity of canonical manifest evidence.

    Args:
        manifest_id: Stable backup identity.
        entries: Ordered per-file evidence.
        created_at: UTC creation time.
        request_id: Trace identifier.

    Returns:
        Lowercase hexadecimal SHA256 hash.
    """
    logger.debug("Hashing canonical backup manifest evidence")
    return hashlib.sha256(
        _manifest_payload(manifest_id, entries, created_at, request_id)
    ).hexdigest()


def _commit_directory(staging: Path, destination: Path) -> None:
    """Atomically rename a staged backup with bounded sharing-violation retries.

    Windows file scanners can briefly retain a handle after the manifest is closed.
    Retrying the same atomic rename is safe because neither path is modified between
    attempts and the destination must not yet exist.

    Args:
        staging: Fully verified staged backup directory.
        destination: Final immutable backup directory.

    Raises:
        PermissionError: If every bounded atomic rename attempt is refused.
    """
    logger.debug("Atomically committing staged DATA backup directory")
    for attempt in range(_WINDOWS_RENAME_ATTEMPTS):
        try:
            staging.replace(destination)
            return
        except PermissionError:
            if attempt + 1 == _WINDOWS_RENAME_ATTEMPTS:
                raise
            time.sleep(_WINDOWS_RENAME_DELAY_SECONDS)


def _target_files(
    targets: Sequence[BackupTarget],
    data_root: Path,
    request_id: str,
) -> tuple[tuple[Path, BackupTarget], ...]:
    """Resolve declared targets into unique ordered approved files.

    Args:
        targets: Caller-declared files or directories.
        data_root: Resolved configured Data root.
        request_id: Trace identifier.

    Returns:
        Ordered absolute files paired with their governing declarations.

    Raises:
        DataError: If a target is missing, empty, duplicated, or unapproved.
    """
    logger.info("Resolving %d declared backup targets", len(targets))
    if not targets:
        raise _error("DB_WRITE_FAILED", request_id, "create_backup")
    resolved: dict[Path, BackupTarget] = {}
    for target in targets:
        path = resolve_approved_storage_path(target.relative_path, request_id)
        if not path.exists():
            raise _error("DB_WRITE_FAILED", request_id, "create_backup")
        files = (
            (path,)
            if path.is_file()
            else tuple(
                candidate
                for candidate in sorted(path.rglob("*"))
                if candidate.is_file()
            )
        )
        if not files:
            raise _error("DB_WRITE_FAILED", request_id, "create_backup")
        for file_path in files:
            relative = file_path.relative_to(data_root)
            admitted = resolve_approved_storage_path(relative, request_id)
            if admitted in resolved:
                raise _error("DB_WRITE_FAILED", request_id, "create_backup")
            resolved[admitted] = target
    return tuple(sorted(resolved.items(), key=lambda item: str(item[0])))


def _audit(
    action: str,
    request_id: str,
    timestamp: datetime,
    payload: dict[str, str],
) -> None:
    """Persist one bounded backup or retention audit event.

    Args:
        action: Stable audit action identifier.
        request_id: Trace identifier.
        timestamp: Explicit UTC event time.
        payload: Secret-safe string evidence.

    Raises:
        DataError: If durable audit persistence fails.
    """
    logger.info("Persisting %s audit evidence", action)
    persist_audit_event(
        AuditEvent(
            contract_version="v1",
            schema_id="utils.audit_event.v1",
            event_id=generate_id("evt"),
            timestamp=timestamp,
            domain="data",
            action=action,
            request_id=request_id,
            correlation_id=generate_id("cor"),
            payload=payload,
        )
    )


def create_backup(targets: Sequence[BackupTarget]) -> BackupManifest:
    """Snapshot approved files into one immutable hashed backup manifest.

    Args:
        targets: Declared approved-root-relative files or directories with explicit
            schema and normalization versions.

    Returns:
        Immutable manifest carrying measured evidence for every file.

    Raises:
        DataError: If a target is unapproved, unavailable, concurrently locked, or
            cannot be copied, verified, committed, or audited.
    """
    request_id = generate_id("req")
    logger.info("Creating immutable DATA backup %s", request_id)
    data_root = resolve_data_root(request_id)
    files = _target_files(targets, data_root, request_id)
    created_at = utc_now()
    manifest_id = derive_stable_id(
        "id",
        f"{request_id}:{created_at.isoformat()}",
    )
    backup_root = resolve_approved_storage_path(_BACKUP_ROOT, request_id)
    final_directory = backup_root / manifest_id
    staging_directory = backup_root / f"{manifest_id}.tmp"
    entries = tuple(
        BackupEntry(
            relative_path=file_path.relative_to(data_root),
            content_hash=compute_file_hash(file_path),
            byte_count=file_path.stat().st_size,
            schema_version=target.schema_version,
            normalization_version=target.normalization_version,
        )
        for file_path, target in files
    )
    manifest = BackupManifest(
        manifest_id=manifest_id,
        entries=entries,
        manifest_hash=_manifest_hash(manifest_id, entries, created_at, request_id),
        created_at=created_at,
        request_id=request_id,
    )

    try:
        with acquire_write_lock(final_directory, request_id):
            if final_directory.exists() or staging_directory.exists():
                raise _error("DB_WRITE_FAILED", request_id, "create_backup")
            staging_directory.mkdir(parents=True)
            expected_hashes = {
                entry.relative_path: entry.content_hash for entry in entries
            }
            for file_path, _target in files:
                relative = file_path.relative_to(data_root)
                destination = staging_directory / "payload" / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, destination)
                if compute_file_hash(destination) != expected_hashes[relative]:
                    raise _error("DB_WRITE_FAILED", request_id, "create_backup")
            (staging_directory / _MANIFEST_NAME).write_text(
                manifest.model_dump_json(indent=2),
                encoding="utf-8",
            )
            _commit_directory(staging_directory, final_directory)
            try:
                _audit(
                    "create_data_backup",
                    request_id,
                    created_at,
                    {
                        "manifest_id": manifest_id,
                        "target_count": str(len(entries)),
                    },
                )
            except Exception:
                shutil.rmtree(final_directory, ignore_errors=True)
                raise
    except DataError:
        if staging_directory.exists():
            shutil.rmtree(staging_directory, ignore_errors=True)
        raise
    except OSError as error:
        if staging_directory.exists():
            shutil.rmtree(staging_directory, ignore_errors=True)
        logger.error("DATA backup creation failed")
        raise _error("DB_WRITE_FAILED", request_id, "create_backup") from error
    return manifest


def _load_manifest(manifest_id: str, request_id: str) -> tuple[BackupManifest, Path]:
    """Load and verify one named immutable backup manifest.

    Args:
        manifest_id: Exact backup identity.
        request_id: Restore trace identifier.

    Returns:
        Verified manifest and its backup directory.

    Raises:
        DataError: If the identity is unsafe, missing, malformed, or corrupted.
    """
    logger.info("Loading backup manifest %s", manifest_id)
    if (
        not manifest_id
        or manifest_id != manifest_id.strip()
        or Path(manifest_id).name != manifest_id
    ):
        raise _error("DATA_NOT_FOUND", request_id, "restore_backup")
    directory = resolve_approved_storage_path(
        _BACKUP_ROOT / manifest_id,
        request_id,
    )
    path = directory / _MANIFEST_NAME
    if not path.is_file():
        raise _error("DATA_NOT_FOUND", request_id, "restore_backup")
    try:
        manifest = BackupManifest.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as error:
        raise _error("FILE_CORRUPTED", request_id, "restore_backup") from error
    expected_hash = _manifest_hash(
        manifest.manifest_id,
        manifest.entries,
        manifest.created_at,
        manifest.request_id,
    )
    if manifest.manifest_id != manifest_id or manifest.manifest_hash != expected_hash:
        raise _error("FILE_CORRUPTED", request_id, "restore_backup")
    return manifest, directory


def _prepare_restore(
    manifest: BackupManifest,
    directory: Path,
    request_id: str,
) -> list[_PreparedRestore]:
    """Resolve and verify every source and destination before restore writes.

    Args:
        manifest: Verified backup manifest.
        directory: Directory containing the backup payload.
        request_id: Restore trace identifier.

    Returns:
        Prepared source-evidence and target staging paths.

    Raises:
        DataError: If any payload is missing, corrupted, or unapproved.
    """
    logger.info("Preparing %d backup entries for restore", len(manifest.entries))
    prepared: list[_PreparedRestore] = []
    for entry in manifest.entries:
        source = directory / "payload" / entry.relative_path
        target = resolve_approved_storage_path(entry.relative_path, request_id)
        stage = target.with_name(f"{target.name}.{request_id}.restore.tmp")
        rollback = target.with_name(f"{target.name}.{request_id}.restore.rollback")
        valid = source.is_file() and compute_file_hash(source) == entry.content_hash
        _require(valid, "FILE_CORRUPTED", request_id, "restore_backup")
        prepared.append((entry, target, stage, rollback))
    return prepared


def _stage_restore(
    prepared: Sequence[_PreparedRestore],
    directory: Path,
    request_id: str,
) -> None:
    """Copy and verify all restore payloads into target-local staging files.

    Args:
        prepared: Prepared restore paths and integrity evidence.
        directory: Backup directory containing immutable payloads.
        request_id: Restore trace identifier.

    Raises:
        DataError: If a staged copy does not match its manifest hash.
        OSError: If a staging file cannot be written.
    """
    logger.info("Staging %d verified restore payloads", len(prepared))
    for entry, target, stage, _rollback in prepared:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(directory / "payload" / entry.relative_path, stage)
        _require(
            compute_file_hash(stage) == entry.content_hash,
            "FILE_CORRUPTED",
            request_id,
            "restore_backup",
        )


def _rollback_restore(
    committed: Sequence[tuple[Path, Path, bool]],
    prepared: Sequence[_PreparedRestore],
) -> None:
    """Restore pre-operation targets and clean every temporary restore file.

    Args:
        committed: Target, rollback path, and prior-existence evidence.
        prepared: All prepared staging and rollback paths.
    """
    logger.warning("Rolling back %d committed restore targets", len(committed))
    for target, rollback, existed in reversed(committed):
        if target.exists():
            target.unlink()
        if existed and rollback.exists():
            rollback.replace(target)
    for _entry, _target, stage, rollback in prepared:
        if stage.exists():
            stage.unlink()
        if rollback.exists():
            rollback.unlink()


def _commit_restore(
    manifest_id: str,
    prepared: Sequence[_PreparedRestore],
    directory: Path,
    request_id: str,
    restored_at: datetime,
) -> None:
    """Lock, stage, atomically swap, audit, and finalize a restore.

    Args:
        manifest_id: Backup identity being restored.
        prepared: Verified restore path plan.
        directory: Backup directory containing payloads.
        request_id: Restore trace identifier.
        restored_at: Explicit UTC restore evidence time.

    Raises:
        DataError: If locking, verification, commit, or audit fails.
    """
    logger.info("Committing atomic restore for %s", manifest_id)
    committed: list[tuple[Path, Path, bool]] = []
    try:
        with ExitStack() as stack:
            ordered = sorted(prepared, key=lambda item: str(item[1]))
            for _entry, target, _stage, _rollback in ordered:
                stack.enter_context(acquire_write_lock(target, request_id))
            _stage_restore(prepared, directory, request_id)
            for _entry, target, stage, rollback in prepared:
                _require(
                    not rollback.exists(),
                    "DB_WRITE_FAILED",
                    request_id,
                    "restore_backup",
                )
                existed = target.exists()
                if existed:
                    target.replace(rollback)
                stage.replace(target)
                committed.append((target, rollback, existed))
            _audit(
                "restore_data_backup",
                request_id,
                restored_at,
                {
                    "manifest_id": manifest_id,
                    "restored_count": str(len(prepared)),
                },
            )
            for _target, rollback, existed in committed:
                if existed:
                    rollback.unlink()
    except Exception as error:
        logger.error("DATA backup restore failed; rolling back target files")
        _rollback_restore(committed, prepared)
        if isinstance(error, DataError):
            raise
        raise _error("DB_WRITE_FAILED", request_id, "restore_backup") from error


def restore_from_backup(manifest_id: str) -> RestoreReport:
    """Restore every file in a named manifest after complete hash verification.

    Args:
        manifest_id: Exact backup identity returned by :func:`create_backup`.

    Returns:
        Truthful report of restored target paths.

    Raises:
        DataError: If the manifest is absent or corrupted, a target is locked, or
            the full restore cannot be committed and audited atomically.
    """
    request_id = generate_id("req")
    logger.info("Restoring immutable DATA backup %s", manifest_id)
    manifest, directory = _load_manifest(manifest_id, request_id)
    prepared = _prepare_restore(manifest, directory, request_id)
    restored_at = utc_now()
    _commit_restore(manifest_id, prepared, directory, request_id, restored_at)

    restored_paths = tuple(entry.relative_path for entry in manifest.entries)
    return RestoreReport(
        manifest_id=manifest_id,
        restored_paths=restored_paths,
        restored_count=len(restored_paths),
        restored_at=restored_at,
        request_id=request_id,
    )


def _license_retention_days(path: Path, request_id: str) -> int | None:
    """Return a companion manifest's canonical retention limit when declared.

    Args:
        path: Raw payload whose companion manifest may carry licence metadata.
        request_id: Retention trace identifier.

    Returns:
        Declared non-negative retention days, or ``None`` when unrestricted.

    Raises:
        DataError: If present licence metadata is malformed.
    """
    logger.debug("Reading canonical licence retention evidence for %s", path.name)
    manifest_path = path.with_suffix(path.suffix + ".manifest.json")
    if not manifest_path.exists():
        return None
    try:
        manifest = StorageManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        value = manifest.license_metadata.get("retention_days")
        if value is None:
            return None
        days = int(value)
        _require(days >= 0, "LICENSE_RESTRICTION", request_id, "retention")
        return days
    except DataError:
        raise
    except (OSError, ValidationError, ValueError) as error:
        raise _error("LICENSE_RESTRICTION", request_id, "retention") from error


def _retention_root(dataset: str, max_age_days: int, request_id: str) -> Path:
    """Validate one retention request and return its approved raw root.

    Args:
        dataset: Relative dataset identity below ``data/raw``.
        max_age_days: Positive maximum age.
        request_id: Retention trace identifier.

    Returns:
        Existing approved dataset path.

    Raises:
        DataError: If the request or resolved path is unsafe.
    """
    logger.debug("Validating raw DATA retention scope")
    dataset_path = Path(dataset)
    valid = (
        bool(dataset)
        and dataset == dataset.strip()
        and not dataset_path.is_absolute()
        and ".." not in dataset_path.parts
        and max_age_days > 0
    )
    _require(valid, "PERMISSION_DENIED", request_id, "retention")
    root = resolve_approved_storage_path(Path("data/raw") / dataset_path, request_id)
    _require(root.exists(), "PERMISSION_DENIED", request_id, "retention")
    return root


def _expired_payloads(
    root: Path,
    max_age_days: int,
    request_id: str,
) -> tuple[Path, ...]:
    """Return raw payloads older than policy without weakening licence terms.

    Args:
        root: Approved raw dataset file or directory.
        max_age_days: Positive requested maximum age.
        request_id: Retention trace identifier.

    Returns:
        Ordered expired raw payload files.

    Raises:
        DataError: If canonical licence terms would be weakened.
    """
    logger.info("Inspecting raw DATA payload ages")
    candidates = (
        (root,)
        if root.is_file()
        else tuple(
            path
            for path in sorted(root.rglob("*"))
            if path.is_file() and not path.name.endswith(".manifest.json")
        )
    )
    cutoff = utc_now() - timedelta(days=max_age_days)
    expired: list[Path] = []
    for path in candidates:
        licence_days = _license_retention_days(path, request_id)
        permitted = licence_days is None or max_age_days <= licence_days
        _require(permitted, "LICENSE_RESTRICTION", request_id, "retention")
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        if modified_at < cutoff:
            expired.append(path)
    return tuple(expired)


def _rollback_retention(moved: Sequence[tuple[Path, Path]], quarantine: Path) -> None:
    """Restore quarantined payloads after a failed retention commit.

    Args:
        moved: Quarantine-to-original path pairs.
        quarantine: Operation-specific quarantine directory.
    """
    logger.warning("Rolling back %d quarantined retention files", len(moved))
    for source, destination in reversed(moved):
        if source.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.replace(destination)
    if quarantine.exists():
        shutil.rmtree(quarantine, ignore_errors=True)


def _purge_expired(
    root: Path,
    expired: Sequence[Path],
    dataset: str,
    request_id: str,
    observed_at: datetime,
) -> None:
    """Quarantine, audit, and delete one bounded expired payload set.

    Args:
        root: Approved raw dataset scope.
        expired: Ordered expired payload files.
        dataset: Safe dataset identifier for audit evidence.
        request_id: Retention trace identifier.
        observed_at: Explicit UTC operation time.

    Raises:
        DataError: If the mutation or audit cannot complete safely.
    """
    logger.info("Purging %d expired raw DATA payloads", len(expired))
    quarantine = root.parent / f"{root.name}.{request_id}.retention"
    moved: list[tuple[Path, Path]] = []
    try:
        with acquire_write_lock(root, request_id):
            _require(
                not quarantine.exists(),
                "DB_WRITE_FAILED",
                request_id,
                "retention",
            )
            quarantine.mkdir(parents=True)
            for path in expired:
                payload_destination = quarantine / path.relative_to(root.parent)
                payload_destination.parent.mkdir(parents=True, exist_ok=True)
                path.replace(payload_destination)
                moved.append((payload_destination, path))
                manifest_path = path.with_suffix(path.suffix + ".manifest.json")
                if manifest_path.exists():
                    manifest_destination = payload_destination.with_suffix(
                        payload_destination.suffix + ".manifest.json"
                    )
                    manifest_path.replace(manifest_destination)
                    moved.append((manifest_destination, manifest_path))
            _audit(
                "purge_data_retention",
                request_id,
                observed_at,
                {"dataset": dataset, "purged_count": str(len(expired))},
            )
            shutil.rmtree(quarantine)
    except Exception as error:
        logger.error("DATA retention purge failed; restoring quarantined files")
        _rollback_retention(moved, quarantine)
        if isinstance(error, DataError):
            raise
        raise _error("DB_WRITE_FAILED", request_id, "retention") from error


def enforce_retention_policy(
    dataset: str,
    max_age_days: int,
    *,
    dry_run: bool = True,
) -> int:
    """Count or purge expired raw payloads without weakening licence retention.

    Args:
        dataset: Relative identity below the canonical ``data/raw`` root.
        max_age_days: Positive maximum payload age in days.
        dry_run: When true, report the candidate count without mutation.

    Returns:
        Number of raw payloads selected by the policy.

    Raises:
        DataError: If the dataset path is unsafe/unapproved, licence terms would be
            weakened, or the purge cannot commit and audit safely.
    """
    request_id = generate_id("req")
    logger.info("Enforcing raw DATA retention for dataset %s", dataset)
    root = _retention_root(dataset, max_age_days, request_id)
    expired = _expired_payloads(root, max_age_days, request_id)

    observed_at = utc_now()
    if dry_run:
        _audit(
            "inspect_data_retention",
            request_id,
            observed_at,
            {"dataset": dataset, "candidate_count": str(len(expired))},
        )
        return len(expired)

    _purge_expired(root, expired, dataset, request_id, observed_at)
    return len(expired)


__all__ = [
    "create_backup",
    "enforce_retention_policy",
    "restore_from_backup",
]
