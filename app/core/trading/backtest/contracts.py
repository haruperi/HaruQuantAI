"""Historical execution contracts and instrument valuation inputs.

Description:
    Describe execution models, data feeds, equity, and returned effects.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Consistent, explicit strategy execution boundaries.
Key Capabilities:
    - FR-shared-hsl-execution: Hosts log decisions; focused tests verify effects.
Python API Usage:
    Import the typed contracts and services from this module.
CLI Usage:
    uv run pytest tests/core/trading tests/workspace/algo_wizard --no-cov
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.enums import Timeframe
from app.core.trading.blocks.series import BarData
from app.core.trading.strategy.contracts import (
    InstrumentEconomics,
    StrategyDocument,
    StrategyEffects,
)


class PrecisionMode(StrEnum):
    """Simulation price resolution mode."""

    OHLC = "OHLC"
    TICK = "TICK"


class SameBarExecutionRule(StrEnum):
    """Tie-breaking execution order when both SL and TP are crossed within same bar."""

    WORST_CASE = "WORST_CASE"
    BEST_CASE = "BEST_CASE"


@dataclass(frozen=True, slots=True)
class BacktestSettings:
    """Historical backtest execution parameters and friction models."""

    initial_capital: float = 100000.0
    slippage_points: float = 0.0
    commission_per_order: float = 0.0
    precision_mode: PrecisionMode = PrecisionMode.OHLC
    same_bar_sl_tp_rule: SameBarExecutionRule = SameBarExecutionRule.WORST_CASE
    point_value: float = 1.0
    pip_size: float = 0.0001
    economics: InstrumentEconomics | None = None


@dataclass(frozen=True, slots=True)
class RunSpec:
    """Specification of strategy, market series, and execution parameters for a run."""

    strategy: StrategyDocument
    symbol: str
    timeframe: Timeframe
    bars: Sequence[MarketBar]
    settings: BacktestSettings = field(default_factory=BacktestSettings)
    additional_bars: Mapping[tuple[str, str], BarData] = field(default_factory=dict)
    bar_close_times: Mapping[tuple[str, str], tuple[int, ...]] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class TradeRecord:
    """Executed and completed trading position record."""

    ticket: int | str
    symbol: str
    direction: int
    volume: float
    open_time: int
    open_price: float
    close_time: int
    close_price: float
    sl: float = 0.0
    tp: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    pnl: float = 0.0
    net_pnl: float = 0.0
    close_reason: str = ""
    magic: int = 0
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert trade record to dictionary."""
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "direction": self.direction,
            "volume": self.volume,
            "open_time": self.open_time,
            "open_price": self.open_price,
            "close_time": self.close_time,
            "close_price": self.close_price,
            "sl": self.sl,
            "tp": self.tp,
            "commission": self.commission,
            "slippage": self.slippage,
            "pnl": self.pnl,
            "net_pnl": self.net_pnl,
            "close_reason": self.close_reason,
            "magic": self.magic,
            "comment": self.comment,
        }


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """Point-in-time portfolio mark-to-market equity evaluation."""

    timestamp: int
    equity: float
    balance: float
    drawdown: float = 0.0
    drawdown_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert equity point to dictionary."""
        return {
            "timestamp": self.timestamp,
            "equity": self.equity,
            "balance": self.balance,
            "drawdown": self.drawdown,
            "drawdown_pct": self.drawdown_pct,
        }


@dataclass(frozen=True, slots=True)
class MaeMfeRecord:
    """Maximum Adverse Excursion and Maximum Favorable Excursion metrics for a trade."""

    ticket: int | str
    mae_price: float
    mae_points: float
    mae_pnl: float
    mfe_price: float
    mfe_points: float
    mfe_pnl: float

    def to_dict(self) -> dict[str, Any]:
        """Convert MAE/MFE record to dictionary."""
        return {
            "ticket": self.ticket,
            "mae_price": self.mae_price,
            "mae_points": self.mae_points,
            "mae_pnl": self.mae_pnl,
            "mfe_price": self.mfe_price,
            "mfe_points": self.mfe_points,
            "mfe_pnl": self.mfe_pnl,
        }


@dataclass(frozen=True, slots=True)
class RunResult:
    """Historical backtest execution result containing trades, equity, and metrics."""

    strategy_id: str
    trades: tuple[TradeRecord, ...]
    equity_curve: tuple[EquityPoint, ...]
    metrics: dict[str, float]
    mae_mfe: tuple[MaeMfeRecord, ...]
    effects: tuple[StrategyEffects, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert backtest result to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "trades": [t.to_dict() for t in self.trades],
            "equity_curve": [e.to_dict() for e in self.equity_curve],
            "metrics": dict(self.metrics),
            "mae_mfe": [m.to_dict() for m in self.mae_mfe],
        }


__all__ = [
    "BacktestSettings",
    "EquityPoint",
    "MaeMfeRecord",
    "PrecisionMode",
    "RunResult",
    "RunSpec",
    "SameBarExecutionRule",
    "TradeRecord",
]
