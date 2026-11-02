"""Unified Actions facade for trading rule and annotation action blocks.

Description:
    Provides an object-oriented and namespace-bound API facade over discrete
    StrategyQuant-faithful action building blocks.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-FACADE: Centralized namespace for strategy action execution.
Python API Usage:
    from app.extend.blocks.actions import Actions
    Actions.send_email("Subject", "Body")
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.actions.assign_variable import assign_variable
from app.extend.blocks.actions.base import ActionRecord
from app.extend.blocks.actions.custom_action import custom_action
from app.extend.blocks.actions.draw_down_arrow import draw_down_arrow
from app.extend.blocks.actions.draw_up_arrow import draw_up_arrow
from app.extend.blocks.actions.draw_vertical_line import draw_vertical_line
from app.extend.blocks.actions.log_to_file import log_to_file
from app.extend.blocks.actions.log_to_journal import log_to_journal
from app.extend.blocks.actions.send_email import send_email
from app.extend.blocks.types import Variable

logger = get_logger(__name__)


class Actions:
    """Centralized facade for action building blocks."""

    @staticmethod
    def assign(
        variable: Variable[Any],
        value: Any,
        is_boolean: bool = False,
    ) -> ActionRecord:
        """Assign variable value.

        Args:
            variable: Target variable container.
            value: Value or callable.
            is_boolean: Boolean coercion flag.

        Returns:
            ActionRecord instance.
        """
        logger.debug(
            "FR-ACTIONS-FACADE: Actions.assign(var='%s')",
            variable.name,
        )
        return assign_variable(variable, value, is_boolean)

    @staticmethod
    def custom(
        command: str = "",
        handler: Callable[[str], Any] | None = None,
    ) -> ActionRecord:
        """Execute custom action command.

        Args:
            command: Command string.
            handler: Optional command handler.

        Returns:
            ActionRecord instance.
        """
        logger.debug("FR-ACTIONS-FACADE: Actions.custom(cmd='%s')", command)
        return custom_action(command, handler)

    @staticmethod
    def draw_down_arrow(shift: int = 0) -> ActionRecord:
        """Record down arrow annotation.

        Args:
            shift: Relative bar shift.

        Returns:
            ActionRecord instance.
        """
        logger.debug(
            "FR-ACTIONS-FACADE: Actions.draw_down_arrow(shift=%d)",
            shift,
        )
        return draw_down_arrow(shift)

    @staticmethod
    def draw_up_arrow(shift: int = 0) -> ActionRecord:
        """Record up arrow annotation.

        Args:
            shift: Relative bar shift.

        Returns:
            ActionRecord instance.
        """
        logger.debug("FR-ACTIONS-FACADE: Actions.draw_up_arrow(shift=%d)", shift)
        return draw_up_arrow(shift)

    @staticmethod
    def draw_vertical_line(shift: int = 0) -> ActionRecord:
        """Record vertical line annotation.

        Args:
            shift: Relative bar shift.

        Returns:
            ActionRecord instance.
        """
        logger.debug(
            "FR-ACTIONS-FACADE: Actions.draw_vertical_line(shift=%d)",
            shift,
        )
        return draw_vertical_line(shift)

    @staticmethod
    def log_file(
        filename: str = "strategy.log",
        message: str = "",
        base_dir: Path | str | None = None,
    ) -> ActionRecord:
        """Log message to designated file.

        Args:
            filename: Destination file name.
            message: Message text.
            base_dir: Optional sandbox base directory.

        Returns:
            ActionRecord instance.
        """
        logger.debug("FR-ACTIONS-FACADE: Actions.log_file(file='%s')", filename)
        return log_to_file(filename, message, base_dir)

    @staticmethod
    def log_journal(message: str = "some message") -> ActionRecord:
        """Log message to system journal.

        Args:
            message: Log message text.

        Returns:
            ActionRecord instance.
        """
        logger.debug("FR-ACTIONS-FACADE: Actions.log_journal(msg='%s')", message)
        return log_to_journal(message)

    @staticmethod
    def send_email(
        subject: str = "Some subject",
        message: str = "some message",
        dispatcher: Callable[[str, str], bool] | None = None,
    ) -> ActionRecord:
        """Send email alert notification.

        Args:
            subject: Notification subject.
            message: Message content.
            dispatcher: Optional email dispatcher.

        Returns:
            ActionRecord instance.
        """
        logger.debug("FR-ACTIONS-FACADE: Actions.send_email(subj='%s')", subject)
        return send_email(subject, message, dispatcher)


__all__ = ["Actions"]
