"""Proposal-lineage binding that cannot influence deterministic intent fields."""

from __future__ import annotations

from app.services.strategy.contracts.responses import guard_strategy_boundary
from app.services.strategy.intents.intent import TradeIntent
from app.services.strategy.proposal_intake.requests import (
    StrategyProposalEvaluationRequest,  # noqa: TC001
)
from app.utils import get_logger

logger = get_logger(__name__)


def _bind_proposal_lineage(
    intent: TradeIntent,
    request: StrategyProposalEvaluationRequest,
) -> TradeIntent:
    """Bind source identities only to the intent lineage mapping.

    Returns:
        Canonical intent with external source identities added to lineage.
    """
    payload = intent.model_dump(mode="python")
    payload["lineage"] = {
        **dict(intent.lineage),
        "source_proposal_id": request.source_proposal_id,
        "source_task_id": request.source_task_id,
        "source_content_hash": request.source_content_hash,
        "proposal_evaluation_request_id": request.evaluation_request_id,
    }
    return TradeIntent.model_validate(payload)


@guard_strategy_boundary
def bind_proposal_lineage(
    intent: TradeIntent,
    request: StrategyProposalEvaluationRequest,
) -> TradeIntent:
    """Add proposal identity as lineage without changing deterministic fields.

    Args:
        intent: Independently constructed canonical Strategy intent.
        request: Receiver-owned proposal request.

    Returns:
        Intent with source proposal identity added only to lineage.
    """
    logger.info("Binding external proposal identity to Strategy intent lineage")
    return _bind_proposal_lineage(intent, request)


__all__ = ["bind_proposal_lineage"]
