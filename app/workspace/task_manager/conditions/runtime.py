"""Project runtime duration condition evaluator.

Description:
    Evaluates elapsed project running time (in milliseconds) against a minute threshold
    using signed 64-bit delta wrapping, core time formatting, and ConditionComparator.

Purpose:
    FEAT-TASK-CONDITIONS: Evaluate project running time duration conditions.

Key Capabilities:
    - FR-task-conditions-runtime: Compute wrapped signed 64-bit duration delta and
      format elapsed seconds using canonical time formatter.

Python API Usage:
    ```python
    from app.workspace.task_manager.conditions.runtime import RuntimeCondition

    check = RuntimeCondition.evaluate(running_ms=7199999, comparator="<", minutes=120)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/conditions/test_runtime.py -q
    ```
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.lib.time import format_duration_seconds
from app.core.trading.conditions import ConditionComparator
from app.workspace.task_manager.conditions.models import ConditionCheck

logger = get_logger(__name__)

__all__ = ["RuntimeCondition"]


class RuntimeCondition:
    """Evaluates project elapsed running time against configured minute thresholds."""

    @staticmethod
    def evaluate(
        running_ms: int,
        *,
        comparator: str = "<",
        minutes: int = 120,
    ) -> ConditionCheck:
        """Evaluate running time condition.

        Args:
            running_ms: Elapsed project milliseconds (nonnegative signed 64-bit int).
            comparator: Comparison operator string (e.g. '<', '>', '=', '>=', '<=').
            minutes: Target duration threshold in minutes (default 120).

        Returns:
            ConditionCheck containing boolean outcome and formatted duration string.
        """
        threshold_ms = minutes * 60000
        delta = ((running_ms - threshold_ms + (1 << 63)) % (1 << 64)) - (1 << 63)
        met = ConditionComparator.validate(float(delta), comparator)
        last_checked_value = format_duration_seconds(running_ms // 1000)

        logger.debug(
            "FR-task-conditions-runtime: ms=%d (%s) cmp=%r min=%d -> met=%s",
            running_ms,
            last_checked_value,
            comparator,
            minutes,
            met,
        )
        return ConditionCheck(met=met, last_checked_value=last_checked_value)
