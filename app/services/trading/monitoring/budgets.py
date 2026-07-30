"""Fail-closed validation of Risk-owned rebalance budget authority."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from app.services.risk import get_decision_state
from app.services.trading.contracts import (
    PortfolioRebalanceExecutionRequest,
    TradingError,
)
from app.services.trading.contracts.responses import success_trading_response
from app.utils import get_logger

type StandardResponse[T] = Any
AllocationRiskDecision = Any
PortfolioBudgetExecutionVerdict = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)


class BudgetGate:
    """Validate current Risk-owned budget evidence without calculating policy."""

    @staticmethod
    def _validate_value(
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
            and allocation.state is get_decision_state("APPROVE")
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

    @staticmethod
    def validate(
        request: PortfolioRebalanceExecutionRequest,
        allocation: AllocationRiskDecision,
        verdict: PortfolioBudgetExecutionVerdict,
        *,
        now: datetime,
    ) -> StandardResponse[None]:
        """Validate budget authority and return a standard response.

        Args:
            request: Trading-owned canonical rebalance execution request.
            allocation: Current Risk-owned allocation decision.
            verdict: Current Risk-owned execution-time budget verdict.
            now: Injected aware UTC evaluation time.

        Returns:
            Successful empty response or a canonical mapped Trading error.
        """
        try:
            BudgetGate._validate_value(request, allocation, verdict, now=now)
        except TradingError as error:
            from app.services.trading.contracts.errors import map_trading_error

            return map_trading_error(error, {"plan_id": request.plan_id})
        return success_trading_response(
            None,
            risk_level="high",
            legacy_status="approved",
            extensions={"plan_id": request.plan_id},
        )


def validate_budget_authority(
    request: PortfolioRebalanceExecutionRequest,
    allocation: AllocationRiskDecision,
    verdict: PortfolioBudgetExecutionVerdict,
    *,
    now: datetime,
) -> StandardResponse[None]:
    """Validate current Risk-owned budget authority.

    Args:
        request: Canonical rebalance execution request.
        allocation: Current Risk allocation decision.
        verdict: Current execution-time budget verdict.
        now: Injected aware UTC evaluation time.

    Returns:
        Successful empty response or a canonical mapped Trading error.
    """
    return BudgetGate.validate(request, allocation, verdict, now=now)


__all__ = ["validate_budget_authority"]
