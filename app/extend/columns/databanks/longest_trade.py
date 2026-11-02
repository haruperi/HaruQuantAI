"""Longest Trade databank column snippet.

Description:
    Evaluates Longest Trade metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-LONGEST-TRADE:
      Evaluate Longest Trade strategy metric.

Python API Usage:
    from app.extend.columns.databanks.longest_trade import (
        LongestTrade,
    )
    col = LongestTrade()
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
)

logger = get_logger(__name__)


def to_snake(name: str) -> str:
    """Helper to convert identifier to snake case."""
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    s2 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
    return re.sub(r"_+", "_", s2)


class LongestTrade(DatabankColumn):
    """Evaluates Longest Trade metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="LongestTrade",
            label="Longest Trade",
            value_type="TEXT",
            decimals=0,
            maximize=None,
            source_ref="SQ.Columns.Databanks.LongestTrade",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Longest Trade across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "LONGEST-TRADE",
            "LongestTrade",
        )
        _ = (sample_type, direction)
        return str(stats.metrics.get("LongestTrade", ""))
