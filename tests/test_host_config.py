"""Tests for typed HostSettings models, loader, and singleton behavior."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest
from app.host.config import (
    ROOT_DIR,
    AgentsSettings,
    BacktestEngineSettings,
    CalibrationIndicatorsSettings,
    CpuSettings,
    CtraderSettings,
    DatabanksSettings,
    DesktopNotifySettings,
    EmailNotifySettings,
    GeminiAgentSettings,
    GeneralSettings,
    GlobalSettings,
    HostConfigurationError,
    HostSettings,
    McpSettings,
    MemorySettings,
    Metatrader5Settings,
    OllamaAgentSettings,
    OpenAiAgentSettings,
    OptimizationsSettings,
    PerformanceSettings,
    TelegramNotifySettings,
    TroubleshootingSettings,
    UserAccessSettings,
    WorkspacePathsSettings,
    load_host_settings,
    settings,
)
from pydantic import ValidationError

REPO = Path(__file__).resolve().parents[1]


def write_test_db(
    data_dir: Path,
    rows: list[tuple[str, str, object, int]],
) -> Path:
    """Create an isolated test database with host_settings rows."""
    db_path = data_dir / "database" / "haruquantai.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute(
                "CREATE TABLE host_settings ("
                "scope TEXT NOT NULL, key TEXT NOT NULL, value_json TEXT NOT NULL, "
                "schema_version INTEGER NOT NULL, updated_at_utc TEXT NOT NULL, "
                "PRIMARY KEY (scope, key))"
            )
            for scope, key, value, version in rows:
                raw = value if isinstance(value, str) else json.dumps(value)
                connection.execute(
                    "INSERT INTO host_settings VALUES (?, ?, ?, ?, ?)",
                    (scope, key, raw, version, "2026-01-01T00:00:00+00:00"),
                )
    return db_path


def test_singleton_auto_populates_when_database_exists() -> None:
    """The default singleton loads live settings when haruquantai.db exists."""
    assert settings.general.theme == "dark"
    assert settings.general.language == "en"
    assert settings.cpu.core_usage == "all"
    assert settings.memory.memory_limit_gb == 8
    assert settings.agents.active_provider == "gemini"
    assert settings.revision == 3
    assert "application" in settings.records
    assert "host" in settings.records


def test_host_settings_pure_defaults() -> None:
    """Unparameterized HostSettings construction yields standard defaults."""
    default = HostSettings()
    assert default.host == "127.0.0.1"
    assert default.port == 8000
    assert default.control_port == 5050
    assert default.api_port == 8080
    assert default.product_name == "HaruQuantAI"
    assert default.revision == 1
    assert default.records == {}
    assert default.general.web_server_port == 8080
    assert default.cpu.custom_cores == 8


def test_host_settings_construction_is_pure(tmp_path: Path) -> None:
    HostSettings(data_dir=tmp_path / "data")
    assert not (tmp_path / "data").exists()


def test_host_settings_is_frozen_and_closed() -> None:
    config = HostSettings()
    with pytest.raises(ValidationError):
        config.port = 9000
    with pytest.raises(ValidationError):
        HostSettings.model_validate({"unknown_field": "value"})


def test_blank_host_and_data_dir_fail_validation() -> None:
    with pytest.raises(ValidationError):
        HostSettings.model_validate({"host": " "})
    with pytest.raises(ValidationError):
        HostSettings.model_validate({"data_dir": " "})


def test_derived_paths_follow_data_dir(tmp_path: Path) -> None:
    config = HostSettings(data_dir=tmp_path)
    assert config.database_path == tmp_path / "database" / "haruquantai.db"
    assert config.database_dir == tmp_path / "database"
    assert config.log_dir == tmp_path / "logs"
    assert config.market_dir == tmp_path / "market"
    assert config.strategies_dir == tmp_path / "strategies"
    assert config.databank_dir == tmp_path / "databank"
    assert config.projects_dir == tmp_path / "projects"
    assert config.ui_dir == ROOT_DIR / "app" / "ui"
    assert config.plugins_dir == ROOT_DIR / "plugins"


def test_secrets_hidden_from_repr() -> None:
    """Ensure no credential fields appear in repr for any settings model."""
    rendered = repr(settings)
    assert "AIzaSy" not in rendered
    assert "sk-proj" not in rendered
    assert "fb8128" not in rendered
    assert "bot_token" not in rendered

    gemini = GeminiAgentSettings(api_key="super-secret-gemini")
    assert "super-secret-gemini" not in repr(gemini)

    openai = OpenAiAgentSettings(api_key="super-secret-openai")
    assert "super-secret-openai" not in repr(openai)

    ctrader = CtraderSettings(
        client_secret="ct-secret",  # pragma: allowlist secret
        access_token="ct-access",
        refresh_token="ct-refresh",
    )
    assert "ct-secret" not in repr(ctrader)
    assert "ct-access" not in repr(ctrader)
    assert "ct-refresh" not in repr(ctrader)

    mt5 = Metatrader5Settings(password="mt5-password")
    assert "mt5-password" not in repr(mt5)

    mcp = McpSettings(auth_token="mcp-token")
    assert "mcp-token" not in repr(mcp)

    email = EmailNotifySettings(password="email-password")
    assert "email-password" not in repr(email)

    telegram = TelegramNotifySettings(bot_token="telegram-token")
    assert "telegram-token" not in repr(telegram)

    user = UserAccessSettings(
        password_hash="hash-123",  # pragma: allowlist secret
        password_salt="salt-123",  # pragma: allowlist secret
    )
    assert "hash-123" not in repr(user)
    assert "salt-123" not in repr(user)


def test_ensure_directories_creates_data_tree_only_when_called(
    tmp_path: Path,
) -> None:
    config = HostSettings(data_dir=tmp_path / "data")
    assert not (tmp_path / "data").exists()
    config.ensure_directories()
    for name in ("database", "logs", "market", "strategies", "databank", "projects"):
        assert (tmp_path / "data" / name).is_dir()
    assert not (ROOT_DIR / "plugins").is_file()


def test_load_host_settings_missing_database_returns_defaults(
    tmp_path: Path,
) -> None:
    loaded = load_host_settings(tmp_path / "nonexistent.db", data_dir=tmp_path)
    assert loaded.records == {}
    assert loaded.port == 8000
    assert loaded.revision == 1


def test_load_host_settings_loads_typed_sections(tmp_path: Path) -> None:
    write_test_db(
        tmp_path,
        [
            (
                "application",
                "app.general",
                {"theme": "light", "web_server_port": 8099},
                1,
            ),
            (
                "application",
                "config.cpu",
                {"core_usage": "custom", "custom_cores": 4},
                1,
            ),
            (
                "application",
                "calibration.indicators",
                {"QQE.RSIPeriod": [14], "QQE.sF": [5]},
                1,
            ),
            ("host", "__revision__", 42, 1),
        ],
    )
    loaded = load_host_settings(data_dir=tmp_path)
    assert loaded.general.theme == "light"
    assert loaded.general.web_server_port == 8099
    assert loaded.port == 8099
    assert loaded.cpu.core_usage == "custom"
    assert loaded.cpu.custom_cores == 4
    assert loaded.calibration.qqe_rsi_period == (14,)
    assert loaded.revision == 42


def test_load_host_settings_rejects_incompatible_schema(tmp_path: Path) -> None:
    path = tmp_path / "database" / "haruquantai.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.execute("CREATE TABLE host_settings (bad_col TEXT)")
    with pytest.raises(HostConfigurationError, match="Incompatible"):
        load_host_settings(data_dir=tmp_path)


def test_load_host_settings_rejects_invalid_schema_version(tmp_path: Path) -> None:
    write_test_db(
        tmp_path,
        [("application", "app.general", {"web_server_port": 8080}, 2)],
    )
    with pytest.raises(HostConfigurationError, match="schema version"):
        load_host_settings(data_dir=tmp_path)


def test_load_host_settings_rejects_malformed_json(tmp_path: Path) -> None:
    write_test_db(
        tmp_path,
        [("application", "app.general", "{bad_json", 1)],
    )
    with pytest.raises(HostConfigurationError, match="Malformed"):
        load_host_settings(data_dir=tmp_path)


def test_load_host_settings_rejects_duplicate_keys(tmp_path: Path) -> None:
    write_test_db(
        tmp_path,
        [("application", "app.general", '{"theme":"dark","theme":"light"}', 1)],
    )
    with pytest.raises(HostConfigurationError, match="Malformed"):
        load_host_settings(data_dir=tmp_path)


def test_load_host_settings_rejects_non_finite_constant(tmp_path: Path) -> None:
    write_test_db(
        tmp_path,
        [("application", "app.general", '{"auto_save_interval_s":NaN}', 1)],
    )
    with pytest.raises(HostConfigurationError, match="Malformed"):
        load_host_settings(data_dir=tmp_path)


def test_load_host_settings_rejects_data_dir_file(tmp_path: Path) -> None:
    file_path = tmp_path / "a_file"
    file_path.write_text("hello", encoding="utf-8")
    with pytest.raises(HostConfigurationError, match="not a file"):
        load_host_settings(database_path=tmp_path)  # directory passed instead of file


def test_submodels_are_frozen_and_closed() -> None:
    for model_cls in (
        GeneralSettings,
        CalibrationIndicatorsSettings,
        GeminiAgentSettings,
        OpenAiAgentSettings,
        OllamaAgentSettings,
        AgentsSettings,
        CpuSettings,
        CtraderSettings,
        DatabanksSettings,
        GlobalSettings,
        MemorySettings,
        Metatrader5Settings,
        OptimizationsSettings,
        PerformanceSettings,
        TroubleshootingSettings,
        McpSettings,
        BacktestEngineSettings,
        DesktopNotifySettings,
        EmailNotifySettings,
        TelegramNotifySettings,
        UserAccessSettings,
        WorkspacePathsSettings,
    ):
        instance = model_cls()
        assert isinstance(instance, model_cls)
        with pytest.raises(ValidationError):
            model_cls.model_validate({"unknown_random_field": 123})


def test_import_is_inert_in_clean_environment(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import app.host.config; print('OK')"],
        cwd=tmp_path,
        env=dict(os.environ, PYTHONPATH=str(REPO)),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
    assert not (tmp_path / "data").exists()
