"""Run cycles project condition evaluator.

Description:
    Evaluates project run cycles against a threshold using signed 32-bit delta wrapping
    and the core ConditionComparator.

Purpose:
    FEAT-TASK-CONDITIONS: Evaluate cycle count conditions.

Key Capabilities:
    - FR-task-conditions-cycles: Compute wrapped signed 32-bit cycle delta and validate
      with shared ConditionComparator.

Python API Usage:
    ```python
    from app.workspace.task_manager.conditions.cycles import RunCyclesCondition

    check = RunCyclesCondition.evaluate(run_cycles=99, comparator="<", number=100)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/conditions/test_cycles.py -q
    ```
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.trading.conditions import ConditionComparator
from app.workspace.task_manager.conditions.models import ConditionCheck

logger = get_logger(__name__)

__all__ = ["RunCyclesCondition"]


class RunCyclesCondition:
    """Evaluates project run cycle count against configured thresholds."""

    @staticmethod
    def evaluate(
        run_cycles: int,
        *,
        comparator: str = "<",
        number: int = 100,
    ) -> ConditionCheck:
        """Evaluate run cycles condition.

        Args:
            run_cycles: Project run cycle counter (nonnegative signed 32-bit int).
            comparator: Comparison operator string (e.g. '<', '>', '=', '>=', '<=').
            number: Target threshold integer.

        Returns:
            ConditionCheck containing boolean outcome and exact str(run_cycles).
        """
        delta = ((run_cycles - number + (1 << 31)) % (1 << 32)) - (1 << 31)
        met = ConditionComparator.validate(float(delta), comparator)
        last_checked_value = str(run_cycles)

        logger.debug(
            "FR-task-conditions-cycles: run_cycles=%d cmp=%r num=%d -> met=%s",
            run_cycles,
            comparator,
            number,
            met,
        )
        return ConditionCheck(met=met, last_checked_value=last_checked_value)
