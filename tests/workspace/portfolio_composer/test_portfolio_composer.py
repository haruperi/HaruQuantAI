"""Unit tests for PortfolioComposerService and core engine (PC Phase 10.2)."""

from __future__ import annotations

import pytest
from app.workspace.portfolio_composer.allocations import BoundedRandom
from app.workspace.portfolio_composer.portfolio_composer import (
    ComposerMemberSpec,
    ComposerRunConfig,
    ComposerTrade,
    PortfolioComposerService,
)


class FakeRNG(BoundedRandom):
    """Predictable RNG for deterministic allocation weights."""

    def __init__(self, draws: list[int]) -> None:
        self.draws = list(draws)

    def next_index(self, upper_exclusive: int) -> int:
        if not self.draws:
            return 0
        return self.draws.pop(0)


class TestPortfolioComposerService:
    """Test suite for PortfolioComposerService methods and execution pipeline."""

    def test_add_buy_hold_strategy(self) -> None:
        """Verify buy & hold strategy synthesis generates a single long trade."""
        service = PortfolioComposerService()
        member = service.add_buy_hold_strategy(
            symbol="AAPL",
            start_day="2020-01-01",
            end_day="2025-01-01",
            initial_capital=50000.0,
        )

        assert member.enabled is True
        assert "AAPL" in member.name
        assert len(member.trades) == 1
        trade = member.trades[0]
        assert trade.symbol == "AAPL"
        assert trade.order_type == "BUY"
        assert trade.open_time_ms < trade.close_time_ms

    def test_golden_fixture_2_members_3_simulations_with_margin_reject(self) -> None:
        """Golden fixture: 2 members with max_simulations=3 and margin reject."""
        service = PortfolioComposerService()

        # Member 1 has modest trade sizes and profitable outcomes
        t1_1 = ComposerTrade(
            ticket=101,
            open_time_ms=1000,
            close_time_ms=2000,
            open_price=100.0,
            size=10.0,
            pnl=500.0,
            required_margin=1000.0,
        )
        t1_2 = ComposerTrade(
            ticket=102,
            open_time_ms=3000,
            close_time_ms=4000,
            open_price=100.0,
            size=10.0,
            pnl=700.0,
            required_margin=1000.0,
        )
        m1 = ComposerMemberSpec(
            strategy_id="strat_1",
            name="Strategy 1",
            enabled=True,
            trades=(t1_1, t1_2),
        )

        # Member 2 has a large trade that exceeds free margin under low leverage
        t2_1 = ComposerTrade(
            ticket=201,
            open_time_ms=1500,
            close_time_ms=2500,
            open_price=500.0,
            size=200.0,
            pnl=1000.0,
            required_margin=150000.0,  # exceeds initial capital of 100,000
        )
        t2_2 = ComposerTrade(
            ticket=202,
            open_time_ms=3500,
            close_time_ms=4500,
            open_price=100.0,
            size=5.0,
            pnl=-100.0,
            required_margin=500.0,
        )
        m2 = ComposerMemberSpec(
            strategy_id="strat_2",
            name="Strategy 2",
            enabled=True,
            trades=(t2_1, t2_2),
        )

        config = ComposerRunConfig(
            initial_capital=100000.0,
            leverage=1,
            model_type="markowitz",
            selection_type="SharpRatio",
            max_simulations=3,
            members=(m1, m2),
            conf_level=95,
            risk_free_rate=0.7,
        )

        rng = FakeRNG([10, 50, 80])
        receipt = service.recompute(config, rng=rng)

        assert receipt.model_type == "markowitz"
        assert receipt.selection_type == "SharpRatio"
        assert len(receipt.simulation_points) == 3
        assert sum(1 for pt in receipt.simulation_points if pt.is_selected) == 1

        # Check that high margin order was rejected and logged
        assert receipt.rejected_margin_orders >= 1
        reject_logs = [log for log in receipt.log_entries if log.level == "REJECTED"]
        assert len(reject_logs) >= 1
        assert reject_logs[0].strategy_id == "strat_2"

        # Check precision: rounded to 3 decimals for SharpRatio
        score_str = f"{receipt.selection_score:.3f}"
        assert float(score_str) == pytest.approx(receipt.selection_score, abs=1e-5)

    def test_manual_model_type_respects_explicit_weights(self) -> None:
        """Verify manual model type uses member weight_pct directly."""
        service = PortfolioComposerService()
        m1 = ComposerMemberSpec(
            strategy_id="strat_1",
            name="Strategy 1",
            weight_pct=40.0,
            trades=(
                ComposerTrade(
                    ticket=1, open_time_ms=1000, close_time_ms=2000, pnl=200.0
                ),
            ),
        )
        m2 = ComposerMemberSpec(
            strategy_id="strat_2",
            name="Strategy 2",
            weight_pct=60.0,
            trades=(
                ComposerTrade(
                    ticket=2, open_time_ms=1100, close_time_ms=2100, pnl=300.0
                ),
            ),
        )

        config = ComposerRunConfig(
            initial_capital=100000.0,
            model_type="manual",
            selection_type="NetProfit",
            members=(m1, m2),
        )

        receipt = service.recompute(config)
        assert receipt.model_type == "manual"
        assert receipt.selected_weights == (40, 60)
        assert receipt.selection_score > 0

    def test_save_portfolio(self) -> None:
        """Verify save_portfolio returns a deterministic string ID."""
        service = PortfolioComposerService()
        config = ComposerRunConfig(model_type="manual")
        receipt = service.recompute(config)

        port_id = service.save_portfolio(
            project_id="proj_1",
            databank_name="Results",
            portfolio_name="MyComposedPortfolio",
            receipt=receipt,
        )
        assert port_id.startswith("port_")
