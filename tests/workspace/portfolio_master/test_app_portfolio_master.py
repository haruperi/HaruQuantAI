"""Tests for AppPortfolioMaster service and search engine."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.extend.correlation_of.catalog import CorrelationOrderRecord
from app.workspace.portfolio_master.app_portfolio_master import (
    AppPortfolioMasterService,
    PortfolioMasterSearchConfig,
    RankingFilterCondition,
)


class TestAppPortfolioMasterService:
    """Test suite for AppPortfolioMasterService."""

    def test_golden_fixture_brute_force_correlation_filtering(self) -> None:
        """Assert exact golden fixture from line 160 in 11-AppPortfolioMaster.md.

        3 strategies: S1, S2 (corr > 0.5), S1, S3 (corr <= 0.5), S2, S3 (corr <= 0.5).
        max_correlation = 0.5.
        Evaluates 3 pairs, rejects (S1, S2) on correlation, accepts (S1, S3) and (S2, S3).
        """
        # Day 1: 1767225600000, Day 2: 1767312000000, Day 3: 1767398400000, Day 4: 1767484800000
        t1, t2, t3, t4 = (
            1767225600000,
            1767312000000,
            1767398400000,
            1767484800000,
        )

        pool = {
            "S1": [
                CorrelationOrderRecord(
                    open_time_ms=t1, close_time_ms=t1 + 1000, profit_loss=10.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t2, close_time_ms=t2 + 1000, profit_loss=20.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t3, close_time_ms=t3 + 1000, profit_loss=30.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t4, close_time_ms=t4 + 1000, profit_loss=40.0
                ),
            ],
            "S2": [
                CorrelationOrderRecord(
                    open_time_ms=t1, close_time_ms=t1 + 1000, profit_loss=10.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t2, close_time_ms=t2 + 1000, profit_loss=22.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t3, close_time_ms=t3 + 1000, profit_loss=29.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t4, close_time_ms=t4 + 1000, profit_loss=41.0
                ),
            ],
            "S3": [
                CorrelationOrderRecord(
                    open_time_ms=t1, close_time_ms=t1 + 1000, profit_loss=5.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t2, close_time_ms=t2 + 1000, profit_loss=10.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t3, close_time_ms=t3 + 1000, profit_loss=20.0
                ),
                CorrelationOrderRecord(
                    open_time_ms=t4, close_time_ms=t4 + 1000, profit_loss=5.0
                ),
            ],
        }

        svc = AppPortfolioMasterService()
        config = PortfolioMasterSearchConfig(
            search_mode="BRUTE_FORCE",
            min_strategies=2,
            max_strategies=2,
            max_correlation=0.5,
            correlation_method="ProfitLoss",
            correlation_period="DAY",
        )
        svc.save_settings("proj-golden", config)

        response = svc.start("proj-golden", strategy_pool=pool)
        summary = response.data

        assert summary.combinations_evaluated == 3
        assert summary.portfolios_rejected_correlation == 1
        assert summary.portfolios_rejected_conditions == 0
        assert summary.portfolios_accepted == 2
        assert len(summary.stored_portfolio_ids) == 2

    def test_invalid_size_bounds(self) -> None:
        """Assert size bounds outside [1..50] raise DomainError with code."""
        svc = AppPortfolioMasterService()

        # min < 1
        with pytest.raises(DomainError) as exc_info1:
            svc.save_settings(
                "p1", PortfolioMasterSearchConfig(min_strategies=0, max_strategies=5)
            )
        assert exc_info1.value.code == "PORTFOLIO_MASTER_INVALID_SIZE_BOUNDS"

        # max > 50
        with pytest.raises(DomainError) as exc_info2:
            svc.save_settings(
                "p1", PortfolioMasterSearchConfig(min_strategies=2, max_strategies=51)
            )
        assert exc_info2.value.code == "PORTFOLIO_MASTER_INVALID_SIZE_BOUNDS"

        # min > max
        with pytest.raises(DomainError) as exc_info3:
            svc.save_settings(
                "p1", PortfolioMasterSearchConfig(min_strategies=5, max_strategies=2)
            )
        assert exc_info3.value.code == "PORTFOLIO_MASTER_INVALID_SIZE_BOUNDS"

    def test_lifecycle_and_state(self) -> None:
        """Assert get_state, save_settings, pause, resume, and stop operations."""
        svc = AppPortfolioMasterService()
        default_state = svc.get_state("proj-new").data
        assert default_state.min_strategies == 2
        assert default_state.max_strategies == 5

        custom_config = PortfolioMasterSearchConfig(
            min_strategies=3, max_strategies=4, max_correlation=0.4
        )
        saved = svc.save_settings("proj-new", custom_config).data
        assert saved.min_strategies == 3

        svc.pause("proj-new")
        assert svc._statuses["proj-new"] == "paused"

        svc.resume("proj-new")
        assert svc._statuses["proj-new"] == "running"

        svc.stop("proj-new")
        assert svc._statuses["proj-new"] == "stopped"

    def test_acceptance_conditions_filtering(self) -> None:
        """Assert conditions filter out candidate portfolios."""
        svc = AppPortfolioMasterService()
        config = PortfolioMasterSearchConfig(
            search_mode="BRUTE_FORCE",
            min_strategies=2,
            max_strategies=2,
            acceptance_conditions=(
                RankingFilterCondition(
                    metric="NetProfit", comparison=">", value=1000.0
                ),
            ),
        )
        svc.save_settings("proj-filter", config)
        res = svc.start("proj-filter")
        summary = res.data
        assert summary.portfolios_rejected_conditions >= 1
        assert summary.portfolios_accepted == 0

    def test_genetic_random_search_mode(self) -> None:
        """Assert genetic/monte carlo random search generates candidates."""
        svc = AppPortfolioMasterService()
        config = PortfolioMasterSearchConfig(
            search_mode="GENETIC",
            min_strategies=2,
            max_strategies=2,
            max_combinations=5,
        )
        svc.save_settings("proj-genetic", config)
        res = svc.start("proj-genetic", seed=123)
        summary = res.data
        assert summary.combinations_evaluated >= 1
