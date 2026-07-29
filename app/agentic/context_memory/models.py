"""Evidence claims, context bundles, and governed memory records.

Memory is separated into four stores with distinct durability and retention:
immutable `evidence`, `experiment`, operational `audit`, and bounded
disposable `working` memory. Corrections append; nothing overwrites history.

Memory is context, never evidence authority. A claim supported only by memory
is unsupported, and no memory record may carry an instruction, permission,
mandate, or threshold.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.utils import canonical_digest, get_logger

logger = get_logger(__name__)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 64

StoreClass = Literal["evidence", "experiment", "audit", "working"]
InjectionStatus = Literal["clean", "suspected", "stripped"]
SourceTrust = Literal["authoritative", "licensed", "public", "unverified"]

# Patterns that indicate retrieved text is trying to act as an instruction
# rather than as evidence. Detection is best-effort; the actual guarantee is
# structural — untrusted evidence never occupies an instruction slot.
_INSTRUCTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bignore (all |any )?(previous|prior|above)\b", re.IGNORECASE),
    re.compile(
        r"\bdisregard (the |your )?(instructions|policy|rules)\b", re.IGNORECASE
    ),
    re.compile(r"\byou are now\b", re.IGNORECASE),
    re.compile(r"\bsystem prompt\b", re.IGNORECASE),
    re.compile(r"\bnew instructions?\b", re.IGNORECASE),
    re.compile(r"\bact as\b", re.IGNORECASE),
    re.compile(r"\boverride\b.{0,20}\b(mandate|policy|permission)\b", re.IGNORECASE),
    re.compile(r"\bapprove\b.{0,20}\b(this|yourself|own)\b", re.IGNORECASE),
)

# Keys a memory record may never carry: memory cannot grant permission, create
# approval, alter a mandate or threshold, or change a model profile.
FORBIDDEN_MEMORY_KEYS: frozenset[str] = frozenset(
    {
        "mandate",
        "permission",
        "permissions",
        "approval",
        "attestation",
        "threshold",
        "model_profile",
        "system_prompt",
        "instruction",
        "kill_switch",
    },
)


def _text(value: str, field: str, *, limit: int = _MAX_TEXT) -> str:
    """Validate bounded non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.
        limit: Maximum permitted character count.

    Returns:
        Validated text.

    Raises:
        ValueError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    if len(value) > limit:
        message = f"{field} must not exceed {limit} characters"
        raise ValueError(message)
    return value


def _utc(value: datetime, field: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field: Safe field label for validation.

    Returns:
        Validated UTC timestamp.

    Raises:
        ValueError: If the value is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field} must be aware UTC"
        raise ValueError(message)
    return value


def _hash(value: str, field: str) -> str:
    """Validate lowercase SHA-256 hexadecimal.

    Args:
        value: Candidate digest.
        field: Safe field label for validation.

    Returns:
        Validated digest.

    Raises:
        ValueError: If the digest shape is invalid.
    """
    if _SHA256.fullmatch(value) is None:
        message = f"{field} must be lowercase SHA-256 hexadecimal"
        raise ValueError(message)
    return value


def classify_injection(text: str) -> InjectionStatus:
    """Classify whether retrieved text attempts to act as an instruction.

    Detection is best-effort and is never the security boundary; it labels
    evidence so a caller can exclude or quarantine it.

    Args:
        text: Candidate retrieved text.

    Returns:
        `suspected` when an instruction pattern matches, otherwise `clean`.
    """
    for pattern in _INSTRUCTION_PATTERNS:
        if pattern.search(text) is not None:
            logger.warning("Instruction pattern detected in retrieved evidence")
            return "suspected"
    return "clean"


class _MemoryModel(BaseModel):
    """Private strict immutable behaviour shared by context contracts."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class EvidenceClaim(_MemoryModel):
    """One source-backed material statement eligible for model context.

    Attributes:
        claim_id: Stable claim identity.
        task_id: Owning task identity.
        statement: Bounded material statement.
        source_ref: Owning-domain source reference.
        source_trust: Declared source trust class.
        licence_ref: Licence or usage-policy reference.
        available_at: UTC time the system could first have known this.
        observed_at: UTC time the system retrieved it.
        content_hash: Canonical digest of the original content.
        confidence_basis: Bounded statement of what supports the claim.
        falsifier: Bounded statement of what would refute the claim.
        injection_status: Injection classification of the source text.
    """

    claim_id: str
    task_id: str
    statement: str
    source_ref: str
    source_trust: SourceTrust
    licence_ref: str
    available_at: datetime
    observed_at: datetime
    content_hash: str
    confidence_basis: str
    falsifier: str
    injection_status: InjectionStatus

    @field_validator("claim_id", "task_id", "source_ref", "licence_ref")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded claim reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "claim reference", limit=_MAX_SHORT_TEXT)

    @field_validator("statement", "confidence_basis", "falsifier")
    @classmethod
    def _validate_prose(cls, value: str) -> str:
        """Validate one bounded claim prose field.

        Args:
            value: Candidate text.

        Returns:
            Validated text.
        """
        return _text(value, "claim text")

    @field_validator("available_at", "observed_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one claim timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "claim timestamp")

    @field_validator("content_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate the original-content digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "content_hash")

    @model_validator(mode="after")
    def _validate_lineage(self) -> Self:
        """Validate that availability precedes observation.

        Returns:
            The validated claim.

        Raises:
            ValueError: If the claim was observed before it was available.
        """
        if self.observed_at < self.available_at:
            message = "observed_at must not precede available_at"
            raise ValueError(message)
        return self


class MemoryRecord(_MemoryModel):
    """One governed memory write in a declared store.

    Attributes:
        record_id: Stable record identity.
        store_class: Owning store.
        task_id: Owning task identity.
        scope: Governed scope the record belongs to.
        author_role_id: Registered role that proposed the write.
        content: Bounded redacted JSON-safe content.
        source_evidence_refs: Supporting evidence references.
        created_at: UTC write time.
        expires_at: UTC expiry for TTL-bound stores.
        retention_class: Declared retention class.
        sensitivity: Declared sensitivity class.
        injection_status: Injection classification of the written content.
        redacted_paths: Paths redacted before persistence.
        content_hash: Canonical digest of the written content.
        supersedes: Record this one corrects, when appending a correction.
    """

    record_id: str
    store_class: StoreClass
    task_id: str
    scope: Mapping[str, str]
    author_role_id: str
    content: Mapping[str, str]
    source_evidence_refs: tuple[str, ...]
    created_at: datetime
    expires_at: datetime | None = None
    retention_class: str
    sensitivity: Literal["public", "internal", "restricted"]
    injection_status: InjectionStatus
    redacted_paths: tuple[str, ...] = ()
    content_hash: str
    supersedes: str | None = None

    @field_validator("record_id", "task_id", "author_role_id", "retention_class")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded record reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "memory record reference", limit=_MAX_SHORT_TEXT)

    @field_validator("scope", "content")
    @classmethod
    def _validate_mapping(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze one bounded record mapping.

        Args:
            value: Candidate mapping.

        Returns:
            Frozen ordered mapping.

        Raises:
            ValueError: If the mapping is empty or oversized.
        """
        if not value:
            message = "memory record mapping is required"
            raise ValueError(message)
        if len(value) > _MAX_ITEMS:
            message = f"memory record mapping must not exceed {_MAX_ITEMS} keys"
            raise ValueError(message)
        frozen = {
            _text(key, "memory key", limit=_MAX_SHORT_TEXT): _text(
                item,
                "memory value",
            )
            for key, item in sorted(value.items())
        }
        return MappingProxyType(frozen)

    @field_validator("source_evidence_refs", "redacted_paths")
    @classmethod
    def _validate_refs(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate one bounded reference tuple.

        Args:
            value: Candidate references.

        Returns:
            Validated references.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"reference tuple must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(_text(item, "reference", limit=_MAX_SHORT_TEXT) for item in value)

    @field_validator("created_at")
    @classmethod
    def _validate_created(cls, value: datetime) -> datetime:
        """Validate the write timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "created_at")

    @field_validator("expires_at")
    @classmethod
    def _validate_expiry(cls, value: datetime | None) -> datetime | None:
        """Validate the optional expiry timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp, or None.
        """
        if value is None:
            return None
        return _utc(value, "expires_at")

    @field_validator("content_hash")
    @classmethod
    def _validate_hash(cls, value: str) -> str:
        """Validate the written-content digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "content_hash")

    @model_validator(mode="after")
    def _validate_record(self) -> Self:
        """Validate store rules and prohibited memory effects.

        Returns:
            The validated record.

        Raises:
            ValueError: If working memory lacks a TTL, an expiry precedes the
                write, or the content attempts a prohibited memory effect.
        """
        if self.store_class == "working" and self.expires_at is None:
            message = "working memory must declare a TTL expiry"
            raise ValueError(message)
        if self.expires_at is not None and self.expires_at <= self.created_at:
            message = "expires_at must follow created_at"
            raise ValueError(message)
        for key in self.content:
            lowered = key.lower()
            if any(token in lowered for token in FORBIDDEN_MEMORY_KEYS):
                message = (
                    f"memory content must not carry {key}; memory cannot grant "
                    "permission, create approval, or alter policy"
                )
                raise ValueError(message)
        return self

    @field_serializer("scope", "content", mode="plain")
    def _serialize_mapping(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize one record mapping deterministically.

        Args:
            value: Frozen mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


class ContextBundle(_MemoryModel):
    """One bounded eligible context set assembled for a governed task.

    Trusted structured context and untrusted evidence are separate fields by
    construction, so retrieved text can never occupy an instruction slot.

    Attributes:
        bundle_id: Stable bundle identity.
        task_id: Owning task identity.
        assembled_at: UTC assembly time.
        decision_time: Point-in-time boundary applied.
        trusted_context: Trusted structured context.
        untrusted_evidence: Ordered eligible evidence claims.
        excluded: Ordered (reference, enumerated reason) exclusions.
        token_budget: Deterministic token ceiling applied.
        token_estimate: Estimated tokens of the assembled bundle.
    """

    bundle_id: str
    task_id: str
    assembled_at: datetime
    decision_time: datetime
    trusted_context: Mapping[str, str]
    untrusted_evidence: tuple[EvidenceClaim, ...]
    excluded: tuple[tuple[str, str], ...]
    token_budget: int
    token_estimate: int

    @field_validator("bundle_id", "task_id")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded bundle reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "context bundle reference", limit=_MAX_SHORT_TEXT)

    @field_validator("assembled_at", "decision_time")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one bundle timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "context bundle timestamp")

    @field_validator("trusted_context")
    @classmethod
    def _validate_trusted(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the trusted structured context.

        Args:
            value: Candidate trusted context.

        Returns:
            Frozen ordered trusted context.
        """
        frozen = {
            _text(key, "trusted key", limit=_MAX_SHORT_TEXT): _text(
                item,
                "trusted value",
            )
            for key, item in sorted(value.items())
        }
        return MappingProxyType(frozen)

    @field_validator("token_budget", "token_estimate")
    @classmethod
    def _validate_tokens(cls, value: int) -> int:
        """Validate one token count.

        Args:
            value: Candidate token count.

        Returns:
            Validated token count.

        Raises:
            ValueError: If the count is negative.
        """
        if value < 0:
            message = "token counts must be non-negative"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_budget(self) -> Self:
        """Validate that the bundle respects its declared budget.

        Returns:
            The validated bundle.

        Raises:
            ValueError: If the estimate exceeds the budget.
        """
        if self.token_estimate > self.token_budget:
            message = "assembled context must not exceed its token budget"
            raise ValueError(message)
        return self

    @field_serializer("trusted_context", mode="plain")
    def _serialize_trusted(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize trusted context deterministically.

        Args:
            value: Frozen trusted context.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def build_evidence_claim(fields: Mapping[str, object]) -> EvidenceClaim:
    """Build one source-backed evidence claim.

    Args:
        fields: Complete claim fields.

    Returns:
        A validated immutable evidence claim.
    """
    return EvidenceClaim.model_validate(fields)


def build_memory_record(fields: Mapping[str, object]) -> MemoryRecord:
    """Build one governed memory record.

    Args:
        fields: Complete record fields.

    Returns:
        A validated immutable memory record.
    """
    logger.debug("Building an Agentic memory record")
    return MemoryRecord.model_validate(fields)


def derive_content_hash(value: object) -> str:
    """Derive the canonical digest of memory or evidence content.

    Args:
        value: JSON-safe content material.

    Returns:
        The canonical content digest.
    """
    return canonical_digest(value)
