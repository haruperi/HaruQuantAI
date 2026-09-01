"""Deterministic evaluation of untrusted external proposals."""

from __future__ import annotations

import hashlib
import uuid
from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.contracts.common.models import create_audit_event
from app.kernel.serialization import canonical_digest
from app.services.data import persist_audit_event
from app.services.strategy.contracts.execution import (
    StrategyDecision,
)
from app.services.strategy.contracts.responses import (
    guard_strategy_boundary,
    unwrap_data_response,
    unwrap_strategy_response,
)
from app.services.strategy.intents.builder import build_trade_intent
from app.services.strategy.proposal_intake.lineage import _bind_proposal_lineage
from app.services.strategy.proposal_intake.requests import (
    StrategyProposalEvaluationRequest,  # noqa: TC001
)
from app.services.strategy.proposal_intake.results import (
    ProposalEvaluationStatus,
    StrategyProposalEvaluationResult,
)
from app.services.strategy.proposal_intake.validation import (
    _validate_strategy_proposal,
)
from app.services.strategy.signals.boundary import evaluate_strategy_signals

if TYPE_CHECKING:
    from app.services.strategy.contracts.execution import StrategyExecutionContext
    from app.services.strategy.contracts.policy import StrategyValidationPolicy
    from app.services.strategy.contracts.references import (
        StrategyConfig,
        StrategyRef,
        ValidatedStrategyConfig,
    )
    from app.services.strategy.contracts.signals import (
        StrategySignal,
        StrategySignalEvidence,
    )
    from app.services.strategy.intents.intent import TradeIntent
    from app.services.strategy.signals.protocol import SignalEvaluator

logger = get_logger(__name__)


def _evaluation_result(
    request: StrategyProposalEvaluationRequest,
    *,
    status: ProposalEvaluationStatus,
    reason_codes: tuple[str, ...] = (),
    signals: tuple[StrategySignal, ...] = (),
    intent: TradeIntent | None = None,
) -> StrategyProposalEvaluationResult:
    """Build one deterministic final proposal result.

    Returns:
        Immutable final proposal result.
    """
    material = {
        "request": request.evaluation_request_id,
        "status": status,
        "reasons": reason_codes,
        "signals": tuple(signal.signal_id for signal in signals),
        "intent": None if intent is None else intent.intent_id,
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
        evaluated_signals=signals,
        trade_intent=intent,
        request_id=request.request_id,
        correlation_id=request.correlation_id,
    )


def _deterministic_event_id(evaluation_id: str) -> str:
    """Derive one repeatable UUID4-shaped event identifier.

    Returns:
        Canonical deterministic audit-event identifier.
    """
    digest = hashlib.sha256(evaluation_id.encode("utf-8")).digest()
    return f"evt-{uuid.UUID(bytes=digest[:16], version=4)}"


def _publish_evaluation(
    result: StrategyProposalEvaluationResult,
    request: StrategyProposalEvaluationRequest,
    context: StrategyExecutionContext,
) -> StrategyProposalEvaluationResult:
    """Persist one bounded idempotent proposal-evaluation audit event.

    Returns:
        Result carrying the persisted audit-event reference.
    """
    event_id = _deterministic_event_id(result.evaluation_id)
    unwrap_data_response(
        persist_audit_event(
            create_audit_event(
                event_id=event_id,
                timestamp=context.decision_timestamp,
                domain="strategy",
                action="PROPOSAL_EVALUATION",
                principal_id=request.principal_id,
                request_id=request.request_id,
                correlation_id=request.correlation_id,
                payload={
                    "evaluation_id": result.evaluation_id,
                    "status": result.status,
                    "reason_codes": result.reason_codes,
                    "source_proposal_id": result.source_proposal_id,
                    "strategy_id": result.strategy_id,
                    "strategy_version": result.strategy_version,
                    "signal_ids": tuple(
                        signal.signal_id for signal in result.evaluated_signals
                    ),
                    "intent_id": (
                        None
                        if result.trade_intent is None
                        else result.trade_intent.intent_id
                    ),
                },
            )
        ),
        operation="data.persist_audit_event.strategy_proposal_evaluation",
    )
    return result.model_copy(update={"audit_event_ref": event_id})


def _decision_from_signal(
    request: StrategyProposalEvaluationRequest,
    signal: StrategySignal,
    config: ValidatedStrategyConfig,
) -> StrategyDecision:
    """Build one canonical unsized market proposal from an active signal.

    Returns:
        Canonical proposal decision derived only from Strategy evidence.
    """
    digest = canonical_digest(
        {
            "signal_id": signal.signal_id,
            "config_hash": config.config_hash,
        }
    )
    decision_id = f"proposal-decision-{digest}"
    return StrategyDecision(
        decision_id=decision_id,
        sequence=0,
        action="PROPOSE",
        symbol=signal.symbol,
        side=signal.side,
        intent_type="OPEN",
        order_type="MARKET",
        valid_from=signal.timestamp,
        expires_at=request.expires_at,
        allow_partial_fills=False,
        rationale_ref=signal.signal_id,
        rationale_refs=(signal.signal_id,),
        diagnostic_facts={"signal_name": signal.signal_name},
        lineage={
            "strategy_id": signal.strategy_id,
            "strategy_version": signal.strategy_version,
            "config_hash": config.config_hash,
            "signal_id": signal.signal_id,
        },
    )


@guard_strategy_boundary
def evaluate_strategy_proposal(
    request: StrategyProposalEvaluationRequest,
    auth: object,
    ref: StrategyRef,
    config: StrategyConfig,
    policy: StrategyValidationPolicy,
    evidence: StrategySignalEvidence,
    indicators: tuple[object, ...],
    context: StrategyExecutionContext,
    evaluator: SignalEvaluator,
) -> StrategyProposalEvaluationResult:
    """Evaluate an external proposal through deterministic Strategy behavior.

    Args:
        request: Receiver-owned proposal request.
        auth: Authenticated principal context.
        ref: Exact unresolved Strategy reference.
        config: Declarative Strategy configuration.
        policy: Recorded Strategy validation policy.
        evidence: Point-in-time Strategy signal evidence.
        indicators: Official point-in-time Indicator results.
        context: Fixed deterministic execution context.
        evaluator: Hash-bound concrete Strategy evaluator.

    Returns:
        Audited proposal result with optional canonical intent.
    """
    logger.info("Evaluating external proposal %s", request.evaluation_request_id)
    validation = _validate_strategy_proposal(
        request,
        auth,
        ref,
        config,
        policy,
        evidence,
        context,
        evaluator,
    )
    if isinstance(validation, StrategyProposalEvaluationResult):
        return _publish_evaluation(validation, request, context)
    validated_ref, validated_config = validation
    signals = unwrap_strategy_response(
        evaluate_strategy_signals(
            validated_ref,
            validated_config,
            evidence,
            indicators,
            context,
            evaluator,
        ),
        operation="strategy.proposal_intake.evaluate_strategy_signals",
    )
    active = tuple(
        signal
        for signal in signals
        if signal.active and signal.symbol == request.instrument
    )
    if not active:
        result = _evaluation_result(
            request,
            status="no_signal",
            reason_codes=("NO_ACTIVE_SIGNAL",),
            signals=signals,
        )
        return _publish_evaluation(result, request, context)
    if len(active) != 1:
        result = _evaluation_result(
            request,
            status="rejected",
            reason_codes=("AMBIGUOUS_ACTIVE_SIGNALS",),
            signals=signals,
        )
        return _publish_evaluation(result, request, context)
    signal = active[0]
    if signal.side != request.requested_direction:
        result = _evaluation_result(
            request,
            status="no_signal",
            reason_codes=("REQUEST_DIRECTION_NOT_SUPPORTED",),
            signals=signals,
        )
        return _publish_evaluation(result, request, context)
    intent = None
    if request.evaluation_scope == "TRADE_INTENT_IF_SUPPORTED":
        decision = _decision_from_signal(request, signal, validated_config)
        base_intent = unwrap_strategy_response(
            build_trade_intent(decision, context, 0),
            operation="strategy.proposal_intake.build_trade_intent",
        )
        intent = _bind_proposal_lineage(base_intent, request)
    result = _evaluation_result(
        request,
        status="accepted_for_evaluation",
        signals=signals,
        intent=intent,
    )
    return _publish_evaluation(result, request, context)


__all__ = ["evaluate_strategy_proposal"]
