"""Stagnation (%) databank column snippet.

Description:
    Evaluates Stagnation (%) metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-STAGNATION-PCT:
      Evaluate Stagnation (%) strategy metric.

Python API Usage:
    from app.extend.columns.databanks.stagnation_pct import (
        StagnationPct,
    )
    col = StagnationPct()
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


class StagnationPct(DatabankColumn):
    """Evaluates Stagnation (%) metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="StagnationPct",
            label="Stagnation (%)",
            value_type="PCT",
            decimals=2,
            maximize=False,
            source_ref="SQ.Columns.Databanks.StagnationPct",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Stagnation (%) across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "STAGNATION-PCT",
            "StagnationPct",
        )
        _ = (sample_type, direction)
        trades = filter_snapshot_trades(stats, sample_type, direction)
        _ = trades
        snake_key = to_snake("StagnationPct")
        raw = stats.metrics.get("StagnationPct", stats.metrics.get(snake_key, 0.0))
        val = float(raw) if isinstance(raw, (int, float)) else 0.0
        if not math.isfinite(val):
            return 0.0
        return round(val, self.decimals)
