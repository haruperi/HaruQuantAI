"""Tests for Data's shared central settings source."""

from pathlib import Path

from app.services.data import (
    build_data_settings,
    data_provider_settings_context,
    ensure_source,
    list_composable_sources,
)
from app.utils import generate_id, load_broker_provider_settings


def test_data_settings_load_required_persistence_bootstrap() -> None:
    """Load database bootstrap values through Utils' canonical source order."""
    settings = build_data_settings()

    assert settings.database_url
    assert isinstance(settings.data_dir, Path)
    assert settings.sqlite_busy_timeout_seconds is not None
    assert settings.write_lock_lease_seconds is not None


def test_provider_settings_context_enables_mt5_composition() -> None:
    """Injected provider settings make MT5 composable without connecting."""
    provider_settings = load_broker_provider_settings({"mt5_enabled": True})

    with data_provider_settings_context(provider_settings):
        composable = list_composable_sources()
        registered = ensure_source("mt5", generate_id("req"))

    assert composable.data is not None
    assert "mt5" in composable.data
    assert registered.status == "success"
    assert "mt5" not in (list_composable_sources().data or ())
