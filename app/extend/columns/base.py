"""Base definitions and types for strategy column extension cohort.

Description:
    Provides ColumnDescriptor, Category/ValueType literals, and input snapshots
    for evaluating Databanks, Trades, and WalkForward metric columns.

Purpose:
    FEAT-EXTEND-COLUMNS: Concrete column definitions and evaluator base.

Key Capabilities:
    - FR-columns-base-models: Typed column descriptor models and input snapshots.

Python API Usage:
    from app.extend.columns.base import ColumnDescriptor
    desc = ColumnDescriptor("NetProfit", "Databanks", "Net Profit", "MONEY", 2)

CLI Usage:
    python -m app.cli extend columns list
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

ColumnCategory = Literal["Databanks", "Trades", "WalkForward"]
ColumnValueType = Literal[
    "MONEY",
    "PCT",
    "PIPS",
    "NUMBER",
    "INT",
    "TEXT",
    "DATETIME",
    "CHART",
]


@dataclass(frozen=True, slots=True)
class ColumnDescriptor:
    """Descriptor defining identity, presentation, and target for a column."""

    column_id: str
    category: ColumnCategory
    label: str
    value_type: ColumnValueType
    decimals: int = 2
    maximize: bool | None = None
    source_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert descriptor to dictionary."""
        return {
            "column_id": self.column_id,
            "category": self.category,
            "label": self.label,
            "value_type": self.value_type,
            "decimals": self.decimals,
            "maximize": self.maximize,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True, slots=True)
class StrategyStatsSnapshot:
    """Strategy performance and trade outcome input snapshot."""

    metrics: dict[str, float | int | str] = field(default_factory=dict)
    trades: tuple[dict[str, Any], ...] = ()
    parameters: dict[str, Any] = field(default_factory=dict)
    initial_deposit: float = 10000.0
    strategy_name: str = ""


@dataclass(frozen=True, slots=True)
class TradeRecord:
    """Executed trade record snapshot for single-trade column evaluation."""

    ticket: int = 1
    symbol: str = "EURUSD"
    type: str = "BUY"
    direction: str = "BUY"
    open_time: str | int = 0
    close_time: str | int = 0
    open_price: float = 0.0
    close_price: float = 0.0
    size: float = 1.0
    profit_loss: float = 0.0
    profit_loss_pips: float = 0.0
    profit_loss_pct: float = 0.0
    comment: str = ""
    mae: float = 0.0
    mfe: float = 0.0
    mae_pips: float = 0.0
    mfe_pips: float = 0.0
    sl_level: float | None = None
    pt_level: float | None = None
    sample_type: str = "FullSample"
    bars_in_trade: int = 0
    time_in_trade: str = ""
    comm_swap: float = 0.0
    slippage_money: float = 0.0
    result_name: str = "Main"


@dataclass(frozen=True, slots=True)
class WalkForwardRunStats:
    """Walk-forward run period performance statistics."""

    run_index: int = 1
    start_date: str = ""
    end_date: str = ""
    net_profit: float = 0.0
    net_profit_pct: float = 0.0
    drawdown: float = 0.0
    drawdown_pct: float = 0.0
    trades_count: int = 0
    stagnation_pct: float = 0.0
    score: float = 0.0


def safe_divide(num: float, den: float, default: float = 0.0) -> float:
    """Safely divide numbers, returning default on zero or non-finite denominator."""
    if den == 0.0 or not math.isfinite(den):
        return default
    res = num / den
    return res if math.isfinite(res) else default


def filter_snapshot_trades(
    stats: StrategyStatsSnapshot,
    sample_type: str = "FullSample",
    direction: str = "Both",
) -> list[dict[str, Any]]:
    """Filter trades in a strategy stats snapshot by sample type and direction."""
    target_dir = direction.upper()
    return [
        t
        for t in stats.trades
        if (
            sample_type == "FullSample"
            or t.get("sample_type", "FullSample") == sample_type
        )
        and (
            direction == "Both"
            or str(t.get("type", t.get("direction", "BUY"))).upper() == target_dir
        )
    ]


def compute_snapshot_pnl_drawdown(
    trades: list[dict[str, Any]],
    initial_deposit: float,
    metric_dd: float = 0.0,
) -> tuple[list[float], float, float, float]:
    """Calculate trade P&L list, gross profit, gross loss, and max drawdown."""
    pls = [float(t.get("profit_loss", t.get("pnl", 0.0))) for t in trades]
    gross_profit = sum(p for p in pls if p > 0.0)
    gross_loss = sum(p for p in pls if p < 0.0)

    peak = initial_deposit
    curr_bal = initial_deposit
    max_dd = 0.0
    for p in pls:
        curr_bal += p
        peak = max(peak, curr_bal)
        dd = peak - curr_bal
        max_dd = max(max_dd, dd)
    if not max_dd and metric_dd:
        max_dd = abs(metric_dd)

    return pls, gross_profit, gross_loss, max_dd


class DatabankColumn(ABC):
    """Base class for StrategyQuant Databank metric columns."""

    def __init__(
        self,
        column_id: str,
        label: str,
        value_type: ColumnValueType = "NUMBER",
        decimals: int = 2,
        *,
        maximize: bool | None = None,
        preferred_min: float | None = None,
        preferred_max: float | None = None,
        is_dependent_on_trading_period: bool = False,
        source_ref: str = "",
    ) -> None:
        self.column_id = column_id
        self.label = label
        self.value_type = value_type
        self.decimals = decimals
        self.maximize = maximize
        self.preferred_min = preferred_min
        self.preferred_max = preferred_max
        self.is_dependent_on_trading_period = is_dependent_on_trading_period
        self.source_ref = source_ref

    @property
    def descriptor(self) -> ColumnDescriptor:
        """Return immutable descriptor representation."""
        return ColumnDescriptor(
            column_id=self.column_id,
            category="Databanks",
            label=self.label,
            value_type=self.value_type,
            decimals=self.decimals,
            maximize=self.maximize,
            source_ref=self.source_ref,
        )

    @abstractmethod
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Compute the column metric from strategy performance snapshot."""
        ...

    def get_value(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Alias for compute / metadata extraction."""
        return self.compute(stats, sample_type=sample_type, direction=direction)


class TradelistColumn(ABC):
    """Base class for StrategyQuant Trades list columns."""

    def __init__(
        self,
        column_id: str,
        label: str,
        value_type: ColumnValueType = "TEXT",
        decimals: int = 0,
        *,
        source_ref: str = "",
    ) -> None:
        self.column_id = column_id
        self.label = label
        self.value_type = value_type
        self.decimals = decimals
        self.source_ref = source_ref

    @property
    def descriptor(self) -> ColumnDescriptor:
        """Return immutable descriptor representation."""
        return ColumnDescriptor(
            column_id=self.column_id,
            category="Trades",
            label=self.label,
            value_type=self.value_type,
            decimals=self.decimals,
            source_ref=self.source_ref,
        )

    @abstractmethod
    def get_value(
        self,
        trade: TradeRecord,
        *,
        index: int = 1,
        running_balance: float = 0.0,
        running_dd_money: float = 0.0,
        running_dd_pct: float = 0.0,
    ) -> Any:
        """Extract or compute column value for a single trade row."""
        ...


class WalkForwardColumn(ABC):
    """Base class for StrategyQuant Walk-Forward evaluation columns."""

    def __init__(
        self,
        column_id: str,
        label: str,
        value_type: ColumnValueType = "NUMBER",
        decimals: int = 2,
        *,
        maximize: bool | None = None,
        source_ref: str = "",
    ) -> None:
        self.column_id = column_id
        self.label = label
        self.value_type = value_type
        self.decimals = decimals
        self.maximize = maximize
        self.source_ref = source_ref

    @property
    def descriptor(self) -> ColumnDescriptor:
        """Return immutable descriptor representation."""
        return ColumnDescriptor(
            column_id=self.column_id,
            category="WalkForward",
            label=self.label,
            value_type=self.value_type,
            decimals=self.decimals,
            maximize=self.maximize,
            source_ref=self.source_ref,
        )

    @abstractmethod
    def compute(self, wf_runs: Sequence[WalkForwardRunStats]) -> float:
        """Compute summary walk-forward metric across run sequence."""
        ...
