"""Cross-package contract identity guard for the migrated ``sources`` package.

``CAP-DATA-026`` Phase 3 migrated source governance in place: ``sources/`` now builds
``models``-package contracts, while ``gateway/`` and ``scheduler/`` still hold legacy
``contracts``-package ones. Pydantic validates by type identity, so mixing the two is
not automatically safe — that is precisely what broke the Phase 2 test fixtures.

The migration is safe here only because every consumer *reads attributes* off the
descriptors and plans it receives, and none passes them into another contract
constructor. These tests pin that property. If a future change makes a consumer
reconstruct a descriptor, or makes governance emit a legacy-package object, one of
these fails rather than the defect surfacing as a confusing validation error deep in a
retrieval call.

Delete this file in Phase 11, when only one contract package remains.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.sources import composition as _composition
from app.services.data.sources.registry import (
    _reset_registry,
    get_source_descriptor,
)
from app.utils import generate_id


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Reset the source registry around each test.

    Returns:
        None. The registry is cleared before and after every test so composition is
        exercised from a known state.
    """
    _reset_registry()
    yield
    _reset_registry()


def _settings(tmp_path: Path) -> DataSettings:
    """Build an isolated settings profile exposing one local source.

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        Settings confined to ``tmp_path`` with a single ``csv`` local source.
    """
    return DataSettings(
        database_url="sqlite:///identity.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        approved_storage_roots=(tmp_path,),
        data_local_sources=("csv",),
        data_provider_sources=(),
        data_raw_root=Path("raw"),
    )


def test_composed_descriptor_comes_from_the_models_package(tmp_path: Path) -> None:
    """Assert governance emits ``models``-package contracts after the migration.

    Raises:
        AssertionError: If a descriptor is still built from the legacy package.
    """
    (tmp_path / "raw").mkdir(parents=True, exist_ok=True)
    with data_settings_context(_settings(tmp_path)):
        _composition.ensure_source("csv", generate_id("req"))
        descriptor = get_source_descriptor("csv")

    assert type(descriptor).__module__.startswith("app.services.data.sources"), (
        f"Descriptor came from {type(descriptor).__module__}. Source governance was "
        "migrated to `sources`; emitting a legacy contract means the migration is "
        "incomplete."
    )


def test_descriptor_exposes_every_attribute_consumers_read(tmp_path: Path) -> None:
    """Assert the attributes legacy consumers depend on survive the round trip.

    ``gateway/historical.py`` reads ``revision`` and ``license_policy.*``;
    ``gateway/reference.py`` and ``feeds/runtime.py`` read ``source_id`` and
    ``readiness``. Duck typing makes these work across packages, but only while the
    attributes exist.

    Raises:
        AssertionError: If a consumed attribute is missing.
    """
    (tmp_path / "raw").mkdir(parents=True, exist_ok=True)
    with data_settings_context(_settings(tmp_path)):
        _composition.ensure_source("csv", generate_id("req"))
        descriptor = get_source_descriptor("csv")

    for attribute in ("source_id", "readiness", "revision", "license_policy"):
        assert hasattr(descriptor, attribute), (
            f"Descriptor lost `{attribute}`, which a legacy consumer reads."
        )
    for attribute in ("status", "export_allowed", "attribution_required"):
        assert hasattr(descriptor.license_policy, attribute), (
            f"Licence policy lost `{attribute}`, read by gateway/historical.py."
        )


def test_registry_returns_the_same_object_it_was_given(tmp_path: Path) -> None:
    """Assert the registry stores descriptors rather than reconstructing them.

    Reconstruction is what would convert a class across packages and reintroduce the
    identity hazard. Storing preserves whatever the caller supplied.

    Raises:
        AssertionError: If two reads return different objects.
    """
    (tmp_path / "raw").mkdir(parents=True, exist_ok=True)
    with data_settings_context(_settings(tmp_path)):
        _composition.ensure_source("csv", generate_id("req"))
        first = get_source_descriptor("csv")
        second = get_source_descriptor("csv")

    assert first is second, (
        "The registry returned a different object on the second read, so it is "
        "reconstructing descriptors. That converts classes across packages and "
        "reintroduces the cross-package identity hazard."
    )


def test_composable_sources_reflect_the_active_settings_profile(
    tmp_path: Path,
) -> None:
    """Assert governance reads settings through the single shared context variable.

    Phase 3 found that a duplicated settings module gives each half of the domain its
    own ``ContextVar``, so a context-local profile is honoured by one half and silently
    ignored by the other. This test fails if that duplication returns.

    Raises:
        AssertionError: If the active profile is not observed by governance.
    """
    (tmp_path / "raw").mkdir(parents=True, exist_ok=True)
    with data_settings_context(_settings(tmp_path)):
        composable = _composition.list_composable_sources()

    assert "csv" in composable
    assert "parquet" not in composable, (
        "Governance did not observe the context-local settings profile, which means "
        "settings state is duplicated across two modules again."
    )
