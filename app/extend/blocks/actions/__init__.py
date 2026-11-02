"""Trading rule and annotation action blocks package.

Description:
    Exports StrategyQuant-faithful action blocks, class aliases, functional
    helpers, and the unified Actions facade.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-EXPORTS: Public package exports for action blocks.
Python API Usage:
    from app.extend.blocks.actions import Actions, AssignVariable, SendEmail
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.actions.assign_variable import (
    AssignVariable,
    AssignVariableAction,
    assign_variable,
)
from app.extend.blocks.actions.base import (
    ORDER_NOT_DEFINED,
    ActionRecord,
)
from app.extend.blocks.actions.custom_action import (
    CustomAction,
    custom_action,
)
from app.extend.blocks.actions.draw_down_arrow import (
    DrawDownArrow,
    DrawDownArrowAction,
    draw_down_arrow,
)
from app.extend.blocks.actions.draw_up_arrow import (
    DrawUpArrow,
    DrawUpArrowAction,
    draw_up_arrow,
)
from app.extend.blocks.actions.draw_vertical_line import (
    DrawVerticalLine,
    DrawVerticalLineAction,
    draw_vertical_line,
)
from app.extend.blocks.actions.facade import Actions
from app.extend.blocks.actions.log_to_file import (
    LogToFile,
    LogToFileAction,
    log_to_file,
)
from app.extend.blocks.actions.log_to_journal import (
    LogToJournal,
    LogToJournalAction,
    log_to_journal,
)
from app.extend.blocks.actions.send_email import (
    SendEmail,
    SendEmailAction,
    send_email,
)

__all__ = [
    "ORDER_NOT_DEFINED",
    "ActionRecord",
    "Actions",
    "AssignVariable",
    "AssignVariableAction",
    "CustomAction",
    "DrawDownArrow",
    "DrawDownArrowAction",
    "DrawUpArrow",
    "DrawUpArrowAction",
    "DrawVerticalLine",
    "DrawVerticalLineAction",
    "LogToFile",
    "LogToFileAction",
    "LogToJournal",
    "LogToJournalAction",
    "SendEmail",
    "SendEmailAction",
    "assign_variable",
    "custom_action",
    "draw_down_arrow",
    "draw_up_arrow",
    "draw_vertical_line",
    "log_to_file",
    "log_to_journal",
    "send_email",
]
