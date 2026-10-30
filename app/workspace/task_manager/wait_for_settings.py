"""Wait for settings serialization and parsing contracts.

Description:
    Provides serialization and deserialization helpers for task "Wait For"
    automation settings. Reads and writes configuration from and to JSON-compatible
    mappings and dictionaries without executing file waits or polling filesystems.

Purpose:
    FEAT-TASK-MANAGER: Support task automation and settings workflows.

Key Capabilities:
    - FR-task-manager-wait-for-settings: Read and write task WaitFor configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.wait_for_settings import (
        WaitForConfig,
        WaitForSettings,
    )

    config = WaitForSettings.load({"file": "data.csv", "action": "user"})
    target = {}
    WaitForSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_wait_for_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["WaitForConfig", "WaitForSettings"]


@dataclass(frozen=True, slots=True)
class WaitForConfig:
    """Immutable configuration for a task WaitFor setting.

    Attributes:
        file: Target file path or identifier to wait for.
        action: Action trigger identifier (default 'user').
    """

    file: str = ""
    action: str = "user"


class WaitForSettings:
    """Helper for reading and writing task WaitFor configuration dictionaries."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: WaitForConfig | None = None,
    ) -> WaitForConfig:
        """Load WaitFor configuration from a mapping, preserving identity if None.

        Args:
            payload: JSON mapping containing configuration fields, or None.
            current: Current WaitForConfig instance to preserve when payload is None.
                If omitted when payload is None, a default WaitForConfig is returned.

        Returns:
            The preserved current config if payload is None, or a new WaitForConfig
            loaded from payload.
        """
        if payload is None:
            if current is not None:
                return current
            return WaitForConfig()

        file_raw = payload.get("file")
        if file_raw is None:
            file_raw = payload.get("File")
        file_val = "" if file_raw is None or file_raw == "" else str(file_raw)

        action_raw = payload.get("action")
        if action_raw is None:
            action_raw = payload.get("Action")
        action_val = (
            "user" if action_raw is None or action_raw == "" else str(action_raw)
        )

        logger.debug(
            "FR-task-manager-wait-for-settings: loaded wait_for config "
            "file=%r action=%r",
            file_val,
            action_val,
        )
        return WaitForConfig(file=file_val, action=action_val)

    @staticmethod
    def write(target: dict[str, Any], config: WaitForConfig) -> None:
        """Write WaitFor configuration fields into a target dictionary.

        Args:
            target: Destination dictionary to update in-place. Unrelated keys
                and existing nested structures are preserved.
            config: WaitForConfig containing values to write.
        """
        target["file"] = config.file
        target["action"] = config.action
        logger.debug(
            "FR-task-manager-wait-for-settings: written wait_for config "
            "file=%r action=%r",
            config.file,
            config.action,
        )
