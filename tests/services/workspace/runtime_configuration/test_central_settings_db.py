"""Unit tests for central application database, settings table, and typed access."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from app.services.workspace.runtime_configuration.runtime_configuration import (
    RuntimeConfigurationService,
    get_all_settings,
    get_category_settings,
    get_setting,
    get_setting_record,
    get_settings_history,
    init_central_database,
    reset_setting_to_default,
    set_setting,
    set_settings,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary initialized central database for testing."""
    db_file = tmp_path / "test_haruquantai.db"
    return init_central_database(db_file)


def test_init_central_database_creates_all_tables_and_seeds(temp_db: Path) -> None:
    """Verify all 5 tables and default records exist."""
    assert temp_db.is_file()

    conn = sqlite3.connect(str(temp_db))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = {r[0] for r in cursor.fetchall()}
        assert {
            "settings",
            "settings_history",
            "users",
            "sessions",
            "permissions",
        }.issubset(tables)

        # Check default seeds
        cursor.execute("SELECT COUNT(*) FROM settings;")
        settings_count = cursor.fetchone()[0]
        assert settings_count >= 50

        cursor.execute("SELECT COUNT(*) FROM users;")
        users_count = cursor.fetchone()[0]
        assert users_count >= 2

        cursor.execute("SELECT COUNT(*) FROM permissions;")
        perms_count = cursor.fetchone()[0]
        assert perms_count >= 20
    finally:
        conn.close()


def test_get_and_set_typed_settings(temp_db: Path) -> None:
    """Verify typed reads and writes with automatic casting."""
    # 1. String
    assert get_setting("system.app_name", db_path=temp_db) == "haruquant-dev"
    set_setting(
        "system.app_name", "haruquant-custom", changed_by="admin_user", db_path=temp_db
    )
    assert get_setting("system.app_name", db_path=temp_db) == "haruquant-custom"

    # 2. Bool
    assert get_setting("system.allow_live_mutations", db_path=temp_db) is False
    set_setting(
        "system.allow_live_mutations", True, changed_by="admin_user", db_path=temp_db
    )
    assert get_setting("system.allow_live_mutations", db_path=temp_db) is True

    # 3. Int
    assert get_setting("workspace.worker_count", db_path=temp_db) == 4
    set_setting("workspace.worker_count", 8, changed_by="admin_user", db_path=temp_db)
    assert get_setting("workspace.worker_count", db_path=temp_db) == 8

    # 4. Float
    assert get_setting("ai.temperature", db_path=temp_db) == 0.2
    set_setting("ai.temperature", 0.75, changed_by="admin_user", db_path=temp_db)
    assert get_setting("ai.temperature", db_path=temp_db) == 0.75

    # 5. JSON
    indicators = get_setting("ui.chart_default_indicators", db_path=temp_db)
    assert isinstance(indicators, list)
    assert "EMA_20" in indicators

    new_indicators = ["EMA_50", "RSI_14", "MACD"]
    set_setting(
        "ui.chart_default_indicators",
        new_indicators,
        changed_by="admin_user",
        db_path=temp_db,
    )
    assert get_setting("ui.chart_default_indicators", db_path=temp_db) == new_indicators


def test_settings_history_audit(temp_db: Path) -> None:
    """Verify changes generate audit log records in settings_history."""
    set_setting("system.log_level", "DEBUG", changed_by="alice", db_path=temp_db)
    set_setting("system.log_level", "WARNING", changed_by="bob", db_path=temp_db)

    history = get_settings_history("system.log_level", db_path=temp_db)
    assert len(history) >= 2
    latest = history[0]
    assert latest["key"] == "system.log_level"
    assert latest["old_value"] == "DEBUG"
    assert latest["new_value"] == "WARNING"
    assert latest["changed_by"] == "bob"


def test_category_and_all_queries(temp_db: Path) -> None:
    """Verify filtering settings by category."""
    ai_settings = get_category_settings("ai", db_path=temp_db)
    assert isinstance(ai_settings, dict)
    assert "ai.model_agent" in ai_settings
    assert ai_settings["ai.model_agent"] == "gemini-3.6-flash"

    broker_settings = get_category_settings("broker", db_path=temp_db)
    assert "broker.runtime_broker" in broker_settings
    assert broker_settings["broker.runtime_broker"] == "mt5"

    all_settings = get_all_settings(db_path=temp_db)
    assert len(all_settings) >= 50
    assert "credentials.google_api_key" in all_settings


def test_batch_set_settings(temp_db: Path) -> None:
    """Verify atomic batch setting updates."""
    set_settings(
        {
            "risk.max_risk_per_trade_pct": 2.5,
            "trading.max_slippage_pips": 4.0,
        },
        changed_by="risk_manager",
        db_path=temp_db,
    )
    assert get_setting("risk.max_risk_per_trade_pct", db_path=temp_db) == 2.5
    assert get_setting("trading.max_slippage_pips", db_path=temp_db) == 4.0


def test_reset_setting_to_default(temp_db: Path) -> None:
    """Verify reset to default restores original configured default_value."""
    set_setting(
        "system.timezone", "America/New_York", changed_by="tester", db_path=temp_db
    )
    assert get_setting("system.timezone", db_path=temp_db) == "America/New_York"

    reset_setting_to_default("system.timezone", changed_by="tester", db_path=temp_db)
    assert get_setting("system.timezone", db_path=temp_db) == "UTC+3"


def test_get_setting_record_metadata(temp_db: Path) -> None:
    """Verify metadata retrieval for a setting record."""
    rec = get_setting_record("credentials.openai_api_key", db_path=temp_db)
    assert rec is not None
    assert rec["category"] == "credentials"
    assert rec["is_secret"] is True
    assert rec["is_readonly"] is False
    assert rec["value_type"] == "string"


def test_users_and_sessions_foreign_key(temp_db: Path) -> None:
    """Verify sessions table enforces foreign key to users."""
    conn = sqlite3.connect(str(temp_db))
    try:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()

        # Valid session for existing user
        cursor.execute(
            """
            INSERT INTO sessions (
                session_digest, user_id, csrf_digest, created_at, expires_at
            ) VALUES ('sess_123', 'user_admin', 'csrf_456',
                      '2026-09-02T12:00:00Z', '2026-09-03T12:00:00Z');
            """
        )
        conn.commit()

        # Invalid session for non-existent user should fail
        sql = """
        INSERT INTO sessions (
            session_digest, user_id, csrf_digest, created_at, expires_at
        ) VALUES ('sess_999', 'non_existent_user', 'csrf_456',
                  '2026-09-02T12:00:00Z', '2026-09-03T12:00:00Z');
        """
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(sql)
    finally:
        conn.close()


def test_permissions_check_constraint(temp_db: Path) -> None:
    """Verify permissions table check constraints."""
    conn = sqlite3.connect(str(temp_db))
    try:
        cursor = conn.cursor()

        # Wildcard in permission_key must fail CHECK constraint
        wildcard_sql = """
        INSERT INTO permissions (
            permission_id, permission_key, domain, action, is_mutating,
            created_at, updated_at
        ) VALUES ('p_wildcard', 'workspace:*', 'workspace', 'read', 0,
                  '2026-09-02T12:00:00Z', '2026-09-02T12:00:00Z');
        """
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(wildcard_sql)

        # Invalid action must fail CHECK constraint
        invalid_action_sql = """
        INSERT INTO permissions (
            permission_id, permission_key, domain, action, is_mutating,
            created_at, updated_at
        ) VALUES ('p_invalid_act', 'workspace:purge', 'workspace', 'purge', 1,
                  '2026-09-02T12:00:00Z', '2026-09-02T12:00:00Z');
        """
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(invalid_action_sql)
    finally:
        conn.close()


def test_runtime_configuration_service_delegation(temp_db: Path) -> None:
    """Verify RuntimeConfigurationService instance methods delegate properly."""
    service = RuntimeConfigurationService()
    assert service.get_setting("system.app_name", db_path=temp_db) == "haruquant-dev"

    service.set_setting(
        "system.app_name",
        "haruquant-service",
        changed_by="service_test",
        db_path=temp_db,
    )
    assert (
        service.get_setting("system.app_name", db_path=temp_db) == "haruquant-service"
    )

    category_settings = service.get_category_settings("system", db_path=temp_db)
    assert category_settings["system.app_name"] == "haruquant-service"
