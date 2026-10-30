"""Notification settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Notification"
    automation settings. Configures delivery channel, recipient endpoint, and
    message templating.

Purpose:
    FEAT-TASK-MANAGER: Support notification task configuration workflows.

Key Capabilities:
    - FR-settings-notification: Read and write Notification configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.notification import (
        NotificationConfig,
        NotificationSettings,
    )

    config = NotificationSettings.load(
        {"channel": "email", "recipient": "user@example.com"}
    )
    target = {}
    NotificationSettings.write(target, config)
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

__all__ = ["NotificationConfig", "NotificationSettings"]


@dataclass(frozen=True, slots=True)
class NotificationConfig:
    """Immutable configuration for Notification task."""

    channel: str = "email"
    recipient: str = ""
    subject: str = "Task Manager Notification"
    message_template: str = "Project {projectName} finished task {taskName}."


class NotificationSettings:
    """Serialization and deserialization helper for Notification configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: NotificationConfig | None = None,
    ) -> NotificationConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else NotificationConfig()

        base = current or NotificationConfig()
        chan = str(payload.get("channel") or base.channel)
        recip = str(payload.get("recipient") or base.recipient)
        subj = str(payload.get("subject") or base.subject)
        tmpl = str(
            payload.get("message_template")
            or payload.get("messageTemplate")
            or payload.get("message")
            or base.message_template
        )

        return NotificationConfig(
            channel=chan,
            recipient=recip,
            subject=subj,
            message_template=tmpl,
        )

    @staticmethod
    def write(target: dict[str, Any], config: NotificationConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["channel"] = config.channel
        target["recipient"] = config.recipient
        target["subject"] = config.subject
        target["messageTemplate"] = config.message_template

    @staticmethod
    def to_dict(config: NotificationConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
