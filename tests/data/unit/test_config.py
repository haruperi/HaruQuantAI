"""Tests for the typed DATA settings boundary."""

from pathlib import Path

import pytest
from app.services.data.config import (
    DataSettings,
    data_settings_context,
    get_data_settings,
)
from pydantic import ValidationError


def test_data_settings_reads_process_overrides_through_shared_base(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Typed DATA settings honor process overrides without direct module reads."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///typed.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "2.5")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "45")

    settings = get_data_settings()

    assert settings.database_url == "sqlite:///typed.sqlite3"
    assert settings.data_dir == tmp_path
    assert settings.sqlite_busy_timeout_seconds == 2.5
    assert settings.write_lock_lease_seconds == 45


def test_data_settings_rejects_padded_numeric_input() -> None:
    """Padded numeric configuration fails before a storage operation."""
    with pytest.raises(ValidationError):
        DataSettings(write_lock_lease_seconds=" 30")  # type: ignore[arg-type]


def test_data_settings_context_is_local_and_reversible(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An explicit isolated profile is restored after its context exits."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///outer.sqlite3")
    explicit = DataSettings(
        database_url="sqlite:///inner.sqlite3",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1,
        write_lock_lease_seconds=30,
    )

    with data_settings_context(explicit):
        assert get_data_settings() is explicit

    assert get_data_settings().database_url == "sqlite:///outer.sqlite3"
