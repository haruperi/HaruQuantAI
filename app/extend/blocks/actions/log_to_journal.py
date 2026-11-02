"""Log to journal action block.

Description:
    Writes diagnostic and audit log messages to the platform journal or
    terminal log stream.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-LOG-TO-JOURNAL: Write log message to platform journal stream.
Python API Usage:
    from app.extend.blocks.actions.log_to_journal import (
        LogToJournal,
        log_to_journal,
    )
    rec = log_to_journal("System initialized")
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.actions.base import ActionRecord
from app.extend.blocks.base import BaseBlock
from app.extend.blocks.metadata import (
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
        logger.info("FR-ACTIONS-LOG-TO-JOURNAL: JOURNAL: %s", self.message)
        return ActionRecord(
            action_type="log_to_journal",
            params={"message": self.message},
        )


# Direct donor class alias matching SQ.Blocks.OtherActions.LogToJournal
LogToJournal = LogToJournalAction


def log_to_journal(message: str = "some message") -> ActionRecord:
    """Log a message to the journal / logger sink.

    Args:
        message: Log message text.

    Returns:
        ActionRecord describing journal log action.
    """
    action = LogToJournalAction(message=message)
    return action.execute()


__all__ = ["LogToJournal", "LogToJournalAction", "log_to_journal"]
