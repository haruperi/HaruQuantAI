"""Parameterized variables trading strategy.

Description:
    Demonstrates strategy variables and optimization parameters (IntVar1, IntVar2,
    DoubleVar1, BoolVar1, StringVar1) and uses IntVar1 dynamically as the CCI
    period to drive zero-line crossover entries and opposite order deletion.
    Conforms to StrategyQuant SQ.Strategies.VariablesStrategyTest.

Purpose:
    FEAT-STRATEGIES: StrategyQuant donor-faithful VariablesStrategyTest strategy.

Key Capabilities:
    - FR-STRAT-VARIABLES: Parameter exposure and dynamic indicator parameterization.

Python API Usage:
    from app.extend.strategies.variables_strategy_test import VariablesStrategyTest
    strat = VariablesStrategyTest()
    strat.IntVar1 = 14
    strat.Initialize()
    strat.OnBarUpdate()

CLI Usage:
    uv run pytest tests/extend/test_strategies_catalog.py --no-cov
"""

from __future__ import annotations

from typing import override

from app.core.host.logging import get_logger
from app.extend.strategies.base import (
    OrderCloseTypes,
    OrderTypes,
    Parameter,
    Strategy,
    UpdateEventTypes,
)

logger = get_logger(__name__)


class VariablesStrategyTest(Strategy):
    """Demonstrates parameterized variables and CCI period customization."""

    IntVar1: Parameter[int] = Parameter(11)
    IntVar2: Parameter[int] = Parameter(22)
    DoubleVar1: Parameter[float] = Parameter(11.11)
    BoolVar1: Parameter[bool] = Parameter(True)
    StringVar1: Parameter[str] = Parameter("aaaa")

    def __init__(
        self,
        int_var_1: int = 11,
        int_var_2: int = 22,
        double_var_1: float = 11.11,
        bool_var_1: bool = True,
        string_var_1: str = "aaaa",
    ) -> None:
        super().__init__()
        self.IntVar1 = int_var_1
        self.IntVar2 = int_var_2
        self.DoubleVar1 = double_var_1
        self.BoolVar1 = bool_var_1
        self.StringVar1 = string_var_1

    @override
    def Initialize(self) -> None:
        """Strategy parameter initialization hook."""
        logger.info(
            "FR-STRAT-VARIABLES: Initialize with IntVar1=%s, StringVar1=%s",
            self.IntVar1,
            self.StringVar1,
        )

    @override
    def OnBarUpdate(self) -> None:
        """Evaluate CCI using IntVar1 as period and execute reverse entries."""
        if self.UpdateEventType != UpdateEventTypes.BarOpen:
            return

        cci_value = self.Indicators.CCI(self.Open, self.IntVar1).Value.get(0)

        if cci_value > 0:
            self._close_opposite_order(1234, OrderTypes.Sell)
            self.Trader.Buy(self.Symbol).setMagicNumber(1234).Send()

        if cci_value < 0:
            self._close_opposite_order(1234, OrderTypes.Buy)
            self.Trader.Sell(self.Symbol).setMagicNumber(1234).Send()

        logger.info("FR-STRAT-VARIABLES: OnBarUpdate executed with cci=%s", cci_value)

    def _close_opposite_order(self, magic_number: int, order_type: int) -> None:
        """Close open orders matching magic number and order type."""
        count = self.Trader.getOpenOrdersCount(False)
        for i in range(count):
            order = self.Trader.getOpenOrder(i, False)
            if (
                order.getMagicNumber() == magic_number
                and order.getOrderType() == order_type
            ):
                order.Close(OrderCloseTypes.Deleted)
