"""SYS-WF-007 complete governed Portfolio activation chain."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import PortfolioConstructionResult
from app.utils import logger

from tests.portfolio import conftest as portfolio_fixtures
from tests.portfolio.integration import (
    test_activation_workflow as activation_workflow,
)

construction_request_data = portfolio_fixtures.construction_request_data
construction_result = portfolio_fixtures.construction_result
portfolio_settings = portfolio_fixtures.portfolio_settings
portfolio_now = portfolio_fixtures.portfolio_now
run_activation_chain = activation_workflow.test_activation_chain_uses_receiver_owned_simulation_and_risk_contracts  # noqa: E501


def test_candidate_simulation_risk_review_and_activation_chain(
    construction_request_data: dict[str, Any],
    construction_result: PortfolioConstructionResult,
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A candidate becomes active only through Simulation and Risk owners."""
    logger.info("Testing SYS-WF-007 Portfolio activation chain")
    run_activation_chain(
        construction_request_data,
        construction_result,
        portfolio_settings,
        portfolio_now,
        monkeypatch,
    )
