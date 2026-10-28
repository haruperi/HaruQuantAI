"""File, journal, and email logging action blocks."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.host.logging import get_logger
from app.include.actions.base import ActionRecord

logger = get_logger(__name__)


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


__all__ = [
    "LogToFileAction",
    "LogToJournalAction",
    "SendEmailAction",
    "log_to_file",
    "log_to_journal",
    "send_email",
]
