"""Unit tests for CrossCheckRetestOnAdditionalMarketsService."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.algo_wizard.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    TimeframeSpec,
)
from app.workspace.retester.cross_check_retest_on_additional_markets import (
    AdditionalMarketsConfig,
    AdditionalMarketSetup,
    CrossCheckRetestOnAdditionalMarketsService,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test",
        name="TestStrategy",
        timeframe=TimeframeSpec(primary="H1"),
    )
    return HSLStrategyDocument(strategy=payload)


class TestCrossCheckRetestOnAdditionalMarkets:
    """Test suite for CrossCheckRetestOnAdditionalMarketsService."""

    def test_golden_fixture_two_markets(self) -> None:
        """Assert running with 2 additional markets stores Additional_1, Additional_2, and Portfolio."""
        strat = _make_strategy()
        setups = (
            AdditionalMarketSetup(
                result_key="Additional_1", symbol="GBPUSD", timeframe="H1"
            ),
            AdditionalMarketSetup(
                result_key="Additional_2", symbol="AUDUSD", timeframe="H1"
            ),
        )
        stats = {
            "Additional_1": {"net_profit": 600.0},
            "Additional_2": {"net_profit": 400.0},
        }
        config = AdditionalMarketsConfig(
            enabled=True,
            markets=setups,
            compute_combined_portfolio=True,
            acceptance_conditions=(
                CrossCheckCondition(
                    name="MinPortfolio",
                    metric="PortfolioNetProfit",
                    operator=">=",
                    threshold=800.0,
                ),
            ),
        )

        res = CrossCheckRetestOnAdditionalMarketsService.run(
            strat, config, market_stats=stats
        )

        assert "Additional_1" in res.market_results
        assert "Additional_2" in res.market_results
        assert "Portfolio" in res.market_results
        assert res.market_results["Additional_1"] == 600.0
        assert res.market_results["Additional_2"] == 400.0
        assert res.portfolio_net_profit == 1000.0
        assert res.passed is True

    def test_empty_markets_raises_domain_error(self) -> None:
        """Assert enabled with empty markets raises RETESTER_ADDITIONAL_MARKETS_EMPTY."""
        strat = _make_strategy()
        config = AdditionalMarketsConfig(enabled=True, markets=())
        with pytest.raises(DomainError) as exc_info:
            CrossCheckRetestOnAdditionalMarketsService.run(strat, config)
        assert exc_info.value.code == "RETESTER_ADDITIONAL_MARKETS_EMPTY"
