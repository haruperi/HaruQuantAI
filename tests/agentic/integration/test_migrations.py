"""Integration evidence for the authoritative Agentic migration manifest."""

from pathlib import Path

from app.agentic import get_agentic_migrations, run_agentic_migrations
from app.kernel.identity import generate_id
from app.services.data import build_data_settings, data_settings_context


def _settings(tmp_path: Path) -> object:
    """Build isolated non-production Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///agentic-manifest.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def test_agentic_manifest_is_complete_ordered_and_unique() -> None:
    """The manifest contains every immutable Agentic migration exactly once."""
    steps = get_agentic_migrations()

    assert len(steps) == 5
    assert [step.migration_id[:3] for step in steps] == [
        "001",
        "002",
        "003",
        "004",
        "005",
    ]
    assert len({step.migration_id for step in steps}) == len(steps)
    assert len({step.checksum for step in steps}) == len(steps)


def test_agentic_manifest_runs_idempotently(tmp_path: Path) -> None:
    """Data applies the complete manifest once and verifies it thereafter."""
    with data_settings_context(_settings(tmp_path)):
        first = run_agentic_migrations(generate_id("req"))
        second = run_agentic_migrations(generate_id("req"))

    assert first.status == "success"
    assert second.status == "success"
    assert first.data is not None
    assert second.data is not None
    assert len(first.data.applied_ids) == 5
    assert second.data.applied_ids == ()
    assert len(second.data.skipped_ids) == 5
