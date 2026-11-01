"""Unit tests for ResultsPortfolioComposerLogService (PC Phase 10.4)."""

from __future__ import annotations

from app.workspace.portfolio_composer.portfolio_composer import (
    ComposerMemberSpec,
    ComposerRunConfig,
    ComposerTrade,
    PortfolioComposerService,
)
from app.workspace.portfolio_composer.results_portfolio_composer_log import (
    ResultsPortfolioComposerLogService,
)


class TestResultsPortfolioComposerLogService:
    """Test suite for ResultsPortfolioComposerLogService execution logs."""

    def test_golden_fixture_margin_rejection(self) -> None:
        """Verify 1 order of 10 exceeding margin returns rejected=1 and REJECTED log."""
        service = PortfolioComposerService()

        # Build 10 orders: 9 valid and 1 that exceeds initial capital margin
        trades: list[ComposerTrade] = []
        for i in range(1, 10):
            trades.append(
                ComposerTrade(
                    ticket=i,
                    open_time_ms=1000 * i,
                    close_time_ms=1000 * i + 500,
                    open_price=10.0,
                    size=1.0,
                    pnl=50.0,
                    required_margin=100.0,
                )
            )
        # 10th order has massive margin requirement
        trades.append(
            ComposerTrade(
                ticket=10,
                open_time_ms=10000,
                close_time_ms=10500,
                open_price=500000.0,
                size=1.0,
                pnl=100.0,
                required_margin=500000.0,
            )
        )

        member = ComposerMemberSpec(
            strategy_id="strat_margin_test",
            name="Margin Test Strategy",
            trades=tuple(trades),
        )

        config = ComposerRunConfig(
            initial_capital=10000.0,
            leverage=1,
            model_type="manual",
            members=(member,),
        )

        receipt = service.recompute(config)
        resp = ResultsPortfolioComposerLogService.get_log(receipt)

        assert resp.data is not None
        payload = resp.data
        assert payload.total_orders_evaluated == 10
        assert payload.rejected_margin_orders == 1

        rejected_entries = [e for e in payload.entries if e.level == "REJECTED"]
        assert len(rejected_entries) == 1
        assert rejected_entries[0].strategy_id == "strat_margin_test"
        assert rejected_entries[0].timestamp_ms == 10000
