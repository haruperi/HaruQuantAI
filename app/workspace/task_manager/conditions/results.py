"""Results count project condition evaluator.

Description:
    Evaluates databank strategy result counts against configured thresholds using
    signed 32-bit delta wrapping, databank validation, and the core ConditionComparator.

Purpose:
    FEAT-TASK-CONDITIONS: Evaluate databank record count conditions.

Key Capabilities:
    - FR-task-conditions-results: Validate databank presence, compute wrapped signed
      32-bit delta, and validate with shared ConditionComparator.

Python API Usage:
    ```python
    from app.workspace.task_manager.conditions.results import ResultsCountCondition

    check = ResultsCountCondition.evaluate({"Results": 99}, comparator="<", number=100)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/conditions/test_results.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping

from app.core.host.logging import get_logger
from app.core.trading.conditions import ConditionComparator
from app.workspace.task_manager.conditions.models import ConditionCheck

logger = get_logger(__name__)

__all__ = ["ResultsCountCondition"]


class ResultsCountCondition:
    """Evaluates databank results record count against configured thresholds."""

    @staticmethod
    def evaluate(
        databank_counts: Mapping[str, int],
        *,
        comparator: str = "<",
        number: int = 100,
        databank: str = "Results",
    ) -> ConditionCheck:
        """Evaluate databank results count condition.

        Args:
            databank_counts: Mapping of databank name to record count.
            comparator: Comparison operator string (e.g. '<', '>', '=', '>=', '<=').
            number: Target threshold integer.
            databank: Target databank name (default 'Results').

        Returns:
            ConditionCheck containing boolean outcome and exact str(count).

        Raises:
            ValueError: If the requested databank is absent from databank_counts.
        """
        if databank not in databank_counts:
            raise ValueError(f"Databank {databank} doesn't exist")

        count = databank_counts[databank]
        delta = ((count - number + (1 << 31)) % (1 << 32)) - (1 << 31)
        met = ConditionComparator.validate(float(delta), comparator)
        last_checked_value = str(count)

        logger.debug(
            "FR-task-conditions-results: bank=%r count=%d cmp=%r num=%d -> met=%s",
            databank,
            count,
            comparator,
            number,
            met,
        )
        return ConditionCheck(met=met, last_checked_value=last_checked_value)
