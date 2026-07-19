"""Unit tests for deterministic Portfolio construction publication."""

# ruff: noqa: INP001

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import pytest
from app.services.portfolio.config import PortfolioSettings
from app.services.portfolio.construction import ConstructionService
from app.services.portfolio.contracts import PortfolioConstructionRequest
from app.services.portfolio.evidence import ValidatedConstructionEvidence
from app.services.portfolio.exceptions import PortfolioError
from app.utils import logger


def _validated_evidence(
    request: PortfolioConstructionRequest,
) -> ValidatedConstructionEvidence:
    """Build already-validated evidence for construction-only tests.

    Args:
        request: Validated construction request.

    Returns:
        Minimal typed validated evidence bundle.
    """
    logger.debug("Building construction-only validated evidence")
    return ValidatedConstructionEvidence(
        request=request,
        strategy_refs=(),
        eligibility_decisions=(),
        account_snapshot=cast("Any", object()),
        market_dataset=cast("Any", object()),
        analytics_evidence=cast("Any", object()),
        fx_evidence=(),
        component_volatilities={
            "component-a": request.fixed_weights[0].capital_weight
            if request.fixed_weights
            else Decimal("0.1"),
            "component-b": Decimal("0.2"),
        },
        component_observations={"component-a": 30, "component-b": 30},
        evidence_hash="a" * 64,
        strategy_lineage_hash="b" * 64,
    )


def test_construction_returns_identical_bytes_and_hash(
    construction_request_data: dict[str, Any],
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Verify identical inputs and config produce identical output.

    Args:
        construction_request_data: Complete request data.
        portfolio_settings: Complete explicit settings.
        portfolio_now: Stable UTC test time.
    """
    logger.info("Testing Portfolio construction reproducibility")
    request = PortfolioConstructionRequest(**construction_request_data)
    service = ConstructionService(portfolio_settings)
    evidence = _validated_evidence(request)

    first = service.construct(evidence, created_at=portfolio_now)
    second = service.construct(evidence, created_at=portfolio_now)

    assert first == second
    assert first.model_dump_json() == second.model_dump_json()
    assert first.canonical_hash == second.canonical_hash


def test_construction_publishes_nothing_on_failure(
    construction_request_data: dict[str, Any],
    portfolio_settings: PortfolioSettings,
    portfolio_now: datetime,
) -> None:
    """Verify failed method validation returns no partial result.

    Args:
        construction_request_data: Complete request data.
        portfolio_settings: Complete explicit settings.
        portfolio_now: Stable UTC test time.
    """
    logger.info("Testing atomic Portfolio construction failure")
    construction_request_data["method"] = "inverse_volatility"
    request = PortfolioConstructionRequest(**construction_request_data)
    evidence = _validated_evidence(request)
    evidence = replace(
        evidence,
        component_observations={"component-a": 1, "component-b": 1},
    )

    with pytest.raises(PortfolioError, match="OBSERVATIONS"):
        ConstructionService(portfolio_settings).construct(
            evidence,
            created_at=portfolio_now,
        )
