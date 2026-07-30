"""Function-only constructors for proposal-intake contract values."""

from __future__ import annotations

from app.services.strategy.proposal_intake.requests import (
    StrategyProposalEvaluationRequest,
)
from app.services.strategy.proposal_intake.results import (
    StrategyProposalEvaluationResult,
)
from app.utils import canonical_digest


def create_strategy_proposal_evaluation_request(
    **kwargs: object,
) -> StrategyProposalEvaluationRequest:
    """Create one content-addressed proposal-evaluation request.

    Args:
        **kwargs: Complete request fields excluding derived identities.

    Returns:
        Immutable proposal-evaluation request.

    Raises:
        ValueError: If a caller attempts to supply a derived identity.
    """
    prohibited = {"evaluation_request_id", "idempotency_key"} & kwargs.keys()
    if prohibited:
        raise ValueError("proposal request identities are derived")
    material = {
        "contract_version": "v1",
        "schema_id": "strategy.proposal_evaluation_request.v1",
        **kwargs,
    }
    digest = canonical_digest(material)
    return StrategyProposalEvaluationRequest.model_validate(
        {
            **kwargs,
            "evaluation_request_id": f"proposal-eval-{digest}",
            "idempotency_key": digest,
        }
    )


def create_strategy_proposal_evaluation_result(
    **kwargs: object,
) -> StrategyProposalEvaluationResult:
    """Create one immutable proposal-evaluation result.

    Args:
        **kwargs: Complete result field values.

    Returns:
        Immutable proposal-evaluation result.
    """
    return StrategyProposalEvaluationResult.model_validate(kwargs)


__all__ = [
    "create_strategy_proposal_evaluation_request",
    "create_strategy_proposal_evaluation_result",
]
