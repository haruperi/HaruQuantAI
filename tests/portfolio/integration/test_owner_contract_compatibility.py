"""Producer-consumer compatibility tests for Portfolio owner requests."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app.services.analytics import is_analytics_value
from app.services.portfolio import execute_portfolio_handle_operation
from app.utils import get_logger

from tests.portfolio.unit.test_workflows import _plan, _service

ActivePortfolioAllocation = object
PortfolioSettings = object
logger = get_logger(__name__)


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
    operation = execute_portfolio_handle_operation(
        service,
        "submit_rebalance",
        _plan(active_allocation, portfolio_now, portfolio_settings),
        account_evidence_ref="account-1",
        market_evidence_ref="market-1",
        fx_evidence_refs=(),
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        approval_token_ref="approval-token-ref-1",
        trading_request_id="req-44444444-4444-4444-8444-444444444444",
        valid_until=portfolio_now + timedelta(minutes=5),
    )
    await operation
    assert (
        getattr(recorder.last_risk_request, "schema_id", None)
        == "risk.allocation_review_request.v1"
    )
    assert (
        getattr(recorder.last_trading_request, "schema_id", None)
        == "trading.portfolio_rebalance_execution_request.v1"
    )
    assert is_analytics_value(
        recorder.last_analytics_request,
        "PortfolioRebalanceMeasurementRequest",
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
