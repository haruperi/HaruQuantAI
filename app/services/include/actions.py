"""Trading rule and annotation action blocks implementation.

Description:
    Provides side-effect and annotation action blocks for trading rule
    execution, backtesting, and live trading operations. Implements variable
    assignment with boolean formula coercion, chart drawing descriptors (down arrow,
    up arrow, vertical line), logging actions (journal and file sinks), and email
    notification dispatching.

Purpose:
    FEAT-SERVICES-ACTIONS: Action blocks for trading rule execution and annotations.

Key Capabilities:
    - FR-SERVICES-ACTION-ASSIGN: Assign variable with boolean coercion.
      Associated: `[AssignVariableAction.execute()]`, `[assign_variable()]`
      Logging: Emits debug log on variable assignment with variable name and value.
    - FR-SERVICES-ACTION-CUSTOM: Custom command action descriptor and handler.
      Associated: `[CustomAction.execute()]`, `[custom_action()]`
      Logging: Emits debug log on custom command execution.
    - FR-SERVICES-ACTION-DRAW: Chart drawing annotation descriptors.
      Associated: `[DrawDownArrowAction.execute()]`, `[DrawUpArrowAction.execute()]`,
        `[DrawVerticalLineAction.execute()]`, `[draw_down_arrow()]`,
        `[draw_up_arrow()]`, `[draw_vertical_line()]`
      Logging: Emits debug log on chart drawing action with bar shift.
    - FR-SERVICES-ACTION-LOG: Diagnostic journal and file logging operations.
      Associated: `[LogToFileAction.execute()]`, `[LogToJournalAction.execute()]`,
        `[log_to_file()]`, `[log_to_journal()]`
      Logging: Emits info log to journal and audit log on file write.
    - FR-SERVICES-ACTION-EMAIL: Email notification and alert dispatching.
      Associated: `[SendEmailAction.execute()]`, `[send_email()]`
      Logging: Emits info log on email notification dispatch.
    - FR-SERVICES-ACTIONS-FACADE: Centralized Actions facade for unified access.
      Associated: `[Actions]`
      Logging: Emits debug log routing through the unified facade.

Python API Usage:
    ```python
    from app.services.include.actions import Actions, assign_variable
    from app.services.include.types import Variable

    var = Variable[float]("take_profit", "float", 1.2500)
    Actions.assign(var, 1.2550)

    # Chart annotations
    record = Actions.draw_up_arrow(shift=1)

    # Logging & notifications
    Actions.log_journal("Order filled at 1.2550")
    Actions.send_email(subject="Trade Alert", message="Target reached")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/include/test_types_actions.py --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.services.include.types import Variable

logger = get_logger(__name__)

# Constants matching undefined order status
ORDER_NOT_DEFINED: float = -1.0

__all__ = [
    "ORDER_NOT_DEFINED",
    "ActionRecord",
    "Actions",
    "AssignVariableAction",
    "CustomAction",
    "DrawDownArrowAction",
    "DrawUpArrowAction",
    "DrawVerticalLineAction",
    "LogToFileAction",
    "LogToJournalAction",
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


@dataclass(frozen=True)
class ActionRecord:
    """Immutable audit record representing an executed action descriptor."""

    action_type: str
    params: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class AssignVariableAction:
    """Action block to assign a value or evaluated formula to a variable."""

    def __init__(
        self,
        variable: Variable[Any],
        value: Any,
        is_boolean: bool = False,
    ) -> None:
        """Initialize assign variable action.

        Args:
            variable: Target Variable state container.
            value: Value or callable returning a value.
            is_boolean: Whether to coerce value to boolean.
        """
        self.variable = variable
        self.value = value
        self.is_boolean = is_boolean

    def execute(self) -> ActionRecord:
        """Execute variable assignment."""
        resolved = (
            self.value()
            if callable(self.value)
            else (
                self.value.evaluate()
                if hasattr(self.value, "evaluate") and callable(self.value.evaluate)
                else self.value
            )
        )

        if self.is_boolean:
            # Truthiness: 0 or ORDER_NOT_DEFINED (-1) is False; otherwise True.
            if isinstance(resolved, (int, float)):
                final_val: Any = resolved not in (0.0, ORDER_NOT_DEFINED)
            else:
                final_val = bool(resolved)
        else:
            final_val = resolved

        self.variable.set_value(final_val)
        logger.debug(
            "FR-SERVICES-ACTION-ASSIGN: Assigned '%s' = %s (is_bool=%s)",
            self.variable.name,
            final_val,
            self.is_boolean,
        )
        return ActionRecord(
            action_type="assign_variable",
            params={
                "name": self.variable.name,
                "value": final_val,
                "is_boolean": self.is_boolean,
            },
        )


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


class DrawDownArrowAction:
    """Action block to record a down arrow chart annotation."""

    def __init__(self, shift: int = 0) -> None:
        """Initialize down arrow action.

        Args:
            shift: Relative bar shift (default: 0).
        """
        self.shift = shift

    def execute(self) -> ActionRecord:
        """Execute down arrow annotation action."""
        logger.debug(
            "FR-SERVICES-ACTION-DRAW: DrawDownArrow(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_down_arrow",
            params={"shift": self.shift},
        )


class DrawUpArrowAction:
    """Action block to record an up arrow chart annotation."""

    def __init__(self, shift: int = 0) -> None:
        """Initialize up arrow action.

        Args:
            shift: Relative bar shift (default: 0).
        """
        self.shift = shift

    def execute(self) -> ActionRecord:
        """Execute up arrow annotation action."""
        logger.debug(
            "FR-SERVICES-ACTION-DRAW: DrawUpArrow(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_up_arrow",
            params={"shift": self.shift},
        )


class DrawVerticalLineAction:
    """Action block to record a vertical line chart annotation."""

    def __init__(self, shift: int = 0) -> None:
        """Initialize vertical line action.

        Args:
            shift: Relative bar shift (default: 0).
        """
        self.shift = shift

    def execute(self) -> ActionRecord:
        """Execute vertical line annotation action."""
        logger.debug(
            "FR-SERVICES-ACTION-DRAW: DrawVerticalLine(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_vertical_line",
            params={"shift": self.shift},
        )


class LogToFileAction:
    """Action block to write messages to a file."""

    def __init__(
        self,
        filename: str = "some_logfile.txt",
        message: str = "some message",
        base_dir: Path | str | None = None,
    ) -> None:
        """Initialize file logging action.

        Args:
            filename: Destination file name.
            message: Message text to append.
            base_dir: Optional base directory to sandbox file output.
        """
        self.filename = filename
        self.message = message
        self.base_dir = Path(base_dir) if base_dir else None

    def execute(self) -> ActionRecord:
        """Execute file logging."""
        written_path: str | None = None
        if self.base_dir is not None:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            target = self.base_dir / self.filename
            with target.open("a", encoding="utf-8") as f:
                f.write(self.message + "\n")
            written_path = str(target)

        logger.debug(
            "FR-SERVICES-ACTION-LOG: LogToFile(file='%s', msg='%s')",
            self.filename,
            self.message,
        )
        return ActionRecord(
            action_type="log_to_file",
            params={
                "filename": self.filename,
                "message": self.message,
                "path": written_path,
            },
        )


class LogToJournalAction:
    """Action block to write messages to the system journal/terminal log."""

    def __init__(self, message: str = "some message") -> None:
        """Initialize journal logging action.

        Args:
            message: Log message text.
        """
        self.message = message

    def execute(self) -> ActionRecord:
        """Execute journal logging."""
        logger.info("FR-SERVICES-ACTION-LOG: JOURNAL: %s", self.message)
        return ActionRecord(
            action_type="log_to_journal",
            params={"message": self.message},
        )


class SendEmailAction:
    """Action block to send an email notification or alert."""

    def __init__(
        self,
        email_subject: str = "Some subject",
        message: str = "some message",
        dispatcher: Callable[[str, str], bool] | None = None,
    ) -> None:
        """Initialize send email action.

        Args:
            email_subject: Subject line for notification.
            message: Notification body content.
            dispatcher: Optional callback to deliver the email.
        """
        self.email_subject = email_subject
        self.message = message
        self.dispatcher = dispatcher

    def execute(self) -> ActionRecord:
        """Execute email notification."""
        logger.info(
            "FR-SERVICES-ACTION-EMAIL: EMAIL: [%s] %s",
            self.email_subject,
            self.message,
        )
        delivered = False
        if self.dispatcher is not None:
            delivered = self.dispatcher(self.email_subject, self.message)
        return ActionRecord(
            action_type="send_email",
            params={
                "email_subject": self.email_subject,
                "message": self.message,
                "delivered": delivered,
            },
        )


# ---------------------------------------------------------------------------
# Functional Action Helper Primitives
# ---------------------------------------------------------------------------


def assign_variable(
    variable: Variable[Any],
    value: Any,
    is_boolean: bool = False,
) -> ActionRecord:
    """Assign a value or formula result to a variable.

    Args:
        variable: Target variable container.
        value: New value or callable.
        is_boolean: Coerce to boolean (0 and -1 map to False).

    Returns:
        ActionRecord summarizing the operation.
    """
    action = AssignVariableAction(variable, value, is_boolean)
    return action.execute()


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


def draw_down_arrow(shift: int = 0) -> ActionRecord:
    """Record a down arrow annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing down arrow.
    """
    action = DrawDownArrowAction(shift)
    return action.execute()


def draw_up_arrow(shift: int = 0) -> ActionRecord:
    """Record an up arrow annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing up arrow.
    """
    action = DrawUpArrowAction(shift)
    return action.execute()


def draw_vertical_line(shift: int = 0) -> ActionRecord:
    """Record a vertical line annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing vertical line.
    """
    action = DrawVerticalLineAction(shift)
    return action.execute()


def log_to_file(
    filename: str = "some_logfile.txt",
    message: str = "some message",
    base_dir: Path | str | None = None,
) -> ActionRecord:
    """Append a log message to a file.

    Args:
        filename: Destination log file name.
        message: Message text to record.
        base_dir: Optional sandbox base directory.

    Returns:
        ActionRecord describing file log action.
    """
    action = LogToFileAction(filename, message, base_dir)
    return action.execute()


def log_to_journal(message: str = "some message") -> ActionRecord:
    """Log a message to the journal / logger sink.

    Args:
        message: Log message text.

    Returns:
        ActionRecord describing journal log action.
    """
    action = LogToJournalAction(message)
    return action.execute()


def send_email(
    email_subject: str = "Some subject",
    message: str = "some message",
    dispatcher: Callable[[str, str], bool] | None = None,
) -> ActionRecord:
    """Send or record an email notification action.

    Args:
        email_subject: Email subject line.
        message: Email body text.
        dispatcher: Optional delivery handler.

    Returns:
        ActionRecord describing email dispatch.
    """
    action = SendEmailAction(email_subject, message, dispatcher)
    return action.execute()


# ---------------------------------------------------------------------------
# Unified Actions Facade
# ---------------------------------------------------------------------------


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
