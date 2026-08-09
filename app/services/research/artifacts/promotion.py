"""Versioned candidate profile promotion (TC-IMP-RES-10, EXTEND FEAT-RES-12).

Produces versioned candidate profiles for Strategy/Risk/Simulator/Optimization
with review evidence. A candidate profile is an advisory promotion artifact: it
references (never redefines) downstream domain contracts and carries the review
evidence required before promotion. Promotion authority remains with the
downstream domain and the human owner.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from app.services.research.contracts.errors import ValidationError
from app.utils import canonical_digest, to_json_safe

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_TARGETS = frozenset({"strategy", "risk", "simulator", "optimization"})
_REVIEW_OUTCOMES = frozenset(
    {"pending", "approved", "rejected", "superseded", "withdrawn"}
)


def _utc(value: datetime) -> None:
    """Validate one UTC instant.

    Raises:
        ValidationError: If the value is not UTC-aware.
    """
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValidationError("RES_INPUT_INVALID", "CANDIDATE_TIME_NOT_UTC")


def _require_text(value: str, *, detail: str) -> None:
    """Reject empty/whitespace-only strings.

    Raises:
        ValidationError: If the value is empty or whitespace-only.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("RES_INPUT_INVALID", detail)


@dataclass(frozen=True, slots=True)
class CandidateProfile:
    """Immutable versioned candidate profile with review evidence.

    Attributes:
        contract_version: Compatibility version; always ``v1``.
        schema_id: Stable namespaced schema identity.
        candidate_id: Research-owned candidate identifier.
        target_domain: Downstream domain the candidate targets.
        candidate_version: Versioned candidate identity for the target domain.
        evidence_ref: Bounded evidence reference backing the candidate.
        review_outcome: Review outcome label.
        reviewer: Reviewer principal recording the outcome.
        review_reason: Recorded review reason.
        superseded_by: Candidate identity superseding this one, or ``None``.
        promoted_at_utc: Promotion instant, or ``None`` before promotion.
        canonical_hash: Canonical SHA-256 of the candidate material.
        advisory_only: Always ``True``; Research is advisory-only.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["research.candidate_profile.v1"]
    candidate_id: str
    target_domain: Literal["strategy", "risk", "simulator", "optimization"]
    candidate_version: str
    evidence_ref: str
    review_outcome: Literal[
        "pending", "approved", "rejected", "superseded", "withdrawn"
    ]
    reviewer: str
    review_reason: str
    superseded_by: str | None
    promoted_at_utc: datetime | None
    canonical_hash: str
    advisory_only: Literal[True] = field(default=True, init=False)

    def __post_init__(self) -> None:
        """Validate candidate identity, target, and review consistency.

        Raises:
            ValidationError: If identity, target, or review are invalid.
        """
        _require_text(self.candidate_id, detail="CANDIDATE_ID_EMPTY")
        if self.target_domain not in _TARGETS:
            raise ValidationError("RES_INPUT_INVALID", "CANDIDATE_TARGET")
        _require_text(self.candidate_version, detail="CANDIDATE_VERSION_EMPTY")
        _require_text(self.evidence_ref, detail="CANDIDATE_EVIDENCE_REF_EMPTY")
        if self.review_outcome not in _REVIEW_OUTCOMES:
            raise ValidationError("RES_INPUT_INVALID", "CANDIDATE_REVIEW_OUTCOME")
        _require_text(self.reviewer, detail="CANDIDATE_REVIEWER_EMPTY")
        _require_text(self.review_reason, detail="CANDIDATE_REVIEW_REASON_EMPTY")
        if self.superseded_by is not None:
            _require_text(self.superseded_by, detail="CANDIDATE_SUPERSEDED_BY_EMPTY")
            if self.review_outcome != "superseded":
                raise ValidationError(
                    "RES_INPUT_INVALID", "CANDIDATE_SUPERSEDED_NOT_SUPERSEDED"
                )
        if self.promoted_at_utc is not None:
            _utc(self.promoted_at_utc)
            if self.review_outcome != "approved":
                raise ValidationError(
                    "RES_INPUT_INVALID", "CANDIDATE_PROMOTED_NOT_APPROVED"
                )
        elif self.review_outcome == "approved":
            raise ValidationError(
                "RES_INPUT_INVALID", "CANDIDATE_APPROVED_NOT_PROMOTED"
            )
        if (
            not isinstance(self.canonical_hash, str)
            or _SHA256.fullmatch(self.canonical_hash) is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "CANDIDATE_HASH_INVALID")


def _candidate_material(candidate: CandidateProfile) -> Mapping[str, object]:
    """Return the canonical hash material for one candidate."""
    return {
        "contract_version": candidate.contract_version,
        "schema_id": candidate.schema_id,
        "candidate_id": candidate.candidate_id,
        "target_domain": candidate.target_domain,
        "candidate_version": candidate.candidate_version,
        "evidence_ref": candidate.evidence_ref,
        "generated_at_utc": (
            None
            if candidate.promoted_at_utc is None
            else candidate.promoted_at_utc.isoformat()
        ),
    }


def build_candidate_profile(
    *,
    candidate_id: str,
    target_domain: Literal["strategy", "risk", "simulator", "optimization"],
    candidate_version: str,
    evidence_ref: str,
    review_outcome: Literal[
        "pending", "approved", "rejected", "superseded", "withdrawn"
    ],
    reviewer: str,
    review_reason: str,
    superseded_by: str | None = None,
    promoted_at_utc: datetime | None = None,
) -> dict[str, Any]:
    """Build a validated JSON-safe candidate profile v1 mapping.

    Args:
        candidate_id: Research-owned candidate identifier.
        target_domain: Downstream domain the candidate targets.
        candidate_version: Versioned candidate identity for the target domain.
        evidence_ref: Bounded evidence reference backing the candidate.
        review_outcome: Review outcome label.
        reviewer: Reviewer principal recording the outcome.
        review_reason: Recorded review reason.
        superseded_by: Candidate identity superseding this one, or ``None``.
        promoted_at_utc: Promotion instant, or ``None`` before promotion.

    Returns:
        JSON-safe candidate profile mapping with ``canonical_hash``.

    Raises:
        ValidationError: If identity, target, or review are invalid.
    """
    material = {
        "contract_version": "v1",
        "schema_id": "research.candidate_profile.v1",
        "candidate_id": candidate_id,
        "target_domain": target_domain,
        "candidate_version": candidate_version,
        "evidence_ref": evidence_ref,
        "generated_at_utc": (
            None if promoted_at_utc is None else promoted_at_utc.isoformat()
        ),
    }
    canonical_hash = canonical_digest(material)
    candidate = CandidateProfile(
        contract_version="v1",
        schema_id="research.candidate_profile.v1",
        candidate_id=candidate_id,
        target_domain=target_domain,
        candidate_version=candidate_version,
        evidence_ref=evidence_ref,
        review_outcome=review_outcome,
        reviewer=reviewer,
        review_reason=review_reason,
        superseded_by=superseded_by,
        promoted_at_utc=promoted_at_utc,
        canonical_hash=canonical_hash,
    )
    return dict(to_json_safe(_candidate_mapping(candidate)))  # type: ignore[arg-type]


def _candidate_mapping(candidate: CandidateProfile) -> Mapping[str, object]:
    """Return the full transport mapping for one candidate."""
    return {
        "contract_version": candidate.contract_version,
        "schema_id": candidate.schema_id,
        "candidate_id": candidate.candidate_id,
        "target_domain": candidate.target_domain,
        "candidate_version": candidate.candidate_version,
        "evidence_ref": candidate.evidence_ref,
        "review_outcome": candidate.review_outcome,
        "reviewer": candidate.reviewer,
        "review_reason": candidate.review_reason,
        "superseded_by": candidate.superseded_by,
        "promoted_at_utc": (
            None
            if candidate.promoted_at_utc is None
            else candidate.promoted_at_utc.isoformat()
        ),
        "canonical_hash": candidate.canonical_hash,
        "advisory_only": True,
    }


def parse_candidate_profile(
    value: Mapping[str, object],
) -> dict[str, Any]:
    """Parse and fully validate a candidate profile v1 mapping.

    Args:
        value: Candidate JSON-safe candidate profile mapping.

    Returns:
        Re-validated JSON-safe candidate profile mapping.

    Raises:
        ValidationError: If the mapping is structurally or semantically invalid.
    """
    if not isinstance(value, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "CANDIDATE_NOT_MAPPING")
    if value.get("contract_version") != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "CANDIDATE_VERSION")
    if value.get("schema_id") != "research.candidate_profile.v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "CANDIDATE_SCHEMA")
    if value.get("advisory_only") is not True:
        raise ValidationError("RES_INPUT_INVALID", "CANDIDATE_NOT_ADVISORY")
    promoted = value.get("promoted_at_utc")
    return build_candidate_profile(
        candidate_id=str(value["candidate_id"]),
        target_domain=str(value["target_domain"]),  # type: ignore[arg-type]
        candidate_version=str(value["candidate_version"]),
        evidence_ref=str(value["evidence_ref"]),
        review_outcome=str(value["review_outcome"]),  # type: ignore[arg-type]
        reviewer=str(value["reviewer"]),
        review_reason=str(value["review_reason"]),
        superseded_by=(
            None if value.get("superseded_by") is None else str(value["superseded_by"])
        ),
        promoted_at_utc=(
            None if promoted is None else datetime.fromisoformat(str(promoted))
        ),
    )


# ---- TC-IMP-RES-11 evidence audit trail additions (EXTEND FEAT-RES-12) ----


@dataclass(frozen=True, slots=True)
class ExpectancyReviewEvidence:
    """Immutable expectancy-approval review audit evidence.

    Records the reviewer, decision, reason, and superseded version for an
    expectancy approval so the audit trail is preserved (financial records are
    append-only; corrections are reversal/supersession events).

    Attributes:
        contract_version: Compatibility version; always ``v1``.
        schema_id: Stable namespaced schema identity.
        profile_id: Expectancy profile under review.
        reviewer: Reviewer principal.
        decision: Recorded decision label.
        reason: Recorded decision reason.
        superseded_version: Version superseded by this review, or ``None``.
        reviewed_at_utc: Review instant.
        canonical_hash: Canonical SHA-256 of the review material.
        advisory_only: Always ``True``; Research is advisory-only.
    """

    contract_version: Literal["v1"]
    schema_id: Literal["research.expectancy_review.v1"]
    profile_id: str
    reviewer: str
    decision: str
    reason: str
    superseded_version: str | None
    reviewed_at_utc: datetime
    canonical_hash: str
    advisory_only: Literal[True] = field(default=True, init=False)

    def __post_init__(self) -> None:
        """Validate review identity and decision.

        Raises:
            ValidationError: If identity or decision are invalid.
        """
        _require_text(self.profile_id, detail="REVIEW_PROFILE_ID_EMPTY")
        _require_text(self.reviewer, detail="REVIEW_REVIEWER_EMPTY")
        _require_text(self.decision, detail="REVIEW_DECISION_EMPTY")
        _require_text(self.reason, detail="REVIEW_REASON_EMPTY")
        _utc(self.reviewed_at_utc)
        if (
            not isinstance(self.canonical_hash, str)
            or _SHA256.fullmatch(self.canonical_hash) is None
        ):
            raise ValidationError("RES_INPUT_INVALID", "REVIEW_HASH_INVALID")


def build_expectancy_review_evidence(
    *,
    profile_id: str,
    reviewer: str,
    decision: str,
    reason: str,
    superseded_version: str | None,
    reviewed_at_utc: datetime,
) -> dict[str, Any]:
    """Build a validated JSON-safe expectancy review evidence v1 mapping.

    Args:
        profile_id: Expectancy profile under review.
        reviewer: Reviewer principal.
        decision: Recorded decision label.
        reason: Recorded decision reason.
        superseded_version: Version superseded by this review, or ``None``.
        reviewed_at_utc: Review instant.

    Returns:
        JSON-safe review evidence mapping with ``canonical_hash``.
    """
    material = {
        "contract_version": "v1",
        "schema_id": "research.expectancy_review.v1",
        "profile_id": profile_id,
        "reviewer": reviewer,
        "decision": decision,
        "reason": reason,
        "superseded_version": superseded_version,
        "reviewed_at_utc": reviewed_at_utc.isoformat(),
    }
    canonical_hash = canonical_digest(material)
    evidence = ExpectancyReviewEvidence(
        contract_version="v1",
        schema_id="research.expectancy_review.v1",
        profile_id=profile_id,
        reviewer=reviewer,
        decision=decision,
        reason=reason,
        superseded_version=superseded_version,
        reviewed_at_utc=reviewed_at_utc,
        canonical_hash=canonical_hash,
    )
    return dict(to_json_safe(_review_mapping(evidence)))  # type: ignore[arg-type]


def _review_mapping(evidence: ExpectancyReviewEvidence) -> Mapping[str, object]:
    """Return the full transport mapping for one review evidence."""
    return {
        "contract_version": evidence.contract_version,
        "schema_id": evidence.schema_id,
        "profile_id": evidence.profile_id,
        "reviewer": evidence.reviewer,
        "decision": evidence.decision,
        "reason": evidence.reason,
        "superseded_version": evidence.superseded_version,
        "reviewed_at_utc": evidence.reviewed_at_utc.isoformat(),
        "canonical_hash": evidence.canonical_hash,
        "advisory_only": True,
    }


def parse_expectancy_review_evidence(
    value: Mapping[str, object],
) -> dict[str, Any]:
    """Parse and fully validate an expectancy review evidence v1 mapping.

    Args:
        value: Candidate JSON-safe review evidence mapping.

    Returns:
        Re-validated JSON-safe review evidence mapping.

    Raises:
        ValidationError: If the mapping is structurally or semantically invalid.
    """
    if not isinstance(value, Mapping):
        raise ValidationError("RES_INPUT_INVALID", "REVIEW_NOT_MAPPING")
    if value.get("contract_version") != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "REVIEW_VERSION")
    if value.get("schema_id") != "research.expectancy_review.v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "REVIEW_SCHEMA")
    if value.get("advisory_only") is not True:
        raise ValidationError("RES_INPUT_INVALID", "REVIEW_NOT_ADVISORY")
    return build_expectancy_review_evidence(
        profile_id=str(value["profile_id"]),
        reviewer=str(value["reviewer"]),
        decision=str(value["decision"]),
        reason=str(value["reason"]),
        superseded_version=(
            None
            if value.get("superseded_version") is None
            else str(value["superseded_version"])
        ),
        reviewed_at_utc=datetime.fromisoformat(str(value["reviewed_at_utc"])),
    )


def record_expectancy_review_evidence(
    *,
    profile_id: str,
    reviewer: str,
    decision: str,
    reason: str,
    superseded_version: str | None,
    reviewed_at_utc: datetime,
) -> dict[str, Any]:
    """Record one expectancy-approval review audit evidence mapping.

    Args:
        profile_id: Expectancy profile under review.
        reviewer: Reviewer principal.
        decision: Recorded decision label.
        reason: Recorded decision reason.
        superseded_version: Version superseded by this review, or ``None``.
        reviewed_at_utc: Review instant.

    Returns:
        JSON-safe review evidence mapping.
    """
    return build_expectancy_review_evidence(
        profile_id=profile_id,
        reviewer=reviewer,
        decision=decision,
        reason=reason,
        superseded_version=superseded_version,
        reviewed_at_utc=reviewed_at_utc,
    )


__all__ = (
    "CandidateProfile",
    "ExpectancyReviewEvidence",
    "build_candidate_profile",
    "build_expectancy_review_evidence",
    "parse_candidate_profile",
    "parse_expectancy_review_evidence",
    "record_expectancy_review_evidence",
)
