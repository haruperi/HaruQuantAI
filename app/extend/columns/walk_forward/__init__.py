"""WalkForward column definitions and evaluators (WalkForward/* cohort).

Description:
    Implements WalkForwardColumnEvaluator and registers all 8 WalkForward column
    descriptors evaluating walk-forward matrix and run sequence statistics.

Purpose:
    FEAT-EXTEND-COLUMNS-WF: Concrete walk-forward column evaluators.

Key Capabilities:
    - FR-COLUMNS-WF-EVALUATE: Evaluate walk-forward run sequence metrics.

Python API Usage:
    from app.extend.columns.walk_forward import WalkForwardColumnEvaluator
    val = WalkForwardColumnEvaluator.evaluate("WFPctOfProfitableRuns", wf_runs)

CLI Usage:
    uv run pytest tests/extend/test_columns_catalog.py --no-cov
"""

from __future__ import annotations

from collections.abc import Sequence

from app.core.host.logging import get_logger
from app.extend.columns.base import (
    ColumnDescriptor,
    WalkForwardColumn,
    WalkForwardRunStats,
)
from app.extend.columns.walk_forward.wf_max_dd_by_run import WFMaxDDbyRun
from app.extend.columns.walk_forward.wf_max_pct_dd_by_run import WFMaxPctDDbyRun
from app.extend.columns.walk_forward.wf_max_profit_by_run import WFMaxProfitByRun
from app.extend.columns.walk_forward.wf_max_profit_by_run_in_pct import (
    WFMaxProfitByRunInPct,
)
from app.extend.columns.walk_forward.wf_max_stagnation_in_pct import (
    WFMaxStagnationInPct,
)
from app.extend.columns.walk_forward.wf_min_trades_in_run import WFMinTradesInRun
from app.extend.columns.walk_forward.wf_pct_of_profitable_runs import (
    WFPctOfProfitableRuns,
)
from app.extend.columns.walk_forward.wf_score import WFScore

logger = get_logger(__name__)

WALK_FORWARD_INSTANCES: dict[str, WalkForwardColumn] = {
    "WFMaxDDbyRun": WFMaxDDbyRun(),
    "WFMaxPctDDbyRun": WFMaxPctDDbyRun(),
    "WFMaxProfitByRun": WFMaxProfitByRun(),
    "WFMaxProfitByRunInPct": WFMaxProfitByRunInPct(),
    "WFMaxStagnationInPct": WFMaxStagnationInPct(),
    "WFMinTradesInRun": WFMinTradesInRun(),
    "WFPctOfProfitableRuns": WFPctOfProfitableRuns(),
    "WFScore": WFScore(),
}

WALK_FORWARD_COLUMNS: dict[str, ColumnDescriptor] = {
    k: v.descriptor for k, v in WALK_FORWARD_INSTANCES.items()
}


class WalkForwardColumnEvaluator:
    """Evaluates Walk-Forward run metrics across run sequences."""

    @classmethod
    def list_descriptors(cls) -> tuple[ColumnDescriptor, ...]:
        """List all 8 registered WalkForward column descriptors."""
        return tuple(WALK_FORWARD_COLUMNS.values())

    @classmethod
    def evaluate(cls, column_id: str, wf_runs: Sequence[WalkForwardRunStats]) -> float:
        """Evaluate a walk-forward summary metric across run periods."""
        logger.debug(
            "FR-COLUMNS-WF-EVALUATE: evaluating col=%s runs=%d",
            column_id,
            len(wf_runs),
        )
        col = WALK_FORWARD_INSTANCES.get(column_id)
        if col is None:
            return 0.0
        return col.compute(wf_runs)


__all__ = [
    "WALK_FORWARD_COLUMNS",
    "WALK_FORWARD_INSTANCES",
    "WFMaxDDbyRun",
    "WFMaxPctDDbyRun",
    "WFMaxProfitByRun",
    "WFMaxProfitByRunInPct",
    "WFMaxStagnationInPct",
    "WFMinTradesInRun",
    "WFPctOfProfitableRuns",
    "WFScore",
    "WalkForwardColumnEvaluator",
]
