"""Immutable contracts for point-in-time research-source evidence."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Literal

from app.services.data.contracts.errors import DataError
from app.utils import canonical_digest, generate_id

type SourceKind = Literal[
    "filing", "statement", "transcript", "macro", "news", "social", "alternative"
]
type TrustStatus = Literal["trusted", "unverified", "rejected"]
type EligibilityStatus = Literal["eligible", "ineligible"]
type RecordStatus = Literal["active", "superseded", "tombstoned"]
type JSONScalar = None | bool | int | float | str

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ALLOWED_SCHEMES = ("https://",)
_MAX_TEXT_LENGTH = 1_024
_MAX_SOURCE_BYTES = 1_048_576
_MAX_PAGE_RECORDS = 200


def _text(value: str, field: str) -> str:
    """Return validated bounded text.

    Args:
        value: Candidate text.
        field: Public-safe field label.

    Returns:
        Validated text.

    Raises:
        DataError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip() or len(value) > _MAX_TEXT_LENGTH:
        raise DataError("INVALID_INPUT", safe_details={"field": field})
    return value


def _utc(value: datetime, field: str) -> datetime:
    """Return one validated UTC instant.

    Args:
        value: Candidate instant.
        field: Public-safe field label.

    Returns:
        Validated UTC instant.

    Raises:
        DataError: If the instant is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise DataError("INVALID_INPUT", safe_details={"field": field})
    return value


def _hash(value: str, field: str) -> str:
    """Return one validated SHA-256 digest.

    Args:
        value: The ``value`` argument.
        field: The ``field`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    if _SHA256.fullmatch(value) is None:
        raise DataError("INVALID_INPUT", safe_details={"field": field})
    return value


@dataclass(frozen=True, slots=True)
class ResearchSourcePolicy:
    """Governed source-use and retention policy."""

    policy_id: str
    source_id: str
    allowed_hosts: tuple[str, ...]
    permitted_environments: tuple[str, ...]
    permitted_uses: tuple[str, ...]
    geography: tuple[str, ...]
    training_allowed: bool
    retention_days: int
    rate_limit: int
    rate_window_seconds: float
    expires_at: datetime | None
    minimum_trust: TrustStatus = "trusted"

    def __post_init__(self) -> None:
        """Validate the closed source policy.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        _text(self.policy_id, "policy_id")
        _text(self.source_id, "source_id")
        if (
            not self.allowed_hosts
            or any(not host or "/" in host for host in self.allowed_hosts)
            or not self.permitted_environments
            or not self.permitted_uses
            or self.retention_days <= 0
            or self.rate_limit <= 0
            or self.rate_window_seconds <= 0
        ):
            raise DataError("INVALID_INPUT", safe_details={"field": "source_policy"})
        if self.expires_at is not None:
            _utc(self.expires_at, "expires_at")


@dataclass(frozen=True, slots=True)
class ResearchSourceIngestRequest:
    """Bounded request to retrieve and persist one official source document."""

    source_url: str
    source_id: str
    source_kind: SourceKind
    external_id: str
    title: str
    asset_scope: tuple[str, ...]
    issuer_scope: tuple[str, ...]
    language: str
    event_at: datetime | None
    published_at: datetime
    available_at: datetime
    decision_use: str
    environment: str
    license_id: str
    currency: str | None
    unit: str | None
    request_id: str
    timeout_seconds: float = 10.0
    max_bytes: int = 262_144

    def __post_init__(self) -> None:
        """Validate the acquisition request without opening a socket.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        if not self.source_url.startswith(_ALLOWED_SCHEMES):
            raise DataError("INVALID_INPUT", safe_details={"field": "source_url"})
        for value, field in (
            (self.source_id, "source_id"),
            (self.external_id, "external_id"),
            (self.title, "title"),
            (self.language, "language"),
            (self.decision_use, "decision_use"),
            (self.environment, "environment"),
            (self.license_id, "license_id"),
            (self.request_id, "request_id"),
        ):
            _text(value, field)
        _utc(self.published_at, "published_at")
        _utc(self.available_at, "available_at")
        if self.event_at is not None:
            _utc(self.event_at, "event_at")
        if self.available_at < self.published_at:
            raise DataError(
                "INVALID_INPUT", safe_details={"field": "availability_order"}
            )
        if self.timeout_seconds <= 0 or not 0 < self.max_bytes <= _MAX_SOURCE_BYTES:
            raise DataError("LIMIT_EXCEEDED")


@dataclass(frozen=True, slots=True)
class ResearchSourceDocument:
    """Immutable point-in-time source identity and integrity evidence."""

    document_id: str
    source_id: str
    source_kind: SourceKind
    document_kind: str
    external_id: str
    title: str
    source_url: str
    asset_scope: tuple[str, ...]
    issuer_scope: tuple[str, ...]
    macro_series_scope: tuple[str, ...]
    language: str
    event_at: datetime | None
    published_at: datetime
    first_seen_at: datetime
    available_at: datetime
    retrieved_at: datetime
    revision: int
    previous_document_id: str | None
    original_hash: str
    normalized_hash: str
    license_id: str
    parser_version: str
    record_status: RecordStatus
    retention_until: datetime
    trust_status: TrustStatus
    manipulation_status: Literal["clear", "suspected", "confirmed"]
    injection_status: Literal["clear", "suspected", "unsafe"]
    currency: str | None
    unit: str | None
    provenance: Mapping[str, JSONScalar]

    def __post_init__(self) -> None:
        """Validate immutable source lineage.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        for value, field in (
            (self.document_id, "document_id"),
            (self.source_id, "source_id"),
            (self.document_kind, "document_kind"),
            (self.external_id, "external_id"),
            (self.title, "title"),
            (self.source_url, "source_url"),
            (self.language, "language"),
            (self.license_id, "license_id"),
            (self.parser_version, "parser_version"),
        ):
            _text(value, field)
        for instant, field in (
            (self.published_at, "published_at"),
            (self.first_seen_at, "first_seen_at"),
            (self.available_at, "available_at"),
            (self.retrieved_at, "retrieved_at"),
            (self.retention_until, "retention_until"),
        ):
            _utc(instant, field)
        if self.event_at is not None:
            _utc(self.event_at, "event_at")
        _hash(self.original_hash, "original_hash")
        _hash(self.normalized_hash, "normalized_hash")
        if self.revision <= 0 or self.available_at > self.retrieved_at:
            raise DataError("INVALID_INPUT", safe_details={"field": "revision_lineage"})
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True, slots=True)
class ResearchSourceObservation:
    """Immutable point-in-time structured observation."""

    observation_id: str
    document_id: str
    source_id: str
    series_id: str
    observation_period: str
    value: JSONScalar
    unit: str | None
    published_at: datetime
    available_at: datetime
    retrieved_at: datetime
    revision: int
    previous_observation_id: str | None
    content_hash: str
    parser_version: str
    trust_status: TrustStatus
    provenance: Mapping[str, JSONScalar]

    def __post_init__(self) -> None:
        """Validate immutable observation lineage.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        for value, field in (
            (self.observation_id, "observation_id"),
            (self.document_id, "document_id"),
            (self.source_id, "source_id"),
            (self.series_id, "series_id"),
            (self.observation_period, "observation_period"),
            (self.parser_version, "parser_version"),
        ):
            _text(value, field)
        for instant, field in (
            (self.published_at, "published_at"),
            (self.available_at, "available_at"),
            (self.retrieved_at, "retrieved_at"),
        ):
            _utc(instant, field)
        if self.revision <= 0 or self.available_at > self.retrieved_at:
            raise DataError(
                "INVALID_INPUT", safe_details={"field": "observation_lineage"}
            )
        _hash(self.content_hash, "content_hash")
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))


@dataclass(frozen=True, slots=True)
class VerifiedResearchSource:
    """Immutable evidence that one provider parser was verified."""

    source_id: str
    verified_at: datetime
    external_record_id: str
    parser_version: str
    fixture_sha256: str
    environments: tuple[str, ...]
    license_policy: str

    def __post_init__(self) -> None:
        """Validate verified-source evidence.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        for value, field in (
            (self.source_id, "source_id"),
            (self.external_record_id, "external_record_id"),
            (self.parser_version, "parser_version"),
            (self.license_policy, "license_policy"),
        ):
            _text(value, field)
        _utc(self.verified_at, "verified_at")
        _hash(self.fixture_sha256, "fixture_sha256")
        if not self.environments:
            raise DataError("INVALID_INPUT", safe_details={"field": "environments"})


@dataclass(frozen=True, slots=True)
class ResearchSourceQuery:
    """Decision-time query with deterministic bounded pagination."""

    decision_time: datetime
    source_kinds: tuple[SourceKind, ...] = ()
    asset_scope: tuple[str, ...] = ()
    issuer_scope: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    language: str | None = None
    minimum_trust: TrustStatus = "trusted"
    require_injection_clear: bool = True
    limit: int = 50
    cursor: str | None = None
    request_id: str = dataclass_field(default_factory=lambda: generate_id("req"))

    def __post_init__(self) -> None:
        """Validate query time, filters, and bounds.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        _utc(self.decision_time, "decision_time")
        _text(self.request_id, "request_id")
        if not 0 < self.limit <= _MAX_PAGE_RECORDS:
            raise DataError("LIMIT_EXCEEDED")
        if self.cursor is not None and (
            not self.cursor.isdigit() or int(self.cursor) < 0
        ):
            raise DataError("INVALID_INPUT", safe_details={"field": "cursor"})


@dataclass(frozen=True, slots=True)
class ResearchSourcePage:
    """Detached ordered source page."""

    records: tuple[ResearchSourceDocument, ...]
    next_cursor: str | None
    decision_time: datetime
    query_hash: str

    def __post_init__(self) -> None:
        """Validate page identity and detach ordered records.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        _utc(self.decision_time, "decision_time")
        _hash(self.query_hash, "query_hash")
        if len(self.records) > _MAX_PAGE_RECORDS:
            raise DataError("LIMIT_EXCEEDED")


@dataclass(frozen=True, slots=True)
class ResearchSourceEligibility:
    """Typed source eligibility decision."""

    status: EligibilityStatus
    reasons: tuple[str, ...]
    document_id: str
    decision_time: datetime

    def __post_init__(self) -> None:
        """Validate eligibility consistency.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        _text(self.document_id, "document_id")
        _utc(self.decision_time, "decision_time")
        if (self.status == "eligible") == bool(self.reasons):
            raise DataError("INVALID_INPUT", safe_details={"field": "eligibility"})


def query_digest(query: ResearchSourceQuery) -> str:
    """Return the canonical query identity.

    Args:
        query: The ``query`` argument.

    Returns:
        The result produced by the operation.
    """
    return canonical_digest(
        {
            "decision_time": query.decision_time,
            "source_kinds": query.source_kinds,
            "asset_scope": query.asset_scope,
            "issuer_scope": query.issuer_scope,
            "source_ids": query.source_ids,
            "language": query.language,
            "minimum_trust": query.minimum_trust,
            "require_injection_clear": query.require_injection_clear,
            "limit": query.limit,
            "cursor": query.cursor,
        }
    )


__all__ = (
    "ResearchSourceDocument",
    "ResearchSourceEligibility",
    "ResearchSourceIngestRequest",
    "ResearchSourceObservation",
    "ResearchSourcePage",
    "ResearchSourcePolicy",
    "ResearchSourceQuery",
    "VerifiedResearchSource",
    "query_digest",
)
