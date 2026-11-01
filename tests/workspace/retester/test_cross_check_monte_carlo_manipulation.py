"""Unit tests for CrossCheckMonteCarloManipulationService."""

from app.extend.monte_carlo.manipulation.randomly_skip_trades import RandomlySkipTrades
from app.extend.what_if.base import WhatIfRecord
from app.workspace.retester.cross_check_monte_carlo_manipulation import (
    CrossCheckMonteCarloManipulationService,
    MCManipulationConfig,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_trade(record_id: int, profit: float) -> WhatIfRecord:
    return WhatIfRecord(
        record_id=record_id,
        kind="trade",
        direction=1,
        time_open_msc=1000 + record_id * 100,
        time_close_msc=1050 + record_id * 100,
        volume=1.0,
        profit=profit,
    )


class TestCrossCheckMonteCarloManipulation:
    """Test suite for MC Manipulation cross-check service."""

    def test_golden_fixture_monotone_bands(self) -> None:
        """Assert 20 simulations produce deterministic bands and monotone non-increasing net profit."""
        trades = tuple(_make_trade(i, 50.0 + (i % 3) * 20.0) for i in range(1, 21))
        config = MCManipulationConfig(
            enabled=True,
            simulations=20,
            seed=42,
            methods=(RandomlySkipTrades(probability=10),),
            confidence_level=90,
            acceptance_conditions=(
                CrossCheckCondition(
                    name="MinProfit", metric="NetProfit", operator=">=", threshold=0.0
                ),
            ),
        )

        res1 = CrossCheckMonteCarloManipulationService.run(trades, 10000.0, config)
        res2 = CrossCheckMonteCarloManipulationService.run(trades, 10000.0, config)

        # Deterministic repeated execution
        assert res1.bands == res2.bands
        assert res1.passed is True
        assert len(res1.bands) == 11

        # Monotone non-increasing net_profit as confidence increases (50% -> 99%)
        profits = [b.net_profit for b in res1.bands]
        for i in range(len(profits) - 1):
            assert profits[i] >= profits[i + 1]

    def test_condition_failure_at_confidence(self) -> None:
        """Condition failing at specified confidence level marks result as failed."""
        trades = tuple(_make_trade(i, 10.0) for i in range(1, 6))
        config = MCManipulationConfig(
            enabled=True,
            simulations=10,
            confidence_level=90,
            acceptance_conditions=(
                CrossCheckCondition(
                    name="StrictProfit",
                    metric="NetProfit",
                    operator=">=",
                    threshold=5000.0,
                ),
            ),
        )
        res = CrossCheckMonteCarloManipulationService.run(trades, 1000.0, config)
        assert res.passed is False
        assert len(res.failure_reasons) == 1
