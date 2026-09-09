"""Public contract for immutable artifact custody and bounded downloads.

The ``workspace.artifacts@1`` capability stages, validates, and atomically
publishes immutable artifact bytes inside a Workspace-owned custody root,
retains referenced artifacts and legal holds, and resolves authorized
bounded download grants. Public callers exchange semantic artifact
identities and grants only; host filesystem paths never cross this
boundary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.contracts.workspace.errors import WorkspaceError

# Semantic artifact identities are opaque tokens. They must never contain
# path separators, drive/UNC markers, whitespace, or any character that a
# filesystem could interpret as traversal, so path-like inputs fail at
# validation before any custody-root path is derived.
ARTIFACT_ID_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

# Content hashes are lowercase hex SHA-256 digests prefixed with "sha256:".
CONTENT_HASH_PATTERN: re.Pattern[str] = re.compile(r"^sha256:[0-9a-f]{64}$")

# Schema/media declarations follow RFC 6838 media-type syntax
# ("type/subtype" with restricted token characters) so unsupported or
# malformed declarations fail closed before publication.
SCHEMA_DECLARATION_PATTERN: re.Pattern[str] = re.compile(
    r"^[a-z0-9][a-z0-9!#$&^_.+-]{0,126}/[a-z0-9][a-z0-9!#$&^_.+-]{0,126}$"
)

_GENERIC_ID_PATTERN: re.Pattern[str] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
)


class ManageArtifactsOperation(StrEnum):
    """Operations supported by ``workspace.artifacts@1``."""

    PUBLISH_ARTIFACT = "PUBLISH_ARTIFACT"
    INSPECT_ARTIFACT = "INSPECT_ARTIFACT"
    AUTHORIZE_DOWNLOAD = "AUTHORIZE_DOWNLOAD"
    RESOLVE_DOWNLOAD = "RESOLVE_DOWNLOAD"
    ADD_REFERENCE = "ADD_REFERENCE"
    REMOVE_REFERENCE = "REMOVE_REFERENCE"
    SET_LEGAL_HOLD = "SET_LEGAL_HOLD"
    RECONCILE_CUSTODY = "RECONCILE_CUSTODY"


class ArtifactCustodyState(StrEnum):
    """Durable classification states for artifact custody objects.

    Every durable row must classify into exactly one of these states at
    restart; unknown or missing state is never treated as published.
    """

    STAGING_INCOMPLETE = "STAGING_INCOMPLETE"
    BYTES_READY_METADATA_PENDING = "BYTES_READY_METADATA_PENDING"
    PUBLISHED_VALID = "PUBLISHED_VALID"


class ArtifactValidationError(WorkspaceError):
    """Raised when artifact request data violates the strict identity rules.

    Path-like artifact identities (traversal strings, Windows drive paths,
    UNC shares), malformed content hashes, invalid schema declarations, and
    missing or negative byte counts all fail with this typed error before
    any filesystem or database effect occurs.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize the artifact validation error.

        Args:
            message: Human-readable validation failure description.
            field: Optional request field that failed validation.
        """
        self.field = field
        detail = f" (field={field})" if field else ""
        super().__init__(f"{message}{detail}", error_code="ARTIFACT_VALIDATION_FAILED")


class ArtifactPublicationConflictError(WorkspaceError):
    """Raised when a publication conflicts with immutable custody state.

    Covers replaying an idempotency key with changed semantics and
    publishing an already-published artifact identity with different
    content; neither case may overwrite the existing publication.
    """

    def __init__(self, artifact_id: str, reason: str) -> None:
        """Initialize the publication conflict error.

        Args:
            artifact_id: The conflicting artifact identity.
            reason: Bounded conflict reason (no paths or payload data).
        """
        self.artifact_id = artifact_id
        self.reason = reason
        super().__init__(
            f"Publication conflict for {artifact_id!r}: {reason}",
            error_code="ARTIFACT_PUBLICATION_CONFLICT",
        )


class ArtifactNotFoundError(WorkspaceError):
    """Raised when a referenced artifact identity has no published record."""

    def __init__(self, artifact_id: str) -> None:
        """Initialize the artifact not found error.

        Args:
            artifact_id: The unresolved artifact identity.
        """
        self.artifact_id = artifact_id
        super().__init__(
            f"Artifact not found: {artifact_id!r}",
            error_code="ARTIFACT_NOT_FOUND",
        )


class ArtifactAccessDeniedError(WorkspaceError):
    """Raised when a download is requested outside its authorized scope.

    Cross-account access, wrong-principal grants, and grants whose
    presented fields do not exactly match durable grant state fail with
    this typed denial; no host path is disclosed and no bytes are
    returned.
    """

    def __init__(self, artifact_id: str, reason: str) -> None:
        """Initialize the artifact access denied error.

        Args:
            artifact_id: The requested artifact identity.
            reason: Bounded denial reason (no paths or payload data).
        """
        self.artifact_id = artifact_id
        self.reason = reason
        super().__init__(
            f"Artifact access denied for {artifact_id!r}: {reason}",
            error_code="ARTIFACT_ACCESS_DENIED",
        )


class ArtifactGrantExpiredError(WorkspaceError):
    """Raised when a download grant is resolved after its expiry."""

    def __init__(self, grant_id: str, expired_at: str) -> None:
        """Initialize the artifact grant expired error.

        Args:
            grant_id: The expired grant identity.
            expired_at: ISO 8601 UTC expiry timestamp that elapsed.
        """
        self.grant_id = grant_id
        self.expired_at = expired_at
        super().__init__(
            f"Download grant expired at {expired_at}",
            error_code="ARTIFACT_GRANT_EXPIRED",
        )


class ArtifactIntegrityError(WorkspaceError):
    """Raised when custody bytes fail immutable checksum verification.

    Published metadata whose object file is missing, truncated, hash
    mismatched, or replaced by a symlink/reparse point fails closed with
    this typed integrity incident; the artifact is never reported valid.
    """

    def __init__(self, artifact_id: str, reason: str) -> None:
        """Initialize the artifact integrity error.

        Args:
            artifact_id: The artifact whose custody bytes failed
                verification.
            reason: Bounded integrity failure reason (no paths).
        """
        self.artifact_id = artifact_id
        self.reason = reason
        super().__init__(
            f"Artifact integrity failure for {artifact_id!r}: {reason}",
            error_code="ARTIFACT_INTEGRITY",
        )


class ArtifactAdmissionUnavailableError(WorkspaceError):
    """Raised when a heavy operation cannot obtain resource admission.

    Publication and custody maintenance request a finite resource
    admission lease before touching the custody root. When the admission
    provider is absent or refuses/queues the request, the operation fails
    closed with this typed error instead of attempting unadmitted work.
    """

    def __init__(self, operation: ManageArtifactsOperation, reason: str) -> None:
        """Initialize the admission unavailable error.

        Args:
            operation: The heavy operation that could not be admitted.
            reason: Bounded unavailability reason.
        """
        self.operation = operation
        self.reason = reason
        super().__init__(
            f"Resource admission unavailable for {operation.value}: {reason}",
            error_code="ARTIFACT_ADMISSION_UNAVAILABLE",
        )


def _require_token(value: str, field_name: str) -> None:
    """Validate one non-empty generic identifier field.

    Args:
        value: Identifier value under validation.
        field_name: Field name for error reporting.

    Raises:
        ArtifactValidationError: If the value is empty or malformed.
    """
    if not isinstance(value, str) or not _GENERIC_ID_PATTERN.match(value):
        message = f"{field_name} must match {field_name} token rules"
        raise ArtifactValidationError(message, field=field_name)


@dataclass(frozen=True, slots=True)
class ArtifactPublication:
    """Declaration of one immutable artifact publication.

    Attributes:
        artifact_id: Opaque semantic artifact identity (never a path).
        workspace_id: Owning workspace scope.
        account_id: Owning account scope.
        schema_declaration: RFC 6838 media-type schema declaration.
        byte_count: Exact expected payload size in bytes.
        content_hash: ``sha256:``-prefixed lowercase hex SHA-256 digest.
        idempotency_key: Caller-supplied logical publication identity.
        source_reference: Immutable owner reference that produced the
            artifact (for example a run or databank record identity).
    """

    artifact_id: str
    workspace_id: str
    account_id: str
    schema_declaration: str
    byte_count: int
    content_hash: str
    idempotency_key: str
    source_reference: str

    def __post_init__(self) -> None:
        """Validate the publication declaration.

        Raises:
            ArtifactValidationError: If any identity, hash, schema, or size
                field violates its strict rule.
        """
        if not isinstance(self.artifact_id, str) or not ARTIFACT_ID_PATTERN.match(
            self.artifact_id
        ):
            raise ArtifactValidationError(
                "artifact_id must be an opaque token without path characters",
                field="artifact_id",
            )
        for field_name in ("workspace_id", "account_id"):
            _require_token(getattr(self, field_name), field_name)
        if not isinstance(self.schema_declaration, str) or (
            not SCHEMA_DECLARATION_PATTERN.match(self.schema_declaration)
        ):
            raise ArtifactValidationError(
                "schema_declaration must be a media-type token pair",
                field="schema_declaration",
            )
        if isinstance(self.byte_count, bool) or not isinstance(self.byte_count, int):
            raise ArtifactValidationError(
                "byte_count must be an integer", field="byte_count"
            )
        if self.byte_count < 1:
            raise ArtifactValidationError(
                "byte_count must be a positive finite size", field="byte_count"
            )
        if not isinstance(self.content_hash, str) or not CONTENT_HASH_PATTERN.match(
            self.content_hash
        ):
            raise ArtifactValidationError(
                "content_hash must be 'sha256:' followed by 64 lowercase hex digits",
                field="content_hash",
            )
        _require_token(self.idempotency_key, "idempotency_key")
        _require_token(self.source_reference, "source_reference")


@dataclass(frozen=True, slots=True)
class PublishArtifactRequest:
    """Request to stage, validate, and atomically publish artifact bytes."""

    request_id: str
    actor_id: str
    publication: ArtifactPublication
    payload: bytes

    def __post_init__(self) -> None:
        """Validate the publication request shape.

        Raises:
            ArtifactValidationError: If identifiers are malformed or the
                payload is not bytes.
        """
        _require_token(self.request_id, "request_id")
        _require_token(self.actor_id, "actor_id")
        if not isinstance(self.payload, bytes):
            raise ArtifactValidationError(
                "payload must be an immutable bytes buffer", field="payload"
            )


@dataclass(frozen=True, slots=True)
class CustodyReceipt:
    """Immutable receipt issued for one completed artifact publication."""

    artifact_id: str
    content_hash: str
    byte_count: int
    schema_declaration: str
    idempotency_key: str
    storage_revision: int
    published_at: str


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    """Inspection view of one published artifact's custody metadata."""

    artifact_id: str
    workspace_id: str
    account_id: str
    schema_declaration: str
    byte_count: int
    content_hash: str
    state: ArtifactCustodyState
    reference_count: int
    legal_hold: bool
    storage_revision: int
    published_at: str


@dataclass(frozen=True, slots=True)
class InspectArtifactRequest:
    """Request to inspect one artifact's custody metadata."""

    request_id: str
    actor_id: str
    artifact_id: str
    workspace_id: str
    account_id: str

    def __post_init__(self) -> None:
        """Validate the inspection request.

        Raises:
            ArtifactValidationError: If any identifier is malformed.
        """
        for field_name in ("request_id", "actor_id"):
            _require_token(getattr(self, field_name), field_name)
        if not isinstance(self.artifact_id, str) or not ARTIFACT_ID_PATTERN.match(
            self.artifact_id
        ):
            raise ArtifactValidationError(
                "artifact_id must be an opaque token without path characters",
                field="artifact_id",
            )
        for field_name in ("workspace_id", "account_id"):
            _require_token(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class AuthorizeDownloadRequest:
    """Request to create one bounded download grant."""

    request_id: str
    actor_id: str
    artifact_id: str
    workspace_id: str
    account_id: str
    principal_id: str
    ttl_seconds: int

    def __post_init__(self) -> None:
        """Validate the grant authorization request.

        Raises:
            ArtifactValidationError: If identifiers are malformed or the
                TTL is not a positive bounded integer.
        """
        for field_name in ("request_id", "actor_id", "principal_id"):
            _require_token(getattr(self, field_name), field_name)
        if not isinstance(self.artifact_id, str) or not ARTIFACT_ID_PATTERN.match(
            self.artifact_id
        ):
            raise ArtifactValidationError(
                "artifact_id must be an opaque token without path characters",
                field="artifact_id",
            )
        for field_name in ("workspace_id", "account_id"):
            _require_token(getattr(self, field_name), field_name)
        if isinstance(self.ttl_seconds, bool) or not isinstance(self.ttl_seconds, int):
            raise ArtifactValidationError(
                "ttl_seconds must be an integer", field="ttl_seconds"
            )
        if self.ttl_seconds < 1:
            raise ArtifactValidationError(
                "ttl_seconds must be positive and bounded", field="ttl_seconds"
            )


@dataclass(frozen=True, slots=True)
class DownloadGrant:
    """Bounded authorization to download one artifact's bytes.

    Every field is validated against durable grant state at resolution
    time; any drift (forged or mutated grant) fails as a typed denial.
    """

    grant_id: str
    artifact_id: str
    workspace_id: str
    account_id: str
    principal_id: str
    action: str
    expires_at: str
    generation: int

    def __post_init__(self) -> None:
        """Validate the grant shape.

        Raises:
            ArtifactValidationError: If identifiers are malformed, the
                action is not ``DOWNLOAD``, or the generation is not a
                positive integer.
        """
        for field_name in ("grant_id", "principal_id"):
            _require_token(getattr(self, field_name), field_name)
        if not isinstance(self.artifact_id, str) or not ARTIFACT_ID_PATTERN.match(
            self.artifact_id
        ):
            raise ArtifactValidationError(
                "artifact_id must be an opaque token without path characters",
                field="artifact_id",
            )
        for field_name in ("workspace_id", "account_id", "expires_at"):
            if (
                not isinstance(getattr(self, field_name), str)
                or not getattr(self, field_name).strip()
            ):
                message = f"{field_name} must be a non-empty string"
                raise ArtifactValidationError(message, field=field_name)
        if self.action != "DOWNLOAD":
            raise ArtifactValidationError(
                "grant action must be DOWNLOAD", field="action"
            )
        if isinstance(self.generation, bool) or not isinstance(self.generation, int):
            raise ArtifactValidationError(
                "generation must be an integer", field="generation"
            )
        if self.generation < 1:
            raise ArtifactValidationError(
                "generation must be positive", field="generation"
            )


@dataclass(frozen=True, slots=True)
class ResolveDownloadRequest:
    """Request to resolve one bounded download grant into bytes."""

    request_id: str
    grant: DownloadGrant
    workspace_id: str
    account_id: str
    principal_id: str

    def __post_init__(self) -> None:
        """Validate the resolution request.

        Raises:
            ArtifactValidationError: If identifiers are malformed.
        """
        _require_token(self.request_id, "request_id")
        for field_name in ("workspace_id", "account_id", "principal_id"):
            _require_token(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class ResolvedDownload:
    """Authorized artifact bytes with their immutable custody identity."""

    artifact_id: str
    content_hash: str
    byte_count: int
    schema_declaration: str
    payload: bytes


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """One semantic reference that retains an artifact's bytes."""

    reference_id: str
    artifact_id: str
    owner_namespace: str
    owner_record_id: str
    created_at: str

    def __post_init__(self) -> None:
        """Validate the reference shape.

        Raises:
            ArtifactValidationError: If identifiers are malformed.
        """
        if not isinstance(self.reference_id, str) or not ARTIFACT_ID_PATTERN.match(
            self.reference_id
        ):
            raise ArtifactValidationError(
                "reference_id must be an opaque token without path characters",
                field="reference_id",
            )
        if not isinstance(self.artifact_id, str) or not ARTIFACT_ID_PATTERN.match(
            self.artifact_id
        ):
            raise ArtifactValidationError(
                "artifact_id must be an opaque token without path characters",
                field="artifact_id",
            )
        for field_name in ("owner_namespace", "owner_record_id"):
            _require_token(getattr(self, field_name), field_name)


@dataclass(frozen=True, slots=True)
class AddReferenceRequest:
    """Request to retain an artifact under one new semantic reference."""

    request_id: str
    actor_id: str
    workspace_id: str
    reference: ArtifactReference

    def __post_init__(self) -> None:
        """Validate the add-reference request.

        Raises:
            ArtifactValidationError: If identifiers are malformed.
        """
        _require_token(self.request_id, "request_id")
        _require_token(self.actor_id, "actor_id")
        _require_token(self.workspace_id, "workspace_id")


@dataclass(frozen=True, slots=True)
class RemoveReferenceRequest:
    """Request to remove one semantic reference under a revision fence."""

    request_id: str
    actor_id: str
    reference_id: str
    expected_revision: int

    def __post_init__(self) -> None:
        """Validate the remove-reference request.

        Raises:
            ArtifactValidationError: If identifiers are malformed or the
                expected revision is not positive.
        """
        _require_token(self.request_id, "request_id")
        _require_token(self.actor_id, "actor_id")
        if not isinstance(self.reference_id, str) or not ARTIFACT_ID_PATTERN.match(
            self.reference_id
        ):
            raise ArtifactValidationError(
                "reference_id must be an opaque token without path characters",
                field="reference_id",
            )
        if isinstance(self.expected_revision, bool) or not isinstance(
            self.expected_revision, int
        ):
            raise ArtifactValidationError(
                "expected_revision must be an integer", field="expected_revision"
            )
        if self.expected_revision < 1:
            raise ArtifactValidationError(
                "expected_revision must be positive", field="expected_revision"
            )


@dataclass(frozen=True, slots=True)
class SetLegalHoldRequest:
    """Request to set or clear one artifact's legal hold under a fence."""

    request_id: str
    actor_id: str
    workspace_id: str
    artifact_id: str
    hold: bool
    expected_revision: int

    def __post_init__(self) -> None:
        """Validate the legal-hold request.

        Raises:
            ArtifactValidationError: If identifiers are malformed, the hold
                flag is not a boolean, or the expected revision is not
                positive.
        """
        _require_token(self.request_id, "request_id")
        _require_token(self.actor_id, "actor_id")
        _require_token(self.workspace_id, "workspace_id")
        if not isinstance(self.artifact_id, str) or not ARTIFACT_ID_PATTERN.match(
            self.artifact_id
        ):
            raise ArtifactValidationError(
                "artifact_id must be an opaque token without path characters",
                field="artifact_id",
            )
        if not isinstance(self.hold, bool):
            raise ArtifactValidationError("hold must be a boolean", field="hold")
        if isinstance(self.expected_revision, bool) or not isinstance(
            self.expected_revision, int
        ):
            raise ArtifactValidationError(
                "expected_revision must be an integer", field="expected_revision"
            )
        if self.expected_revision < 1:
            raise ArtifactValidationError(
                "expected_revision must be positive", field="expected_revision"
            )


@dataclass(frozen=True, slots=True)
class ReconcileCustodyRequest:
    """Request to run admitted custody maintenance and cleanup."""

    request_id: str
    actor_id: str

    def __post_init__(self) -> None:
        """Validate the reconciliation request.

        Raises:
            ArtifactValidationError: If identifiers are malformed.
        """
        _require_token(self.request_id, "request_id")
        _require_token(self.actor_id, "actor_id")


@dataclass(frozen=True, slots=True)
class CustodyReconciliationReport:
    """Audit report for one admitted custody reconciliation run."""

    finalized: tuple[str, ...]
    removed_staging: tuple[str, ...]
    removed_orphan_objects: tuple[str, ...]
    retained_referenced: tuple[str, ...]
    retained_legal_hold: tuple[str, ...]
    integrity_incidents: tuple[str, ...]
    revision: int
    receipt_evidence_id: str


@runtime_checkable
class ManageArtifactsCapability(Protocol):
    """Capability protocol for immutable artifact custody."""

    async def publish_artifact(
        self,
        request: PublishArtifactRequest,
    ) -> CustodyReceipt:
        """Stage, validate, and atomically publish one artifact.

        Args:
            request: Validated publication request with bounded payload.

        Returns:
            The immutable custody receipt for the published artifact.

        Raises:
            ArtifactValidationError: If declaration or payload validation
                fails (bad hash, truncation, invalid schema, path-like
                identity, oversized payload).
            ArtifactPublicationConflictError: If the idempotency key is
                replayed with changed semantics.
            ArtifactAdmissionUnavailableError: If resource admission for
                the heavy publication is unavailable or not admitted.
            WorkspaceError: If durable storage or custody I/O fails.
        """
        ...

    async def inspect_artifact(
        self,
        request: InspectArtifactRequest,
    ) -> ArtifactRecord:
        """Return one artifact's custody metadata.

        Args:
            request: Validated inspection request.

        Returns:
            The artifact's published custody metadata.

        Raises:
            ArtifactNotFoundError: If no published artifact exists for the
                identity in the requested scope.
            ArtifactValidationError: If identifiers are malformed.
        """
        ...

    async def authorize_download(
        self,
        request: AuthorizeDownloadRequest,
    ) -> DownloadGrant:
        """Create one bounded download grant.

        Args:
            request: Validated grant authorization request.

        Returns:
            The durable bounded download grant.

        Raises:
            ArtifactNotFoundError: If no published artifact exists for the
                identity in the requested scope.
            ArtifactValidationError: If identifiers or the TTL are invalid.
        """
        ...

    async def resolve_download(
        self,
        request: ResolveDownloadRequest,
    ) -> ResolvedDownload:
        """Resolve one bounded grant into verified artifact bytes.

        Args:
            request: Validated resolution request carrying the grant.

        Returns:
            The authorized artifact bytes and immutable custody identity;
            the returned payload always hashes to the stored checksum.

        Raises:
            ArtifactGrantExpiredError: If the grant is resolved after its
                expiry.
            ArtifactAccessDeniedError: If the grant scope, principal,
                generation, or revocation state denies resolution.
            ArtifactNotFoundError: If the artifact identity is unknown in
                the requested scope.
            ArtifactIntegrityError: If custody bytes fail checksum
                verification.
        """
        ...

    async def add_reference(
        self,
        request: AddReferenceRequest,
    ) -> ArtifactReference:
        """Retain an artifact under one new semantic reference.

        Args:
            request: Validated add-reference request.

        Returns:
            The stored semantic reference.

        Raises:
            ArtifactNotFoundError: If the artifact is not published in the
                referenced scope.
            WorkspaceError: If the reference already exists.
        """
        ...

    async def remove_reference(
        self,
        request: RemoveReferenceRequest,
    ) -> int:
        """Remove one semantic reference under a revision fence.

        Args:
            request: Validated remove-reference request.

        Returns:
            The artifact's storage revision after removal. Artifact bytes
            are never deleted by reference removal.

        Raises:
            ArtifactNotFoundError: If the reference or artifact is unknown.
            WorkspaceError: On revision conflict.
        """
        ...

    async def set_legal_hold(
        self,
        request: SetLegalHoldRequest,
    ) -> int:
        """Set or clear one artifact's legal hold under a revision fence.

        Args:
            request: Validated legal-hold request.

        Returns:
            The artifact's storage revision after the change.

        Raises:
            ArtifactNotFoundError: If the artifact is unknown.
            WorkspaceError: On revision conflict.
        """
        ...

    async def reconcile_custody(
        self,
        request: ReconcileCustodyRequest,
    ) -> CustodyReconciliationReport:
        """Run admitted custody maintenance and eligible cleanup.

        Args:
            request: Validated reconciliation request.

        Returns:
            The audit report for the bounded reconciliation run.

        Raises:
            ArtifactAdmissionUnavailableError: If resource admission for
                maintenance is unavailable or not admitted.
            WorkspaceError: If durable storage or custody I/O fails.
        """
        ...


__all__ = [
    "ARTIFACT_ID_PATTERN",
    "CONTENT_HASH_PATTERN",
    "SCHEMA_DECLARATION_PATTERN",
    "AddReferenceRequest",
    "ArtifactAccessDeniedError",
    "ArtifactAdmissionUnavailableError",
    "ArtifactCustodyState",
    "ArtifactGrantExpiredError",
    "ArtifactIntegrityError",
    "ArtifactNotFoundError",
    "ArtifactPublication",
    "ArtifactPublicationConflictError",
    "ArtifactRecord",
    "ArtifactReference",
    "ArtifactValidationError",
    "AuthorizeDownloadRequest",
    "CustodyReceipt",
    "CustodyReconciliationReport",
    "DownloadGrant",
    "InspectArtifactRequest",
    "ManageArtifactsCapability",
    "ManageArtifactsOperation",
    "PublishArtifactRequest",
    "ReconcileCustodyRequest",
    "RemoveReferenceRequest",
    "ResolvedDownload",
    "SetLegalHoldRequest",
]
