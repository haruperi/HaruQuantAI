"""Integration test for Risk-reviewed Trading/Analytics Portfolio rebalance."""

# ruff: noqa: INP001

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import ActivePortfolioAllocation
from app.utils import logger
from tests.portfolio.unit.test_workflows import _plan, _service


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend.

    Returns:
        AnyIO backend name.
    """
    logger.debug("Selecting asyncio for Portfolio integration workflow")
    return "asyncio"


@pytest.mark.anyio
async def test_rebalance_chain_preserves_risk_trading_and_analytics_ownership(
    active_allocation: ActivePortfolioAllocation,
    portfolio_now: datetime,
    portfolio_settings: PortfolioSettings,
) -> None:
    """WF-PORT-005/006 ends with hash-bound measured execution truth."""
    logger.info("Testing complete Portfolio rebalance integration workflow")
    service, recorder, store = _service(
        active_allocation,
        portfolio_now,
        portfolio_settings,
    )
    original = _plan(active_allocation, portfolio_now, portfolio_settings)
    measured = await service.submit_rebalance(
        original,
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
    versions = tuple(
        plan
        for (plan_id, _version), plan in store.plans.items()
        if plan_id == original.plan_id
    )
    assert tuple(plan.status for plan in versions) == (
        "executed_unmeasured",
        "measured",
    )
    assert measured.analytics_measurement_ref is not None
    assert recorder.last_trading_request is not None
    assert recorder.last_analytics_request is not None
    assert recorder.last_analytics_request.trading_execution_ref == (
        measured.trading_execution_ref
    )
