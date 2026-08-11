"""Deterministic policy and eligibility checks for research sources."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit

from app.services.data.contracts.errors import DataError
from app.services.data.sources.research_contracts import (
    ResearchSourceDocument,
    ResearchSourceEligibility,
    ResearchSourceIngestRequest,
    ResearchSourcePolicy,
)


def validate_research_source_policy(
    request: ResearchSourceIngestRequest,
    policy: ResearchSourcePolicy,
    *,
    now: datetime,
) -> None:
    """Validate source access against the declared policy.

    Args:
        request: Candidate source request.
        policy: Governing source policy.
        now: Current UTC instant.

    Raises:
        DataError: If policy identity, host, environment, use, or expiry fails.
    """
    host = (urlsplit(request.source_url).hostname or "").lower()
    if (
        request.source_id != policy.source_id
        or host not in policy.allowed_hosts
        or request.environment not in policy.permitted_environments
        or request.decision_use not in policy.permitted_uses
        or (policy.expires_at is not None and now > policy.expires_at)
    ):
        raise DataError(
            "LICENSE_RESTRICTION",
            safe_details={"source_id": request.source_id},
            request_id=request.request_id,
        )


def assess_research_source_eligibility(
    document: ResearchSourceDocument,
    *,
    decision_time: datetime,
) -> ResearchSourceEligibility:
    """Assess historical eligibility without discarding reasons.

    Args:
        document: Candidate source evidence.
        decision_time: Historical decision instant.

    Returns:
        Typed eligibility decision.
    """
    reasons: list[str] = []
    if document.available_at > decision_time:
        reasons.append("NOT_YET_AVAILABLE")
    if document.trust_status != "trusted":
        reasons.append("TRUST_NOT_VERIFIED")
    if document.manipulation_status != "clear":
        reasons.append("MANIPULATION_UNRESOLVED")
    if document.injection_status != "clear":
        reasons.append("INJECTION_UNSAFE")
    if document.retention_until < decision_time:
        reasons.append("RETENTION_EXPIRED")
    return ResearchSourceEligibility(
        status="eligible" if not reasons else "ineligible",
        reasons=tuple(reasons),
        document_id=document.document_id,
        decision_time=decision_time,
    )


__all__ = (
    "assess_research_source_eligibility",
    "validate_research_source_policy",
)
