"""Tests for Data's shared central settings source."""

from pathlib import Path

from app.services.data import build_data_settings


def test_data_settings_load_required_persistence_bootstrap() -> None:
    """Load database bootstrap values through Utils' canonical source order."""
    settings = build_data_settings()

    assert settings.database_url
    assert isinstance(settings.data_dir, Path)
    assert settings.sqlite_busy_timeout_seconds is not None
    assert settings.write_lock_lease_seconds is not None
