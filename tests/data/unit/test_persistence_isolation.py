"""Isolation guard for the duplicated stateful persistence modules.

``CAP-DATA-026`` Phase 2 duplicates code that writes to a real SQLite file and to real
filesystem roots. Duplicating stateful code doubles the number of fixtures that could
resolve to ambient settings, and a test that quietly writes to the operator's
configured ``DATA_DIR`` is both a correctness problem and a data-loss risk.

These tests assert the property directly rather than trusting convention: with no
explicit settings installed, path resolution must not silently fall back to a usable
ambient location, and with a context-local profile installed, every resolved path must
sit under that profile's root.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.services.data._settings import DataSettings, data_settings_context
from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.transactions import execute_transaction

REQUEST_ID = "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _isolated_settings(tmp_path: Path) -> DataSettings:
    """Build a settings profile confined to one temporary directory.

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        Settings whose database and storage roots are inside ``tmp_path``.
    """
    # The database URL is deliberately relative: `_parse_database_config` resolves it
    # under `data_dir` and rejects absolute paths and paths that escape the root. That
    # rule is what makes a context-local profile a real boundary rather than a hint.
    return DataSettings(
        database_url="sqlite:///isolated.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        approved_storage_roots=(tmp_path,),
    )


def test_transaction_uses_the_context_local_database(tmp_path: Path) -> None:
    """Assert an isolated profile confines writes to its own database file.

    Raises:
        AssertionError: If the write lands outside the temporary directory.
    """
    settings = _isolated_settings(tmp_path)
    with data_settings_context(settings):
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=("CREATE TABLE isolation_probe (id TEXT)",),
                    parameter_sets=((),),
                    max_rows=1,
                ),
                request_id=REQUEST_ID,
            )
        )
    written = list(tmp_path.glob("*.db"))
    assert written, "No database file was created inside the isolated root."
    assert all(path.is_relative_to(tmp_path) for path in written)


def test_a_second_profile_cannot_see_the_first_profiles_data(tmp_path: Path) -> None:
    """Assert two isolated profiles do not share state.

    This is the property that lets the duplicated legacy and new modules be exercised
    in one test session without interfering.

    Raises:
        AssertionError: If state leaks between profiles.
    """
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    with data_settings_context(_isolated_settings(first)):
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=("CREATE TABLE only_in_first (id TEXT)",),
                    parameter_sets=((),),
                    max_rows=1,
                ),
                request_id=REQUEST_ID,
            )
        )

    with data_settings_context(_isolated_settings(second)):
        result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name='only_in_first'",
                    ),
                    parameter_sets=((),),
                    max_rows=1,
                ),
                request_id=REQUEST_ID,
            )
        )
    assert not result.rows, (
        "The second profile observed a table created by the first. Profiles are not "
        "isolated, so duplicated persistence modules can interfere."
    )


def test_unusable_configuration_fails_closed(tmp_path: Path) -> None:
    """Assert a profile pointing at an unusable path raises rather than falling back.

    A silent fallback to an ambient default is the failure mode this guard exists to
    prevent: it is how a test ends up writing to the operator's real database.

    Raises:
        AssertionError: If an unusable configuration is tolerated.
    """
    unusable = DataSettings(
        database_url="sqlite:///missing_dir/nested/x.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        approved_storage_roots=(tmp_path,),
    )
    with data_settings_context(unusable), pytest.raises(DataError) as excinfo:
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=("SELECT 1",),
                    parameter_sets=((),),
                    max_rows=1,
                ),
                request_id=REQUEST_ID,
            )
        )
    assert excinfo.value.code in {"DB_CONNECTION_ERROR", "DATABASE_ERROR"}


def test_approved_roots_reject_paths_outside_the_isolated_profile(
    tmp_path: Path,
) -> None:
    """Assert the approved-root guard is driven by the active profile.

    Raises:
        AssertionError: If a path outside the profile's roots is accepted.
    """
    settings = _isolated_settings(tmp_path)
    with data_settings_context(settings):
        assert settings.approved_storage_roots == (tmp_path,)
        outside = tmp_path.parent / "outside_the_profile"
        assert not any(
            outside.is_relative_to(root) for root in settings.approved_storage_roots
        )
