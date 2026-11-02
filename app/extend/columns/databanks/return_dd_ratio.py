"""Return / DD databank column snippet.

Description:
    Evaluates Return / DD metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-RETURN-DD-RATIO:
      Evaluate Return / DD strategy metric.

Python API Usage:
    from app.extend.columns.databanks.return_dd_ratio import (
        ReturnDDRatio,
    )
    col = ReturnDDRatio()
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
    compute_snapshot_pnl_drawdown,
    filter_snapshot_trades,
    safe_divide,
)

logger = get_logger(__name__)


def to_snake(name: str) -> str:
    """Helper to convert identifier to snake case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return re.sub(r"_+", "_", s2)


class ReturnDDRatio(DatabankColumn):
    """Evaluates Return / DD metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="ReturnDDRatio",
            label="Return / DD",
            value_type="NUMBER",
            decimals=2,
            maximize=True,
            source_ref="SQ.Columns.Databanks.ReturnDDRatio",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Return / DD across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "RETURN-DD-RATIO",
            "ReturnDDRatio",
        )
        trades = filter_snapshot_trades(stats, sample_type, direction)
        metric_dd = float(
            stats.metrics.get("drawdown", stats.metrics.get("Drawdown", 0.0))
        )
        pls, _, _, max_dd = compute_snapshot_pnl_drawdown(
            trades, stats.initial_deposit, metric_dd
        )
        fallback_p = stats.metrics.get(
            "net_profit", stats.metrics.get("NetProfit", 0.0)
        )
        net_profit = sum(pls) if pls else float(fallback_p)
        if max_dd == 0.0:
            return round(net_profit, self.decimals) if net_profit > 0.0 else 0.0
        return round(safe_divide(net_profit, max_dd), self.decimals)
