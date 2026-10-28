"""Centralized facade for action building blocks."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.include.actions.annotations import (
    draw_down_arrow,
    draw_up_arrow,
    draw_vertical_line,
)
from app.include.actions.assign_variable import assign_variable
from app.include.actions.base import ActionRecord
from app.include.actions.custom import custom_action
from app.include.actions.logging import (
    log_to_journal,
    send_email,
)
from app.include.blocks.actions.log_to_file import log_to_file
from app.include.types import Variable

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
            "FR-SERVICES-ACTIONS-FACADE: Actions.assign(var='%s')",
            variable.name,
        )
        return assign_variable(variable, value, is_boolean)

    @staticmethod
    def custom(
        command: str = "",
        handler: Callable[[str], Any] | None = None,
    ) -> ActionRecord:
        """Trigger a custom action.

        Args:
            command: Command string (default: "").
            handler: Optional callable.

        Returns:
            ActionRecord instance.
        """
        logger.debug(
            "FR-SERVICES-ACTIONS-FACADE: Actions.custom(cmd='%s')",
            command,
        )
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
            "FR-SERVICES-ACTIONS-FACADE: Actions.draw_down_arrow(shift=%d)",
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
        logger.debug(
            "FR-SERVICES-ACTIONS-FACADE: Actions.draw_up_arrow(shift=%d)",
            shift,
        )
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
            "FR-SERVICES-ACTIONS-FACADE: Actions.draw_vertical_line(shift=%d)",
            shift,
        )
        return draw_vertical_line(shift)

    @staticmethod
    def log_file(
        filename: str = "some_logfile.txt",
        message: str = "some message",
        base_dir: Path | str | None = None,
    ) -> ActionRecord:
        """Record file log entry.

        Args:
            filename: Target file name.
            message: Message text.
            base_dir: Optional destination base directory.

        Returns:
            ActionRecord instance.
        """
        logger.debug(
            "FR-SERVICES-ACTIONS-FACADE: Actions.log_file(file='%s')",
            filename,
        )
        return log_to_file(filename, message, base_dir)

    @staticmethod
    def log_journal(message: str = "some message") -> ActionRecord:
        """Record journal log entry.

        Args:
            message: Message text.

        Returns:
            ActionRecord instance.
        """
        logger.debug(
            "FR-SERVICES-ACTIONS-FACADE: Actions.log_journal()",
        )
        return log_to_journal(message)

    @staticmethod
    def send_email(
        subject: str = "Some subject",
        message: str = "some message",
        dispatcher: Callable[[str, str], bool] | None = None,
    ) -> ActionRecord:
        """Dispatch email notification.

        Args:
            subject: Email subject.
            message: Message text.
            dispatcher: Optional delivery callback.

        Returns:
            ActionRecord instance.
        """
        logger.debug(
            "FR-SERVICES-ACTIONS-FACADE: Actions.send_email(subj='%s')",
            subject,
        )
        return send_email(subject, message, dispatcher)


__all__ = ["Actions"]
