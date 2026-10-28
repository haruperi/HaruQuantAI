"""Custom executable action blocks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.host.logging import get_logger
from app.include.actions.base import ActionRecord

logger = get_logger(__name__)


class CustomAction:
    """Action block carrying an arbitrary custom command string."""

    def __init__(
        self,
        command: str = "",
        handler: Callable[[str], Any] | None = None,
    ) -> None:
        """Initialize custom action.

        Args:
            command: Command string (e.g. MQL command or script name).
            handler: Optional callable handler to process the command.
        """
        self.command = command
        self.handler = handler

    def execute(self) -> ActionRecord:
        """Execute custom action and invoke handler if provided."""
        logger.debug(
            "FR-SERVICES-ACTION-CUSTOM: Executing custom action command '%s'",
            self.command,
        )
        result = None
        if self.handler is not None:
            result = self.handler(self.command)
        return ActionRecord(
            action_type="custom_action",
            params={"command": self.command, "result": result},
        )


def custom_action(
    command: str = "",
    handler: Callable[[str], Any] | None = None,
) -> ActionRecord:
    """Execute a custom action command.

    Args:
        command: Command string (default: "").
        handler: Optional callable handler.

    Returns:
        ActionRecord with command details.
    """
    action = CustomAction(command, handler)
    return action.execute()


__all__ = ["CustomAction", "custom_action"]
