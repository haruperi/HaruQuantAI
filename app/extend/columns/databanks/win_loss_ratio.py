"""Win / Loss Ratio databank column snippet.

Description:
    Evaluates Win / Loss Ratio metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-WIN-LOSS-RATIO:
      Evaluate Win / Loss Ratio strategy metric.

Python API Usage:
    from app.extend.columns.databanks.win_loss_ratio import (
        WinLossRatio,
    )
    col = WinLossRatio()
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


class WinLossRatio(DatabankColumn):
    """Evaluates Win / Loss Ratio metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="WinLossRatio",
            label="Win / Loss Ratio",
            value_type="NUMBER",
            decimals=2,
            maximize=True,
            source_ref="SQ.Columns.Databanks.WinLossRatio",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Win / Loss Ratio across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "WIN-LOSS-RATIO",
            "WinLossRatio",
        )
        trades = filter_snapshot_trades(stats, sample_type, direction)
        pls = [float(t.get("profit_loss", t.get("pnl", 0.0))) for t in trades]
        wins = [p for p in pls if p > 0.0]
        losses = [p for p in pls if p < 0.0]
        if wins or losses:
            avg_win = safe_divide(sum(wins), len(wins)) if wins else 0.0
            avg_loss = safe_divide(abs(sum(losses)), len(losses)) if losses else 0.0
            return round(safe_divide(avg_win, avg_loss, default=avg_win), self.decimals)
        raw = stats.metrics.get("WinLossRatio", 0.0)
        return round(float(raw), self.decimals)
