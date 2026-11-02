"""WF Min Trades in Run walk-forward column snippet.

Description:
    Minimum trades in a single walk-forward run.

Purpose:
    FEAT-EXTEND-COLUMNS-WF: Concrete walk-forward column evaluators.

Key Capabilities:
    - FR-COLUMNS-WF-WF-MIN-TRADES-IN-RUN:
      Evaluate WF Min Trades in Run metric across run sequence.

Python API Usage:
    from app.extend.columns.walk_forward.wf_min_trades_in_run import (
        WFMinTradesInRun,
    )
    col = WFMinTradesInRun()
    val = col.compute(wf_runs)

CLI Usage:
    uv run pytest tests/extend/test_columns_catalog.py --no-cov
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import override

from app.core.host.logging import get_logger
from app.extend.columns.base import WalkForwardColumn, WalkForwardRunStats

logger = get_logger(__name__)


class WFMinTradesInRun(WalkForwardColumn):
    """Minimum trades in a single walk-forward run."""

    def __init__(self) -> None:
        super().__init__(
            column_id="WFMinTradesInRun",
            label="WF Min Trades in Run",
            value_type="INT",
            decimals=0,
            maximize=True,
            source_ref="SQ.Columns.WalkForward.WFMinTradesInRun",
        )

    @override
    def compute(self, wf_runs: Sequence[WalkForwardRunStats]) -> float:
        """Evaluate metric across walk-forward run sequence."""
        logger.debug(
            "FR-COLUMNS-WF-%s: evaluating %s",
            "WF-MIN-TRADES-IN-RUN",
            "WFMinTradesInRun",
        )
        if not wf_runs:
            return 0.0
        val = float(min(r.trades_count for r in wf_runs))
        if not math.isfinite(val):
            return 0.0
        return round(val, self.decimals)
