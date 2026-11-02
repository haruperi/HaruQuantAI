"""Win Trades databank column snippet.

Description:
    Evaluates Win Trades metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-NUMBER-OF-PROFITS:
      Evaluate Win Trades strategy metric.

Python API Usage:
    from app.extend.columns.databanks.number_of_profits import (
        NumberOfProfits,
    )
    col = NumberOfProfits()
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


class NumberOfProfits(DatabankColumn):
    """Evaluates Win Trades metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="NumberOfProfits",
            label="Win Trades",
            value_type="INT",
            decimals=0,
            maximize=True,
            source_ref="SQ.Columns.Databanks.NumberOfProfits",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Win Trades across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "NUMBER-OF-PROFITS",
            "NumberOfProfits",
        )
        trades = filter_snapshot_trades(stats, sample_type, direction)
        pls = [float(t.get("profit_loss", t.get("pnl", 0.0))) for t in trades]
        if pls or not stats.metrics:
            return sum(1 for p in pls if p > 0.0)
        return int(stats.metrics.get("NumberOfProfits", 0))
