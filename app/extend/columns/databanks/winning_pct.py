"""Winning (%) databank column snippet.

Description:
    Evaluates Winning (%) metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-WINNING-PCT:
      Evaluate Winning (%) strategy metric.

Python API Usage:
    from app.extend.columns.databanks.winning_pct import (
        WinningPct,
    )
    col = WinningPct()
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


class WinningPct(DatabankColumn):
    """Evaluates Winning (%) metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="WinningPct",
            label="Winning (%)",
            value_type="PCT",
            decimals=2,
            maximize=True,
            source_ref="SQ.Columns.Databanks.WinningPct",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Winning (%) across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "WINNING-PCT",
            "WinningPct",
        )
        trades = filter_snapshot_trades(stats, sample_type, direction)
        pls = [float(t.get("profit_loss", t.get("pnl", 0.0))) for t in trades]
        if pls:
            n_wins = sum(1 for p in pls if p > 0.0)
            return round(safe_divide(n_wins * 100.0, len(pls)), self.decimals)
        raw = stats.metrics.get("WinningPct", 0.0)
        return round(float(raw), self.decimals)
