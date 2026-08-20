"""Tests for notification manager capability injection and composition."""

# ruff: noqa: INP001
from pathlib import Path

from app.capabilities.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.utils.errors.exceptions import ConfigurationError
from app.utils.notifications.manager import (
    build_notification_manager_config,
    close_notification_manager,
    create_notification_manager,
    send_notification,
)
from tests.removability.harness import run_in_fresh_process


class _FakeDelivery(NotificationDeliveryCapabilityV1):
    """Controllable fake notification delivery adapter."""

    def __init__(
        self, channel: str, *, active: bool = True, fail: bool = False
    ) -> None:
        self._channel = channel
        self._active = active
        self._fail = fail
        self.closed = False

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def active(self) -> bool:
        return self._active and not self.closed

    def send(
        self,
        _title: str,
        _text: str,
        _html_body: str | None = None,
    ) -> NotificationDeliveryResultV1:
        if not self.active:
            raise ConfigurationError("NOTIFICATION_CHANNEL_UNAVAILABLE")
        if self._fail:
            raise RuntimeError(f"Delivery failed for {self._channel}")
        return NotificationDeliveryResultV1(
            channel=self._channel,
            status="accepted",
            recipient_count=1,
        )

    def close(self) -> None:
        self.closed = True


def test_manager_with_missing_channel() -> None:
    """Verify missing channel in injected deliveries reports unavailable without error."""
    config = build_notification_manager_config(
        enabled=True,
        default_channels=("desktop", "email"),
    )
    desktop_del = _FakeDelivery("desktop")
    manager = create_notification_manager(
        config,
        deliveries={"desktop": desktop_del},
    )

    result = send_notification(manager, "Alert", "Test message")
    assert result["status"] == "partial"
    res_list = list(result["results"])  # type: ignore[arg-type]
    desktop_res = next(r for r in res_list if r["channel"] == "desktop")
    email_res = next(r for r in res_list if r["channel"] == "email")
    assert desktop_res["status"] == "sent"
    assert email_res["status"] == "unavailable"


def test_manager_no_channel_fallback() -> None:
    """Verify failed channel does not substitute or fall back to another channel."""
    config = build_notification_manager_config(
        enabled=True,
        default_channels=("email",),
    )
    email_del = _FakeDelivery("email", fail=True)
    desktop_del = _FakeDelivery("desktop")
    manager = create_notification_manager(
        config,
        deliveries={"email": email_del, "desktop": desktop_del},
    )

    result = send_notification(manager, "Alert", "Test message")
    assert result["status"] == "error"
    res_list = list(result["results"])  # type: ignore[arg-type]
    assert len(res_list) == 1
    assert res_list[0]["channel"] == "email"
    assert res_list[0]["status"] == "failed"


def test_manager_close_cleans_up_all_injected_deliveries() -> None:
    """Verify closing the manager closes every injected delivery capability."""
    config = build_notification_manager_config(
        enabled=True,
        default_channels=("desktop", "email"),
    )
    desktop_del = _FakeDelivery("desktop")
    email_del = _FakeDelivery("email")
    manager = create_notification_manager(
        config,
        deliveries={"desktop": desktop_del, "email": email_del},
    )
    assert desktop_del.closed is False
    assert email_del.closed is False

    close_notification_manager(manager)
    assert desktop_del.closed is True
    assert email_del.closed is True


def test_absence_and_runtime_isolation() -> None:
    """Verify notifications manager can be loaded in fresh process without eager providers."""
    script = """
import sys
import app.utils.notifications.manager as mgr
assert mgr is not None
"""
    repo_root = Path(__file__).resolve().parents[3]
    res = run_in_fresh_process(repository_root=repo_root, script=script)
    assert res.returncode == 0, res.stderr
