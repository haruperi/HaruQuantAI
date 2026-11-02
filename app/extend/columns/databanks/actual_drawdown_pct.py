"""Actual DD (%) databank column snippet.

Description:
    Evaluates Actual DD (%) metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-ACTUAL-DRAWDOWN-PCT:
      Evaluate Actual DD (%) strategy metric.

Python API Usage:
    from app.extend.columns.databanks.actual_drawdown_pct import (
        ActualDrawdownPct,
    )
    col = ActualDrawdownPct()
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


class ActualDrawdownPct(DatabankColumn):
    """Evaluates Actual DD (%) metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="ActualDrawdownPct",
            label="Actual DD (%)",
            value_type="PCT",
            decimals=2,
            maximize=False,
            source_ref="SQ.Columns.Databanks.ActualDrawdownPct",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Actual DD (%) across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "ACTUAL-DRAWDOWN-PCT",
            "ActualDrawdownPct",
        )
        trades = filter_snapshot_trades(stats, sample_type, direction)
        metric_dd = float(
            stats.metrics.get("drawdown", stats.metrics.get("Drawdown", 0.0))
        )
        _, _, _, max_dd = compute_snapshot_pnl_drawdown(
            trades, stats.initial_deposit, metric_dd
        )
        dep = stats.initial_deposit
        pct = safe_divide(max_dd * 100.0, dep)
        return round(pct, self.decimals)
