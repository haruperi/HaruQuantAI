"""Tests for notification delivery capability v1 contract."""

from pathlib import Path

import app.contracts.notification.delivery.v1 as delivery_mod
import pytest
from app.contracts.notification.delivery.v1 import (
    CAPABILITY_ID,
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)

from tests.removability.harness import run_in_fresh_process


class _FakeNotificationDelivery:
    """Fake conforming implementation for contract verification."""

    def __init__(self, channel: str = "mock_channel") -> None:
        self._channel = channel
        self._active = True
        self.sent_messages: list[tuple[str, str, str | None]] = []
        self.closed = False

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def active(self) -> bool:
        return self._active

    def send(
        self,
        title: str,
        text: str,
        html_body: str | None = None,
    ) -> NotificationDeliveryResultV1:
        if not self._active:
            msg = "Cannot send on inactive transport"
            raise RuntimeError(msg)
        self.sent_messages.append((title, text, html_body))
        return NotificationDeliveryResultV1(
            channel=self._channel,
            status="accepted",
            recipient_count=1,
        )

    def close(self) -> None:
        self._active = False
        self.closed = True


def test_capability_id_constant() -> None:
    """Verify exact capability ID constant."""
    assert CAPABILITY_ID == "notification.delivery.v1"


def test_exports_exact() -> None:
    """Verify exact public exports of the capability module."""
    expected = (
        "CAPABILITY_ID",
        "NotificationDeliveryCapabilityV1",
        "NotificationDeliveryResultV1",
    )
    assert delivery_mod.__all__ == expected


def test_delivery_result_frozen() -> None:
    """Verify NotificationDeliveryResultV1 is immutable and frozen."""
    result = NotificationDeliveryResultV1(
        channel="email",
        status="accepted",
        recipient_count=2,
    )
    assert result.channel == "email"
    assert result.status == "accepted"
    assert result.recipient_count == 2

    with pytest.raises(AttributeError):
        result.channel = "sms"  # type: ignore[misc]


def test_protocol_conformance_and_lifecycle() -> None:
    """Verify fake delivery implements Protocol and supports send/close lifecycle."""
    fake = _FakeNotificationDelivery("sms")
    assert isinstance(fake, NotificationDeliveryCapabilityV1)
    assert fake.channel == "sms"
    assert fake.active is True

    res = fake.send("Alert", "Market opened")
    assert res.channel == "sms"
    assert res.status == "accepted"
    assert res.recipient_count == 1
    assert len(fake.sent_messages) == 1

    fake.close()
    assert fake.active is False
    assert fake.closed is True

    with pytest.raises(RuntimeError, match="Cannot send on inactive transport"):
        fake.send("Alert", "Market closed")


def test_capability_module_import_isolation() -> None:
    """Verify importing capability module imports no provider implementations."""
    script = """
import sys
import app.contracts.notification.delivery.v1 as delivery_v1
assert delivery_v1 is not None
for mod_name in sys.modules:
    assert not mod_name.startswith('app.services'), f'Forbidden business domain imported: {mod_name}'
    assert not mod_name.startswith('app.agentic'), f'Forbidden agentic domain imported: {mod_name}'
    assert not (mod_name.startswith('app.') and 'providers' in mod_name), f'Forbidden provider imported: {mod_name}'
"""
    repo_root = Path(__file__).resolve().parents[3]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr
