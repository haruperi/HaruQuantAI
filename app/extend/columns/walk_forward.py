"""WalkForward column definitions and evaluators (WalkForward/* cohort).

Description:
    Implements WalkForwardColumnEvaluator and registers all 8 WalkForward column
    descriptors evaluating walk-forward matrix and run sequence statistics.

Purpose:
    FEAT-EXTEND-COLUMNS-WF: Concrete walk-forward column evaluators.

Key Capabilities:
    - FR-columns-wf-evaluate: Evaluate walk-forward run sequence metrics.

Python API Usage:
    from app.extend.columns.walk_forward import WalkForwardColumnEvaluator
    val = WalkForwardColumnEvaluator.evaluate("WFPctOfProfitableRuns", wf_runs)

CLI Usage:
    python -m app.cli extend columns walk-forward --list
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from app.core.host.logging import get_logger
from app.extend.columns.base import ColumnDescriptor, WalkForwardRunStats

logger = get_logger(__name__)

WALK_FORWARD_COLUMNS: dict[str, ColumnDescriptor] = {
    "WFMaxDDbyRun": ColumnDescriptor(
        "WFMaxDDbyRun", "WalkForward", "WF Max DD by Run", "MONEY", 2, maximize=False
    ),
    "WFMaxPctDDbyRun": ColumnDescriptor(
        "WFMaxPctDDbyRun", "WalkForward", "WF Max % DD by Run", "PCT", 2, maximize=False
    ),
    "WFMaxProfitByRun": ColumnDescriptor(
        "WFMaxProfitByRun",
        "WalkForward",
        "WF Max Profit by Run",
        "MONEY",
        2,
        maximize=True,
    ),
    "WFMaxProfitByRunInPct": ColumnDescriptor(
        "WFMaxProfitByRunInPct",
        "WalkForward",
        "WF Max % Profit by Run",
        "PCT",
        2,
        maximize=True,
    ),
    "WFMaxStagnationInPct": ColumnDescriptor(
        "WFMaxStagnationInPct",
        "WalkForward",
        "WF Max Stagnation %",
        "PCT",
        2,
        maximize=False,
    ),
    "WFMinTradesInRun": ColumnDescriptor(
        "WFMinTradesInRun",
        "WalkForward",
        "WF Min Trades in Run",
        "INT",
        0,
        maximize=True,
    ),
    "WFPctOfProfitableRuns": ColumnDescriptor(
        "WFPctOfProfitableRuns",
        "WalkForward",
        "WF % of Profitable Runs",
        "PCT",
        2,
        maximize=True,
    ),
    "WFScore": ColumnDescriptor(
        "WFScore", "WalkForward", "WF Score", "NUMBER", 2, maximize=True
    ),
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
            "FR-columns-wf-evaluate: evaluating col=%s runs=%d",
            column_id,
            len(wf_runs),
        )
        if not wf_runs:
            return 0.0

        if column_id == "WFPctOfProfitableRuns":
            profitable = sum(1 for r in wf_runs if r.net_profit > 0.0)
            val = (profitable / len(wf_runs)) * 100.0
        else:
            reducers: dict[str, Callable[[Sequence[WalkForwardRunStats]], float]] = {
                "WFMaxProfitByRun": lambda runs: max(r.net_profit for r in runs),
                "WFMaxProfitByRunInPct": lambda runs: max(
                    r.net_profit_pct for r in runs
                ),
                "WFMaxDDbyRun": lambda runs: max(r.drawdown for r in runs),
                "WFMaxPctDDbyRun": lambda runs: max(r.drawdown_pct for r in runs),
                "WFMaxStagnationInPct": lambda runs: max(
                    r.stagnation_pct for r in runs
                ),
                "WFMinTradesInRun": lambda runs: float(
                    min(r.trades_count for r in runs)
                ),
                "WFScore": lambda runs: sum(r.score for r in runs) / len(runs),
            }
            reducer = reducers.get(column_id)
            val = reducer(wf_runs) if reducer is not None else 0.0

        if not math.isfinite(val):
            return 0.0

        decimals = WALK_FORWARD_COLUMNS.get(
            column_id, ColumnDescriptor("", "WalkForward", "", "NUMBER", 2)
        ).decimals
        return round(val, decimals)
