"""Runnable Portfolio reduce-only action usage example."""

from __future__ import annotations

from decimal import Decimal

from app.services.portfolio.contracts import PortfolioRebalanceAction
from app.utils import logger


def test_build_reduce_only_rebalance_action() -> None:
    """Build a public action that can only reduce existing exposure."""
    logger.info("Running Portfolio reduce-only rebalance usage example")
    action = PortfolioRebalanceAction(
        action_id="action-1",
        component_id="component-a",
        action="reduce_exposure",
        reduce_only=True,
        current_exposure=Decimal("0.6"),
        target_exposure=Decimal("0.5"),
        reduction_amount=Decimal("0.1"),
        eligibility_decision_id="eligibility-a",
    )

    assert action.action == "reduce_exposure"
    assert action.reduce_only is True
