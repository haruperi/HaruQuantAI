"""SYS-WF-006 Strategy eligibility compatibility through Portfolio."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

import pytest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.contracts import PortfolioConstructionRequest
from app.services.portfolio.evidence import validate_construction_evidence
from app.utils import logger

from tests.portfolio import conftest as portfolio_fixtures
from tests.portfolio.unit.test_evidence import (
    _owner_bundle,
    _patch_digest,
    _request_data_with_fx,
)

construction_request_data = portfolio_fixtures.construction_request_data
portfolio_now = portfolio_fixtures.portfolio_now
portfolio_settings = portfolio_fixtures.portfolio_settings


def test_strategy_eligibility_reaches_portfolio_without_contract_redefinition(
    construction_request_data: dict[str, Any],
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Strategy and Risk public contracts form valid construction evidence."""
    logger.info("Testing SYS-WF-006 Strategy eligibility into Portfolio")
    _patch_digest(monkeypatch)
    request = PortfolioConstructionRequest(
        **_request_data_with_fx(construction_request_data)
    )
    refs, decisions, account, market, analytics, fx = _owner_bundle(portfolio_now)
    evidence = validate_construction_evidence(
        request,
        strategy_refs=refs,
        eligibility_decisions=decisions,
        account_snapshot=account,
        market_dataset=market,
        analytics_evidence=analytics,
        fx_evidence=fx,
        component_volatilities={
            "component-a": Decimal("0.1"),
            "component-b": Decimal("0.2"),
        },
        component_observations={"component-a": 30, "component-b": 30},
        now=portfolio_now,
        settings=portfolio_settings,
    )
    assert tuple(ref.manifest.strategy_id for ref in evidence.strategy_refs) == (
        "strategy-a",
        "strategy-b",
    )
    assert tuple(
        decision.decision_id for decision in evidence.eligibility_decisions
    ) == ("eligibility-a", "eligibility-b")
