"""File, journal, and email logging action blocks."""

from __future__ import annotations

from collections.abc import Callable

from app.host.logging import get_logger
from app.include.actions.base import ActionRecord

logger = get_logger(__name__)


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
    "LogToJournalAction",
    "SendEmailAction",
    "log_to_journal",
    "send_email",
]
