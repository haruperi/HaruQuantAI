"""SYS-WF-008 complete governed Portfolio rebalance chain."""

from __future__ import annotations

from datetime import datetime

import pytest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import ActivePortfolioAllocation
from app.utils import logger

from tests.portfolio import conftest as portfolio_fixtures
from tests.portfolio.integration import (
    test_rebalance_workflow as rebalance_workflow,
)

active_allocation = portfolio_fixtures.active_allocation
construction_result = portfolio_fixtures.construction_result
portfolio_settings = portfolio_fixtures.portfolio_settings
portfolio_now = portfolio_fixtures.portfolio_now
run_rebalance_chain = rebalance_workflow.test_rebalance_chain_preserves_risk_trading_and_analytics_ownership  # noqa: E501


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend.

    Returns:
        AnyIO backend name.
    """
    logger.debug("Selecting asyncio for SYS-WF-008")
    return "asyncio"


@pytest.mark.anyio
async def test_drift_risk_trading_and_analytics_measurement_chain(
    active_allocation: ActivePortfolioAllocation,
    portfolio_now: datetime,
    portfolio_settings: PortfolioSettings,
) -> None:
    """A reduce-only plan preserves execution before Analytics measurement."""
    logger.info("Testing SYS-WF-008 Portfolio rebalance chain")
    await run_rebalance_chain(
        active_allocation,
        portfolio_now,
        portfolio_settings,
    )
