"""Simulation benchmark and reference dataset validation strategy.

Description:
    Validates simulated order execution, account balance, and account equity
    against a reference baseline mapping. Enters a buy order at hour 8 and
    closes after 8 bars duration. Conforms to StrategyQuant
    SQ.Strategies.TestSpecialStrategy.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful TestSpecialStrategy strategy.

Key Capabilities:
    - FR-STRAT-TESTSPECIAL: Reference map check of balance, equity, and orders.

Python API Usage:
    from app.extend.strategies.test_special_strategy import TestSpecialStrategy
    strat = TestSpecialStrategy(reference_map)
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import (
    ILiveOrder,
    OrderCloseTypes,
    Strategy,
    UpdateEventTypes,
)

logger = get_logger(__name__)

HOUR_ENTRY_SIGNAL = 8
BARS_DURATION_EXIT = 8


class TestSpecialStrategy(Strategy):
    """Verifies backtest simulation metrics against reference benchmark values."""

    __test__ = False

    def __init__(self, ref_map: dict[int, list[str]] | None = None) -> None:
        super().__init__()
        self._map: dict[int, list[str]] = ref_map or {}
        self._order: ILiveOrder | None = None
        self._closed: bool = True
        self._bars: int = 0
        self._open_time: int = 0

    def set_reference_map(self, ref_map: dict[int, list[str]]) -> None:
        """Assign reference benchmark dataset."""
        self._map = ref_map

    @override
    def Initialize(self) -> None:
        """Strategy initialization hook."""
        logger.info("FR-STRAT-TESTSPECIAL: Initialize invoked")

    @override
    def OnBarUpdate(self) -> None:
        """Validate current state against benchmark map and execute timed trade."""
        if self.UpdateEventType != UpdateEventTypes.BarOpen:
            return

        chart_data = self.MarketData.Chart(0)
        t0 = chart_data.Time(0)

        if self._map:
            self._verify_reference_metrics(t0)

        t1 = chart_data.Time(1)
        dt1 = datetime.fromtimestamp(t1 / 1000.0, tz=UTC)
        hour = dt1.hour

        self._bars += 1

        if self._order is None and hour == HOUR_ENTRY_SIGNAL:
            self._order = (
                self.Trader.Buy(self.Symbol).setSize(0.1).setMagicNumber(1234).Send()
            )
            self._open_time = t1
            self._bars = 0
            self._closed = False
        elif self._order is not None and self._bars == BARS_DURATION_EXIT:
            self._order.Close(OrderCloseTypes.Deleted)
            self._order = None
            self._closed = True

        logger.info(
            "FR-STRAT-TESTSPECIAL: OnBarUpdate executed (bars=%s, closed=%s)",
            self._bars,
            self._closed,
        )

    def _verify_reference_metrics(self, t0: int) -> None:
        """Assert simulated values match reference map data."""
        if t0 not in self._map:
            dt_str = datetime.fromtimestamp(t0 / 1000.0, tz=UTC).strftime(
                "%Y-%m-%d %H:%M"
            )
            raise ValueError(f"This is not good man. Missing data: {dt_str}")

        data = self._map[t0]
        ac_balance = self.Trader.getAccountBalance()
        ac_equity = self.Trader.getAccountEquity()

        closed_f = data[2] == "0"
        ac_balance_f = float(data[6])
        ac_equity_f = float(data[7])

        if round(ac_balance_f, 2) != round(ac_balance, 2):
            raise ValueError(
                f"Incorrect account balance: {ac_balance} != {ac_balance_f}"
            )

        if round(ac_equity_f, 2) != round(ac_equity, 2):
            raise ValueError(f"Incorrect account equity: {ac_equity} != {ac_equity_f}")

        if closed_f != self._closed:
            raise ValueError(f"Incorrect open type: {self._closed} != {closed_f}")
