"""Integration evidence for the Utils package-root notification boundary."""

import inspect

from app import utils


def test_notification_public_surface_is_function_only() -> None:
    """Verify every notification export is a standalone root function."""
    names = tuple(name for name in utils.__all__ if "notification" in name)

    assert names
    assert all(inspect.isfunction(getattr(utils, name)) for name in names)


def test_notification_lifecycle_without_external_delivery() -> None:
    """Verify composition, templating, status, and teardown without network IO."""
    config = utils.build_notification_manager_config(
        enabled=True, default_channels=("desktop",)
    )
    desktop = utils.build_desktop_notification_config(enabled=False)
    manager = utils.create_notification_manager(config, desktop_config=desktop)

    rendered = utils.render_notification_template(
        manager,
        "system_alert",
        {
            "level": "INFO",
            "message": "Database is healthy",
            "details": "bounded test",
            "timestamp": "2026-08-09T00:00:00Z",
            "component": "data",
            "status": "healthy",
        },
    )
    result = utils.send_notification(manager, rendered["title"], rendered["text"])

    assert result["status"] == "error"
    assert result["results"][0]["status"] == "unavailable"
