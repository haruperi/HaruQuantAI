"""Profit Factor databank column snippet.

Description:
    Evaluates Profit Factor metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-PROFIT-FACTOR:
      Evaluate Profit Factor strategy metric.

Python API Usage:
    from app.extend.columns.databanks.profit_factor import (
        ProfitFactor,
    )
    col = ProfitFactor()
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
)

logger = get_logger(__name__)


def to_snake(name: str) -> str:
    """Helper to convert identifier to snake case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return re.sub(r"_+", "_", s2)


class ProfitFactor(DatabankColumn):
    """Evaluates Profit Factor metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="ProfitFactor",
            label="Profit Factor",
            value_type="NUMBER",
            decimals=2,
            maximize=True,
            source_ref="SQ.Columns.Databanks.ProfitFactor",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Profit Factor across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "PROFIT-FACTOR",
            "ProfitFactor",
        )
        trades = filter_snapshot_trades(stats, sample_type, direction)
        pls = [float(t.get("profit_loss", t.get("pnl", 0.0))) for t in trades]
        if pls:
            gp = sum(p for p in pls if p > 0.0)
            gl = abs(sum(p for p in pls if p < 0.0))
            if gl == 0.0:
                return round(gp, self.decimals) if gp > 0.0 else 0.0
            return round(gp / gl, self.decimals)
        raw = stats.metrics.get("ProfitFactor", 0.0)
        return round(float(raw), self.decimals)
