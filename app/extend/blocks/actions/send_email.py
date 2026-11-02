"""Send email notification action block.

Description:
    Dispatches or records email notification alerts with subject line and body
    content using an optional dispatcher callback.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-SEND-EMAIL: Dispatch email alert notification.
Python API Usage:
    from app.extend.blocks.actions.send_email import (
        SendEmail,
        send_email,
    )
    rec = send_email("Alert", "Margin threshold reached")
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar

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


class SendEmailAction(BaseBlock):
    """Action block to send an email notification or alert."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="action.send_email",
        version="1.0.0",
        name="Send Email",
        description="Sends email notification or alert",
        category="actions",
        tags=("action", "email", "alert"),
        execution_kind=ExecutionKind.ACTION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "email_subject",
                PortType.STRING,
                "Subject line",
                default="Some subject",
            ),
            InputPort(
                "message",
                PortType.STRING,
                "Message text",
                default="some message",
            ),
            InputPort(
                "dispatcher",
                PortType.ANY,
                "Optional delivery handler",
                default=None,
            ),
        ),
        outputs=(OutputPort("record", PortType.ANY, "Execution ActionRecord"),),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )

    email_subject: str = Field(
        default="Some subject",
        title="Email Subject",
        description="Subject line for notification",
    )
    message: str = Field(
        default="some message",
        title="Message",
        description="Notification body content",
    )
    dispatcher: Any = Field(
        default=None,
        title="Dispatcher",
        description="Optional callback to deliver the email",
    )

    def execute(self) -> ActionRecord:
        """Execute email notification."""
        logger.info(
            "FR-ACTIONS-SEND-EMAIL: EMAIL: [%s] %s",
            self.email_subject,
            self.message,
        )
        delivered = False
        if self.dispatcher is not None and callable(self.dispatcher):
            delivered = self.dispatcher(self.email_subject, self.message)
        return ActionRecord(
            action_type="send_email",
            params={
                "email_subject": self.email_subject,
                "message": self.message,
                "delivered": delivered,
            },
        )


# Direct donor class alias matching SQ.Blocks.OtherActions.SendEmail
SendEmail = SendEmailAction


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
    action = SendEmailAction(
        email_subject=email_subject,
        message=message,
        dispatcher=dispatcher,
    )
    return action.execute()


__all__ = ["SendEmail", "SendEmailAction", "send_email"]
