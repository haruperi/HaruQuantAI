"""Unit tests for SessionCalendarConfig."""

from pathlib import Path

from app.services.catalogue.session_calendar.config import SessionCalendarConfig


def test_session_calendar_config_defaults() -> None:
    """Verify default values of SessionCalendarConfig."""
    cfg = SessionCalendarConfig()
    assert cfg.database_path is None
    assert cfg.auto_migrate is True


def test_session_calendar_config_custom(tmp_path: Path) -> None:
    """Verify custom values of SessionCalendarConfig."""
    custom_path = tmp_path / "custom_sessions.db"
    cfg = SessionCalendarConfig(database_path=custom_path, auto_migrate=False)
    assert cfg.database_path == custom_path
    assert cfg.auto_migrate is False
