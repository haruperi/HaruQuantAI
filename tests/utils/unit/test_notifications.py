"""Unit coverage for unified notification orchestration."""

import pytest
from app.utils import (
    build_desktop_notification_config,
    build_notification_manager_config,
    close_notification_manager,
    create_notification_manager,
    get_notification_manager_status,
    get_notification_template_names,
    register_notification_template,
    render_notification_template,
    send_notification,
)
from app.utils.errors.exceptions import ConfigurationError
from app.utils.notifications.manager import NotificationManager


class _Notifier:
    """Controllable in-memory notifier for manager policy tests."""

    def __init__(self, outcome: str = "sent") -> None:
        self.active = True
        self._outcome = outcome

    def send(
        self, _title: str, _text: str, _html: str | None = None
    ) -> dict[str, object]:
        if self._outcome == "failed":
            raise RuntimeError("mock failure")
        return {"status": "accepted"}


def test_manager_is_disabled_by_default_and_fail_closed() -> None:
    """Verify default configuration cannot perform outbound work."""
    manager = create_notification_manager(
        build_notification_manager_config(default_channels=("desktop",)),
        desktop_config=build_desktop_notification_config(enabled=True),
    )

    with pytest.raises(ConfigurationError, match="NOTIFICATIONS_DISABLED"):
        send_notification(manager, "Warning", "Check state")


def test_templates_are_session_local_and_escape_html() -> None:
    """Verify built-ins and custom templates render deterministic safe HTML."""
    manager = create_notification_manager(build_notification_manager_config())
    register_notification_template(
        manager, "custom", "Alert {name}", "Value {value}", "<p>{value}</p>"
    )

    rendered = render_notification_template(
        manager, "custom", {"name": "worker", "value": "<unsafe>"}
    )

    assert rendered["title"] == "Alert worker"
    assert rendered["html"] == "<p>&lt;unsafe&gt;</p>"
    assert "trading_signal" in get_notification_template_names(manager)


def test_manager_status_and_close_do_not_expose_config_values() -> None:
    """Verify status is bounded and close is deterministic."""
    manager = create_notification_manager(build_notification_manager_config())
    close_notification_manager(manager)

    assert get_notification_manager_status(manager) == {
        "enabled": False,
        "closed": True,
        "channels": (),
    }


def test_manager_reports_success_partial_failure_and_rate_limit() -> None:
    """Verify channel isolation and deterministic rate-limit exhaustion."""
    config = build_notification_manager_config(
        enabled=True,
        default_channels=("desktop", "email"),
        rate_limit=1,
        rate_window_seconds=60,
    )
    manager = NotificationManager(
        config,  # type: ignore[arg-type]
        {"desktop": _Notifier(), "email": _Notifier("failed")},
    )

    first = send_notification(manager, "Title", "Text")
    second = send_notification(manager, "Title", "Text")

    assert first["status"] == "partial"
    assert second["status"] == "error"


@pytest.mark.parametrize(
    ("operation", "error"),
    [
        (
            lambda: build_notification_manager_config(default_channels=("bad",)),
            "CHANNEL",
        ),
        (lambda: build_notification_manager_config(rate_limit=0), "CONFIG"),
        (lambda: create_notification_manager(object()), "CONFIG"),
        (
            lambda: create_notification_manager(
                build_notification_manager_config(), desktop_config=object()
            ),
            "CONFIG",
        ),
        (lambda: get_notification_manager_status(object()), "MANAGER"),
    ],
)
def test_manager_rejects_invalid_inputs(operation: object, error: str) -> None:
    """Verify malformed manager values fail closed."""
    with pytest.raises(ConfigurationError, match=error):
        operation()  # type: ignore[operator]


def test_manager_rejects_empty_message_and_channel_selection() -> None:
    """Verify messages and explicit channel selection are mandatory."""
    manager = NotificationManager(
        build_notification_manager_config(enabled=True),  # type: ignore[arg-type]
        {},
    )
    with pytest.raises(ConfigurationError, match="MESSAGE"):
        send_notification(manager, "", "text", channels=("desktop",))
    with pytest.raises(ConfigurationError, match="CHANNELS"):
        send_notification(manager, "title", "text")
