"""File, journal, and email logging action blocks.

Description:
    Groups and re-exports logging and notification action building blocks.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-LOGGING-REEXPORT: Grouped export of logging action blocks.
Python API Usage:
    from app.extend.blocks.actions.logging import (
        LogToFile,
        LogToJournal,
        SendEmail,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

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
    "LogToFile",
    "LogToFileAction",
    "LogToJournal",
    "LogToJournalAction",
    "SendEmail",
    "SendEmailAction",
    "log_to_file",
    "log_to_journal",
    "send_email",
]
