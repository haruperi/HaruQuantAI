"""Component-tier verification for filesystem, schema, and compiled boundaries."""

from pathlib import Path

import pytest

from tests.data.unit.test_account_state import (
    component_account_snapshot_fails_closed_when_incomplete,
)
from tests.data.unit.test_backup import (
    component_database_backup_hashes_after_persisted_lease,
    component_manifest_records_hash_per_target,
    component_restore_is_atomic_on_hash_mismatch,
    component_restore_round_trip,
    component_retention_purges_payload_and_manifest,
)
from tests.data.unit.test_calendar_provider import (
    component_get_events_normalizes_calendar_events,
)
from tests.data.unit.test_calendar_scraper import (
    component_save_rejects_directory_outside_approved_roots,
    component_save_skips_empty_dataframes,
    component_to_dataframe_returns_valid_structure,
)
from tests.data.unit.test_persistence_migrations import (
    component_complete_manifest_rejects_orphaned_applied_step,
    component_run_domain_migrations_applies_and_skips_steps,
    component_run_domain_migrations_rejects_out_of_order_step,
)


@pytest.fixture
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return an isolated Data root for real backup component checks.

    Args:
        tmp_path: Disposable filesystem root.
        monkeypatch: Isolated side-effect fixture.

    Returns:
        Prepared Data root.
    """
    for relative in (
        Path("data/raw"),
        Path("data/processed"),
        Path("data/cache"),
        Path("artifacts/data"),
    ):
        (tmp_path / relative).mkdir(parents=True)
    monkeypatch.setattr(
        "app.services.data.evidence.audit_store._persist_audit_event_raw",
        lambda _event: None,
    )
    return tmp_path


@pytest.mark.parametrize(
    "verification",
    [
        component_manifest_records_hash_per_target,
        component_database_backup_hashes_after_persisted_lease,
        component_restore_round_trip,
        component_restore_is_atomic_on_hash_mismatch,
        component_retention_purges_payload_and_manifest,
    ],
)
def test_backup_boundary(verification: object, data_root: Path) -> None:
    """Run one real filesystem/database backup verification.

    Args:
        verification: Focused backup verification function.
        data_root: Migrated disposable Data root fixture.
    """
    verification(data_root)  # type: ignore[operator]


@pytest.mark.parametrize(
    "verification",
    [
        component_run_domain_migrations_applies_and_skips_steps,
        component_complete_manifest_rejects_orphaned_applied_step,
        component_run_domain_migrations_rejects_out_of_order_step,
    ],
)
def test_migration_boundary(
    verification: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Run one real SQLite migration-ledger verification.

    Args:
        verification: Focused migration verification function.
        monkeypatch: Isolated settings fixture.
        tmp_path: Disposable database directory.
    """
    verification(monkeypatch, tmp_path)  # type: ignore[operator]


def test_calendar_storage_boundary(tmp_path: Path) -> None:
    """Run the approved-root filesystem rejection verification."""
    component_save_rejects_directory_outside_approved_roots(tmp_path)


def test_calendar_dataframe_boundary(tmp_path: Path) -> None:
    """Run real dataframe normalization and empty-file persistence checks."""
    component_to_dataframe_returns_valid_structure()
    component_save_skips_empty_dataframes(tmp_path)


def test_calendar_provider_boundary() -> None:
    """Run the asynchronous provider normalization verification."""
    component_get_events_normalizes_calendar_events()


def test_account_adapter_boundary() -> None:
    """Run the asynchronous broker-evidence failure verification."""
    component_account_snapshot_fails_closed_when_incomplete()
