"""Initial Deposit databank column snippet.

Description:
    Evaluates Initial Deposit metric for databank strategy snapshot.

Purpose:
    FEAT-EXTEND-COLUMNS-DATABANKS: Concrete databank column evaluators.

Key Capabilities:
    - FR-COLUMNS-DATABANK-INITIAL-DEPOSIT:
      Evaluate Initial Deposit strategy metric.

Python API Usage:
    from app.extend.columns.databanks.initial_deposit import (
        InitialDeposit,
    )
    col = InitialDeposit()
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


class InitialDeposit(DatabankColumn):
    """Evaluates Initial Deposit metric for databank strategy snapshot."""

    def __init__(self) -> None:
        super().__init__(
            column_id="InitialDeposit",
            label="Initial Deposit",
            value_type="MONEY",
            decimals=2,
            maximize=None,
            source_ref="SQ.Columns.Databanks.InitialDeposit",
        )

    @override
    def compute(
        self,
        stats: StrategyStatsSnapshot,
        *,
        sample_type: str = "FullSample",
        direction: str = "Both",
    ) -> float | int | str:
        """Evaluate Initial Deposit across strategy performance snapshot."""
        logger.debug(
            "FR-COLUMNS-DATABANK-%s: evaluating %s",
            "INITIAL-DEPOSIT",
            "InitialDeposit",
        )
        _ = (sample_type, direction)
        return stats.initial_deposit
