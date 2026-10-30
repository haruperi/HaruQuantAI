"""Go to task settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Go to task"
    automation settings. Configures jump target task name and condition lists.

Purpose:
    FEAT-TASK-MANAGER: Support loop and conditional branching task configuration.

Key Capabilities:
    - FR-settings-go-to-task: Read and write GoToTask configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.go_to_task import (
        GoToTaskConfig,
        GoToTaskSettings,
    )

    config = GoToTaskSettings.load({"task": "BuildStrategies"})
    target = {}
    GoToTaskSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["GoToTaskConfig", "GoToTaskSettings"]


@dataclass(frozen=True, slots=True)
class GoToTaskConfig:
    """Immutable configuration for Go to task settings."""

    target_task: str = ""
    conditions: list[dict[str, Any]] = field(default_factory=list)


class GoToTaskSettings:
    """Serialization and deserialization helper for GoToTask configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: GoToTaskConfig | None = None,
    ) -> GoToTaskConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else GoToTaskConfig()

        base = current or GoToTaskConfig()
        task = str(
            payload.get("target_task")
            or payload.get("targetTask")
            or payload.get("task")
            or base.target_task
        )
        raw_conds = payload.get("conditions", base.conditions)
        conds: list[dict[str, Any]] = []
        if isinstance(raw_conds, Sequence) and not isinstance(raw_conds, (str, bytes)):
            conds.extend(dict(c) for c in raw_conds if isinstance(c, Mapping))
        else:
            conds = [dict(c) for c in base.conditions]

        return GoToTaskConfig(target_task=task, conditions=conds)

    @staticmethod
    def write(target: dict[str, Any], config: GoToTaskConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["task"] = config.target_task
        target["conditions"] = [dict(c) for c in config.conditions]

    @staticmethod
    def to_dict(config: GoToTaskConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
