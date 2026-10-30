"""Data models for task manager project condition evaluation.

Description:
    Defines the ConditionCheck data model returned by all task manager condition
    evaluators.

Purpose:
    FEAT-TASK-CONDITIONS: Provide typed evaluation outcome contracts.

Key Capabilities:
    - FR-task-conditions-models: Slotted immutable model for condition check outcomes.

Python API Usage:
    ```python
    from app.workspace.task_manager.conditions.models import ConditionCheck

    outcome = ConditionCheck(met=True, last_checked_value="100")
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/conditions/ -q
    ```
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ConditionCheck"]


@dataclass(frozen=True, slots=True)
class ConditionCheck:
    """Immutable result of a project condition evaluation.

    Attributes:
        met: Whether the condition evaluates to True.
        last_checked_value: String representation of checked value for UI reporting.
    """

    met: bool
    last_checked_value: str
