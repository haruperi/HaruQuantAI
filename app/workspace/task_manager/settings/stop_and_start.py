"""Stop and start settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Stop & Start"
    automation settings. Configures target project or service, action (stop,
    start, restart), and condition branching.

Purpose:
    FEAT-TASK-MANAGER: Support project stop and start automation task settings.

Key Capabilities:
    - FR-settings-stop-and-start: Read and write StopAndStart configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.stop_and_start import (
        StopAndStartConfig,
        StopAndStartSettings,
    )

    config = StopAndStartSettings.load({"action": "restart"})
    target = {}
    StopAndStartSettings.write(target, config)
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

__all__ = ["StopAndStartConfig", "StopAndStartSettings"]


@dataclass(frozen=True, slots=True)
class StopAndStartConfig:
    """Immutable configuration for Stop and Start task."""

    action: str = "stop"
    target_project: str = ""
    conditions: list[dict[str, Any]] = field(default_factory=list)


class StopAndStartSettings:
    """Serialization and deserialization helper for StopAndStart configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: StopAndStartConfig | None = None,
    ) -> StopAndStartConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else StopAndStartConfig()

        base = current or StopAndStartConfig()
        act = str(payload.get("action") or base.action)
        tgt = str(
            payload.get("target_project")
            or payload.get("targetProject")
            or payload.get("project")
            or base.target_project
        )
        raw_conds = payload.get("conditions", base.conditions)
        conds: list[dict[str, Any]] = []
        if isinstance(raw_conds, Sequence) and not isinstance(raw_conds, (str, bytes)):
            conds.extend(dict(c) for c in raw_conds if isinstance(c, Mapping))
        else:
            conds = [dict(c) for c in base.conditions]

        return StopAndStartConfig(
            action=act,
            target_project=tgt,
            conditions=conds,
        )

    @staticmethod
    def write(target: dict[str, Any], config: StopAndStartConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["action"] = config.action
        target["targetProject"] = config.target_project
        target["conditions"] = [dict(c) for c in config.conditions]

    @staticmethod
    def to_dict(config: StopAndStartConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
