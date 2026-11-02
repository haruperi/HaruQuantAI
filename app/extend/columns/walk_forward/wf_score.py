"""WF Score walk-forward column snippet.

Description:
    Average walk-forward score across runs.

Purpose:
    FEAT-EXTEND-COLUMNS-WF: Concrete walk-forward column evaluators.

Key Capabilities:
    - FR-COLUMNS-WF-WF-SCORE:
      Evaluate WF Score metric across run sequence.

Python API Usage:
    from app.extend.columns.walk_forward.wf_score import (
        WFScore,
    )
    col = WFScore()
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


class WFScore(WalkForwardColumn):
    """Average walk-forward score across runs."""

    def __init__(self) -> None:
        super().__init__(
            column_id="WFScore",
            label="WF Score",
            value_type="NUMBER",
            decimals=2,
            maximize=True,
            source_ref="SQ.Columns.WalkForward.WFScore",
        )

    @override
    def compute(self, wf_runs: Sequence[WalkForwardRunStats]) -> float:
        """Evaluate metric across walk-forward run sequence."""
        logger.debug(
            "FR-COLUMNS-WF-%s: evaluating %s",
            "WF-SCORE",
            "WFScore",
        )
        if not wf_runs:
            return 0.0
        val = sum(r.score for r in wf_runs) / len(wf_runs)
        if not math.isfinite(val):
            return 0.0
        return round(val, self.decimals)
