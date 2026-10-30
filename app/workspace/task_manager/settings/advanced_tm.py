"""Advanced task manager settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for advanced Task Manager
    project settings (e.g. exit conditions, max runtime, error tolerance, and
    completion actions). Reads and writes configuration from and to JSON-compatible
    mappings.

Purpose:
    FEAT-TASK-MANAGER: Support advanced task automation and project configuration.

Key Capabilities:
    - FR-settings-advanced-tm: Read and write advanced project configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.advanced_tm import (
        AdvancedTMConfig,
        AdvancedTMSettings,
    )

    config = AdvancedTMSettings.load({"maxRuntimeMinutes": 120})
    target = {}
    AdvancedTMSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["AdvancedTMConfig", "AdvancedTMSettings"]


@dataclass(frozen=True, slots=True)
class AdvancedTMConfig:
    """Immutable configuration for advanced Task Manager project settings."""

    max_runtime_minutes: int = 0
    stop_on_error: bool = False
    max_consecutive_errors: int = 3
    email_on_completion: bool = False
    notification_email: str = ""
    exit_on_condition: bool = False


class AdvancedTMSettings:
    """Serialization and deserialization helper for AdvancedTM configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: AdvancedTMConfig | None = None,
    ) -> AdvancedTMConfig:
        """Load configuration from a payload dictionary or mapping."""
        if payload is None:
            return current if current is not None else AdvancedTMConfig()

        base = current or AdvancedTMConfig()
        max_runtime = int(
            payload.get("max_runtime_minutes")
            or payload.get("maxRuntimeMinutes")
            or base.max_runtime_minutes
        )
        stop_on_err = bool(
            payload.get("stop_on_error")
            if "stop_on_error" in payload
            else payload.get("stopOnError", base.stop_on_error)
        )
        max_errors = int(
            payload.get("max_consecutive_errors")
            or payload.get("maxConsecutiveErrors")
            or base.max_consecutive_errors
        )
        email_on_comp = bool(
            payload.get("email_on_completion")
            if "email_on_completion" in payload
            else payload.get("emailOnCompletion", base.email_on_completion)
        )
        notification_email = str(
            payload.get("notification_email")
            or payload.get("notificationEmail")
            or base.notification_email
        )
        exit_on_cond = bool(
            payload.get("exit_on_condition")
            if "exit_on_condition" in payload
            else payload.get("exitOnCondition", base.exit_on_condition)
        )

        return AdvancedTMConfig(
            max_runtime_minutes=max_runtime,
            stop_on_error=stop_on_err,
            max_consecutive_errors=max_errors,
            email_on_completion=email_on_comp,
            notification_email=notification_email,
            exit_on_condition=exit_on_cond,
        )

    @staticmethod
    def write(target: dict[str, Any], config: AdvancedTMConfig) -> None:
        """Write configuration to a target dictionary, preserving other keys."""
        target["maxRuntimeMinutes"] = config.max_runtime_minutes
        target["stopOnError"] = config.stop_on_error
        target["maxConsecutiveErrors"] = config.max_consecutive_errors
        target["emailOnCompletion"] = config.email_on_completion
        target["notificationEmail"] = config.notification_email
        target["exitOnCondition"] = config.exit_on_condition

    @staticmethod
    def to_dict(config: AdvancedTMConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
