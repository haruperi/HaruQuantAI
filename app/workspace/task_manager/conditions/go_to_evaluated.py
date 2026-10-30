"""GoTo evaluated cycles project condition evaluator.

Description:
    Evaluates GoTo evaluated cycles against a threshold using double-precision
    subtraction (without 32-bit wrapping) and the core ConditionComparator.

Purpose:
    FEAT-TASK-CONDITIONS: Evaluate GoTo task evaluated cycle conditions.

Key Capabilities:
    - FR-task-conditions-goto-evaluated: Compute double-precision delta and validate
      with shared ConditionComparator.

Python API Usage:
    ```python
    from app.workspace.task_manager.conditions.go_to_evaluated import (
        GoToEvaluatedCondition,
    )

    check = GoToEvaluatedCondition.evaluate(
        evaluated_cycles=99,
        comparator="<",
        number=100,
    )
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/conditions/ -q
    ```
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.trading.conditions import ConditionComparator
from app.workspace.task_manager.conditions.models import ConditionCheck

logger = get_logger(__name__)

__all__ = ["GoToEvaluatedCondition"]


class GoToEvaluatedCondition:
    """Evaluates GoTo task evaluated cycles count against configured thresholds."""

    @staticmethod
    def evaluate(
        evaluated_cycles: int,
        *,
        comparator: str = "<",
        number: int = 100,
    ) -> ConditionCheck:
        """Evaluate GoTo evaluated cycles condition.

        Args:
            evaluated_cycles: Evaluated cycle counter (nonnegative signed 32-bit int).
            comparator: Comparison operator string (e.g. '<', '>', '=', '>=', '<=').
            number: Target threshold integer.

        Returns:
            ConditionCheck containing boolean outcome and exact str(evaluated_cycles).
        """
        delta = float(evaluated_cycles) - float(number)
        met = ConditionComparator.validate(float(delta), comparator)
        last_checked_value = str(evaluated_cycles)

        logger.debug(
            "FR-task-conditions-goto-evaluated: cycles=%d cmp=%r num=%d -> met=%s",
            evaluated_cycles,
            comparator,
            number,
            met,
        )
        return ConditionCheck(met=met, last_checked_value=last_checked_value)
