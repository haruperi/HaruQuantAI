"""Shared explicit Portfolio test fixtures."""

# ruff: noqa: INP001

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from app.services.portfolio.config import PortfolioSettings, RebalanceSchedule
from app.services.portfolio.contracts import (
    ActivePortfolioAllocation,
    PortfolioComponentWeight,
    PortfolioConstructionResult,
)
from app.utils import logger


@pytest.fixture
def portfolio_now() -> datetime:
    """Return a stable aware UTC Portfolio test time.

    Returns:
        Stable UTC test instant.
    """
    logger.debug("Creating stable Portfolio test time")
    return datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


@pytest.fixture
def portfolio_settings(portfolio_now: datetime) -> PortfolioSettings:
    """Return complete explicit Portfolio policy settings.

    Args:
        portfolio_now: Stable UTC test instant.

    Returns:
        Validated Portfolio settings.
    """
    logger.debug("Creating explicit Portfolio test settings")
    return PortfolioSettings(
        portfolio_weight_sum_tolerance=Decimal("0.00000001"),
        portfolio_min_weight=Decimal(0),
        portfolio_max_weight=Decimal(1),
        portfolio_max_strategies=10,
        portfolio_min_evidence_observations=30,
        portfolio_max_evidence_age_seconds=3600,
        portfolio_allocation_decision_ttl_seconds=900,
        portfolio_activation_approval_policy={
            "simulation": "automatic_within_policy",
            "paper": "explicit_human",
            "live": "explicit_human",
        },
        portfolio_rebalance_drift_threshold=Decimal("0.05"),
        portfolio_rebalance_schedule=RebalanceSchedule(
            anchor_at=portfolio_now,
            interval_seconds=3600,
        ),
    )


@pytest.fixture
def construction_request_data(portfolio_now: datetime) -> dict[str, Any]:
    """Return complete primitive construction request input.

    Args:
        portfolio_now: Stable UTC test instant.

    Returns:
        Complete request constructor data.
    """
    logger.debug("Creating Portfolio construction request fixture data")
    digest_a = "a" * 64
    digest_b = "b" * 64
    return {
        "request_id": "req-portfolio-0001",
        "workflow_id": "wf-portfolio-0001",
        "correlation_id": "corr-portfolio-0001",
        "causation_id": None,
        "portfolio_id": "portfolio-alpha",
        "portfolio_version": "version-1",
        "scope": {"environment": "simulation", "tenant": "owner"},
        "components": (
            {
                "component_id": "component-a",
                "strategy_id": "strategy-a",
                "strategy_version": "1.0.0",
                "registry_record_hash": digest_a,
                "eligibility_decision_id": "eligibility-a",
            },
            {
                "component_id": "component-b",
                "strategy_id": "strategy-b",
                "strategy_version": "1.0.0",
                "registry_record_hash": digest_b,
                "eligibility_decision_id": "eligibility-b",
            },
        ),
        "method": "equal",
        "fixed_weights": (),
        "evidence": {
            "account_snapshot_id": "account-snapshot-1",
            "account_snapshot_hash": digest_a,
            "account_snapshot_as_of": portfolio_now,
            "market_dataset_id": "market-dataset-1",
            "market_dataset_hash": digest_b,
            "market_dataset_as_of": portfolio_now,
            "analytics_evidence_id": "analytics-evidence-1",
            "analytics_evidence_hash": "c" * 64,
            "analytics_evidence_as_of": portfolio_now,
            "fx_evidence_ids": (),
            "fx_evidence_hashes": (),
        },
        "measurement_start": datetime(2026, 7, 1, tzinfo=UTC),
        "measurement_end": portfolio_now,
        "base_currency": "USD",
        "runtime_profile": "simulation",
        "execution_route": "sim",
        "simulation_policy_version": "simulation-policy-1",
        "requested_at": portfolio_now,
    }


@pytest.fixture
def construction_result(portfolio_now: datetime) -> PortfolioConstructionResult:
    """Return a complete immutable construction result.

    Args:
        portfolio_now: Stable UTC test instant.

    Returns:
        Complete construction result.
    """
    logger.debug("Creating Portfolio construction result fixture")
    weights = tuple(
        PortfolioComponentWeight(
            component_id=f"component-{suffix}",
            strategy_id=f"strategy-{suffix}",
            strategy_version="1.0.0",
            capital_weight=Decimal("0.5"),
            proposed_risk_budget_weight=Decimal("0.5"),
        )
        for suffix in ("a", "b")
    )
    return PortfolioConstructionResult(
        result_id="portfolio-result-1",
        portfolio_id="portfolio-alpha",
        portfolio_version="version-1",
        scope={"environment": "simulation", "tenant": "owner"},
        status="constructed",
        component_weights=weights,
        method="equal",
        config_hash="a" * 64,
        evidence_hash="b" * 64,
        strategy_lineage_hash="c" * 64,
        canonical_hash="d" * 64,
        created_at=portfolio_now,
        request_id="req-portfolio-0001",
        workflow_id="wf-portfolio-0001",
        correlation_id="corr-portfolio-0001",
    )


@pytest.fixture
def active_allocation(
    construction_result: PortfolioConstructionResult,
    portfolio_now: datetime,
) -> ActivePortfolioAllocation:
    """Return a complete governed active allocation version.

    Args:
        construction_result: Complete construction result.
        portfolio_now: Stable UTC test instant.

    Returns:
        Complete active allocation.
    """
    logger.debug("Creating active Portfolio allocation fixture")
    return ActivePortfolioAllocation(
        allocation_id="allocation-1",
        portfolio_id=construction_result.portfolio_id,
        allocation_version="allocation-version-1",
        scope=construction_result.scope,
        construction_result_id=construction_result.result_id,
        construction_result_hash=construction_result.canonical_hash,
        component_weights=construction_result.component_weights,
        simulation_result_id="simulation-result-1",
        simulation_result_hash="e" * 64,
        risk_decision_id="risk-decision-1",
        risk_budget_projection_ref="risk-projection-1",
        activated_at=portfolio_now,
        expires_at=portfolio_now + timedelta(days=1),
        idempotency_key="activation-idempotency-1",
        canonical_hash="f" * 64,
        request_id=construction_result.request_id,
        workflow_id=construction_result.workflow_id,
        correlation_id=construction_result.correlation_id,
        audit_ref="audit-1",
    )
