"""Integration evidence for unified settings migration preservation."""

import sqlite3
from pathlib import Path

from app.services.api import run_api_migrations
from app.services.api.composition.migrations import get_api_migration_steps
from app.services.data import (
    build_data_settings,
    build_migration_request,
    data_settings_context,
    run_domain_migrations,
)
from app.utils import generate_id


def test_api_0006_preserves_legacy_user_settings(tmp_path: Path) -> None:
    """Copy every legacy user document before dropping the old table."""
    settings = build_data_settings(
        database_url="sqlite:///settings-migration.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )
    database_path = tmp_path / "settings-migration.db"
    request_id = generate_id("req")
    steps = get_api_migration_steps()
    with data_settings_context(settings):
        baseline = run_domain_migrations(
            build_migration_request(
                domain="api",
                steps=steps[:1],
                request_id=request_id,
            )
        )
        assert baseline.status == "success"
        with sqlite3.connect(database_path) as connection:
            connection.execute(
                "INSERT INTO api_user_settings "
                "(user_id, settings_json, version, updated_at) "
                "VALUES (?, ?, ?, ?)",
                ("user-1", '{"theme":"dark"}', 3, "2026-08-04T00:00:00+00:00"),
            )
        migrated = run_api_migrations(generate_id("req"))
        assert migrated.status == "success"

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            "SELECT scope, subject_id, settings_json, version, created_at, "
            "updated_at, updated_by, request_id FROM api_settings"
        ).fetchone()
        legacy_table = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'api_user_settings'"
        ).fetchone()
    assert row == (
        "user",
        "user-1",
        '{"theme":"dark"}',
        3,
        "2026-08-04T00:00:00+00:00",
        "2026-08-04T00:00:00+00:00",
        "user-1",
        "",
    )
    assert legacy_table is None
