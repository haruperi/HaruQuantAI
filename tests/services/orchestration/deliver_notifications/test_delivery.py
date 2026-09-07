"""Focused tests for governed notification delivery."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid7

import pytest
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


class _Provider:
    channel = "desktop"
    active = True

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.messages: list[str] = []

    def send(
        self, title: str, text: str, html_body: str | None = None
    ) -> NotificationDeliveryResultV1:
        del title, html_body
        self.messages.append(text)
        if self.fail:
            raise RuntimeError("secret provider detail")
        return NotificationDeliveryResultV1(channel=self.channel, status="accepted")

    def close(self) -> None:
        return None


def _channel(rate_limit: str = "1/minute") -> NotificationChannelConfig:
    return NotificationChannelConfig(
        channel_id=str(uuid7()),
        kind="DESKTOP",
        is_enabled=True,
        rate_limit=rate_limit,
    )


def _template() -> NotificationTemplate:
    return NotificationTemplate(
        template_id=str(uuid7()),
        version=1,
        message_kind="TEST",
        body_template="Completed {name}; token={token}",
        redaction_policy="standard",
    )


@pytest.mark.asyncio
async def test_delivery_is_redacted_durable_and_idempotent() -> None:
    provider = _Provider()
    service = DeliverNotificationsService(
        NotificationStore(":memory:"),
        provider,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )
    channel = _channel()
    template = _template()
    first = await service.deliver(
        delivery_id="delivery-1",
        channel=channel,
        template=template,
        variables={"name": "run", "token": "secret-value"},
        master_enabled=True,
    )
    replay = await service.deliver(
        delivery_id="delivery-1",
        channel=channel,
        template=template,
        variables={"name": "run", "token": "secret-value"},
        master_enabled=True,
    )
    assert first.status == "DELIVERED"
    assert replay == first
    assert len(provider.messages) == 1
    assert "secret-value" not in provider.messages[0]
    service.close()


@pytest.mark.asyncio
async def test_policy_rate_limit_and_uncertain_failure_are_explicit() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    channel = _channel()
    template = _template()
    disabled = DeliverNotificationsService(NotificationStore(":memory:"), _Provider())
    receipt = await disabled.deliver(
        delivery_id="disabled",
        channel=channel,
        template=template,
        variables={"name": "run", "token": "safe"},
    )
    assert receipt.status == "DISABLED"
    disabled.close()

    provider = _Provider(fail=True)
    service = DeliverNotificationsService(
        NotificationStore(":memory:"), provider, clock=lambda: now
    )
    uncertain = await service.deliver(
        delivery_id="uncertain",
        channel=channel,
        template=template,
        variables={"name": "run", "token": "safe"},
        master_enabled=True,
    )
    limited = await service.deliver(
        delivery_id="limited",
        channel=channel,
        template=template,
        variables={"name": "other", "token": "safe"},
        master_enabled=True,
    )
    assert uncertain.status == "UNKNOWN"
    assert uncertain.error == "DELIVERY_OUTCOME_UNKNOWN"
    assert limited.status == "SUPPRESSED_RATE_LIMIT"
    service.close()


@pytest.mark.asyncio
async def test_restart_replays_receipt_without_resending(tmp_path: Path) -> None:
    database_path = str(tmp_path / "notifications.sqlite3")
    channel = _channel()
    template = _template()
    first_provider = _Provider()
    first_service = DeliverNotificationsService(
        NotificationStore(database_path), first_provider
    )
    first = await first_service.deliver(
        delivery_id="durable-delivery",
        channel=channel,
        template=template,
        variables={"name": "run", "token": "safe"},
        master_enabled=True,
    )
    first_service.close()

    restarted_provider = _Provider()
    restarted = DeliverNotificationsService(
        NotificationStore(database_path), restarted_provider
    )
    replay = await restarted.deliver(
        delivery_id="durable-delivery",
        channel=channel,
        template=template,
        variables={"name": "run", "token": "safe"},
        master_enabled=True,
    )
    assert replay == first
    assert restarted_provider.messages == []
    restarted.close()
