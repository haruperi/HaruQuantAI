"""Unit tests for CrossCheckMonteCarloRetestService."""

from app.core.data.contracts import MarketBar
from app.workspace.algo_wizard.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    ParameterSpec,
    TimeframeSpec,
)
from app.workspace.retester.cross_check_monte_carlo_retest import (
    CrossCheckMonteCarloRetestService,
    MCRetestConfig,
    MCRetestMethodSpec,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test",
        name="TestStrategy",
        timeframe=TimeframeSpec(primary="H1"),
        parameters={"FastPeriod": ParameterSpec(type="int", default=12)},
    )
    return HSLStrategyDocument(strategy=payload)


def _make_bars(count: int = 15) -> list[MarketBar]:
    return [
        MarketBar(
            time=1600000000 + i * 3600,
            open=1.1000 + i * 0.0010,
            high=1.1005 + i * 0.0010,
            low=1.0995 + i * 0.0010,
            close=1.1002 + i * 0.0010,
            tick_volume=100,
            spread=2,
        )
        for i in range(count)
    ]


class TestCrossCheckMonteCarloRetest:
    """Test suite for CrossCheckMonteCarloRetestService."""

    def test_golden_fixture_retest_spread(self) -> None:
        """Assert 10 simulations with RandomizeSpread and seed=7 produce deterministic bands."""
        strat = _make_strategy()
        bars = _make_bars(15)
        config = MCRetestConfig(
            enabled=True,
            simulations=10,
            seed=7,
            methods=(
                MCRetestMethodSpec(
                    method_id="RandomizeSpread",
                    params={"min_spread": 1, "max_spread": 3},
                ),
            ),
            confidence_level=90,
            acceptance_conditions=(
                CrossCheckCondition(
                    name="PositiveReturn",
                    metric="NetProfit",
                    operator=">=",
                    threshold=-500.0,
                ),
            ),
        )

        res1 = CrossCheckMonteCarloRetestService.run(strat, bars, config)
        res2 = CrossCheckMonteCarloRetestService.run(strat, bars, config)

        assert res1.simulations == 10
        assert res1.bands == res2.bands
        assert res1.passed is True
        assert len(res1.bands) == 11
