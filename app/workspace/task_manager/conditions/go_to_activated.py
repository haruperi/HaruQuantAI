"""GoTo activated cycles project condition evaluator.

Description:
    Evaluates GoTo activated cycles against a threshold using double-precision
    subtraction (without 32-bit wrapping) and the core ConditionComparator.

Purpose:
    FEAT-TASK-CONDITIONS: Evaluate GoTo task activated cycle conditions.

Key Capabilities:
    - FR-task-conditions-goto-activated: Compute double-precision delta and validate
      with shared ConditionComparator.

Python API Usage:
    ```python
    from app.workspace.task_manager.conditions.go_to_activated import (
        GoToActivatedCondition,
    )

    check = GoToActivatedCondition.evaluate(
        activated_cycles=99,
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

__all__ = ["GoToActivatedCondition"]


class GoToActivatedCondition:
    """Evaluates GoTo task activated cycles count against configured thresholds."""

    @staticmethod
    def evaluate(
        activated_cycles: int,
        *,
        comparator: str = "<",
        number: int = 100,
    ) -> ConditionCheck:
        """Evaluate GoTo activated cycles condition.

        Args:
            activated_cycles: Activated cycle counter (nonnegative signed 32-bit int).
            comparator: Comparison operator string (e.g. '<', '>', '=', '>=', '<=').
            number: Target threshold integer.

        Returns:
            ConditionCheck containing boolean outcome and exact str(activated_cycles).
        """
        delta = float(activated_cycles) - float(number)
        met = ConditionComparator.validate(float(delta), comparator)
        last_checked_value = str(activated_cycles)

        logger.debug(
            "FR-task-conditions-goto-activated: cycles=%d cmp=%r num=%d -> met=%s",
            activated_cycles,
            comparator,
            number,
            met,
        )
        return ConditionCheck(met=met, last_checked_value=last_checked_value)
