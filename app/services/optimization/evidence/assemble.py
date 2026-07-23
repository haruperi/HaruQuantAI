"""Assembly of versioned Optimization evidence without recomputation."""

from __future__ import annotations

from app.services.optimization.evidence.contracts import (
    EvidenceAssemblyRequest,
    FinalDecision,
    OptimizationResult,
)
from app.services.optimization.search import CandidateState
from app.utils import canonical_digest, logger


def _select_decision(request: EvidenceAssemblyRequest) -> FinalDecision:
    """Select an advisory decision from evidence availability and status.

    Args:
        request: Validated supplied evidence.

    Returns:
        Deterministic advisory final decision.
    """
    logger.debug("Selecting Optimization advisory final decision")
    accepted = tuple(
        item
        for item in request.search.candidates
        if item.state is CandidateState.ACCEPTED
    )
    if not accepted:
        failed = any(
            item.state is CandidateState.FAILED for item in request.search.candidates
        )
        return FinalDecision.FAILED if failed else FinalDecision.REJECTED
    if request.walk_forward is None:
        return FinalDecision.VALIDATION_NEEDED
    if request.walk_forward.status != "completed":
        return FinalDecision.RESEARCH_ONLY
    if request.monte_carlo is None or request.robustness is None:
        return FinalDecision.VALIDATION_NEEDED
    return FinalDecision.READY_FOR_RISK_REVIEW


def build_optimization_evidence(
    request: EvidenceAssemblyRequest,
) -> OptimizationResult:
    """Assemble canonical supplied evidence into ``OptimizationResult v1``.

    Args:
        request: Validated source evidence.

    Returns:
        Advisory versioned Optimization result.

    Raises:
        ValueError: If source evidence cannot be canonically represented.
    """
    logger.info("Building canonical Optimization result evidence")
    ranked = tuple(
        item.model_dump(mode="json")
        for item in request.search.candidates
        if item.state is CandidateState.ACCEPTED
    )
    diagnostics: dict[str, object] = {
        "search": request.search.model_dump(mode="json"),
        "walk_forward": (
            None
            if request.walk_forward is None
            else request.walk_forward.model_dump(mode="json")
        ),
        "monte_carlo": (
            None
            if request.monte_carlo is None
            else request.monte_carlo.model_dump(mode="json")
        ),
        "robustness": dict(request.robustness or {}),
        "analytics_evidence": dict(request.analytics_evidence or {}),
        "risk_evidence": dict(request.risk_evidence or {}),
    }
    reproducible_diagnostics = dict(diagnostics)
    reproducible_search = dict(request.search.model_dump(mode="json"))
    reproducible_search.pop("runtime_ms", None)
    reproducible_diagnostics["search"] = reproducible_search
    hash_payload = {
        "schema_id": "optimization.result.v1",
        "search_id": request.search.search_id,
        "request_hash": request.search.request_hash,
        "ranked_candidates": ranked,
        "diagnostics": reproducible_diagnostics,
        "chart_data": dict(request.chart_data or {}),
        "audit_references": request.audit_references,
    }
    try:
        reproducibility_hash = canonical_digest(hash_payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("Optimization evidence is not canonicalizable") from exc
    warnings = list(request.search.warnings)
    if request.walk_forward is None:
        warnings.append("walk_forward_evidence_missing")
    if request.monte_carlo is None:
        warnings.append("monte_carlo_evidence_missing")
    if request.robustness is None:
        warnings.append("robustness_assessment_missing")
    return OptimizationResult(
        search_id=request.search.search_id,
        reproducibility_hash=reproducibility_hash,
        ranked_candidates=ranked,
        diagnostics=diagnostics,
        warnings=tuple(warnings),
        chart_data=dict(request.chart_data or {}),
        audit_references=request.audit_references,
        final_decision=_select_decision(request),
    )


__all__ = ["build_optimization_evidence"]
