"""Cross-pilot effectful replacement and lifecycle verification tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from app.contracts.data.tick_stream.v1 import (
    TickStreamRequestV1,
)
from app.contracts.notification.delivery.v1 import (
    NotificationDeliveryCapabilityV1,
    NotificationDeliveryResultV1,
)
from app.kernel.effects import EffectScope
from app.services.data.market_events.fake_tick_stream.plugin import (
    create_provider as create_fake_tick_stream,
)
from app.utils.errors.exceptions import ConfigurationError
from app.utils.notifications.manager import (
    build_notification_manager_config,
    close_notification_manager,
    create_notification_manager,
    send_notification,
)


@dataclass
class ResourceTracker:
    """Explicit counter ledger tracking active asynchronous and synchronous resources."""

    tasks: int = 0
    listeners: int = 0
    timers: int = 0
    clients: int = 0
    subscriptions: int = 0
    buffers: int = 0

    def assert_zero(self) -> None:
        """Assert all tracked resource counters are strictly zero."""
        assert self.tasks == 0, f"Leaked tasks: {self.tasks}"
        assert self.listeners == 0, f"Leaked listeners: {self.listeners}"
        assert self.timers == 0, f"Leaked timers: {self.timers}"
        assert self.clients == 0, f"Leaked clients: {self.clients}"
        assert self.subscriptions == 0, f"Leaked subscriptions: {self.subscriptions}"
        assert self.buffers == 0, f"Leaked buffers: {self.buffers}"


class _TrackedDeliveryAdapter(NotificationDeliveryCapabilityV1):
    """Notification delivery adapter that increments/decrements tracker counters."""

    def __init__(self, channel: str, tracker: ResourceTracker) -> None:
        self._channel = channel
        self._tracker = tracker
        self._active = True
        self._tracker.clients += 1

    @property
    def channel(self) -> str:
        return self._channel

    @property
    def active(self) -> bool:
        return self._active

    def send(
        self,
        _title: str,
        _text: str,
        _html_body: str | None = None,
    ) -> NotificationDeliveryResultV1:
        if not self._active:
            raise ConfigurationError("NOTIFICATION_CHANNEL_UNAVAILABLE")
        return NotificationDeliveryResultV1(
            channel=self._channel,
            status="accepted",
            recipient_count=1,
        )

    def close(self) -> None:
        if self._active:
            self._active = False
            self._tracker.clients -= 1


def test_notification_absence_and_no_fallback() -> None:
    """Verify notification delivery absence produces unavailable status with zero fallback."""
    tracker = ResourceTracker()
    tracker.assert_zero()

    desktop_del = _TrackedDeliveryAdapter("desktop", tracker)
    assert tracker.clients == 1

    config = build_notification_manager_config(
        enabled=True,
        default_channels=("desktop", "email"),
    )
    manager = create_notification_manager(
        config,
        deliveries={"desktop": desktop_del},
    )

    result = send_notification(manager, "Notice", "System notification")
    assert result["status"] == "partial"
    res_list = list(result["results"])  # type: ignore[arg-type]
    assert any(r["channel"] == "desktop" and r["status"] == "sent" for r in res_list)
    assert any(
        r["channel"] == "email" and r["status"] == "unavailable" for r in res_list
    )

    close_notification_manager(manager)
    tracker.assert_zero()


def test_notification_replacement_lifecycle() -> None:
    """Verify notification delivery replacement shuts down old generation cleanly."""
    tracker = ResourceTracker()
    tracker.assert_zero()

    # Generation 1
    email_gen1 = _TrackedDeliveryAdapter("email", tracker)
    assert tracker.clients == 1
    config = build_notification_manager_config(
        enabled=True,
        default_channels=("email",),
    )
    manager1 = create_notification_manager(
        config,
        deliveries={"email": email_gen1},
    )
    res1 = send_notification(manager1, "Gen1", "Message from gen1")
    assert res1["status"] == "success"

    # Replacement to Generation 2
    close_notification_manager(manager1)
    tracker.assert_zero()

    email_gen2 = _TrackedDeliveryAdapter("email", tracker)
    assert tracker.clients == 1
    manager2 = create_notification_manager(
        config,
        deliveries={"email": email_gen2},
    )
    res2 = send_notification(manager2, "Gen2", "Message from gen2")
    assert res2["status"] == "success"

    close_notification_manager(manager2)
    tracker.assert_zero()


@pytest.mark.anyio
async def test_stream_upstream_loss_and_replacement() -> None:
    """Verify stream handles drain/replacement with unique event identities and zero leak."""
    tracker = ResourceTracker()
    tracker.assert_zero()

    scope1 = EffectScope()
    stream1 = create_fake_tick_stream(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 3},
        scope=scope1,
    )
    tracker.buffers += 1

    req = TickStreamRequestV1(symbol="EURUSD", buffer_size=3)
    await stream1.start(req)
    tracker.tasks += 1
    tracker.subscriptions += 1

    gen1_id = stream1.generation_id
    assert gen1_id is not None

    events_gen1: list[tuple[str, int]] = []
    async for ev in stream1.events():
        events_gen1.append((gen1_id, ev.sequence))

    assert len(events_gen1) == 3

    await stream1.stop()
    tracker.tasks -= 1
    tracker.subscriptions -= 1
    scope1.close()
    tracker.buffers -= 1
    tracker.assert_zero()

    # Replacement Generation 2
    scope2 = EffectScope()
    stream2 = create_fake_tick_stream(
        dependencies={},
        config={"symbol": "EURUSD", "buffer_size": 3},
        scope=scope2,
    )
    tracker.buffers += 1

    await stream2.start(req)
    tracker.tasks += 1
    tracker.subscriptions += 1

    gen2_id = stream2.generation_id
    assert gen2_id is not None
    assert gen2_id != gen1_id

    events_gen2: list[tuple[str, int]] = []
    async for ev in stream2.events():
        events_gen2.append((gen2_id, ev.sequence))

    assert len(events_gen2) == 3

    await stream2.stop()
    tracker.tasks -= 1
    tracker.subscriptions -= 1
    scope2.close()
    tracker.buffers -= 1
    tracker.assert_zero()

    # Assert uniqueness of (generation_id, sequence) across generations
    all_identities = set(events_gen1 + events_gen2)
    assert len(all_identities) == 6


@pytest.mark.anyio
async def test_partial_startup_all_zero_resources() -> None:
    """Verify partial startup failures leave all resource counters strictly zero."""
    tracker = ResourceTracker()
    tracker.assert_zero()

    scope = EffectScope()
    with pytest.raises(
        ValueError,
        match="fake tick stream config must be symbol EURUSD and buffer_size 3",
    ):
        create_fake_tick_stream(
            dependencies={},
            config={"symbol": "INVALID", "buffer_size": 10},
            scope=scope,
        )

    scope.close()
    tracker.assert_zero()
