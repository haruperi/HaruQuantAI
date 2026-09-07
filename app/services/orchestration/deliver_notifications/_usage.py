"""Bounded offline usage for governed notification delivery."""

import asyncio
import uuid

from app.contracts.notification.delivery.v1 import NotificationDeliveryResultV1
from app.contracts.orchestration.models import (
    NotificationChannelConfig,
    NotificationTemplate,
)
from app.services.orchestration.deliver_notifications._persistence import (
    NotificationStore,
)
from app.services.orchestration.deliver_notifications.deliver_notifications import (
    DeliverNotificationsService,
)


class _OfflineProvider:
    channel = "desktop"
    active = True

    def send(
        self, title: str, text: str, html_body: str | None = None
    ) -> NotificationDeliveryResultV1:
        del title, text, html_body
        return NotificationDeliveryResultV1(channel=self.channel, status="accepted")

    def close(self) -> None:
        return None


async def _run_usage_example() -> None:
    service = DeliverNotificationsService(
        NotificationStore(":memory:"), _OfflineProvider()
    )
    receipt = await service.deliver(
        delivery_id="demo-delivery",
        channel=NotificationChannelConfig(
            channel_id=str(uuid.uuid7()),
            kind="DESKTOP",
            is_enabled=True,
            rate_limit="10/minute",
        ),
        template=NotificationTemplate(
            template_id=str(uuid.uuid7()),
            version=1,
            message_kind="TEST",
            body_template="Job {job_id} completed",
            redaction_policy="standard",
        ),
        variables={"job_id": "demo-job"},
        master_enabled=True,
    )
    service.close()
    print(f"delivery_status={receipt.status}")


if __name__ == "__main__":
    asyncio.run(_run_usage_example())
