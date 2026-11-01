"""Unit tests for CrossCheckOptProfileSPPService."""

from app.core.data.contracts import MarketBar
from app.workspace.algo_wizard.models import (
    HSLStrategyDocument,
    HSLStrategyPayload,
    TimeframeSpec,
)
from app.workspace.retester.cross_check_opt_profile_sys_param_permutation import (
    CrossCheckOptProfileSPPService,
    SPPConfig,
)


def _make_strategy() -> HSLStrategyDocument:
    payload = HSLStrategyPayload(
        id="strat_test",
        name="TestStrategy",
        timeframe=TimeframeSpec(primary="H1"),
    )
    return HSLStrategyDocument(strategy=payload)


class TestCrossCheckOptProfileSPP:
    """Test suite for CrossCheckOptProfileSPPService."""

    def test_golden_fixture_four_runs(self) -> None:
        """4 parameter runs with [120.0, 80.0, 40.0, -10.0] yield profitable=75.0%, median=60.0, passed=True."""
        strat = _make_strategy()
        bars: list[MarketBar] = []
        profits = [120.0, 80.0, 40.0, -10.0]

        config = SPPConfig(
            enabled=True,
            min_profitable_runs_pct=70.0,
        )

        res = CrossCheckOptProfileSPPService.run(
            strategy=strat,
            bars=bars,
            config=config,
            custom_runs=profits,
        )

        assert res.total_runs == 4
        assert res.profitable_runs_pct == 75.0
        assert res.median_net_profit == 60.0  # Median of 80.0 and 40.0 is 60.0
        assert res.passed is True
        assert len(res.failure_reasons) == 0

    def test_insufficient_profitable_runs_fails(self) -> None:
        """When profitable percentage is below minimum, passed is False."""
        strat = _make_strategy()
        bars: list[MarketBar] = []
        profits = [100.0, -50.0, -30.0, -20.0]  # 25% profitable

        config = SPPConfig(
            enabled=True,
            min_profitable_runs_pct=70.0,
        )

        res = CrossCheckOptProfileSPPService.run(
            strategy=strat,
            bars=bars,
            config=config,
            custom_runs=profits,
        )

        assert res.profitable_runs_pct == 25.0
        assert res.passed is False
        assert len(res.failure_reasons) == 1
