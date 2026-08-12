"""Durable single-purpose human approval attestations."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict

from app.services.api.identity.errors import IdentityError
from app.services.api.identity.persistence import (
    consume_approval_record,
    create_approval_record,
    read_approval_record,
)
from app.utils import canonical_json, derive_stable_id, get_logger, utc_now

logger = get_logger(__name__)

_MAX_APPROVAL_TTL_SECONDS = 3600


class ApprovalRecord(BaseModel):
    """Secret-free scoped approval evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    approval_id: str
    issuer_id: str
    subject_id: str
    scope: str
    evidence_hash: str
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None


def create_approval(
    *,
    issuer_id: str,
    subject_id: str,
    scope: str,
    evidence: object,
    ttl_seconds: int,
    request_id: str,
    now: datetime | None = None,
) -> ApprovalRecord:
    """Create one scoped, expiring, single-purpose human approval.

    Args:
        issuer_id: Authorized human approver.
        subject_id: Principal permitted to consume the approval.
        scope: Exact receiver operation scope.
        evidence: Immutable request/artefact material being approved.
        ttl_seconds: Positive short approval lifetime.
        request_id: Canonical operation request identifier.
        now: Injectable UTC instant.

    Returns:
        Persisted approval evidence.

    Raises:
        IdentityError: If principals are the same or persistence fails.
        ValueError: If the scope or lifetime is invalid.
    """
    logger.info("Creating one scoped UI/API approval")
    if issuer_id == subject_id:
        raise IdentityError("APPROVAL_PRINCIPALS_MUST_DIFFER")
    if not scope or scope != scope.strip():
        raise ValueError("approval scope must be non-empty and trimmed")
    if ttl_seconds <= 0 or ttl_seconds > _MAX_APPROVAL_TTL_SECONDS:
        raise ValueError("approval lifetime is outside the approved range")
    created_at = now or utc_now()
    evidence_hash = hashlib.sha256(canonical_json(evidence).encode("utf-8")).hexdigest()
    approval_id = derive_stable_id(
        "id",
        f"api-approval:{issuer_id}:{subject_id}:{scope}:{evidence_hash}",
    )
    expires_at = created_at + timedelta(seconds=ttl_seconds)
    create_approval_record(
        approval_id=approval_id,
        issuer_id=issuer_id,
        subject_id=subject_id,
        scope=scope,
        evidence_hash=evidence_hash,
        created_at=created_at.isoformat(),
        expires_at=expires_at.isoformat(),
        request_id=request_id,
    )
    return ApprovalRecord(
        approval_id=approval_id,
        issuer_id=issuer_id,
        subject_id=subject_id,
        scope=scope,
        evidence_hash=evidence_hash,
        created_at=created_at,
        expires_at=expires_at,
    )


def consume_approval(
    approval_id: str,
    *,
    subject_id: str,
    scope: str,
    evidence: object,
    request_id: str,
    now: datetime | None = None,
) -> ApprovalRecord:
    """Validate and atomically consume one exact approval.

    Args:
        approval_id: Persisted approval identity.
        subject_id: Authenticated consuming principal.
        scope: Exact receiver scope.
        evidence: Exact request/artefact material.
        request_id: Canonical operation request identifier.
        now: Injectable UTC instant.

    Returns:
        Consumed approval evidence.

    Raises:
        IdentityError: If approval evidence is absent, stale, mismatched, or used.
    """
    logger.info("Consuming one scoped UI/API approval")
    current = now or utc_now()
    expected_hash = hashlib.sha256(canonical_json(evidence).encode("utf-8")).hexdigest()
    rows = read_approval_record(approval_id, request_id=request_id)
    if len(rows) != 1:
        raise IdentityError("APPROVAL_REQUIRED")
    row = rows[0]
    if (
        str(row["subject_id"]) != subject_id
        or str(row["scope"]) != scope
        or str(row["evidence_hash"]) != expected_hash
        or row["consumed_at"] is not None
        or datetime.fromisoformat(str(row["expires_at"])) <= current
    ):
        raise IdentityError("APPROVAL_INVALID")
    affected_rows = consume_approval_record(
        approval_id=approval_id,
        consumed_at=current.isoformat(),
        request_id=request_id,
    )
    if affected_rows != 1:
        raise IdentityError("APPROVAL_ALREADY_CONSUMED")
    return ApprovalRecord(
        approval_id=approval_id,
        issuer_id=str(row["issuer_id"]),
        subject_id=subject_id,
        scope=scope,
        evidence_hash=expected_hash,
        created_at=datetime.fromisoformat(str(row["created_at"])),
        expires_at=datetime.fromisoformat(str(row["expires_at"])),
        consumed_at=current,
    )


__all__ = ("ApprovalRecord", "consume_approval", "create_approval")
