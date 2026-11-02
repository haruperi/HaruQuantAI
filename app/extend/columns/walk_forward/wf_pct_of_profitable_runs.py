"""WF % of Profitable Runs walk-forward column snippet.

Description:
    Percentage of profitable walk-forward runs.

Purpose:
    FEAT-EXTEND-COLUMNS-WF: Concrete walk-forward column evaluators.

Key Capabilities:
    - FR-COLUMNS-WF-WF-PCT-OF-PROFITABLE-RUNS:
      Evaluate WF % of Profitable Runs metric across run sequence.

Python API Usage:
    from app.extend.columns.walk_forward.wf_pct_of_profitable_runs import (
        WFPctOfProfitableRuns,
    )
    col = WFPctOfProfitableRuns()
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


class WFPctOfProfitableRuns(WalkForwardColumn):
    """Percentage of profitable walk-forward runs."""

    def __init__(self) -> None:
        super().__init__(
            column_id="WFPctOfProfitableRuns",
            label="WF % of Profitable Runs",
            value_type="PCT",
            decimals=2,
            maximize=True,
            source_ref="SQ.Columns.WalkForward.WFPctOfProfitableRuns",
        )

    @override
    def compute(self, wf_runs: Sequence[WalkForwardRunStats]) -> float:
        """Evaluate metric across walk-forward run sequence."""
        logger.debug(
            "FR-COLUMNS-WF-%s: evaluating %s",
            "WF-PCT-OF-PROFITABLE-RUNS",
            "WFPctOfProfitableRuns",
        )
        if not wf_runs:
            return 0.0
        val = (sum(1 for r in wf_runs if r.net_profit > 0.0) / len(wf_runs)) * 100.0
        if not math.isfinite(val):
            return 0.0
        return round(val, self.decimals)
