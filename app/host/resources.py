"""Resource custody, safe archive access, and bounded artifact services.

Description:
    Provides centralized artifact custody, immutable content-addressed storage,
    path containment validation, safe archive inspection and extraction, bounded
    LRU/TTL caching, remote artifact acquisition via httpx, and FastAPI REST
    transport endpoints for the HaruQuantAI platform host. In quantitative trading
    systems, strategy packages, backtest reports, historical tick revisions, custom
    indicators, and neural model weights must be stored immutably and extracted
    safely. This module prevents Zip-Slip directory traversal vectors, compression
    bombs (decompression denial-of-service), uncontained symbolic link escapes, and
    memory exhaustion from unbounded caching or runaway downloads.

    Externally, it serves four critical operational workflows: (1) host bootstrap
    or lifespan composition mounts the resources router via
    `create_resources_router()`; (2) domain workspaces and plugins interact
    through scoped `ResourceAccess` capability facades to stage, publish, and
    retrieve artifacts without escaping tenant boundaries; (3) remote archive
    sources are acquired through bounded `acquire_remote()` streaming pipelines
    with content validation and automatic rollback; and (4) routine host
    maintenance purges orphaned staging files via `cleanup_staging()` to enforce
    bounded disk utilization.

    Internally, `validate_contained_path()` canonicalizes filesystem paths and
    resolves junctions/symlinks against sandbox boundaries; `inspect_archive()`
    inspects ZIP and TAR archives without unpacking, validating entry counts,
    uncompressed byte totals, and compression ratios against strict `ArchiveLimits`;
    `safe_extract_archive()` performs transaction-safe extraction with automatic
    directory rollback upon failure; `ResourceCache` enforces thread-safe
    byte-bounded LRU eviction; and `ResourceManager` coordinates
    staging-to-publication transitions into immutable SHA-256 content-addressed
    directories (`store/<hash[:2]>/<hash[2:]>`).

Purpose:
    FEAT-HOST-RESOURCES: Resource Services, Safe Archives, and Bounded Artifact Access.
    Provides immutable artifact custody, content-addressed storage, path containment,
    Zip-Slip and expansion bomb protection, bounded caching, and REST management.

Key Capabilities:
    - FR-HOST-RESOURCES-STAGING-PUBLICATION: Staging to Content-Addressed Publication
      Associated: `[ResourceManager.stage_file()]`, `[ResourceManager.stage_bytes()]`,
      `[ResourceManager.publish()]`
      Logging: Emits INFO log detailing resource ID, scope, SHA-256 digest, byte
      size, and immutable store path upon successful staging and publication.
    - FR-HOST-RESOURCES-CONTAINMENT-SECURITY: Strict Sandbox Path Containment
      Associated: `[validate_contained_path()]`
      Logging: Emits DEBUG log on safe path resolution; WARNING/ERROR log on
      traversal attempts, drive escapes, or forbidden symlinks.
    - FR-HOST-RESOURCES-ARCHIVE-INSPECTION: Pre-Extraction Archive Safety Inspection
      Associated: `[inspect_archive()]`
      Logging: Emits INFO log summarizing entry counts, compression ratio, and
      safety status; WARNING log on detected Zip-Slip entries or limit violations.
    - FR-HOST-RESOURCES-ARCHIVE-EXTRACTION: Contained Archive Extraction
      Associated: `[safe_extract_archive()]`
      Logging: Emits INFO log with destination path and extracted file count; ERROR
      log on extraction abort with automatic rollback of partially created files.
    - FR-HOST-RESOURCES-BOUNDED-CACHE: Thread-Safe Byte-Bounded LRU Artifact Cache
      Associated: `[ResourceCache.get()]`, `[ResourceCache.put()]`,
      `[ResourceCache.invalidate()]`
      Logging: Emits DEBUG log on cache hit/miss; INFO log on LRU eviction events
      recording freed bytes and eviction counts.
    - FR-HOST-RESOURCES-HTTPX-ACQUISITION: Bounded Remote Artifact Acquisition
      Associated: `[acquire_remote()]`
      Logging: Emits INFO log on remote fetch start/success; ERROR log on HTTP
      failures, timeout expiration, or downloaded byte limit violations.
    - FR-HOST-RESOURCES-ORPHAN-CLEANUP: Automated Staging Garbage Collection
      Associated: `[ResourceManager.cleanup_staging()]`
      Logging: Emits INFO log recording the number of orphaned staging
      directories purged and freed disk capacity.
    - FR-HOST-RESOURCES-REST-PROJECTION: FastAPI REST Endpoints Projection
      Associated: `[create_resources_router()]`
      Logging: Emits DEBUG log on router mounting; INFO log on stage, acquire,
      publish, inspect, extract, and cleanup API invocations.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.resources import (
        ArchiveLimits,
        ResourceManager,
        ResourceScope,
        inspect_archive,
        safe_extract_archive,
    )

    manager = ResourceManager(root_dir=Path("data/resources"))

    # Stage raw bytes
    meta = manager.stage_bytes(
        b"strategy binary payload",
        name="strategy_v1.bin",
        scope=ResourceScope.WORKSPACE,
    )

    # Publish staged artifact into immutable store
    published = manager.publish(meta.resource_id)
    assert published.status == "published"

    # Inspect and safely extract an archive
    inspection = inspect_archive(Path("package.zip"))
    if inspection.is_safe:
        files = safe_extract_archive(Path("package.zip"), Path("sandbox/"))
    ```

CLI Usage:
    ```bash
    # Inspect an archive for safety violations and compression ratio
    uv run python -m app.host.resources --inspect path/to/archive.zip

    # Clean up orphaned staging files older than 3600 seconds
    uv run python -m app.host.resources --cleanup-staging --root data/resources
    ```
"""

from __future__ import annotations

import argparse
import hashlib
import mimetypes
import shutil
import sys
import tarfile
import threading
import time
import urllib.parse
import uuid
import zipfile
from collections import OrderedDict
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any

import httpx
from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.host.logging import get_logger
from app.host.response import StandardResponse

logger = get_logger(__name__)

# Canonical envelope alias matching transport conventions
ApiResponse = StandardResponse

__all__ = [
    "AcquireRemoteRequest",
    "AcquisitionError",
    "ApiResponse",
    "ArchiveBombError",
    "ArchiveEntryInfo",
    "ArchiveFormat",
    "ArchiveInspection",
    "ArchiveLimits",
    "CacheStats",
    "CorruptResourceError",
    "ExtractArchiveRequest",
    "InspectArchiveRequest",
    "PublishRequest",
    "ResourceAccess",
    "ResourceCache",
    "ResourceConflictError",
    "ResourceError",
    "ResourceManager",
    "ResourceMetadata",
    "ResourceNotFoundError",
    "ResourceRouterService",
    "ResourceScope",
    "ResourceSecurityError",
    "ResourceStatus",
    "StagingRequest",
    "acquire_remote",
    "create_resources_router",
    "inspect_archive",
    "main",
    "safe_extract_archive",
    "validate_contained_path",
]

# Internal constants for safety verification and limits
_ZIP_SYMLINK_MASK: int = 0o120000
_ZIP_SYMLINK_FLAG: int = 0o170000
_TAR_MAGIC_OFFSET: int = 257
_TAR_MAGIC_END: int = 262
_TAR_USTAR_MAGIC: bytes = b"ustar"
_HTTP_BAD_REQUEST: int = 400
_CHUNK_SIZE: int = 65536
_ONE_MIB: int = 1024 * 1024


# ============================================================================
# Enums and Domain Models
# ============================================================================


class ResourceScope(StrEnum):
    """Categorical authorization scope for stored resources."""

    WORKSPACE = "workspace"
    PLUGIN = "plugin"
    SYSTEM = "system"
    TRANSIENT = "transient"


class ResourceStatus(StrEnum):
    """Lifecycle progression state for stored resources."""

    STAGED = "staged"
    PUBLISHED = "published"
    EXPIRED = "expired"
    TOMBSTONED = "tombstoned"


class ArchiveFormat(StrEnum):
    """Supported archive encapsulation formats."""

    ZIP = "zip"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    TAR_BZ2 = "tar.bz2"
    TAR_XZ = "tar.xz"


class ResourceMetadata(BaseModel):
    """Immutable metadata record describing an owned resource."""

    resource_id: str = Field(description="Unique resource identifier.")
    scope: ResourceScope = Field(description="Ownership authorization scope.")
    name: str = Field(description="Original or assigned file name.")
    content_hash: str = Field(description="SHA-256 hexadecimal content digest.")
    size_bytes: int = Field(ge=0, description="Exact file size in bytes.")
    mime_type: str = Field(description="Detected or declared MIME content type.")
    status: ResourceStatus = Field(description="Current lifecycle status.")
    created_at_utc: datetime = Field(description="UTC timestamp of creation.")
    published_at_utc: datetime | None = Field(
        default=None, description="UTC timestamp of publication."
    )
    expires_at_utc: datetime | None = Field(
        default=None, description="Optional UTC timestamp of expiration."
    )
    tags: dict[str, str] = Field(
        default_factory=dict, description="Arbitrary indexing tags."
    )
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Domain-specific structured attributes."
    )


class ArchiveEntryInfo(BaseModel):
    """Inspection record for an individual archive member."""

    path: str = Field(description="Normalized relative path inside archive.")
    size_bytes: int = Field(ge=0, description="Uncompressed size in bytes.")
    compressed_size_bytes: int = Field(ge=0, description="Compressed size in bytes.")
    is_directory: bool = Field(description="Whether entry is a directory.")
    is_symlink: bool = Field(description="Whether entry is a symbolic link.")
    is_encrypted: bool = Field(description="Whether entry is password-protected.")


class ArchiveLimits(BaseModel):
    """Safety boundaries and thresholds for archive inspection and extraction."""

    max_entries: int = Field(
        default=10_000, gt=0, description="Maximum allowed member entries."
    )
    max_uncompressed_bytes: int = Field(
        default=500 * 1024 * 1024,
        gt=0,
        description="Maximum total uncompressed byte ceiling (default 500 MiB).",
    )
    max_expansion_ratio: float = Field(
        default=100.0,
        gt=0.0,
        description="Maximum uncompressed:compressed ratio before flagging a bomb.",
    )
    allow_symlinks: bool = Field(
        default=False, description="Whether symbolic links are permitted."
    )


class ArchiveInspection(BaseModel):
    """Comprehensive safety and structural report of an inspected archive."""

    archive_format: ArchiveFormat = Field(description="Detected archive format.")
    entry_count: int = Field(ge=0, description="Total member count.")
    uncompressed_bytes: int = Field(ge=0, description="Total uncompressed bytes.")
    compressed_bytes: int = Field(ge=0, description="Total compressed bytes.")
    expansion_ratio: float = Field(
        ge=0.0, description="Calculated expansion ratio (uncompressed/compressed)."
    )
    is_safe: bool = Field(
        description="True if archive complies with all containment and bomb limits."
    )
    violations: list[str] = Field(
        default_factory=list, description="List of detected safety violations."
    )
    entries: list[ArchiveEntryInfo] = Field(
        default_factory=list, description="Inspected archive member details."
    )


class CacheStats(BaseModel):
    """Telemetry metrics snapshot for the bounded resource cache."""

    max_bytes: int = Field(ge=0, description="Configured byte capacity.")
    used_bytes: int = Field(ge=0, description="Currently utilized byte capacity.")
    entry_count: int = Field(ge=0, description="Current number of cached items.")
    hit_count: int = Field(ge=0, description="Total cache lookups satisfied.")
    miss_count: int = Field(ge=0, description="Total cache lookups missed.")
    eviction_count: int = Field(ge=0, description="Total items evicted due to bounds.")


class StagingRequest(BaseModel):
    """Request payload for staging a resource via JSON."""

    scope: ResourceScope = Field(default=ResourceScope.WORKSPACE)
    name: str = Field(min_length=1)
    tags: dict[str, str] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    expires_in_seconds: int | None = Field(default=None, gt=0)


class AcquireRemoteRequest(BaseModel):
    """Request payload for fetching and staging a remote artifact via HTTP."""

    url: str = Field(description="Remote HTTP/HTTPS URL.")
    scope: ResourceScope = Field(default=ResourceScope.WORKSPACE)
    name: str | None = Field(default=None, description="Optional custom file name.")
    max_bytes: int = Field(
        default=100 * 1024 * 1024,
        gt=0,
        description="Maximum permitted download size in bytes.",
    )
    timeout_seconds: float = Field(
        default=30.0, gt=0.0, description="Request timeout in seconds."
    )
    tags: dict[str, str] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)


class PublishRequest(BaseModel):
    """Request payload for publishing a staged resource."""

    expected_hash: str | None = Field(
        default=None, description="Optional SHA-256 digest to verify before publish."
    )
    tags: dict[str, str] | None = Field(
        default=None, description="Optional additional tags to attach."
    )


class InspectArchiveRequest(BaseModel):
    """Request payload for inspecting an archive resource."""

    resource_id: str = Field(min_length=1)
    limits: ArchiveLimits | None = Field(default=None)


class ExtractArchiveRequest(BaseModel):
    """Request payload for extracting an archive resource into a contained target."""

    resource_id: str = Field(min_length=1)
    target_subpath: str = Field(
        default="extracted", description="Contained subpath for extraction."
    )
    limits: ArchiveLimits | None = Field(default=None)


# ============================================================================
# Exceptions
# ============================================================================


class ResourceError(Exception):
    """Base exception for all resource management failures."""


class ResourceNotFoundError(ResourceError):
    """Raised when a requested resource identifier does not exist."""


class ResourceSecurityError(ResourceError):
    """Raised when a path traversal, symlink escape, or security violation occurs."""


class ArchiveBombError(ResourceSecurityError):
    """Raised when an archive exceeds expansion ratio, size, or entry count limits."""


class CorruptResourceError(ResourceError):
    """Raised when a resource's content hash does not match expected digest."""


class ResourceConflictError(ResourceError):
    """Raised when an invalid lifecycle transition is attempted on a resource."""


class AcquisitionError(ResourceError):
    """Raised when acquiring a remote artifact via HTTP fails or violates bounds."""


# ============================================================================
# Containment and Path Validation
# ============================================================================


def validate_contained_path(
    base_dir: Path,
    candidate_path: Path | str,
    *,
    allow_symlinks: bool = False,
) -> Path:
    """Validate that candidate_path resolves strictly inside base_dir sandbox.

    Args:
        base_dir: Sandbox base directory. Must exist or be resolvable.
        candidate_path: Target relative or absolute subpath to evaluate.
        allow_symlinks: Whether symbolic links pointing within base_dir are allowed.

    Returns:
        Canonical resolved Path within base_dir.

    Raises:
        ResourceSecurityError: If candidate_path escapes base_dir.
    """
    candidate_str = str(candidate_path).strip()
    if not candidate_str:
        raise ResourceSecurityError("Candidate path cannot be empty")

    raw_path = Path(candidate_str)
    parts = raw_path.parts
    if ".." in parts:
        logger.warning(
            "Path traversal rejected: contains parent directory reference",
            extra={"candidate": candidate_str, "base_dir": str(base_dir)},
        )
        msg = (
            f"Path traversal rejected: '{candidate_str}' "
            "contains parent references ('..')"
        )
        raise ResourceSecurityError(msg)

    resolved_base = base_dir.resolve()
    resolved_candidate = (
        raw_path.resolve()
        if raw_path.is_absolute()
        else (resolved_base / raw_path).resolve()
    )

    try:
        resolved_candidate.relative_to(resolved_base)
    except ValueError as exc:
        logger.warning(
            "Sandbox escape rejected: resolved path outside base directory",
            extra={
                "candidate": candidate_str,
                "resolved": str(resolved_candidate),
                "base_dir": str(resolved_base),
            },
        )
        raise ResourceSecurityError(
            f"Path escape rejected: '{candidate_str}' resolves outside base sandbox"
        ) from exc

    if (
        resolved_candidate.drive
        and resolved_base.drive
        and resolved_candidate.drive.lower() != resolved_base.drive.lower()
    ):
        raise ResourceSecurityError(
            f"Drive escape rejected: '{candidate_str}' targets foreign drive"
        )

    if not allow_symlinks:
        current = resolved_candidate
        while current not in (resolved_base, current.parent):
            if current.is_symlink():
                logger.warning(
                    "Symbolic link rejected: symlinks forbidden",
                    extra={"path": str(current)},
                )
                raise ResourceSecurityError(
                    f"Symbolic link forbidden in sandbox path: '{current}'"
                )
            current = current.parent

    logger.debug(
        "Path containment verified",
        extra={
            "resolved": str(resolved_candidate),
            "base": str(resolved_base),
            "fr_id": "FR-HOST-RESOURCES-CONTAINMENT-SECURITY",
        },
    )
    return resolved_candidate


# ============================================================================
# Safe Archive Inspection & Extraction
# ============================================================================


def _detect_format_by_header(header: bytes) -> ArchiveFormat | None:
    """Inspect header magic bytes for known archive signatures."""
    if header.startswith((b"PK\x03\x04", b"PK\x05\x06")):
        return ArchiveFormat.ZIP
    if header.startswith(b"\x1f\x8b"):
        return ArchiveFormat.TAR_GZ
    if header.startswith(b"BZh"):
        return ArchiveFormat.TAR_BZ2
    if header.startswith(b"\xfd7zXZ\x00"):
        return ArchiveFormat.TAR_XZ
    if (
        len(header) >= _TAR_MAGIC_END
        and header[_TAR_MAGIC_OFFSET:_TAR_MAGIC_END] == _TAR_USTAR_MAGIC
    ):
        return ArchiveFormat.TAR
    return None


def _detect_format_by_extension(filename: str) -> ArchiveFormat | None:
    """Inspect file name extension for known archive patterns."""
    lower_name = filename.lower()
    if lower_name.endswith(".zip"):
        return ArchiveFormat.ZIP
    if lower_name.endswith((".tar.gz", ".tgz")):
        return ArchiveFormat.TAR_GZ
    if lower_name.endswith((".tar.bz2", ".tbz2")):
        return ArchiveFormat.TAR_BZ2
    if lower_name.endswith((".tar.xz", ".txz")):
        return ArchiveFormat.TAR_XZ
    if lower_name.endswith(".tar"):
        return ArchiveFormat.TAR
    return None


def _detect_archive_format(archive_path: Path) -> ArchiveFormat:
    """Detect archive format from header magic bytes or file extension."""
    if not archive_path.is_file():
        raise ResourceNotFoundError(f"Archive file not found: {archive_path}")

    with archive_path.open("rb") as f:
        header = f.read(512)

    fmt_header = _detect_format_by_header(header)
    if fmt_header is not None:
        return fmt_header

    fmt_ext = _detect_format_by_extension(archive_path.name)
    if fmt_ext is not None:
        return fmt_ext

    raise ResourceSecurityError(
        f"Unsupported or unrecognized archive format for file: {archive_path.name}"
    )


def _inspect_zip(
    archive_path: Path,
    limits: ArchiveLimits,
) -> tuple[int, int, int, list[str], list[ArchiveEntryInfo]]:
    """Inspect ZIP archive members for safety and size bounds."""
    violations: list[str] = []
    entries: list[ArchiveEntryInfo] = []
    uncompressed = 0
    compressed = 0

    try:
        with zipfile.ZipFile(archive_path, mode="r") as zf:
            info_list = zf.infolist()
            if len(info_list) > limits.max_entries:
                violations.append(
                    f"Entry count {len(info_list)} exceeds limit {limits.max_entries}"
                )

            for item in info_list:
                norm_name = item.filename.replace("\\", "/")
                if (
                    norm_name.startswith("/")
                    or ".." in norm_name.split("/")
                    or (len(norm_name) > 1 and norm_name[1] == ":")
                ):
                    violations.append(
                        f"Zip-Slip path traversal detected in member: '{item.filename}'"
                    )

                is_enc = bool(item.flag_bits & 0x1)
                if is_enc:
                    violations.append(f"Encrypted member detected: '{item.filename}'")

                is_sym = (
                    item.external_attr >> 16
                ) & _ZIP_SYMLINK_FLAG == _ZIP_SYMLINK_MASK
                if is_sym and not limits.allow_symlinks:
                    violations.append(
                        f"Symbolic link member forbidden: '{item.filename}'"
                    )

                is_dir = item.is_dir()
                uncompressed += item.file_size
                compressed += item.compress_size

                entries.append(
                    ArchiveEntryInfo(
                        path=item.filename,
                        size_bytes=item.file_size,
                        compressed_size_bytes=item.compress_size,
                        is_directory=is_dir,
                        is_symlink=is_sym,
                        is_encrypted=is_enc,
                    )
                )
    except zipfile.BadZipFile as exc:
        violations.append(f"Corrupt or malformed ZIP archive: {exc}")

    return len(entries), uncompressed, compressed, violations, entries


def _inspect_tar(
    archive_path: Path,
    limits: ArchiveLimits,
) -> tuple[int, int, int, list[str], list[ArchiveEntryInfo]]:
    """Inspect TAR family archive members for safety and size bounds."""
    violations: list[str] = []
    entries: list[ArchiveEntryInfo] = []
    uncompressed = 0

    try:
        with tarfile.open(archive_path, mode="r:*") as tf:
            members = tf.getmembers()
            if len(members) > limits.max_entries:
                violations.append(
                    f"Entry count {len(members)} exceeds limit {limits.max_entries}"
                )

            for member in members:
                norm_name = member.name.replace("\\", "/")
                if (
                    norm_name.startswith("/")
                    or ".." in norm_name.split("/")
                    or (len(norm_name) > 1 and norm_name[1] == ":")
                ):
                    violations.append(
                        f"Tar traversal vector detected in member: '{member.name}'"
                    )

                is_sym = member.issym() or member.islnk()
                if is_sym and not limits.allow_symlinks:
                    violations.append(
                        f"Symbolic link member forbidden: '{member.name}'"
                    )

                if (
                    member.isdev()
                    or member.ischr()
                    or member.isblk()
                    or member.isfifo()
                ):
                    violations.append(
                        f"Special device/FIFO node forbidden: '{member.name}'"
                    )

                is_dir = member.isdir()
                uncompressed += member.size
                entries.append(
                    ArchiveEntryInfo(
                        path=member.name,
                        size_bytes=member.size,
                        compressed_size_bytes=member.size,
                        is_directory=is_dir,
                        is_symlink=is_sym,
                        is_encrypted=False,
                    )
                )
    except (tarfile.TarError, EOFError) as exc:
        violations.append(f"Corrupt or malformed TAR archive: {exc}")

    compressed = archive_path.stat().st_size
    return len(entries), uncompressed, compressed, violations, entries


def inspect_archive(
    archive_path: Path,
    *,
    limits: ArchiveLimits | None = None,
) -> ArchiveInspection:
    """Inspect an archive file for structural properties, bombs, and traversal vectors.

    Args:
        archive_path: Path to the archive file on disk.
        limits: Optional safety boundaries; defaults to canonical ArchiveLimits().

    Returns:
        ArchiveInspection report detailing entries, sizes, and safety status.
    """
    effective_limits = limits or ArchiveLimits()
    fmt = _detect_archive_format(archive_path)

    if fmt == ArchiveFormat.ZIP:
        count, uncompressed, compressed, violations, entries = _inspect_zip(
            archive_path, effective_limits
        )
    else:
        count, uncompressed, compressed, violations, entries = _inspect_tar(
            archive_path, effective_limits
        )

    file_size = archive_path.stat().st_size
    base_compressed = max(compressed, file_size, 1)
    ratio = uncompressed / base_compressed if base_compressed > 0 else 1.0

    if uncompressed > effective_limits.max_uncompressed_bytes:
        violations.append(
            f"Total uncompressed size {uncompressed} exceeds ceiling "
            f"{effective_limits.max_uncompressed_bytes}"
        )

    if uncompressed > _ONE_MIB and ratio > effective_limits.max_expansion_ratio:
        violations.append(
            f"Archive expansion ratio {ratio:.2f} exceeds threshold "
            f"{effective_limits.max_expansion_ratio}"
        )

    is_safe = len(violations) == 0
    if not is_safe:
        logger.warning(
            "Archive safety inspection flagged violations",
            extra={
                "archive": archive_path.name,
                "violations": violations,
                "fr_id": "FR-HOST-RESOURCES-ARCHIVE-INSPECTION",
            },
        )
    else:
        logger.info(
            "Archive safety inspection passed",
            extra={
                "archive": archive_path.name,
                "entries": count,
                "uncompressed_bytes": uncompressed,
                "ratio": round(ratio, 2),
                "fr_id": "FR-HOST-RESOURCES-ARCHIVE-INSPECTION",
            },
        )

    return ArchiveInspection(
        archive_format=fmt,
        entry_count=count,
        uncompressed_bytes=uncompressed,
        compressed_bytes=compressed or file_size,
        expansion_ratio=round(ratio, 4),
        is_safe=is_safe,
        violations=violations,
        entries=entries,
    )


def _rollback_paths(paths: list[Path]) -> None:
    """Recursively delete created paths in reverse order upon extraction failure."""
    for p in reversed(paths):
        try:
            if p.is_file() or p.is_symlink():
                p.unlink(missing_ok=True)
            elif p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass


def _extract_zip(
    archive_path: Path,
    dest_dir: Path,
    allow_symlinks: bool,
) -> list[Path]:
    """Extract validated ZIP archive into destination sandbox."""
    created: list[Path] = []
    with zipfile.ZipFile(archive_path, mode="r") as zf:
        for item in zf.infolist():
            target_file = validate_contained_path(
                dest_dir, item.filename, allow_symlinks=allow_symlinks
            )
            if item.is_dir():
                target_file.mkdir(parents=True, exist_ok=True)
                created.append(target_file)
            else:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(item) as src, target_file.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                created.append(target_file)
    return created


def _extract_tar(
    archive_path: Path,
    dest_dir: Path,
    allow_symlinks: bool,
) -> list[Path]:
    """Extract validated TAR family archive into destination sandbox."""
    created: list[Path] = []
    with tarfile.open(archive_path, mode="r:*") as tf:
        for member in tf.getmembers():
            target_file = validate_contained_path(
                dest_dir, member.name, allow_symlinks=allow_symlinks
            )
            if member.isdir():
                target_file.mkdir(parents=True, exist_ok=True)
                created.append(target_file)
            elif member.isreg():
                target_file.parent.mkdir(parents=True, exist_ok=True)
                f = tf.extractfile(member)
                if f is not None:
                    with f as src, target_file.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    created.append(target_file)
    return created


def safe_extract_archive(
    archive_path: Path,
    destination_dir: Path,
    *,
    limits: ArchiveLimits | None = None,
) -> list[Path]:
    """Safely extract archive members into destination_dir with transactional cleanup.

    Args:
        archive_path: Path to archive file.
        destination_dir: Target directory sandbox.
        limits: Optional safety limits.

    Returns:
        List of created Path objects.

    Raises:
        ArchiveBombError: If archive exceeds size, ratio, or entry count limits.
        ResourceSecurityError: If archive contains traversal vectors or forbidden nodes.
    """
    effective_limits = limits or ArchiveLimits()
    inspection = inspect_archive(archive_path, limits=effective_limits)

    if not inspection.is_safe:
        for violation in inspection.violations:
            if "ratio" in violation.lower() or "ceiling" in violation.lower():
                raise ArchiveBombError(
                    f"Archive rejected as expansion bomb: {violation}"
                )
        violation_details = "; ".join(inspection.violations)
        raise ResourceSecurityError(
            f"Archive rejected due to safety violations: {violation_details}"
        )

    destination_dir.mkdir(parents=True, exist_ok=True)
    created_paths: list[Path] = []

    try:
        if inspection.archive_format == ArchiveFormat.ZIP:
            created_paths = _extract_zip(
                archive_path, destination_dir, effective_limits.allow_symlinks
            )
        else:
            created_paths = _extract_tar(
                archive_path, destination_dir, effective_limits.allow_symlinks
            )

        logger.info(
            "Archive safely extracted",
            extra={
                "archive": archive_path.name,
                "destination": str(destination_dir),
                "extracted_count": len(created_paths),
                "fr_id": "FR-HOST-RESOURCES-ARCHIVE-EXTRACTION",
            },
        )
        return created_paths

    except Exception:
        logger.exception(
            "Archive extraction failed; executing transactional rollback",
            extra={
                "archive": archive_path.name,
                "fr_id": "FR-HOST-RESOURCES-ARCHIVE-EXTRACTION",
            },
        )
        _rollback_paths(created_paths)
        raise


# ============================================================================
# Bounded Resource Cache
# ============================================================================


class _CacheEntry:
    """Internal cache entry wrapper."""

    __slots__ = (
        "content_hash",
        "created_at",
        "data",
        "expires_at",
        "key",
        "last_accessed_at",
        "size_bytes",
    )

    def __init__(
        self,
        key: str,
        data: bytes,
        *,
        content_hash: str = "",
        expires_at: float | None = None,
    ) -> None:
        self.key = key
        self.data = data
        self.size_bytes = len(data)
        self.content_hash = content_hash
        self.created_at = time.time()
        self.last_accessed_at = self.created_at
        self.expires_at = expires_at


class ResourceCache:
    """Thread-safe, byte-bounded LRU and TTL memory cache for resource payloads."""

    def __init__(
        self,
        *,
        max_bytes: int = 100 * 1024 * 1024,
        default_ttl_seconds: float | None = None,
    ) -> None:
        """Initialize ResourceCache with maximum byte capacity and optional default TTL.

        Args:
            max_bytes: Maximum combined byte size of all cached payloads.
            default_ttl_seconds: Optional default expiration duration in seconds.
        """
        self._max_bytes = max_bytes
        self._default_ttl_seconds = default_ttl_seconds
        self._entries: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._used_bytes = 0
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> bytes | None:
        """Retrieve a cached byte payload by key if present and unexpired.

        Args:
            key: Unique cache key.

        Returns:
            Bytes payload if found and unexpired; None otherwise.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._miss_count += 1
                return None

            now = time.time()
            if entry.expires_at is not None and now > entry.expires_at:
                self._entries.pop(key, None)
                self._used_bytes -= entry.size_bytes
                self._miss_count += 1
                return None

            entry.last_accessed_at = now
            self._entries.move_to_end(key, last=True)
            self._hit_count += 1
            return entry.data

    def put(
        self,
        key: str,
        data: bytes,
        *,
        content_hash: str = "",
        ttl_seconds: float | None = None,
    ) -> bool:
        """Store a byte payload in cache, evicting LRU items to honor byte ceiling.

        Args:
            key: Unique cache key.
            data: Binary payload to store.
            content_hash: Optional SHA-256 digest of payload.
            ttl_seconds: Optional TTL override in seconds.

        Returns:
            True if stored; False if payload exceeds max_bytes and cannot be cached.
        """
        item_size = len(data)
        if item_size > self._max_bytes:
            return False

        with self._lock:
            existing = self._entries.pop(key, None)
            if existing is not None:
                self._used_bytes -= existing.size_bytes

            while self._used_bytes + item_size > self._max_bytes and self._entries:
                _oldest_key, oldest_entry = self._entries.popitem(last=False)
                self._used_bytes -= oldest_entry.size_bytes
                self._eviction_count += 1
                logger.info(
                    "Evicted cache entry due to byte capacity limit",
                    extra={
                        "evicted_key": oldest_entry.key,
                        "freed_bytes": oldest_entry.size_bytes,
                        "used_bytes": self._used_bytes,
                        "fr_id": "FR-HOST-RESOURCES-BOUNDED-CACHE",
                    },
                )

            effective_ttl = (
                ttl_seconds if ttl_seconds is not None else self._default_ttl_seconds
            )
            expires_at = (
                time.time() + effective_ttl if effective_ttl is not None else None
            )

            new_entry = _CacheEntry(
                key=key,
                data=data,
                content_hash=content_hash,
                expires_at=expires_at,
            )
            self._entries[key] = new_entry
            self._used_bytes += item_size
            return True

    def invalidate(self, key: str) -> bool:
        """Explicitly invalidate and remove an item from cache.

        Args:
            key: Cache key to invalidate.

        Returns:
            True if item was removed; False if item was not found.
        """
        with self._lock:
            entry = self._entries.pop(key, None)
            if entry is not None:
                self._used_bytes -= entry.size_bytes
                return True
            return False

    def clear(self) -> None:
        """Clear all cached entries and reset utilized bytes."""
        with self._lock:
            self._entries.clear()
            self._used_bytes = 0

    def get_stats(self) -> CacheStats:
        """Return current cache telemetry metrics snapshot."""
        with self._lock:
            return CacheStats(
                max_bytes=self._max_bytes,
                used_bytes=self._used_bytes,
                entry_count=len(self._entries),
                hit_count=self._hit_count,
                miss_count=self._miss_count,
                eviction_count=self._eviction_count,
            )


# ============================================================================
# Remote HTTP Acquisition
# ============================================================================


def _stream_remote_payload(
    url: str,
    dest_path: Path,
    max_bytes: int,
    timeout_seconds: float,
    client: httpx.Client | None,
) -> tuple[int, str]:
    """Execute synchronous streaming download of remote payload."""
    hasher = hashlib.sha256()
    total_bytes = 0
    own_client = client is None
    http_client = (
        client
        if client is not None
        else httpx.Client(timeout=timeout_seconds, follow_redirects=True)
    )

    try:
        with http_client.stream("GET", url) as response:
            if response.status_code >= _HTTP_BAD_REQUEST:
                msg = f"Remote artifact HTTP status {response.status_code}"
                raise AcquisitionError(msg)

            cl_header = response.headers.get("content-length")
            if cl_header and cl_header.isdigit() and int(cl_header) > max_bytes:
                raise AcquisitionError(
                    f"Remote Content-Length {cl_header} exceeds ceiling {max_bytes}"
                )

            with dest_path.open("wb") as out_file:
                for chunk in response.iter_bytes(chunk_size=_CHUNK_SIZE):
                    total_bytes += len(chunk)
                    if total_bytes > max_bytes:
                        raise AcquisitionError(
                            f"Downloaded stream exceeded ceiling {max_bytes} bytes"
                        )
                    hasher.update(chunk)
                    out_file.write(chunk)

        digest = hasher.hexdigest()
        return total_bytes, digest
    finally:
        if own_client:
            http_client.close()


def acquire_remote(
    url: str,
    destination_path: Path,
    *,
    max_bytes: int = 100 * 1024 * 1024,
    timeout_seconds: float = 30.0,
    client: httpx.Client | None = None,
) -> tuple[int, str]:
    """Download a remote artifact via HTTP/HTTPS safely with size bounds.

    Args:
        url: Remote HTTP/HTTPS target URL.
        destination_path: Local staging file path.
        max_bytes: Maximum allowed bytes before aborting download.
        timeout_seconds: Timeout ceiling in seconds.
        client: Optional shared httpx.Client.

    Returns:
        Tuple of (downloaded_size_bytes, sha256_hex_digest).

    Raises:
        ResourceSecurityError: If URL scheme is not http or https.
        AcquisitionError: If download fails, times out, or exceeds max_bytes.
    """
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ResourceSecurityError(
            f"Unsupported URL scheme: '{parsed.scheme}'. Only HTTP/HTTPS allowed."
        )

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        size, digest = _stream_remote_payload(
            url, destination_path, max_bytes, timeout_seconds, client
        )
        logger.info(
            "Remote artifact acquired successfully",
            extra={
                "url": url,
                "size_bytes": size,
                "sha256": digest,
                "fr_id": "FR-HOST-RESOURCES-HTTPX-ACQUISITION",
            },
        )
        return size, digest

    except Exception as exc:
        if destination_path.exists():
            destination_path.unlink(missing_ok=True)
        if isinstance(exc, (ResourceSecurityError, AcquisitionError)):
            raise
        raise AcquisitionError(
            f"Failed to acquire remote artifact from '{url}': {exc}"
        ) from exc


# ============================================================================
# Central Resource Manager
# ============================================================================


def _is_staging_expired(
    entry: Path,
    meta: ResourceMetadata | None,
    now: float,
    max_age_seconds: float,
) -> bool:
    """Check whether a staging directory has expired or been orphaned."""
    if meta is None:
        return (now - entry.stat().st_mtime) > max_age_seconds
    if meta.status in (ResourceStatus.PUBLISHED, ResourceStatus.EXPIRED):
        return True
    if meta.expires_at_utc and datetime.now(UTC) > meta.expires_at_utc:
        return True
    return (now - entry.stat().st_mtime) > max_age_seconds


class ResourceManager:
    """Universal host authority for managing immutable resources."""

    def __init__(
        self,
        root_dir: Path,
        *,
        cache_max_bytes: int = 100 * 1024 * 1024,
    ) -> None:
        """Initialize ResourceManager with isolated filesystem root and cache.

        Args:
            root_dir: Primary directory for host resource custody.
            cache_max_bytes: Byte capacity for internal LRU artifact cache.
        """
        self.root_dir = root_dir.resolve()
        self.staging_dir = self.root_dir / "staging"
        self.store_dir = self.root_dir / "store"
        self.metadata_dir = self.root_dir / "metadata"
        self.extracted_dir = self.root_dir / "extracted"

        for directory in (
            self.staging_dir,
            self.store_dir,
            self.metadata_dir,
            self.extracted_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        self.cache = ResourceCache(max_bytes=cache_max_bytes)
        self._lock = threading.Lock()

    def _save_metadata(self, metadata: ResourceMetadata) -> None:
        """Persist metadata record to JSON file in metadata directory."""
        meta_file = self.metadata_dir / f"{metadata.resource_id}.json"
        temp_file = self.metadata_dir / f"{metadata.resource_id}.tmp"
        with temp_file.open("w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))
        temp_file.replace(meta_file)

    def _load_metadata(self, resource_id: str) -> ResourceMetadata | None:
        """Load metadata record from disk if present."""
        meta_file = self.metadata_dir / f"{resource_id}.json"
        if not meta_file.is_file():
            return None
        with meta_file.open(encoding="utf-8") as f:
            return ResourceMetadata.model_validate_json(f.read())

    def register_resource(self, metadata: ResourceMetadata) -> None:
        """Register or update resource metadata record."""
        with self._lock:
            self._save_metadata(metadata)

    def stage_file(
        self,
        source_path: Path,
        *,
        scope: ResourceScope = ResourceScope.WORKSPACE,
        name: str | None = None,
        tags: dict[str, str] | None = None,
        attributes: dict[str, Any] | None = None,
        expires_in_seconds: int | None = None,
    ) -> ResourceMetadata:
        """Stage an existing local file into transient staging custody.

        Args:
            source_path: Local source file to stage.
            scope: Resource authorization scope.
            name: Optional custom name; defaults to source file name.
            tags: Optional key-value indexing tags.
            attributes: Optional structured attributes.
            expires_in_seconds: Optional transient TTL.

        Returns:
            ResourceMetadata in STAGED status.
        """
        if not source_path.is_file():
            raise ResourceNotFoundError(f"Source file not found: {source_path}")

        resource_id = f"res_{uuid.uuid4().hex}"
        file_name = name or source_path.name
        stage_sub = self.staging_dir / resource_id
        stage_sub.mkdir(parents=True, exist_ok=True)
        dest_path = stage_sub / file_name

        hasher = hashlib.sha256()
        size_bytes = 0

        with (
            source_path.open("rb") as src,
            dest_path.open("wb") as dst,
        ):
            while chunk := src.read(_CHUNK_SIZE):
                size_bytes += len(chunk)
                hasher.update(chunk)
                dst.write(chunk)

        content_hash = hasher.hexdigest()
        mime, _ = mimetypes.guess_type(file_name)
        mime_type = mime or "application/octet-stream"

        now = datetime.now(UTC)
        expires_at = (
            datetime.fromtimestamp(now.timestamp() + expires_in_seconds, tz=UTC)
            if expires_in_seconds is not None
            else None
        )

        metadata = ResourceMetadata(
            resource_id=resource_id,
            scope=scope,
            name=file_name,
            content_hash=content_hash,
            size_bytes=size_bytes,
            mime_type=mime_type,
            status=ResourceStatus.STAGED,
            created_at_utc=now,
            expires_at_utc=expires_at,
            tags=tags or {},
            attributes=attributes or {},
        )
        self._save_metadata(metadata)

        logger.info(
            "Resource file staged",
            extra={
                "resource_id": resource_id,
                "resource_name": file_name,
                "size_bytes": size_bytes,
                "sha256": content_hash,
                "fr_id": "FR-HOST-RESOURCES-STAGING-PUBLICATION",
            },
        )
        return metadata

    def stage_bytes(
        self,
        data: bytes,
        *,
        name: str,
        scope: ResourceScope = ResourceScope.WORKSPACE,
        tags: dict[str, str] | None = None,
        attributes: dict[str, Any] | None = None,
        expires_in_seconds: int | None = None,
    ) -> ResourceMetadata:
        """Stage raw byte data into transient staging custody.

        Args:
            data: Binary payload to stage.
            name: Assigned file name.
            scope: Resource authorization scope.
            tags: Optional key-value indexing tags.
            attributes: Optional structured attributes.
            expires_in_seconds: Optional transient TTL.

        Returns:
            ResourceMetadata in STAGED status.
        """
        resource_id = f"res_{uuid.uuid4().hex}"
        stage_sub = self.staging_dir / resource_id
        stage_sub.mkdir(parents=True, exist_ok=True)
        dest_path = stage_sub / name

        hasher = hashlib.sha256(data)
        content_hash = hasher.hexdigest()
        size_bytes = len(data)

        with dest_path.open("wb") as f:
            f.write(data)

        mime, _ = mimetypes.guess_type(name)
        mime_type = mime or "application/octet-stream"

        now = datetime.now(UTC)
        expires_at = (
            datetime.fromtimestamp(now.timestamp() + expires_in_seconds, tz=UTC)
            if expires_in_seconds is not None
            else None
        )

        metadata = ResourceMetadata(
            resource_id=resource_id,
            scope=scope,
            name=name,
            content_hash=content_hash,
            size_bytes=size_bytes,
            mime_type=mime_type,
            status=ResourceStatus.STAGED,
            created_at_utc=now,
            expires_at_utc=expires_at,
            tags=tags or {},
            attributes=attributes or {},
        )
        self._save_metadata(metadata)

        logger.info(
            "Resource bytes staged",
            extra={
                "resource_id": resource_id,
                "resource_name": name,
                "size_bytes": size_bytes,
                "sha256": content_hash,
                "fr_id": "FR-HOST-RESOURCES-STAGING-PUBLICATION",
            },
        )
        return metadata

    def publish(
        self,
        resource_id: str,
        *,
        expected_hash: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> ResourceMetadata:
        """Publish a staged resource into immutable content-addressed storage.

        Args:
            resource_id: Resource identifier to publish.
            expected_hash: Optional expected SHA-256 hash to assert before publish.
            tags: Optional tags to merge into published metadata.

        Returns:
            ResourceMetadata in PUBLISHED status.

        Raises:
            ResourceNotFoundError: If resource_id is not found.
            ResourceConflictError: If resource is not in STAGED status.
            CorruptResourceError: If content hash does not match staged file.
        """
        with self._lock:
            meta = self._load_metadata(resource_id)
            if meta is None or meta.status == ResourceStatus.TOMBSTONED:
                raise ResourceNotFoundError(f"Resource not found: {resource_id}")

            if meta.status != ResourceStatus.STAGED:
                msg = (
                    f"Resource {resource_id} is in status '{meta.status}', "
                    "cannot publish"
                )
                raise ResourceConflictError(msg)

            staged_file = self.staging_dir / resource_id / meta.name
            if not staged_file.is_file():
                raise ResourceNotFoundError(
                    f"Staged payload file missing for resource {resource_id}"
                )

            hasher = hashlib.sha256()
            with staged_file.open("rb") as f:
                while chunk := f.read(_CHUNK_SIZE):
                    hasher.update(chunk)
            disk_hash = hasher.hexdigest()

            if disk_hash != meta.content_hash:
                msg = (
                    f"Corrupt staged file: recorded hash '{meta.content_hash}' "
                    f"does not match disk hash '{disk_hash}'"
                )
                raise CorruptResourceError(msg)

            if expected_hash and disk_hash.lower() != expected_hash.lower():
                msg = (
                    f"Expected hash '{expected_hash}' does not match "
                    f"actual hash '{disk_hash}'"
                )
                raise CorruptResourceError(msg)

            prefix = disk_hash[:2]
            rest = disk_hash[2:]
            store_sub = self.store_dir / prefix
            store_sub.mkdir(parents=True, exist_ok=True)
            store_file = store_sub / rest

            if not store_file.exists():
                shutil.copy2(staged_file, store_file)

            shutil.rmtree(self.staging_dir / resource_id, ignore_errors=True)

            now = datetime.now(UTC)
            updated_tags = {**meta.tags, **(tags or {})}
            published_meta = meta.model_copy(
                update={
                    "status": ResourceStatus.PUBLISHED,
                    "published_at_utc": now,
                    "tags": updated_tags,
                }
            )
            self._save_metadata(published_meta)

            logger.info(
                "Resource published to immutable store",
                extra={
                    "resource_id": resource_id,
                    "content_hash": disk_hash,
                    "store_path": str(store_file),
                    "fr_id": "FR-HOST-RESOURCES-STAGING-PUBLICATION",
                },
            )
            return published_meta

    def get_metadata(self, resource_id: str) -> ResourceMetadata:
        """Retrieve metadata for a resource by ID.

        Args:
            resource_id: Unique resource identifier.

        Returns:
            ResourceMetadata record.

        Raises:
            ResourceNotFoundError: If resource is absent or tombstoned.
        """
        meta = self._load_metadata(resource_id)
        if meta is None or meta.status == ResourceStatus.TOMBSTONED:
            raise ResourceNotFoundError(f"Resource not found: {resource_id}")
        return meta

    def get_content_path(self, resource_id: str) -> Path:
        """Resolve the disk Path to the resource's content file.

        Args:
            resource_id: Unique resource identifier.

        Returns:
            Path to file in store or staging directory.

        Raises:
            ResourceNotFoundError: If resource or content file does not exist.
        """
        meta = self.get_metadata(resource_id)
        if meta.status == ResourceStatus.PUBLISHED:
            prefix = meta.content_hash[:2]
            rest = meta.content_hash[2:]
            target = self.store_dir / prefix / rest
        elif meta.status == ResourceStatus.STAGED:
            target = self.staging_dir / resource_id / meta.name
        else:
            raise ResourceNotFoundError(
                f"Resource {resource_id} is in unusable status: {meta.status}"
            )

        if not target.is_file():
            raise ResourceNotFoundError(
                f"Content file missing on disk for resource {resource_id}"
            )
        return target

    def read_bytes(self, resource_id: str) -> bytes:
        """Read binary contents of a resource, utilizing internal LRU cache.

        Args:
            resource_id: Unique resource identifier.

        Returns:
            Bytes content of the resource.
        """
        meta = self.get_metadata(resource_id)
        cache_key = f"{resource_id}:{meta.content_hash}"

        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        path = self.get_content_path(resource_id)
        with path.open("rb") as f:
            data = f.read()

        self.cache.put(cache_key, data, content_hash=meta.content_hash)
        return data

    def tombstone(self, resource_id: str) -> ResourceMetadata:
        """Mark a resource as TOMBSTONED and evict from cache.

        Args:
            resource_id: Unique resource identifier.

        Returns:
            Updated ResourceMetadata with TOMBSTONED status.
        """
        with self._lock:
            meta = self._load_metadata(resource_id)
            if meta is None or meta.status == ResourceStatus.TOMBSTONED:
                raise ResourceNotFoundError(f"Resource not found: {resource_id}")

            cache_key = f"{resource_id}:{meta.content_hash}"
            self.cache.invalidate(cache_key)

            tombstoned_meta = meta.model_copy(
                update={"status": ResourceStatus.TOMBSTONED}
            )
            self._save_metadata(tombstoned_meta)

            logger.info(
                "Resource tombstoned",
                extra={
                    "resource_id": resource_id,
                    "fr_id": "FR-HOST-RESOURCES-STAGING-PUBLICATION",
                },
            )
            return tombstoned_meta

    def inspect_resource_archive(
        self,
        resource_id: str,
        *,
        limits: ArchiveLimits | None = None,
    ) -> ArchiveInspection:
        """Inspect an archive stored as a resource without extracting it.

        Args:
            resource_id: Resource identifier of the archive file.
            limits: Optional safety limits.

        Returns:
            ArchiveInspection report.
        """
        path = self.get_content_path(resource_id)
        return inspect_archive(path, limits=limits)

    def extract_resource_archive(
        self,
        resource_id: str,
        target_subpath: str,
        *,
        limits: ArchiveLimits | None = None,
    ) -> list[Path]:
        """Safely extract an archive resource into a contained subfolder.

        Args:
            resource_id: Resource identifier of the archive.
            target_subpath: Relative subpath under extracted sandbox directory.
            limits: Optional safety limits.

        Returns:
            List of created Path objects.
        """
        path = self.get_content_path(resource_id)
        dest_dir = validate_contained_path(self.extracted_dir, target_subpath)
        return safe_extract_archive(path, dest_dir, limits=limits)

    def cleanup_staging(self, *, max_age_seconds: float = 3600.0) -> int:
        """Purge expired or orphaned staging directories to bound disk usage.

        Args:
            max_age_seconds: Age in seconds after which uncommitted staging is pruned.

        Returns:
            Number of purged staging directories.
        """
        cleaned_count = 0
        now = time.time()

        if not self.staging_dir.exists():
            return 0

        for entry in self.staging_dir.iterdir():
            if not entry.is_dir():
                continue

            resource_id = entry.name
            meta = self._load_metadata(resource_id)

            if _is_staging_expired(entry, meta, now, max_age_seconds):
                try:
                    shutil.rmtree(entry, ignore_errors=True)
                    cleaned_count += 1
                    logger.info(
                        "Purged orphaned staging directory",
                        extra={
                            "directory": str(entry),
                            "resource_id": resource_id,
                            "fr_id": "FR-HOST-RESOURCES-ORPHAN-CLEANUP",
                        },
                    )
                except OSError as exc:
                    logger.warning(
                        "Failed to remove staging directory during cleanup",
                        extra={"directory": str(entry), "error": str(exc)},
                    )

        return cleaned_count


# ============================================================================
# Scoped Capability Facade
# ============================================================================


class ResourceAccess:
    """Capability facade restricting resource interactions to an authorized scope."""

    def __init__(
        self,
        manager: ResourceManager,
        *,
        scope: ResourceScope,
        owner_id: str,
    ) -> None:
        """Initialize ResourceAccess facade with manager and scope.

        Args:
            manager: Central host ResourceManager.
            scope: Permitted ResourceScope.
            owner_id: Unique identifier of owning domain or tenant.
        """
        self._manager = manager
        self._scope = scope
        self._owner_id = owner_id

    @property
    def scope(self) -> ResourceScope:
        """Return the bound scope."""
        return self._scope

    def stage(self, data: bytes, *, name: str) -> ResourceMetadata:
        """Stage bytes under bound scope and owner tag."""
        return self._manager.stage_bytes(
            data,
            name=name,
            scope=self._scope,
            tags={"owner_id": self._owner_id},
        )

    def publish(self, resource_id: str) -> ResourceMetadata:
        """Publish a staged resource if scope matches."""
        meta = self._manager.get_metadata(resource_id)
        if meta.scope != self._scope:
            msg = (
                f"Unauthorized: resource scope '{meta.scope}' "
                f"does not match bound scope '{self._scope}'"
            )
            raise ResourceSecurityError(msg)
        return self._manager.publish(resource_id)

    def read(self, resource_id: str) -> bytes:
        """Read resource bytes if scope matches."""
        meta = self._manager.get_metadata(resource_id)
        if meta.scope not in (self._scope, ResourceScope.SYSTEM):
            msg = f"Unauthorized: access to resource scope '{meta.scope}' denied"
            raise ResourceSecurityError(msg)
        return self._manager.read_bytes(resource_id)


# ============================================================================
# REST Transport Projection
# ============================================================================


class ResourceRouterService:
    """Internal service adapter translating HTTP requests to ResourceManager actions."""

    def __init__(self, manager: ResourceManager) -> None:
        self._manager = manager

    async def stage_upload(
        self,
        request: Request,
        name: Annotated[str | None, Query()] = None,
        scope: Annotated[ResourceScope, Query()] = ResourceScope.WORKSPACE,
        expires_in_seconds: Annotated[int | None, Query()] = None,
    ) -> Response:
        """Stage an uploaded binary payload."""
        req_id = request.headers.get("x-request-id")
        data = await request.body()
        filename = (
            name or request.headers.get("x-file-name") or f"upload_{uuid.uuid4().hex}"
        )
        meta = self._manager.stage_bytes(
            data,
            name=filename,
            scope=scope,
            expires_in_seconds=expires_in_seconds,
        )
        resp = ApiResponse.success(
            data=meta.model_dump(mode="json"),
            message=f"Resource {meta.resource_id} staged successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def stage_json(
        self,
        request: Request,
        req: StagingRequest,
    ) -> Response:
        """Stage an empty or initialized resource via JSON payload."""
        req_id = request.headers.get("x-request-id")
        meta = self._manager.stage_bytes(
            b"",
            name=req.name,
            scope=req.scope,
            tags=req.tags,
            attributes=req.attributes,
            expires_in_seconds=req.expires_in_seconds,
        )
        resp = ApiResponse.success(
            data=meta.model_dump(mode="json"),
            message=f"Resource {meta.resource_id} staged successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def acquire_remote_endpoint(
        self,
        request: Request,
        req: AcquireRemoteRequest,
    ) -> Response:
        """Fetch remote artifact via HTTP and stage in custody."""
        req_id = request.headers.get("x-request-id")
        res_id = f"res_{uuid.uuid4().hex}"
        url_path = urllib.parse.urlparse(req.url).path
        file_name = req.name or Path(url_path).name or f"remote_{res_id}"

        stage_sub = self._manager.staging_dir / res_id
        stage_sub.mkdir(parents=True, exist_ok=True)
        dest_path = stage_sub / file_name

        try:
            size_bytes, digest = acquire_remote(
                req.url,
                dest_path,
                max_bytes=req.max_bytes,
                timeout_seconds=req.timeout_seconds,
            )
        except (ResourceSecurityError, AcquisitionError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

        mime, _ = mimetypes.guess_type(file_name)
        mime_type = mime or "application/octet-stream"

        meta = ResourceMetadata(
            resource_id=res_id,
            scope=req.scope,
            name=file_name,
            content_hash=digest,
            size_bytes=size_bytes,
            mime_type=mime_type,
            status=ResourceStatus.STAGED,
            created_at_utc=datetime.now(UTC),
            tags=req.tags,
            attributes=req.attributes,
        )
        self._manager.register_resource(meta)
        resp = ApiResponse.success(
            data=meta.model_dump(mode="json"),
            message=f"Remote artifact acquired and staged as {res_id}.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def publish_resource(
        self,
        request: Request,
        resource_id: str,
        req: PublishRequest | None = None,
    ) -> Response:
        """Publish a staged resource to immutable store."""
        req_id = request.headers.get("x-request-id")
        expected = req.expected_hash if req else None
        extra_tags = req.tags if req else None
        try:
            meta = self._manager.publish(
                resource_id, expected_hash=expected, tags=extra_tags
            )
            resp = ApiResponse.success(
                data=meta.model_dump(mode="json"),
                message=f"Resource {resource_id} published successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        except (ResourceConflictError, CorruptResourceError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

    def get_metadata(
        self,
        request: Request,
        resource_id: str,
    ) -> Response:
        """Query metadata for a resource."""
        req_id = request.headers.get("x-request-id")
        try:
            meta = self._manager.get_metadata(resource_id)
            resp = ApiResponse.success(
                data=meta.model_dump(mode="json"),
                message=f"Retrieved metadata for {resource_id}.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc

    def get_content(
        self,
        resource_id: str,
    ) -> Response:
        """Download raw binary content of a resource."""
        try:
            meta = self._manager.get_metadata(resource_id)
            path = self._manager.get_content_path(resource_id)
            return FileResponse(
                path=path,
                media_type=meta.mime_type,
                filename=meta.name,
            )
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc

    def tombstone_resource(
        self,
        request: Request,
        resource_id: str,
    ) -> Response:
        """Tombstone / delete a resource."""
        req_id = request.headers.get("x-request-id")
        try:
            meta = self._manager.tombstone(resource_id)
            resp = ApiResponse.success(
                data=meta.model_dump(mode="json"),
                message=f"Resource {resource_id} tombstoned successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc

    def inspect_archive_endpoint(
        self,
        request: Request,
        req: InspectArchiveRequest,
    ) -> Response:
        """Inspect an archive resource for safety and structure."""
        req_id = request.headers.get("x-request-id")
        try:
            report = self._manager.inspect_resource_archive(
                req.resource_id, limits=req.limits
            )
            resp = ApiResponse.success(
                data=report.model_dump(mode="json"),
                message=f"Inspected archive for resource {req.resource_id}.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        except ResourceSecurityError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

    def extract_archive_endpoint(
        self,
        request: Request,
        req: ExtractArchiveRequest,
    ) -> Response:
        """Safely extract an archive resource into a contained subfolder."""
        req_id = request.headers.get("x-request-id")
        try:
            paths = self._manager.extract_resource_archive(
                req.resource_id,
                req.target_subpath,
                limits=req.limits,
            )
            resp = ApiResponse.success(
                data={"extracted_paths": [str(p) for p in paths], "count": len(paths)},
                message=f"Archive for {req.resource_id} extracted successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        except (ArchiveBombError, ResourceSecurityError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

    def cache_status(self, request: Request) -> Response:
        """Get cache telemetry metrics snapshot."""
        req_id = request.headers.get("x-request-id")
        stats = self._manager.cache.get_stats()
        resp = ApiResponse.success(
            data=stats.model_dump(mode="json"),
            message="Cache metrics retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def cleanup_staging_endpoint(
        self,
        request: Request,
        max_age_seconds: Annotated[float, Query(ge=0.0)] = 3600.0,
    ) -> Response:
        """Purge expired or orphaned staging directories."""
        req_id = request.headers.get("x-request-id")
        cleaned = self._manager.cleanup_staging(max_age_seconds=max_age_seconds)
        resp = ApiResponse.success(
            data={"purged_count": cleaned},
            message=f"Purged {cleaned} orphaned staging directories.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_resources_router(manager: ResourceManager) -> APIRouter:
    """Create and configure FastAPI APIRouter exposing resource endpoints.

    Args:
        manager: Central host ResourceManager instance.

    Returns:
        Configured FastAPI APIRouter.
    """
    service = ResourceRouterService(manager)
    router = APIRouter(prefix="/resources", tags=["resources"])

    router.add_api_route(
        "/stage/upload",
        service.stage_upload,
        methods=["POST"],
        summary="Stage an uploaded multipart file",
    )
    router.add_api_route(
        "/stage",
        service.stage_json,
        methods=["POST"],
        summary="Stage an artifact via JSON",
    )
    router.add_api_route(
        "/acquire",
        service.acquire_remote_endpoint,
        methods=["POST"],
        summary="Acquire and stage a remote artifact via HTTP",
    )
    router.add_api_route(
        "/{resource_id}/publish",
        service.publish_resource,
        methods=["POST"],
        summary="Publish a staged resource into immutable storage",
    )
    router.add_api_route(
        "/{resource_id}",
        service.get_metadata,
        methods=["GET"],
        summary="Retrieve resource metadata",
    )
    router.add_api_route(
        "/{resource_id}/content",
        service.get_content,
        methods=["GET"],
        summary="Download raw resource binary content",
    )
    router.add_api_route(
        "/{resource_id}",
        service.tombstone_resource,
        methods=["DELETE"],
        summary="Tombstone a resource",
    )
    router.add_api_route(
        "/archive/inspect",
        service.inspect_archive_endpoint,
        methods=["POST"],
        summary="Inspect an archive resource",
    )
    router.add_api_route(
        "/archive/extract",
        service.extract_archive_endpoint,
        methods=["POST"],
        summary="Safely extract an archive resource",
    )
    router.add_api_route(
        "/cache/status",
        service.cache_status,
        methods=["GET"],
        summary="Get artifact cache telemetry",
    )
    router.add_api_route(
        "/staging/cleanup",
        service.cleanup_staging_endpoint,
        methods=["POST"],
        summary="Purge orphaned staging directories",
    )

    logger.debug(
        "Resources REST router initialized",
        extra={"fr_id": "FR-HOST-RESOURCES-REST-PROJECTION"},
    )
    return router


# ============================================================================
# CLI Entrypoint
# ============================================================================


def main() -> int:
    """CLI diagnostics entrypoint for inspecting archives and cache bounds.

    Returns:
        Process exit code (0 for success, non-zero for failure).
    """
    parser = argparse.ArgumentParser(
        description="HaruQuantAI Host Resource Custody and Archive Safety Tool"
    )
    parser.add_argument(
        "--inspect",
        type=Path,
        metavar="PATH",
        help="Inspect an archive file for safety, Zip-Slip, and expansion bombs",
    )
    parser.add_argument(
        "--cleanup-staging",
        action="store_true",
        help="Purge orphaned staging directories under root directory",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("data/resources"),
        help="Resource root directory (default: data/resources)",
    )
    parser.add_argument(
        "--max-age",
        type=float,
        default=3600.0,
        help="Maximum staging age in seconds for cleanup (default: 3600)",
    )

    args = parser.parse_args()

    if args.inspect:
        try:
            report = inspect_archive(args.inspect)
            logger.info("CLI inspect output", extra={"report": report.model_dump()})
            return 0 if report.is_safe else 1
        except (ResourceError, OSError, ValueError) as exc:
            logger.exception("Error inspecting archive", extra={"error": str(exc)})
            return 2

    if args.cleanup_staging:
        try:
            manager = ResourceManager(root_dir=args.root)
            purged = manager.cleanup_staging(max_age_seconds=args.max_age)
            logger.info(
                "CLI cleanup complete",
                extra={"purged": purged, "root": str(args.root)},
            )
            return 0
        except (ResourceError, OSError, ValueError) as exc:
            logger.exception("Error cleaning staging", extra={"error": str(exc)})
            return 2

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
