"""Evaluated gating of a model-profile change.

A one-line profile change may select another supported model only after every
required gate passes. Missing evidence is a failure, not a default pass, so an
unevaluated change can never activate silently.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.agentic.runtime.models import REQUIRED_UPGRADE_GATES, ModelProfile
from app.utils import get_logger

logger = get_logger(__name__)


class _ModelUpgradeDecision(BaseModel):
    """The outcome of evaluating one proposed model-profile change.

    Attributes:
        approved: Whether activation is permitted.
        current_profile_id: Profile currently in force.
        candidate_profile_id: Proposed profile.
        failed_gates: Ordered gates that did not pass.
        missing_gates: Ordered required gates with no recorded evidence.
        reason: Enumerated terminal reason.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    approved: bool
    current_profile_id: str
    candidate_profile_id: str
    failed_gates: tuple[str, ...]
    missing_gates: tuple[str, ...]
    reason: Literal[
        "approved",
        "gate_failed",
        "gate_evidence_missing",
        "candidate_not_evaluated",
        "capability_regression",
    ]


def validate_model_upgrade(
    current: ModelProfile,
    candidate: ModelProfile,
    gate_results: Mapping[str, bool],
) -> _ModelUpgradeDecision:
    """Evaluate whether a proposed model-profile change may activate.

    Args:
        current: Profile currently in force.
        candidate: Proposed replacement profile.
        gate_results: Recorded pass or fail evidence per required gate.

    Returns:
        The upgrade decision, approved only when every gate passed.
    """
    logger.info(
        "Evaluating model upgrade from %s to %s",
        current.profile_id,
        candidate.profile_id,
    )
    missing = tuple(gate for gate in REQUIRED_UPGRADE_GATES if gate not in gate_results)
    failed = tuple(
        gate
        for gate in REQUIRED_UPGRADE_GATES
        if gate in gate_results and not gate_results[gate]
    )

    if candidate.evaluation_state != "evaluated":
        logger.warning(
            "Refusing model upgrade: candidate %s is %s",
            candidate.profile_id,
            candidate.evaluation_state,
        )
        return _ModelUpgradeDecision(
            approved=False,
            current_profile_id=current.profile_id,
            candidate_profile_id=candidate.profile_id,
            failed_gates=failed,
            missing_gates=missing,
            reason="candidate_not_evaluated",
        )

    # A narrower context or output ceiling silently truncates governed work, so
    # it is treated as a capability regression rather than an acceptable change.
    regressed = (
        candidate.max_context_tokens < current.max_context_tokens
        or candidate.max_output_tokens < current.max_output_tokens
        or candidate.structured_output_mode != current.structured_output_mode
    )
    if regressed:
        logger.warning(
            "Refusing model upgrade: candidate %s regresses a declared capability",
            candidate.profile_id,
        )
        return _ModelUpgradeDecision(
            approved=False,
            current_profile_id=current.profile_id,
            candidate_profile_id=candidate.profile_id,
            failed_gates=failed,
            missing_gates=missing,
            reason="capability_regression",
        )

    if missing:
        logger.warning(
            "Refusing model upgrade: %d required gates have no evidence",
            len(missing),
        )
        return _ModelUpgradeDecision(
            approved=False,
            current_profile_id=current.profile_id,
            candidate_profile_id=candidate.profile_id,
            failed_gates=failed,
            missing_gates=missing,
            reason="gate_evidence_missing",
        )

    if failed:
        logger.warning("Refusing model upgrade: %d gates failed", len(failed))
        return _ModelUpgradeDecision(
            approved=False,
            current_profile_id=current.profile_id,
            candidate_profile_id=candidate.profile_id,
            failed_gates=failed,
            missing_gates=(),
            reason="gate_failed",
        )

    logger.info("Model upgrade to %s approved", candidate.profile_id)
    return _ModelUpgradeDecision(
        approved=True,
        current_profile_id=current.profile_id,
        candidate_profile_id=candidate.profile_id,
        failed_gates=(),
        missing_gates=(),
        reason="approved",
    )


def get_required_upgrade_gates() -> tuple[str, ...]:
    """Return the ordered gates a candidate profile must pass.

    Returns:
        Ordered required gate identities.
    """
    return REQUIRED_UPGRADE_GATES
