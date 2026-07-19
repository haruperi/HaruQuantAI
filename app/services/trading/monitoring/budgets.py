"""Fail-closed validation of Risk-owned rebalance budget authority."""

from datetime import datetime

from app.services.risk.contracts import (
    AllocationRiskDecision,
    DecisionState,
    PortfolioBudgetExecutionVerdict,
)
from app.services.trading.contracts import (
    PortfolioRebalanceExecutionRequest,
    TradingError,
)
from app.utils import logger


class BudgetGate:
    """Validate current Risk-owned budget evidence without calculating policy."""

    @staticmethod
    def validate(
        request: PortfolioRebalanceExecutionRequest,
        allocation: AllocationRiskDecision,
        verdict: PortfolioBudgetExecutionVerdict,
        *,
        now: datetime,
    ) -> None:
        """Validate budget authority for one exact immutable rebalance request.

        Args:
            request: Trading-owned canonical rebalance execution request.
            allocation: Current Risk-owned allocation decision.
            verdict: Current Risk-owned execution-time budget verdict.
            now: Injected aware UTC evaluation time.

        Raises:
            TradingError: If evidence is inactive, stale, blocked, or mismatched.
        """
        logger.info("Validating Risk budget authority for plan %s", request.plan_id)
        allocation_matches = (
            allocation.decision_id == request.allocation_decision_id
            and allocation.portfolio_id == request.portfolio_id
            and allocation.reviewed_version == request.allocation_version
            and allocation.state is DecisionState.APPROVE
            and allocation.active
            and bool(allocation.risk_budget_projection)
            and allocation.issued_at <= now < allocation.expires_at
        )
        verdict_matches = (
            verdict.allocation_decision_id == allocation.decision_id
            and verdict.portfolio_id == request.portfolio_id
            and verdict.allocation_version == request.allocation_version
            and verdict.plan_id == request.plan_id
            and verdict.plan_hash == request.canonical_hash
            and verdict.request_id == request.request_id
            and verdict.workflow_id == request.workflow_id
            and verdict.correlation_id == request.correlation_id
            and verdict.issued_at <= now < verdict.expires_at
            and verdict.allowed
        )
        if not allocation_matches or not verdict_matches:
            raise TradingError(
                "BUDGET_BLOCKED",
                "Risk budget authority is missing, stale, blocked, or mismatched",
                trace_context={
                    "request_id": request.request_id,
                    "plan_id": request.plan_id,
                    "allocation_decision_id": request.allocation_decision_id,
                },
            )


__all__ = ["BudgetGate"]
