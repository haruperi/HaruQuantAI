"""Immutable fundamental and sentiment evidence contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Literal

from app.kernel.serialization import canonical_digest
from app.services.research.contracts.errors import ValidationError

type JSONValue = (
    None | bool | int | float | str | tuple[str, ...] | Mapping[str, object]
)
type ApplicabilityStatus = Literal["applicable", "not_applicable"]
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_REFERENCES = 200


def _utc(value: datetime) -> None:
    """Validate one UTC instant.

    Raises:
        ValidationError: If the value is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValidationError("RES_INPUT_INVALID", "INTELLIGENCE_TIME_NOT_UTC")


def _hash(value: str) -> None:
    """Validate one canonical hash.

    Raises:
        ValidationError: If the value is not a SHA-256 digest.
    """
    if _SHA256.fullmatch(value) is None:
        raise ValidationError("RES_INPUT_INVALID", "INTELLIGENCE_HASH_INVALID")


@dataclass(frozen=True, slots=True)
class IntelligenceApplicability:
    """Typed applicability decision for one asset and evidence model."""

    status: ApplicabilityStatus
    asset_class: str
    model: Literal["issuer", "macro", "sentiment"]
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate applicability consistency.

        Raises:
            ValidationError: If status and reasons conflict.
        """
        if not self.asset_class or (self.status == "applicable") == bool(self.reasons):
            raise ValidationError("RES_INPUT_INVALID", "APPLICABILITY_INVALID")


@dataclass(frozen=True, slots=True)
class FundamentalSourceEvidence:
    """Bounded source-backed fundamental evidence."""

    contract_version: Literal["v1"]
    schema_id: Literal["research.fundamental_source_evidence.v1"]
    asset_scope: tuple[str, ...]
    issuer_scope: tuple[str, ...]
    document_references: tuple[str, ...]
    source_kinds: tuple[str, ...]
    observed_from: datetime
    available_by: datetime
    coverage: Mapping[str, int]
    revisions: Mapping[str, int]
    currency_lineage: Mapping[str, str | None]
    unit_lineage: Mapping[str, str | None]
    quality: Mapping[str, object]
    canonical_hash: str
    advisory_only: Literal[True] = True

    def __post_init__(self) -> None:
        """Validate evidence identity, bounds, and lineage.

        Raises:
            ValidationError: If evidence is invalid or oversized.
        """
        _utc(self.observed_from)
        _utc(self.available_by)
        _hash(self.canonical_hash)
        if (
            not self.document_references
            or len(self.document_references) > _MAX_REFERENCES
            or self.observed_from > self.available_by
        ):
            raise ValidationError("RES_INPUT_INVALID", "FUNDAMENTAL_EVIDENCE_INVALID")
        for field in (
            "coverage",
            "revisions",
            "currency_lineage",
            "unit_lineage",
            "quality",
        ):
            object.__setattr__(
                self, field, MappingProxyType(dict(getattr(self, field)))
            )


@dataclass(frozen=True, slots=True)
class SentimentSourceEvidence:
    """Bounded deterministic sentiment/event evidence."""

    contract_version: Literal["v1"]
    schema_id: Literal["research.sentiment_source_evidence.v1"]
    asset_scope: tuple[str, ...]
    document_references: tuple[str, ...]
    event_references: tuple[str, ...]
    available_by: datetime
    measurement_version: str
    polarity: Mapping[str, float | None]
    source_coverage: Mapping[str, int]
    disagreement: bool
    missing_measurements: tuple[str, ...]
    revisions: Mapping[str, int]
    trust_evidence: Mapping[str, str]
    manipulation_evidence: Mapping[str, str]
    injection_evidence: Mapping[str, str]
    canonical_hash: str
    advisory_only: Literal[True] = True

    def __post_init__(self) -> None:
        """Validate sentiment measurements and safety evidence.

        Raises:
            ValidationError: If measurements or lineage are invalid.
        """
        _utc(self.available_by)
        _hash(self.canonical_hash)
        if (
            not self.measurement_version
            or not self.document_references
            or len(self.document_references) > _MAX_REFERENCES
            or any(
                value is not None and not -1.0 <= value <= 1.0
                for value in self.polarity.values()
            )
        ):
            raise ValidationError("RES_INPUT_INVALID", "SENTIMENT_EVIDENCE_INVALID")
        for field in (
            "polarity",
            "source_coverage",
            "revisions",
            "trust_evidence",
            "manipulation_evidence",
            "injection_evidence",
        ):
            object.__setattr__(
                self, field, MappingProxyType(dict(getattr(self, field)))
            )


def evidence_hash(material: Mapping[str, object]) -> str:
    """Return the canonical intelligence evidence hash."""
    return canonical_digest(material)


__all__ = (
    "FundamentalSourceEvidence",
    "IntelligenceApplicability",
    "SentimentSourceEvidence",
    "evidence_hash",
)
