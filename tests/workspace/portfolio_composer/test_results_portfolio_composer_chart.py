"""Unit tests for ResultsPortfolioComposerChartService (PC Phase 10.3)."""

from __future__ import annotations

from app.workspace.portfolio_composer.allocations import BoundedRandom
from app.workspace.portfolio_composer.portfolio_composer import (
    ComposerMemberSpec,
    ComposerRunConfig,
    ComposerTrade,
    PortfolioComposerService,
)
from app.workspace.portfolio_composer.results_portfolio_composer_chart import (
    ResultsPortfolioComposerChartService,
)


class FakeRNG(BoundedRandom):
    """Predictable RNG for tests."""

    def __init__(self, draws: list[int]) -> None:
        self.draws = list(draws)

    def next_index(self, upper_exclusive: int) -> int:
        if not self.draws:
            return 0
        return self.draws.pop(0)


class TestResultsPortfolioComposerChartService:
    """Test suite for chart and frontier projections."""

    def test_golden_fixture_3_simulation_run(self) -> None:
        """Verify 3-simulation run produces 3 FrontierSimulationPoints."""
        service = PortfolioComposerService()
        m1 = ComposerMemberSpec(
            strategy_id="s1",
            name="Strategy 1",
            trades=(
                ComposerTrade(
                    ticket=1, open_time_ms=1000, close_time_ms=2000, pnl=100.0
                ),
            ),
        )
        m2 = ComposerMemberSpec(
            strategy_id="s2",
            name="Strategy 2",
            trades=(
                ComposerTrade(
                    ticket=2, open_time_ms=1500, close_time_ms=2500, pnl=200.0
                ),
            ),
        )

        config = ComposerRunConfig(
            model_type="markowitz",
            selection_type="SharpRatio",
            max_simulations=3,
            members=(m1, m2),
        )

        receipt = service.recompute(config, rng=FakeRNG([20, 40, 60]))
        resp = ResultsPortfolioComposerChartService.get_chart(receipt)

        assert resp.data is not None
        payload = resp.data
        assert payload.model_type == "markowitz"
        assert payload.selection_type == "SharpRatio"
        assert len(payload.frontier_points) == 3
        selected_count = sum(1 for pt in payload.frontier_points if pt.is_selected)
        assert selected_count == 1
        assert len(payload.portfolio_equity) >= 1
        assert "s1" in payload.member_equities
        assert "s2" in payload.member_equities
