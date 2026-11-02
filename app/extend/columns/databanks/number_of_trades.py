"""Total Trades databank column snippet.

Description:
    Evaluates Total Trades metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-NUMBER-OF-TRADES:
      Evaluate Total Trades strategy metric.

Python API Usage:
    from app.extend.columns.databanks.number_of_trades import (
        NumberOfTrades,
    )
    col = NumberOfTrades()
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


class NumberOfTrades(DatabankColumn):
    """Evaluates Total Trades metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="NumberOfTrades",
            label="Total Trades",
            value_type="INT",
            decimals=0,
            maximize=True,
            source_ref="SQ.Columns.Databanks.NumberOfTrades",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Total Trades across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "NUMBER-OF-TRADES",
            "NumberOfTrades",
        )
        trades = filter_snapshot_trades(stats, sample_type, direction)
        if trades or not stats.metrics:
            return len(trades)
        raw_tc = stats.metrics.get(
            "trades_count", stats.metrics.get("NumberOfTrades", 0)
        )
        return int(raw_tc)
