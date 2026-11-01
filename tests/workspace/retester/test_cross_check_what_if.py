"""Unit tests for CrossCheckWhatIfService."""

from app.extend.what_if.base import WhatIfRecord
from app.extend.what_if.exclude_short_trades import ExcludeShortTrades
from app.extend.what_if.take_every_second_trade import TakeEverySecondTrade
from app.workspace.retester.cross_check_what_if import (
    CrossCheckWhatIfService,
    WhatIfCrossCheckConfig,
)
from app.workspace.retester.settings_cross_checks import CrossCheckCondition


def _make_trade(record_id: int, duration_min: int, profit: float) -> WhatIfRecord:
    open_time = 1000 + record_id * 3600000
    close_time = open_time + duration_min * 60000
    return WhatIfRecord(
        record_id=record_id,
        kind="trade",
        direction=1,
        time_open_msc=open_time,
        time_close_msc=close_time,
        volume=1.0,
        profit=profit,
    )


class TestCrossCheckWhatIf:
    """Test suite for CrossCheckWhatIfService."""

    def test_golden_fixture_pipeline(self) -> None:
        """ExcludeShortTrades followed by TakeEverySecondTrade on 4 trades retains 1 trade."""
        trades = (
            _make_trade(
                1, duration_min=20, profit=100.0
            ),  # Long duration (kept by ExcludeShort)
            _make_trade(
                2, duration_min=5, profit=50.0
            ),  # Short duration (dropped by ExcludeShort)
            _make_trade(
                3, duration_min=20, profit=80.0
            ),  # Long duration (kept by ExcludeShort, dropped by TakeEverySecond)
            _make_trade(
                4, duration_min=5, profit=-20.0
            ),  # Short duration (dropped by ExcludeShort)
        )
        config = WhatIfCrossCheckConfig(
            enabled=True,
            scenarios=(
                ExcludeShortTrades(trades_pct=50, minutes=10),
                TakeEverySecondTrade(),
            ),
            acceptance_conditions=(
                CrossCheckCondition(
                    name="MinProfit", metric="NetProfit", operator=">=", threshold=50.0
                ),
            ),
        )
        result = CrossCheckWhatIfService.run(
            trades, initial_capital=10000.0, config=config
        )

        assert result.original_trade_count == 4
        assert result.filtered_trade_count == 1
        assert result.filtered_net_profit == 100.0
        assert result.passed is True
        assert len(result.failure_reasons) == 0

    def test_acceptance_condition_failure(self) -> None:
        """Failing condition returns passed=False and records reason."""
        trades = (_make_trade(1, duration_min=20, profit=10.0),)
        config = WhatIfCrossCheckConfig(
            enabled=True,
            acceptance_conditions=(
                CrossCheckCondition(
                    name="HighProfit",
                    metric="NetProfit",
                    operator=">=",
                    threshold=500.0,
                ),
            ),
        )
        result = CrossCheckWhatIfService.run(
            trades, initial_capital=1000.0, config=config
        )
        assert result.passed is False
        assert len(result.failure_reasons) == 1
