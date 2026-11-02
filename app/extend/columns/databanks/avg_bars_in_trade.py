"""Avg Bars in Trade databank column snippet.

Description:
    Evaluates Avg Bars in Trade metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-AVG-BARS-IN-TRADE:
      Evaluate Avg Bars in Trade strategy metric.

Python API Usage:
    from app.extend.columns.databanks.avg_bars_in_trade import (
        AvgBarsInTrade,
    )
    col = AvgBarsInTrade()
    val = col.compute(stats)

CLI Usage:
    uv run pytest tests/extend/test_columns_catalog.py --no-cov
"""

from __future__ import annotations

import math
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


class AvgBarsInTrade(DatabankColumn):
    """Evaluates Avg Bars in Trade metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="AvgBarsInTrade",
            label="Avg Bars in Trade",
            value_type="NUMBER",
            decimals=1,
            maximize=None,
            source_ref="SQ.Columns.Databanks.AvgBarsInTrade",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Avg Bars in Trade across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "AVG-BARS-IN-TRADE",
            "AvgBarsInTrade",
        )
        _ = (sample_type, direction)
        trades = filter_snapshot_trades(stats, sample_type, direction)
        _ = trades
        snake_key = to_snake("AvgBarsInTrade")
        raw = stats.metrics.get("AvgBarsInTrade", stats.metrics.get(snake_key, 0.0))
        val = float(raw) if isinstance(raw, (int, float)) else 0.0
        if not math.isfinite(val):
            return 0.0
        return round(val, self.decimals)
