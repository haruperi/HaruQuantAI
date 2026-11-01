"""Unit tests for CrossCheckWalkForwardMatrixService."""

from app.core.data.contracts import MarketBar
from app.workspace.algo_wizard.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    TimeframeSpec,
)
from app.workspace.retester.cross_check_walk_forward_matrix import (
    CrossCheckWalkForwardMatrixService,
    WFMatrixConfig,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test",
        name="TestStrategy",
        timeframe=TimeframeSpec(primary="H1"),
    )
    return HSLStrategyDocument(strategy=payload)


class TestCrossCheckWalkForwardMatrix:
    """Test suite for CrossCheckWalkForwardMatrixService."""

    def test_golden_fixture_cluster_connectivity(self) -> None:
        """Assert 3x3 grid with 2x2 passing block (4 cells) yields max_cluster=4 and passed=True."""
        strat = _make_strategy()
        bars: list[MarketBar] = []

        # 3x3 grid: runs in {5, 10, 15}, oos in {20, 30, 40}
        config = WFMatrixConfig(
            enabled=True,
            runs_start=5,
            runs_stop=15,
            runs_step=5,
            oos_pct_start=20,
            oos_pct_stop=40,
            oos_pct_step=10,
            min_passing_neighbors=3,
            cell_conditions=(
                CrossCheckCondition(
                    name="MinScore", metric="WFScore", operator=">=", threshold=70.0
                ),
            ),
        )

        # Set 2x2 block to pass (score=80.0), others to fail (score=50.0)
        # Block: (5, 20), (5, 30), (10, 20), (10, 30)
        overrides: dict[tuple[int, int], tuple[float, float]] = {
            (5, 20): (80.0, 1000.0),
            (5, 30): (80.0, 1000.0),
            (10, 20): (80.0, 1000.0),
            (10, 30): (80.0, 1000.0),
            (5, 40): (50.0, 500.0),
            (10, 40): (50.0, 500.0),
            (15, 20): (50.0, 500.0),
            (15, 30): (50.0, 500.0),
            (15, 40): (50.0, 500.0),
        }

        res = CrossCheckWalkForwardMatrixService.run(
            strategy=strat,
            bars=bars,
            config=config,
            cell_override=overrides,
        )

        assert len(res.cells) == 9
        assert res.max_passing_cluster_size == 4
        assert res.passed is True
        assert len(res.failure_reasons) == 0

    def test_cluster_below_minimum_fails(self) -> None:
        """When max cluster size is below min_passing_neighbors, passed is False."""
        strat = _make_strategy()
        bars: list[MarketBar] = []
        config = WFMatrixConfig(
            enabled=True,
            runs_start=5,
            runs_stop=15,
            runs_step=5,
            oos_pct_start=20,
            oos_pct_stop=40,
            oos_pct_step=10,
            min_passing_neighbors=5,  # Requires at least 5
            cell_conditions=(
                CrossCheckCondition(
                    name="MinScore", metric="WFScore", operator=">=", threshold=70.0
                ),
            ),
        )
        # All fail except 1
        overrides = {(5, 20): (80.0, 1000.0)}
        res = CrossCheckWalkForwardMatrixService.run(
            strat, bars, config, cell_override=overrides
        )
        assert res.max_passing_cluster_size == 1
        assert res.passed is False
        assert len(res.failure_reasons) == 1
