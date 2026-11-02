"""WF Max % Profit by Run walk-forward column snippet.

Description:
    Max percent profit across walk-forward runs.

Purpose:
    FEAT-EXTEND-COLUMNS-WF: Concrete walk-forward column evaluators.

Key Capabilities:
    - FR-COLUMNS-WF-WF-MAX-PROFIT-BY-RUN-IN-PCT:
      Evaluate WF Max % Profit by Run metric across run sequence.

Python API Usage:
    from app.extend.columns.walk_forward.wf_max_profit_by_run_in_pct import (
        WFMaxProfitByRunInPct,
    )
    col = WFMaxProfitByRunInPct()
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


class WFMaxProfitByRunInPct(WalkForwardColumn):
    """Max percent profit across walk-forward runs."""

    def __init__(self) -> None:
        super().__init__(
            column_id="WFMaxProfitByRunInPct",
            label="WF Max % Profit by Run",
            value_type="PCT",
            decimals=2,
            maximize=True,
            source_ref="SQ.Columns.WalkForward.WFMaxProfitByRunInPct",
        )

    @override
    def compute(self, wf_runs: Sequence[WalkForwardRunStats]) -> float:
        """Evaluate metric across walk-forward run sequence."""
        logger.debug(
            "FR-COLUMNS-WF-%s: evaluating %s",
            "WF-MAX-PROFIT-BY-RUN-IN-PCT",
            "WFMaxProfitByRunInPct",
        )
        if not wf_runs:
            return 0.0
        if any(r.net_profit_pct for r in wf_runs):
            val = max(r.net_profit_pct for r in wf_runs)
        else:
            tot = sum(r.net_profit for r in wf_runs)
            max_p = max(r.net_profit for r in wf_runs)
            val = max_p / (tot / 100.0) if tot != 0 else 0.0
        if not math.isfinite(val):
            return 0.0
        return round(val, self.decimals)
