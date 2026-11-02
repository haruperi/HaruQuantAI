"""WF Max % DD by Run walk-forward column snippet.

Description:
    Max percent drawdown across walk-forward runs.

Purpose:
    FEAT-EXTEND-COLUMNS-WF: Concrete walk-forward column evaluators.

Key Capabilities:
    - FR-COLUMNS-WF-WF-MAX-PCT-DD-BY-RUN:
      Evaluate WF Max % DD by Run metric across run sequence.

Python API Usage:
    from app.extend.columns.walk_forward.wf_max_pct_dd_by_run import (
        WFMaxPctDDbyRun,
    )
    col = WFMaxPctDDbyRun()
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


class WFMaxPctDDbyRun(WalkForwardColumn):
    """Max percent drawdown across walk-forward runs."""

    def __init__(self) -> None:
        super().__init__(
            column_id="WFMaxPctDDbyRun",
            label="WF Max % DD by Run",
            value_type="PCT",
            decimals=2,
            maximize=False,
            source_ref="SQ.Columns.WalkForward.WFMaxPctDDbyRun",
        )

    @override
    def compute(self, wf_runs: Sequence[WalkForwardRunStats]) -> float:
        """Evaluate metric across walk-forward run sequence."""
        logger.debug(
            "FR-COLUMNS-WF-%s: evaluating %s",
            "WF-MAX-PCT-DD-BY-RUN",
            "WFMaxPctDDbyRun",
        )
        if not wf_runs:
            return 0.0
        val = max(r.drawdown_pct for r in wf_runs)
        if not math.isfinite(val):
            return 0.0
        return round(val, self.decimals)
