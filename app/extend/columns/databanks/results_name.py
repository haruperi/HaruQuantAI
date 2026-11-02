"""Strategy Name databank column snippet.

Description:
    Evaluates Strategy Name metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-RESULTS-NAME:
      Evaluate Strategy Name strategy metric.

Python API Usage:
    from app.extend.columns.databanks.results_name import (
        ResultsName,
    )
    col = ResultsName()
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


class ResultsName(DatabankColumn):
    """Evaluates Strategy Name metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="ResultsName",
            label="Strategy Name",
            value_type="TEXT",
            decimals=0,
            maximize=None,
            source_ref="SQ.Columns.Databanks.ResultsName",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Strategy Name across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "RESULTS-NAME",
            "ResultsName",
        )
        _ = (sample_type, direction)
        strat = stats.strategy_name
        fallback = stats.metrics.get(
            "strategy_name", stats.metrics.get("ResultsName", "")
        )
        return strat or str(fallback)
