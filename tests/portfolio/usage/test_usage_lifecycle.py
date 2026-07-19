"""Runnable usage evidence for governed Portfolio lifecycle workflows."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from app.services.portfolio import PortfolioService as PublicPortfolioService
from app.services.portfolio.api import PortfolioService
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
    logger.debug("Selecting asyncio for Portfolio lifecycle usage")
    return "asyncio"


@pytest.mark.anyio
async def test_usage_lifecycle_submit_and_measure_rebalance(
    active_allocation: ActivePortfolioAllocation,
    portfolio_now: datetime,
    portfolio_settings: PortfolioSettings,
) -> None:
    """Submit receiver-owned requests and retain measured immutable plan truth."""
    logger.info("Running governed Portfolio rebalance lifecycle usage")
    service, recorder, _ = _service(
        active_allocation,
        portfolio_now,
        portfolio_settings,
    )
    measured = await service.submit_rebalance(
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
    assert measured.status == "measured"
    assert recorder.trading_calls == 1
    assert recorder.analytics_calls == 1


def test_usage_lifecycle_package_root_exposes_portfolio_service() -> None:
    """Import the typed Portfolio service from the supported package root."""
    logger.info("Running Portfolio package-root service usage")
    assert PublicPortfolioService is PortfolioService
