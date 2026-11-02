"""Net Profit (%) databank column snippet.

Description:
    Evaluates Net Profit (%) metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-NET-PROFIT-IN-PCT:
      Evaluate Net Profit (%) strategy metric.

Python API Usage:
    from app.extend.columns.databanks.net_profit_in_pct import (
        NetProfitInPct,
    )
    col = NetProfitInPct()
    val = col.compute(stats)

CLI Usage:
    uv run pytest tests/extend/test_columns_catalog.py --no-cov
"""

from __future__ import annotations

import re
from typing import override

from app.core.host.logging import get_logger
from app.extend.columns.base import (
    DatabankColumn,
    StrategyStatsSnapshot,
    filter_snapshot_trades,
    safe_divide,
)

logger = get_logger(__name__)


def to_snake(name: str) -> str:
    """Helper to convert identifier to snake case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return re.sub(r"_+", "_", s2)


class NetProfitInPct(DatabankColumn):
    """Evaluates Net Profit (%) metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="NetProfitInPct",
            label="Net Profit (%)",
            value_type="PCT",
            decimals=2,
            maximize=True,
            source_ref="SQ.Columns.Databanks.NetProfitInPct",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Net Profit (%) across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "NET-PROFIT-IN-PCT",
            "NetProfitInPct",
        )
        trades = filter_snapshot_trades(stats, sample_type, direction)
        pls = [float(t.get("profit_loss", t.get("pnl", 0.0))) for t in trades]
        fallback_p = stats.metrics.get(
            "net_profit", stats.metrics.get("NetProfit", 0.0)
        )
        net_p = sum(pls) if pls else float(fallback_p)
        dep = stats.initial_deposit
        pct = safe_divide(net_p * 100.0, dep)
        return round(pct, self.decimals)
