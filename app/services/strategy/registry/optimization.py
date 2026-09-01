"""Strategy-owned receiver for approved Optimization parameter handoffs."""

from __future__ import annotations

from collections.abc import Mapping

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest
from app.services.strategy.contracts.outcomes import StrategyMutationResult
from app.services.strategy.contracts.requests import (
    StrategyParameterUpdateRequest,  # noqa: TC001
)
from app.services.strategy.contracts.responses import (
    guard_strategy_boundary,
    unwrap_strategy_response,
)
from app.services.strategy.registry._mutations import _mutation_id
from app.services.strategy.registry.parameters import update_strategy_parameters

logger = get_logger(__name__)

_UPDATE_PERMISSION = "strategy:update"
_EXPECTED_CONTRACT = "v1"
_EXPECTED_SCHEMA = "optimization.result.v1"
_ADOPTABLE_DECISION = "ready_for_risk_review"
_SHA256_LENGTH = 64


def _rejected_adoption(
    request: StrategyParameterUpdateRequest,
    auth: object,
    reason: str,
) -> StrategyMutationResult:
    """Build one fail-closed Optimization-adoption result.

    Returns:
        Rejected immutable Strategy mutation result.
    """
    logger.info("Rejecting Optimization parameter adoption: %s", reason)
    return StrategyMutationResult(
        mutation_id=_mutation_id(request.command_id),
        mutation_type="UPDATE_PARAMETERS",
        status="REJECTED",
        strategy_id=request.strategy_id,
        strategy_version=request.strategy_version,
        reason_codes=(reason,),
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        workflow_id=str(getattr(auth, "workflow_id", "workflow-unavailable")),
        completed_at=request.requested_at,
    )


def _handoff_mapping(handoff: object) -> Mapping[str, object] | None:
    """Project a producer value to its documented public contract fields.

    Returns:
        Bounded handoff mapping or ``None`` for an incompatible value.
    """
    if isinstance(handoff, Mapping):
        return handoff
    dump = getattr(handoff, "model_dump", None)
    if callable(dump):
        value = dump(mode="python")
        if isinstance(value, Mapping):
            return value
    return None


def _parameters_match_candidate(
    ranked_candidates: object,
    requested_parameters: Mapping[str, object],
) -> bool:
    """Return whether one ranked candidate exactly matches requested parameters."""
    if not isinstance(ranked_candidates, list | tuple):
        return False
    requested_hash = canonical_digest(dict(requested_parameters))
    for candidate in ranked_candidates:
        if not isinstance(candidate, Mapping):
            continue
        parameters = candidate.get("executable_parameters")
        if (
            isinstance(parameters, Mapping)
            and canonical_digest(dict(parameters)) == requested_hash
        ):
            return True
    return False


@guard_strategy_boundary
def adopt_approved_optimization_parameters(  # noqa: PLR0911
    request: StrategyParameterUpdateRequest,
    auth: object,
    optimization_handoff: object | None,
) -> StrategyMutationResult:
    """Adopt one explicitly approved Optimization candidate immutably.

    Args:
        request: Governed Strategy parameter-update command.
        auth: Authenticated user approval context.
        optimization_handoff: Producer value matching ``OptimizationResult v1``.

    Returns:
        Accepted, idempotent, or rejected Strategy mutation result.
    """
    logger.info("Receiving approved Optimization parameters for Strategy")
    if (
        _UPDATE_PERMISSION not in tuple(getattr(auth, "permissions", ()))
        or getattr(auth, "principal_id", None) != request.principal_id
        or request.authorization_ref not in tuple(getattr(auth, "scopes", ()))
    ):
        return _rejected_adoption(request, auth, "AUTHORIZATION_DENIED")
    if request.optimization_result_ref is None:
        return _rejected_adoption(request, auth, "OPTIMIZATION_REFERENCE_REQUIRED")
    if optimization_handoff is None:
        return _rejected_adoption(request, auth, "OPTIMIZATION_HANDOFF_UNAVAILABLE")
    handoff = _handoff_mapping(optimization_handoff)
    if handoff is None:
        return _rejected_adoption(request, auth, "OPTIMIZATION_HANDOFF_INVALID")
    if (
        handoff.get("contract_version") != _EXPECTED_CONTRACT
        or handoff.get("schema_id") != _EXPECTED_SCHEMA
        or handoff.get("search_id") != request.optimization_result_ref
        or handoff.get("final_decision") != _ADOPTABLE_DECISION
    ):
        return _rejected_adoption(request, auth, "OPTIMIZATION_HANDOFF_MISMATCH")
    reproducibility_hash = handoff.get("reproducibility_hash")
    if (
        not isinstance(reproducibility_hash, str)
        or len(reproducibility_hash) != _SHA256_LENGTH
        or any(
            character not in "0123456789abcdef" for character in reproducibility_hash
        )
    ):
        return _rejected_adoption(request, auth, "OPTIMIZATION_EVIDENCE_INVALID")
    if not _parameters_match_candidate(
        handoff.get("ranked_candidates"),
        request.parameters,
    ):
        return _rejected_adoption(request, auth, "OPTIMIZATION_CANDIDATE_MISMATCH")
    return unwrap_strategy_response(
        update_strategy_parameters(request, auth),
        operation="strategy.registry.update_strategy_parameters.optimization_adoption",
    )


__all__ = ["adopt_approved_optimization_parameters"]
