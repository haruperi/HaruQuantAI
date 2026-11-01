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
