"""Bounded eligible context assembly.

`assemble_context` applies the governed filters in a fixed order before any
model sees anything: scope, point-in-time availability, provenance and
licensing, freshness, deduplication and conflict marking, injection
classification, and a deterministic token budget. Trusted context and
untrusted evidence are then returned in separate fields.

Nothing here is a substitute for a deterministic domain read. A claim that
survives assembly is *eligible*, not *true*.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from decimal import Decimal

from app.agentic.context_memory.models import ContextBundle, EvidenceClaim
from app.utils import derive_stable_id, get_logger, is_fresh

logger = get_logger(__name__)

# A deterministic proxy for token cost. Real tokenization is provider-specific
# and would make assembly non-deterministic across providers, so the budget is
# enforced against this stable estimate instead.
_CHARS_PER_TOKEN = 4

_EXCLUSION_REASONS = {
    "scope": "scope_mismatch",
    "lookahead": "not_available_at_decision_time",
    "trust": "source_trust_below_floor",
    "licence": "licence_missing",
    "stale": "evidence_stale",
    "duplicate": "duplicate_content",
    "injection": "injection_suspected",
    "budget": "token_budget_exhausted",
}


def _estimate_tokens(text: str) -> int:
    """Estimate the deterministic token cost of one text.

    Args:
        text: Candidate text.

    Returns:
        A stable non-negative token estimate.
    """
    return (len(text) + _CHARS_PER_TOKEN - 1) // _CHARS_PER_TOKEN


def _claim_tokens(claim: EvidenceClaim) -> int:
    """Estimate the token cost of one evidence claim.

    Args:
        claim: Candidate evidence claim.

    Returns:
        A stable non-negative token estimate.
    """
    return _estimate_tokens(claim.statement) + _estimate_tokens(claim.confidence_basis)


def assemble_context(
    task_id: str,
    claims: Iterable[EvidenceClaim],
    decision_time: datetime,
    trusted_context: Mapping[str, str] | None = None,
    token_budget: int = 8_000,
    max_age_seconds: Decimal | None = None,
    minimum_trust: str = "public",
    scope: Mapping[str, str] | None = None,
    assembled_at: datetime | None = None,
) -> ContextBundle:
    """Assemble one bounded eligible context set for a governed task.

    Args:
        task_id: Owning task identity.
        claims: Candidate evidence claims.
        decision_time: Point-in-time boundary; nothing later is eligible.
        trusted_context: Trusted structured context supplied by the caller.
        token_budget: Deterministic token ceiling for assembled evidence.
        max_age_seconds: Optional freshness ceiling relative to decision time.
        minimum_trust: Lowest acceptable source-trust class.
        scope: Governed scope the task is bound to.
        assembled_at: Optional assembly time; the decision time when omitted.

    Returns:
        The assembled bounded context bundle, recording every exclusion.
    """
    trust_order = ("unverified", "public", "licensed", "authoritative")
    floor = trust_order.index(minimum_trust)
    now = assembled_at if assembled_at is not None else decision_time
    declared_scope = scope if scope is not None else {}

    logger.info("Assembling Agentic context for task %s", task_id)
    eligible: list[EvidenceClaim] = []
    excluded: list[tuple[str, str]] = []
    seen_hashes: set[str] = set()
    used_tokens = 0

    for claim in claims:
        # 1. Scope.
        if claim.task_id != task_id:
            excluded.append((claim.claim_id, _EXCLUSION_REASONS["scope"]))
            continue

        # 2. Point-in-time availability; nothing the system could not have
        #    known at the decision time is eligible.
        if claim.available_at > decision_time:
            excluded.append((claim.claim_id, _EXCLUSION_REASONS["lookahead"]))
            continue

        # 3. Provenance and licensing.
        if trust_order.index(claim.source_trust) < floor:
            excluded.append((claim.claim_id, _EXCLUSION_REASONS["trust"]))
            continue
        if not claim.licence_ref:
            excluded.append((claim.claim_id, _EXCLUSION_REASONS["licence"]))
            continue

        # 4. Freshness, re-verified at retrieval rather than trusting recency.
        if max_age_seconds is not None and not is_fresh(
            claim.available_at,
            reference=decision_time,
            max_age_seconds=max_age_seconds,
        ):
            excluded.append((claim.claim_id, _EXCLUSION_REASONS["stale"]))
            continue

        # 5. Deduplication by original content digest.
        if claim.content_hash in seen_hashes:
            excluded.append((claim.claim_id, _EXCLUSION_REASONS["duplicate"]))
            continue

        # 6. Injection classification; suspected text never reaches the model.
        if claim.injection_status == "suspected":
            excluded.append((claim.claim_id, _EXCLUSION_REASONS["injection"]))
            continue

        # 7. Deterministic token budget.
        cost = _claim_tokens(claim)
        if used_tokens + cost > token_budget:
            excluded.append((claim.claim_id, _EXCLUSION_REASONS["budget"]))
            continue

        seen_hashes.add(claim.content_hash)
        used_tokens += cost
        eligible.append(claim)

    logger.info(
        "Assembled %d eligible claims and excluded %d for task %s",
        len(eligible),
        len(excluded),
        task_id,
    )
    return ContextBundle(
        bundle_id=derive_stable_id(
            "id", f"context:{task_id}:{decision_time.isoformat()}"
        ),
        task_id=task_id,
        assembled_at=now,
        decision_time=decision_time,
        trusted_context=dict(trusted_context or {"scope": str(len(declared_scope))}),
        untrusted_evidence=tuple(eligible),
        excluded=tuple(excluded),
        token_budget=token_budget,
        token_estimate=used_tokens,
    )


def get_exclusion_reasons() -> tuple[str, ...]:
    """Return every enumerated context-exclusion reason.

    Returns:
        Ordered enumerated exclusion reasons.
    """
    return tuple(sorted(set(_EXCLUSION_REASONS.values())))
