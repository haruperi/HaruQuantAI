"""Public contract for immutable artifact custody."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable


class ArtifactOperation(StrEnum):
    """Supported artifact-custody operations."""

    PUBLISH = "PUBLISH"
    INSPECT = "INSPECT"
    ISSUE_DOWNLOAD_GRANT = "ISSUE_DOWNLOAD_GRANT"
    RESOLVE_DOWNLOAD = "RESOLVE_DOWNLOAD"
    ADD_REFERENCE = "ADD_REFERENCE"
    REMOVE_REFERENCE = "REMOVE_REFERENCE"
    ADD_HOLD = "ADD_HOLD"
    RELEASE_HOLD = "RELEASE_HOLD"
    CLEANUP = "CLEANUP"


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    """Immutable published artifact metadata."""

    artifact_id: str
    account_id: str
    owner_id: str
    content_hash: str
    byte_count: int
    schema_id: str
    published_at: datetime
    revision: int = 1
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class CustodyReceipt:
    """Publication receipt."""

    artifact: ArtifactRecord
    idempotency_key: str
    published_new: bool
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class PublishArtifactRequest:
    """Request to publish validated immutable bytes."""

    request_id: str
    actor_id: str
    account_id: str
    owner_id: str
    workspace_path: Path
    idempotency_key: str
    content: bytes
    declared_byte_count: int
    declared_content_hash: str
    schema_id: str
    operation: ArtifactOperation = ArtifactOperation.PUBLISH


@dataclass(frozen=True, slots=True)
class InspectArtifactRequest:
    """Request to inspect artifact metadata."""

    account_id: str
    workspace_path: Path
    artifact_id: str
    operation: ArtifactOperation = ArtifactOperation.INSPECT


@dataclass(frozen=True, slots=True)
class DownloadGrant:
    """Server-issued bounded download authorization."""

    grant_id: str
    artifact_id: str
    account_id: str
    principal_id: str
    expires_at: datetime
    content_hash: str
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class IssueDownloadGrantRequest:
    """Request a bounded server-side download grant."""

    request_id: str
    actor_id: str
    workspace_path: Path
    account_id: str
    principal_id: str
    artifact_id: str
    expires_at: datetime
    operation: ArtifactOperation = ArtifactOperation.ISSUE_DOWNLOAD_GRANT


@dataclass(frozen=True, slots=True)
class ResolveDownloadRequest:
    """Resolve a previously issued bounded download grant."""

    workspace_path: Path
    account_id: str
    principal_id: str
    grant: DownloadGrant
    operation: ArtifactOperation = ArtifactOperation.RESOLVE_DOWNLOAD


@dataclass(frozen=True, slots=True)
class ArtifactDownload:
    """Verified download bytes and metadata."""

    artifact: ArtifactRecord
    content: bytes
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class ChangeReferenceRequest:
    """Add or remove one semantic artifact reference."""

    request_id: str
    actor_id: str
    account_id: str
    workspace_path: Path
    artifact_id: str
    reference_id: str
    owner_id: str
    add: bool = True
    operation: ArtifactOperation = ArtifactOperation.ADD_REFERENCE


@dataclass(frozen=True, slots=True)
class ChangeHoldRequest:
    """Add or release one legal/retention hold."""

    request_id: str
    actor_id: str
    account_id: str
    workspace_path: Path
    artifact_id: str
    hold_id: str
    owner_id: str
    add: bool = True
    operation: ArtifactOperation = ArtifactOperation.ADD_HOLD


@dataclass(frozen=True, slots=True)
class CleanupArtifactsRequest:
    """Request bounded cleanup of unreferenced, unheld artifact records."""

    request_id: str
    actor_id: str
    account_id: str
    workspace_path: Path
    max_items: int = 100
    operation: ArtifactOperation = ArtifactOperation.CLEANUP


@dataclass(frozen=True, slots=True)
class ArtifactMutationReceipt:
    """Receipt for a reference/hold mutation."""

    artifact_id: str
    changed: bool
    action: str
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class CleanupReceipt:
    """Bounded cleanup receipt."""

    removed_artifact_ids: tuple[str, ...]
    inspected_count: int
    schema_version: int = 1


ArtifactRequest = (
    PublishArtifactRequest
    | InspectArtifactRequest
    | IssueDownloadGrantRequest
    | ResolveDownloadRequest
    | ChangeReferenceRequest
    | ChangeHoldRequest
    | CleanupArtifactsRequest
)
ArtifactResult = (
    CustodyReceipt
    | ArtifactRecord
    | DownloadGrant
    | ArtifactDownload
    | ArtifactMutationReceipt
    | CleanupReceipt
)


@runtime_checkable
class ArtifactCapability(Protocol):
    """Public artifact-custody capability."""

    async def manage_artifact(self, request: ArtifactRequest) -> ArtifactResult:
        """Execute one scoped artifact operation."""
        ...


__all__ = [
    "ArtifactCapability",
    "ArtifactDownload",
    "ArtifactMutationReceipt",
    "ArtifactOperation",
    "ArtifactRecord",
    "ArtifactRequest",
    "ArtifactResult",
    "ChangeHoldRequest",
    "ChangeReferenceRequest",
    "CleanupArtifactsRequest",
    "CleanupReceipt",
    "CustodyReceipt",
    "DownloadGrant",
    "InspectArtifactRequest",
    "IssueDownloadGrantRequest",
    "PublishArtifactRequest",
    "ResolveDownloadRequest",
]
