"""Log to journal action block."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from app.host.logging import get_logger
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


class LogToJournalAction(BaseBlock):
    """Action block to write messages to the system journal/terminal log."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="action.log_to_journal",
        version="1.0.0",
        name="Log To Journal",
        description="Writes log message to system journal / terminal log",
        category="actions",
        tags=("action", "log", "journal"),
        execution_kind=ExecutionKind.ACTION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "message",
                PortType.STRING,
                "Log message text",
                default="some message",
            ),
        ),
        outputs=(OutputPort("record", PortType.ANY, "Execution ActionRecord"),),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )

    message: str = Field(
        default="some message",
        title="Message",
        description="Log message text",
    )

    def execute(self) -> ActionRecord:
        """Execute journal logging."""
        logger.info("FR-SERVICES-ACTION-LOG: JOURNAL: %s", self.message)
        return ActionRecord(
            action_type="log_to_journal",
            params={"message": self.message},
        )


def log_to_journal(message: str = "some message") -> ActionRecord:
    """Log a message to the journal / logger sink.

    Args:
        message: Log message text.

    Returns:
        ActionRecord describing journal log action.
    """
    action = LogToJournalAction(message=message)
    return action.execute()


__all__ = ["LogToJournalAction", "log_to_journal"]
