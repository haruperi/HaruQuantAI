"""Custom executable action block."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

from pydantic import Field

from app.core.host.logging import get_logger
from app.include.blocks.actions.base import ActionRecord
from app.include.blocks.base import BaseBlock
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)


class CustomAction(BaseBlock):
    """Action block carrying an arbitrary custom command string."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="action.custom",
        version="1.0.0",
        name="Custom Action",
        description="Executes custom command string with optional handler",
        category="actions",
        tags=("action", "custom", "command"),
        execution_kind=ExecutionKind.ACTION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "command",
                PortType.STRING,
                "Custom command string",
                default="",
            ),
            InputPort(
                "handler",
                PortType.ANY,
                "Optional callable handler",
                default=None,
            ),
        ),
        outputs=(OutputPort("record", PortType.ANY, "Execution ActionRecord"),),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )

    command: str = Field(
        default="",
        title="Command",
        description="Command string",
    )
    handler: Any = Field(
        default=None,
        title="Handler",
        description="Optional callable handler to process the command",
    )

    def execute(self) -> ActionRecord:
        """Execute custom action and invoke handler if provided."""
        logger.debug(
            "FR-SERVICES-ACTION-CUSTOM: Executing custom action command '%s'",
            self.command,
        )
        result = None
        if self.handler is not None and callable(self.handler):
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
    action = CustomAction(command=command, handler=handler)
    return action.execute()


__all__ = ["CustomAction", "custom_action"]
