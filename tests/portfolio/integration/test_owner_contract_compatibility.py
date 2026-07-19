"""Producer-consumer compatibility tests for Portfolio owner requests."""

# ruff: noqa: INP001

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app.services.analytics import PortfolioRebalanceMeasurementRequest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import ActivePortfolioAllocation
from app.services.risk import AllocationReviewRequest
from app.services.trading import PortfolioRebalanceExecutionRequest
from app.utils import logger
from tests.portfolio.unit.test_workflows import _plan, _service


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend.

    Returns:
        AnyIO backend name.
    """
    logger.debug("Selecting asyncio for Portfolio compatibility tests")
    return "asyncio"


@pytest.mark.anyio
async def test_rebalance_uses_each_receivers_public_owned_contract(
    active_allocation: ActivePortfolioAllocation,
    portfolio_now: datetime,
    portfolio_settings: PortfolioSettings,
) -> None:
    """Risk, Trading, and Analytics each receive their own public v1 model."""
    logger.info("Testing Portfolio owner-contract receiver compatibility")
    service, recorder, _ = _service(
        active_allocation,
        portfolio_now,
        portfolio_settings,
    )
    await service.submit_rebalance(
        _plan(active_allocation, portfolio_now, portfolio_settings),
        account_evidence_ref="account-1",
        market_evidence_ref="market-1",
        fx_evidence_refs=(),
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        approval_token_ref="approval-token-ref-1",
        trading_request_id="trading-request-1",
        valid_until=portfolio_now + timedelta(minutes=5),
    )
    assert isinstance(recorder.last_risk_request, AllocationReviewRequest)
    assert isinstance(
        recorder.last_trading_request,
        PortfolioRebalanceExecutionRequest,
    )
    assert isinstance(
        recorder.last_analytics_request,
        PortfolioRebalanceMeasurementRequest,
    )
    assert recorder.last_trading_request is not None
    assert set(recorder.last_trading_request.actions[0]) == {
        "action_id",
        "component_id",
        "eligibility_decision_id",
        "action",
        "reduce_only",
        "current_exposure",
        "target_exposure",
        "reduction_amount",
    }
