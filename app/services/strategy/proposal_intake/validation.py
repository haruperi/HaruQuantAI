"""Fail-closed validation for external proposal evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest
from app.services.strategy.contracts.references import (
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
)
from app.services.strategy.contracts.responses import (
    StrategyOperationError,
    guard_strategy_boundary,
    unwrap_strategy_response,
)
from app.services.strategy.proposal_intake.requests import (
    StrategyProposalEvaluationRequest,  # noqa: TC001
)
from app.services.strategy.proposal_intake.results import (
    ProposalEvaluationStatus,
    StrategyProposalEvaluationResult,
)
from app.services.strategy.registry.configuration import validate_strategy_config
from app.services.strategy.registry.resolution import validate_strategy_ref

if TYPE_CHECKING:
    from app.services.strategy.contracts.execution import StrategyExecutionContext
    from app.services.strategy.contracts.policy import StrategyValidationPolicy
    from app.services.strategy.contracts.references import StrategyConfig, StrategyRef
    from app.services.strategy.contracts.signals import StrategySignalEvidence
    from app.services.strategy.signals.protocol import SignalEvaluator

logger = get_logger(__name__)

_EVALUATE_PERMISSION = "strategy:evaluate_proposal"
_EVALUATE_SCOPE = "strategy:proposal_evaluation"

type _ValidatedProposal = tuple[ValidatedStrategyRef, ValidatedStrategyConfig]
type _ValidationOutcome = _ValidatedProposal | StrategyProposalEvaluationResult


def _result(
    request: StrategyProposalEvaluationRequest,
    *,
    status: ProposalEvaluationStatus,
    reason_codes: tuple[str, ...] = (),
) -> StrategyProposalEvaluationResult:
    """Build one validation-stage proposal result.

    Returns:
        Deterministic validation-stage proposal result.
    """
    material = {
        "request": request.evaluation_request_id,
        "status": status,
        "reasons": reason_codes,
    }
    return StrategyProposalEvaluationResult(
        evaluation_id=f"proposal-result-{canonical_digest(material)}",
        evaluation_request_id=request.evaluation_request_id,
        status=status,
        reason_codes=reason_codes,
        source_proposal_id=request.source_proposal_id,
        source_task_id=request.source_task_id,
        source_content_hash=request.source_content_hash,
        strategy_id=request.strategy_id,
        strategy_version=request.strategy_version,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
    )


def _reject(
    request: StrategyProposalEvaluationRequest,
    reason: str,
) -> StrategyProposalEvaluationResult:
    """Return one deterministic rejected validation result."""
    logger.info("Rejecting Strategy proposal validation: %s", reason)
    return _result(request, status="rejected", reason_codes=(reason,))


def _validate_strategy_proposal(  # noqa: PLR0911
    request: StrategyProposalEvaluationRequest,
    auth: object,
    ref: StrategyRef,
    config: StrategyConfig,
    policy: StrategyValidationPolicy,
    evidence: StrategySignalEvidence,
    context: StrategyExecutionContext,
    evaluator: SignalEvaluator,
) -> _ValidationOutcome:
    """Validate proposal authority, identity, and deterministic dependencies.

    Returns:
        Validated reference/config pair or a deterministic rejection result.
    """
    permissions = tuple(getattr(auth, "permissions", ()))
    scopes = tuple(getattr(auth, "scopes", ()))
    if _EVALUATE_PERMISSION not in permissions or _EVALUATE_SCOPE not in scopes:
        return _reject(request, "AUTHORIZATION_DENIED")
    if (
        getattr(auth, "principal_id", None) != request.principal_id
        or getattr(auth, "request_id", None) != request.request_id
        or getattr(auth, "workflow_id", None) != request.workflow_id
        or getattr(auth, "correlation_id", None) != request.correlation_id
    ):
        return _reject(request, "AUTHORIZATION_CONTEXT_MISMATCH")
    if (
        getattr(context, "request_id", None) != request.request_id
        or getattr(context, "workflow_id", None) != request.workflow_id
        or getattr(context, "correlation_id", None) != request.correlation_id
    ):
        return _reject(request, "TRACE_CONTEXT_MISMATCH")
    decision_time = getattr(context, "decision_timestamp", None)
    if decision_time is None or decision_time < request.requested_at:
        return _reject(request, "EVALUATION_TIME_INVALID")
    if decision_time >= request.expires_at:
        return _result(
            request,
            status="expired",
            reason_codes=("PROPOSAL_EXPIRED",),
        )
    if (
        getattr(ref, "strategy_id", None) != request.strategy_id
        or getattr(ref, "exact_version", None) != request.strategy_version
    ):
        return _reject(request, "STRATEGY_REFERENCE_MISMATCH")
    market = getattr(evidence, "primary_market", None)
    if getattr(market, "symbol", None) != request.instrument:
        return _reject(request, "PROPOSAL_INSTRUMENT_MISMATCH")
    try:
        validated_ref = unwrap_strategy_response(
            validate_strategy_ref(ref, policy),
            operation="strategy.proposal_intake.validate_strategy_ref",
        )
        validated_config = unwrap_strategy_response(
            validate_strategy_config(validated_ref, config),
            operation="strategy.proposal_intake.validate_strategy_config",
        )
    except StrategyOperationError:
        return _reject(request, "REGISTRY_OR_CONFIG_VALIDATION_FAILED")
    manifest = validated_ref.manifest
    evaluator_identity = (
        getattr(evaluator, "strategy_id", None),
        getattr(evaluator, "strategy_version", None),
        getattr(evaluator, "module_path", None),
        getattr(evaluator, "source_hash", None),
        getattr(evaluator, "artifact_hash", None),
        getattr(evaluator, "dependency_hash", None),
    )
    expected_identity = (
        manifest.strategy_id,
        manifest.strategy_version,
        manifest.module_path,
        manifest.source_hash,
        manifest.artifact_hash,
        manifest.dependency_hash,
    )
    if evaluator_identity != expected_identity:
        return _reject(request, "EVALUATOR_COMPATIBILITY_FAILED")
    return validated_ref, validated_config


@guard_strategy_boundary
def validate_strategy_proposal(
    request: StrategyProposalEvaluationRequest,
    auth: object,
    ref: StrategyRef,
    config: StrategyConfig,
    policy: StrategyValidationPolicy,
    evidence: StrategySignalEvidence,
    context: StrategyExecutionContext,
    evaluator: SignalEvaluator,
) -> StrategyProposalEvaluationResult:
    """Validate one proposal without evaluating signals or writing state.

    Args:
        request: Receiver-owned proposal request.
        auth: Authenticated principal context.
        ref: Exact unresolved Strategy reference.
        config: Declarative Strategy configuration.
        policy: Recorded Strategy validation policy.
        evidence: Point-in-time Strategy signal evidence.
        context: Fixed deterministic execution context.
        evaluator: Hash-bound concrete Strategy evaluator.

    Returns:
        Accepted-for-evaluation, rejected, or expired result.
    """
    outcome = _validate_strategy_proposal(
        request,
        auth,
        ref,
        config,
        policy,
        evidence,
        context,
        evaluator,
    )
    if isinstance(outcome, StrategyProposalEvaluationResult):
        return outcome
    return _result(request, status="accepted_for_evaluation")


__all__ = ["validate_strategy_proposal"]
