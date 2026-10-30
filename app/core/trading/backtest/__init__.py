"""Core backtesting runner and simulation contracts."""

from typing import TYPE_CHECKING, Any

from app.core.trading.backtest.contracts import (
    BacktestSettings,
    EquityPoint,
    MaeMfeRecord,
    PrecisionMode,
    RunResult,
    RunSpec,
    SameBarExecutionRule,
    TradeRecord,
)

if TYPE_CHECKING:
    from app.core.trading.backtest.runner import BacktestRunner

__all__ = [
    "BacktestRunner",
    "BacktestSettings",
    "EquityPoint",
    "MaeMfeRecord",
    "PrecisionMode",
    "RunResult",
    "RunSpec",
    "SameBarExecutionRule",
    "TradeRecord",
]


def __getattr__(name: str) -> Any:
    if name == "BacktestRunner":
        from app.core.trading.backtest.runner import BacktestRunner

        return BacktestRunner
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
