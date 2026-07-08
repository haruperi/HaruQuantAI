"""Final RiskGovernor decision synthesis logic.

Converts ordered gate outputs into one canonical RiskDecisionPackage
without performing audit writes, signing, persistence, or broker mutation.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from pydantic import Field

from app.services.risk.models import (
    PortfolioRiskSnapshot,
    ProposedAllocation,
    ProposedTrade,
    RiskContract,
    RiskDecisionPackage,
    RiskSeverity,
    StrategyAdmissionRequest,
)
from app.services.risk.models.enums import (
    RiskDecisionStatus,
    RiskReasonCode,
)
from app.services.risk.policy.contracts import EffectiveRiskPolicy  # noqa: TC001
from app.utils.logger import logger
from app.utils.normalization import utc_now


class GateResult(RiskContract):
    """The result of evaluating a single risk gate."""

    gate_name: str = Field(..., description="Unique name of the evaluated gate.")
    status: RiskDecisionStatus = Field(
        ..., description="Decision outcome for this gate."
    )
    reason_code: RiskReasonCode = Field(
        ..., description="Reason code associated with any breach or warning."
    )
    message: str = Field(..., description="Human-readable detail message.")
    severity: RiskSeverity = Field(
        ..., description="Severity level of the gate result."
    )
    breached: bool = Field(..., description="True if a breach was triggered.")
    calculated_volume: Decimal | None = Field(
        default=None, description="Recommended/reduced volume size in lots."
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Calculated values or gate context."
    )


class RiskReductionPlan(RiskContract):
    """Aggregation of volume/size reductions across all risk evaluation gates."""

    original_size: Decimal | None = Field(
        default=None, description="Original requested lot size."
    )
    recommended_size: Decimal | None = Field(
        default=None, description="Recommended size from volatility sizing."
    )
    correlation_reduced_size: Decimal | None = Field(
        default=None, description="Size limit suggested by correlation limits."
    )
    exposure_reduced_size: Decimal | None = Field(
        default=None, description="Size limit suggested by exposure limits."
    )
    drawdown_reduced_size: Decimal | None = Field(
        default=None, description="Size limit suggested by drawdown throttling."
    )
    stress_reduced_size: Decimal | None = Field(
        default=None, description="Size limit suggested by stress test limits."
    )
    final_reduced_size: Decimal | None = Field(
        default=None, description="Final combined lot size (minimum of all)."
    )
    applied_reductions: list[str] = Field(
        default_factory=list,
        description="List of gates that applied size reductions.",
    )


class GovernorEvaluationContext(RiskContract):
    """The collection of inputs, resolved policy, and outputs.

    Represents the context for a governor review run.
    """

    decision_id: str = Field(..., description="Unique decision ID.")
    request_id: str = Field(..., description="Associated request ID.")
    workflow_id: str = Field(..., description="Associated workflow ID.")
    proposed_action: (
        ProposedTrade | ProposedAllocation | StrategyAdmissionRequest | None
    ) = Field(default=None, description="The proposed action under evaluation.")
    policy: EffectiveRiskPolicy = Field(..., description="The resolved active policy.")
    gate_results: list[GateResult] = Field(
        default_factory=list,
        description="Ordered checklist of gate evaluation results.",
    )
    requested_size: Decimal | None = Field(
        default=None, description="Requested lot volume."
    )
    risk_snapshot: PortfolioRiskSnapshot | None = Field(
        default=None, description="Snapshot parameters for portfolio risk."
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary evaluation details."
    )


STATUS_PRECEDENCE: dict[RiskDecisionStatus, int] = {
    RiskDecisionStatus.HALT_ALL: 0,
    RiskDecisionStatus.HALT_STRATEGY: 1,
    RiskDecisionStatus.BLOCK: 2,
    RiskDecisionStatus.REJECT: 3,
    RiskDecisionStatus.NEEDS_MORE_EVIDENCE: 4,
    RiskDecisionStatus.NEEDS_APPROVAL: 5,
    RiskDecisionStatus.REDUCE_SIZE: 6,
    RiskDecisionStatus.APPROVE: 7,
}


def determine_decision_status(
    results: Sequence[GateResult], _policy: EffectiveRiskPolicy
) -> RiskDecisionStatus:
    """Applies precedence rules to determine final decision status.

    Checks the status of all gate results and returns the one with the highest
    severity (lowest rank index in STATUS_PRECEDENCE). If no results are present,
    defaults to APPROVE.

    Args:
        results: Ordered checklist of evaluated gate results.
        _policy: The resolved active policy rules.

    Returns:
        RiskDecisionStatus: Final synthesized status.
    """
    logger.info("Determining final decision status from %d gate results.", len(results))
    if not results:
        logger.debug("No gate results provided; defaulting status to APPROVE.")
        return RiskDecisionStatus.APPROVE

    highest_precedence_status = RiskDecisionStatus.APPROVE
    highest_precedence_rank = STATUS_PRECEDENCE[RiskDecisionStatus.APPROVE]

    for res in results:
        rank = STATUS_PRECEDENCE.get(
            res.status, STATUS_PRECEDENCE[RiskDecisionStatus.BLOCK]
        )
        if rank < highest_precedence_rank:
            highest_precedence_rank = rank
            highest_precedence_status = res.status

    logger.debug(
        "Synthesized highest precedence status: %s (rank %d)",
        highest_precedence_status,
        highest_precedence_rank,
    )
    return highest_precedence_status


def select_primary_risk_reason(results: Sequence[GateResult]) -> RiskReasonCode:
    """Selects deterministic primary failure or warning reason code.

    Finds the gate results that failed (status != APPROVE). From those, selects the one
    with the highest severity rank (using risk_severity_rank). In case of ties,
    uses the first one in list order. If all gates passed, returns RiskReasonCode.OK.

    Args:
        results: Sequence of evaluated gate results.

    Returns:
        RiskReasonCode: Primary failure or warning reason code.
    """
    logger.info("Selecting primary risk reason from %d gate results.", len(results))
    from app.services.risk.models.enums import risk_severity_rank

    failed_results = [r for r in results if r.status != RiskDecisionStatus.APPROVE]
    if not failed_results:
        logger.debug("No failures found; primary reason is OK.")
        return RiskReasonCode.OK

    primary_res = failed_results[0]
    max_rank = risk_severity_rank(primary_res.severity)

    for res in failed_results[1:]:
        rank = risk_severity_rank(res.severity)
        if rank > max_rank:
            max_rank = rank
            primary_res = res

    logger.debug(
        "Selected primary failure gate: %s, reason: %s, severity: %s",
        primary_res.gate_name,
        primary_res.reason_code,
        primary_res.severity,
    )
    return primary_res.reason_code


def aggregate_reductions(results: Sequence[GateResult]) -> RiskReductionPlan:  # noqa: C901, PLR0912
    """Combines size/volume reductions across all evaluation gates.

    Inspects sizing, correlation, exposure, drawdown, and stress gates
    for calculated or reduced volumes, and computes the final combined size.

    Args:
        results: Sequence of evaluated gate results.

    Returns:
        RiskReductionPlan: The aggregated reduction details.
    """
    logger.info("Aggregating size reductions from %d gate results.", len(results))
    original_size = None
    recommended_size = None
    correlation_reduced_size = None
    exposure_reduced_size = None
    drawdown_reduced_size = None
    stress_reduced_size = None

    # Check for original size across all result details
    for res in results:
        details = res.details or {}
        if "original_size" in details:
            val = details["original_size"]
            if val is not None:
                original_size = Decimal(str(val))
        elif "requested_size" in details:
            val = details["requested_size"]
            if val is not None:
                original_size = Decimal(str(val))

    for res in results:
        gate_name = res.gate_name.lower()
        val = res.calculated_volume
        if val is None:
            # Fallback to check details
            val = res.details.get("calculated_volume") or res.details.get(
                "reduced_volume"
            )
        if val is not None:
            val_dec = Decimal(str(val))
            if gate_name == "sizing":
                recommended_size = val_dec
            elif gate_name == "correlation":
                correlation_reduced_size = val_dec
            elif gate_name == "exposure":
                exposure_reduced_size = val_dec
            elif gate_name == "drawdown":
                drawdown_reduced_size = val_dec
            elif gate_name == "stress":
                stress_reduced_size = val_dec

    # Final size is the minimum of all specified reductions
    sizes = []
    for s in (
        recommended_size,
        correlation_reduced_size,
        exposure_reduced_size,
        drawdown_reduced_size,
        stress_reduced_size,
    ):
        if s is not None:
            sizes.append(s)

    final_reduced_size = min(sizes) if sizes else original_size

    # Track which gates actually applied reductions
    applied_reductions = []
    baseline = original_size if original_size is not None else recommended_size
    if baseline is not None:
        if correlation_reduced_size is not None and correlation_reduced_size < baseline:
            applied_reductions.append("correlation")
        if exposure_reduced_size is not None and exposure_reduced_size < baseline:
            applied_reductions.append("exposure")
        if drawdown_reduced_size is not None and drawdown_reduced_size < baseline:
            applied_reductions.append("drawdown")
        if stress_reduced_size is not None and stress_reduced_size < baseline:
            applied_reductions.append("stress")

    plan = RiskReductionPlan(
        original_size=original_size,
        recommended_size=recommended_size,
        correlation_reduced_size=correlation_reduced_size,
        exposure_reduced_size=exposure_reduced_size,
        drawdown_reduced_size=drawdown_reduced_size,
        stress_reduced_size=stress_reduced_size,
        final_reduced_size=final_reduced_size,
        applied_reductions=applied_reductions,
    )
    logger.debug("Aggregated reductions plan: %s", plan.model_dump())
    return plan


def is_decision_token_eligible(decision: RiskDecisionPackage) -> bool:
    """Returns True only for bounded approved or size-reduced outcomes.

    Args:
        decision: The synthesized decision package.

    Returns:
        bool: True if eligible for cryptographic token signing.
    """
    logger.info(
        "Checking decision token eligibility for decision ID: %s",
        decision.decision_id,
    )
    if decision.status not in (
        RiskDecisionStatus.APPROVE,
        RiskDecisionStatus.REDUCE_SIZE,
    ):
        logger.debug("Decision status %s is not eligible for token.", decision.status)
        return False

    if decision.approved_size is not None and decision.approved_size <= 0:
        logger.debug(
            "Decision approved size %s is non-positive; not eligible for token.",
            decision.approved_size,
        )
        return False

    if decision.expiry is not None and decision.expiry <= utc_now():
        logger.debug("Decision is expired; not eligible for token.")
        return False

    logger.debug("Decision is eligible for token.")
    return True


def synthesize_decision(context: GovernorEvaluationContext) -> RiskDecisionPackage:
    """Creates a final RiskDecisionPackage from ordered gate results.

    Does not write audits, sign tokens, or persist states.

    Args:
        context: Synthesized evaluation context holding parameters and gate results.

    Returns:
        RiskDecisionPackage: Synthesized canonical outcome package.
    """
    logger.info("Synthesizing decision package for request: %s", context.request_id)
    status = determine_decision_status(context.gate_results, context.policy)
    _reason_code = select_primary_risk_reason(context.gate_results)
    reduction_plan = aggregate_reductions(context.gate_results)

    composite_breach_flags = []
    breach_messages = []
    reason_codes = []
    for res in context.gate_results:
        if res.status != RiskDecisionStatus.APPROVE:
            composite_breach_flags.append(res.gate_name)
            reason_codes.append(str(res.reason_code))
            breach_messages.append(f"{res.gate_name}: {res.message}")

    if composite_breach_flags:
        rule_key = composite_breach_flags[0]
        reason = "; ".join(breach_messages)
    else:
        rule_key = "default_approve"
        reason = "All risk gates passed successfully."

    config_hash = context.policy.resolved_config.content_hash()

    requested_size = context.requested_size
    if requested_size is None and context.proposed_action:
        requested_size = getattr(context.proposed_action, "volume", None) or getattr(
            context.proposed_action, "requested_size", None
        )

    approved_size = None
    if status in (RiskDecisionStatus.APPROVE, RiskDecisionStatus.REDUCE_SIZE):
        approved_size = (
            reduction_plan.final_reduced_size
            if reduction_plan.final_reduced_size is not None
            else requested_size
        )

    details = dict(context.details)
    details.update(
        {
            "reduction_plan": reduction_plan.model_dump(),
            "policy_id": context.policy.policy_id,
            "policy_version": (
                context.policy.provenance.get("policy_version")
                if context.policy.provenance
                else None
            ),
            "policy_scope": (
                context.policy.provenance.get("policy_scope")
                if context.policy.provenance
                else None
            ),
        }
    )

    pkg = RiskDecisionPackage(
        decision_id=context.decision_id,
        request_id=context.request_id,
        workflow_id=context.workflow_id,
        status=status,
        rule_key=rule_key,
        snapshot_as_of=utc_now(),
        config_hash=config_hash,
        reason=reason,
        composite_breach_flags=composite_breach_flags,
        calculated_volume=approved_size,
        details=details,
        requested_size=requested_size,
        approved_size=approved_size,
        max_allowed_size=reduction_plan.final_reduced_size,
        action=(
            getattr(context.proposed_action, "action", None)
            or (
                context.proposed_action.__class__.__name__
                if context.proposed_action is not None
                else None
            )
        ),
        reason_codes=reason_codes,
        risk_snapshot=context.risk_snapshot,
        policy_hash=context.policy.policy_hash,
        policy_version=(
            context.policy.provenance.get("policy_version")
            if context.policy.provenance
            else None
        ),
        policy_scope=(
            context.policy.provenance.get("policy_scope")
            if context.policy.provenance
            else None
        ),
    )

    logger.info(
        "Decision synthesis complete: ID=%s, status=%s",
        pkg.decision_id,
        pkg.status,
    )
    return pkg


# Rebuild schemas to register types correctly
GateResult.model_rebuild()
RiskReductionPlan.model_rebuild()
GovernorEvaluationContext.model_rebuild()
