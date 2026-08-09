"""Promotion contract consumer port (TC-IMP-OPT-10).

Extends ``FEAT-OPT-07``: Optimization outputs become versioned candidate profiles that
require Research/Strategy/Risk approval before use. The authoritative cross-domain
approval gate is owned by Research (``TC-IMP-RES-10``), which is still ``Partial``.
This module declares the narrow consumer port and a deterministic fail-closed fallback:
a missing approval provider yields ``NOT_PROMOTED`` and the candidate stays at
``ready_for_risk_review`` / ``research_only``. Optimization never auto-promotes a
candidate and never claims live readiness (NFR-OPT-003 safety, financial-records
append-only authority).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from app.utils import get_logger

logger = get_logger(__name__)

PROMOTION_APPROVED = "APPROVED_FOR_ADOPTION"
PROMOTION_NOT_PROMOTED = "NOT_PROMOTED"


class PromotionGatePort(Protocol):
    """Narrow consumer port for the Research-owned cross-domain approval gate.

    The provider (Research ``TC-IMP-RES-10``) supplies the production approval gate
    that coordinates Research/Strategy/Risk sign-off before a candidate profile may be
    adopted.
    """

    def evaluate_promotion(
        self,
        *,
        reproducibility_hash: str,  # noqa: ARG002
        strategy_ref: str,  # noqa: ARG002
    ) -> Mapping[str, object]:
        """Return validated cross-domain promotion approval evidence.

        Args:
            reproducibility_hash: Candidate result reproducibility identity.
            strategy_ref: Approved Strategy version reference.

        Raises:
            NotImplementedError: Protocol declarations are not executable.
        """
        logger.debug("Declaring promotion gate port")
        raise NotImplementedError


def evaluate_promotion_gate(
    *,
    reproducibility_hash: str,
    strategy_ref: str,
    provider: PromotionGatePort | None,
    final_decision: str,
) -> dict[str, object]:
    """Evaluate candidate promotion, failing closed without an approval provider.

    Args:
        reproducibility_hash: Candidate result reproducibility identity.
        strategy_ref: Approved Strategy version reference.
        provider: Optional injected Research-owned approval-gate provider.
        final_decision: The advisory ``OptimizationResult`` final decision string
            (one of ``ready_for_risk_review``, ``validation_needed``,
            ``research_only``, ``rejected``, ``failed``).

    Returns:
        Promotion-evidence mapping. A missing provider yields ``NOT_PROMOTED`` with the
        candidate held at its advisory final decision; a present provider returns its
        evidence. Promotion to ``APPROVED_FOR_ADOPTION`` is only ever the provider's
        authoritative decision — never an Optimization inference.

    Raises:
        ValueError: If the final decision is not a recognized advisory value.
    """
    if final_decision not in {
        "ready_for_risk_review",
        "validation_needed",
        "research_only",
        "rejected",
        "failed",
    }:
        raise ValueError("final_decision is not a recognized advisory value")
    logger.info(
        "Evaluating promotion gate | provider=%s decision=%s",
        "present" if provider is not None else "absent",
        final_decision,
    )
    if provider is None:
        return {
            "promotion_status": PROMOTION_NOT_PROMOTED,
            "advisory_final_decision": final_decision,
            "reason": "approval_gate_absent",
            "deferred_to": "TC-IMP-RES-10",
        }
    evidence = dict(
        provider.evaluate_promotion(
            reproducibility_hash=reproducibility_hash, strategy_ref=strategy_ref
        )
    )
    evidence.setdefault("promotion_status", PROMOTION_NOT_PROMOTED)
    evidence.setdefault("advisory_final_decision", final_decision)
    return evidence


def get_promotion_contract_version() -> str:
    """Return the promotion contract consumer-port version.

    Returns:
        The canonical ``v1`` version string.
    """
    return "v1"


__all__: tuple[str, ...] = (
    "PROMOTION_APPROVED",
    "PROMOTION_NOT_PROMOTED",
    "PromotionGatePort",
    "evaluate_promotion_gate",
    "get_promotion_contract_version",
)
