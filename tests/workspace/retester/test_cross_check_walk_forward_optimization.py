"""Unit tests for CrossCheckWalkForwardOptimizationService."""

from app.core.data.contracts import MarketBar
from app.workspace.algo_wizard.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    TimeframeSpec,
)
from app.workspace.retester.cross_check_walk_forward_optimization import (
    CrossCheckWalkForwardOptimizationService,
    WFOptimizationConfig,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test",
        name="TestStrategy",
        timeframe=TimeframeSpec(primary="H1"),
    )
    return HSLStrategyDocument(strategy=payload)


class TestCrossCheckWalkForwardOptimization:
    """Test suite for CrossCheckWalkForwardOptimizationService."""

    def test_golden_fixture_five_windows(self) -> None:
        """5 windows with 4 profitable OOS runs yield profitable_runs_pct == 80.0."""
        strat = _make_strategy()
        bars: list[MarketBar] = []
        window_returns = [100.0, 50.0, -20.0, 80.0, 120.0]  # 4 out of 5 profitable

        config = WFOptimizationConfig(
            enabled=True,
            runs_count=5,
            oos_pct=30,
            anchored=False,
            acceptance_conditions=(
                CrossCheckCondition(
                    name="MinProfitable",
                    metric="ProfitableRunsPct",
                    operator=">=",
                    threshold=75.0,
                ),
            ),
        )

        res = CrossCheckWalkForwardOptimizationService.run(
            strategy=strat,
            bars=bars,
            config=config,
            custom_window_returns=window_returns,
        )

        assert len(res.windows) == 5
        assert res.profitable_runs_pct == 80.0
        assert res.passed is True
        assert res.stitched_oos_net_profit == 330.0
