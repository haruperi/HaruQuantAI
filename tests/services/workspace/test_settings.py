"""Unit tests for Settings service and feature (FR-WORKSPACE-001)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.workspace import (
    WORKSPACE_SETTINGS,
    SettingsValidationError,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.workspace import (
    WorkspacePersistenceConfig,
    WorkspacePersistenceFeature,
)
from app.services.workspace.settings import (
    DEFAULT_PRESETS_DIR,
    DEFAULT_SETTINGS_DIR,
    DEFAULT_USER_OVERRIDE_FILE,
    KEY_CONFIG_AGENTS,
    KEY_CONFIG_CPU,
    KEY_CONFIG_CTRADER,
    KEY_CONFIG_DATABANKS,
    KEY_CONFIG_GLOBAL,
    KEY_CONFIG_MEMORY,
    KEY_CONFIG_MT5,
    KEY_CONFIG_OPTIMIZATIONS,
    KEY_CONFIG_PERFORMANCE,
    KEY_CONFIG_TROUBLESHOOTING,
    KEY_CONNECT_MCP,
    KEY_NOTIFY_DESKTOP,
    KEY_NOTIFY_EMAIL,
    KEY_NOTIFY_TELEGRAM,
    KEY_USER_ACCESS,
    SPEC,
    AgentsConfigSettings,
    BacktestEngineSettings,
    CpuConfigSettings,
    CTraderConfigSettings,
    DatabanksConfigSettings,
    DesktopNotificationSettings,
    EmailNotificationSettings,
    GeminiProviderConfig,
    GlobalConfigSettings,
    McpConnectSettings,
    MemoryConfigSettings,
    MetaTrader5ConfigSettings,
    OllamaProviderConfig,
    OpenAiProviderConfig,
    OptimizationsConfigSettings,
    PerformanceConfigSettings,
    SettingsConfig,
    SettingsService,
    TelegramNotificationSettings,
    TroubleshootingConfigSettings,
    UserAccessSettings,
    WorkspaceAppSettings,
    feature,
    hash_password,
    verify_password,
)


def test_settings_config_validation() -> None:
    """Verify settings config validation checks."""
    config = SettingsConfig(default_scope="app")
    assert config.default_scope == "app"

    with pytest.raises(ValueError, match="default_scope cannot be empty"):
        SettingsConfig(default_scope=" ")


def test_settings_service_crud_and_validation() -> None:
    """Verify in-memory get, set, validation, and snapshot resolution."""
    service = SettingsService(SettingsConfig())

    # Validation errors
    with pytest.raises(SettingsValidationError, match="cannot be empty"):
        service.set_setting("", {"threads": 4})

    # Application setting
    service.set_setting("max_threads", {"value": 8})
    assert service.get_setting("max_threads") == {"value": 8}
    assert service.get_setting("non_existent") is None

    # Project override
    service.set_setting("max_threads", {"value": 4}, scope="project:p1")

    # Hierarchical resolution
    snapshot_app = service.resolve_effective(("max_threads",))
    assert snapshot_app.entries[0].value == {"value": 8}

    snapshot_proj = service.resolve_effective(("max_threads",), project_id="p1")
    assert snapshot_proj.entries[0].value == {"value": 4}

    # Run override
    service.set_setting("max_threads", {"value": 2}, scope="run:r1")
    snapshot_run = service.resolve_effective(
        ("max_threads",), project_id="p1", run_id="r1"
    )
    assert snapshot_run.entries[0].value == {"value": 2}


def test_preset_export_and_import() -> None:
    """Verify exporting and importing settings presets as JSON dicts."""
    service = SettingsService(SettingsConfig())
    service.set_setting("theme", {"skin": "dark"})
    service.set_setting("port", {"http": 8080})

    preset = service.export_preset("custom_preset")
    assert preset["preset_name"] == "custom_preset"
    assert "theme" in preset["settings"]
    assert "port" in preset["settings"]

    # New service importing preset
    new_service = SettingsService(SettingsConfig())
    new_service.import_preset(preset)
    assert new_service.get_setting("theme") == {"skin": "dark"}
    assert new_service.get_setting("port") == {"http": 8080}

    with pytest.raises(SettingsValidationError):
        new_service.import_preset({"invalid": "data"})


def test_settings_lifecycle_with_persistence(tmp_path: Path) -> None:
    """Verify runtime composition and database hydration."""
    feat = feature()
    assert feat.spec == SPEC

    db_path = str(tmp_path / "settings_test.db")

    async def _test() -> None:
        async with Runtime(
            (
                lambda: WorkspacePersistenceFeature(
                    WorkspacePersistenceConfig(db_path=db_path)
                ),
                feature,
            )
        ) as runtime:
            settings = runtime.require(WORKSPACE_SETTINGS)
            settings.set_setting("persisted_key", {"saved": True})
            assert settings.get_setting("persisted_key") == {"saved": True}

        # Mount a second time to verify persistence hydration
        async with Runtime(
            (
                lambda: WorkspacePersistenceFeature(
                    WorkspacePersistenceConfig(db_path=db_path)
                ),
                feature,
            )
        ) as runtime2:
            settings2 = runtime2.require(WORKSPACE_SETTINGS)
            assert settings2.get_setting("persisted_key") == {"saved": True}

    asyncio.run(_test())


def test_pydantic_model_settings() -> None:
    """Verify strongly-typed Pydantic model get/set operations and validation."""
    service = SettingsService(SettingsConfig())

    # App settings
    app_cfg = WorkspaceAppSettings(
        theme="cyberpunk",
        auto_save_interval_s=120,
    )
    service.set_model("app.general", app_cfg)

    retrieved = service.get_model("app.general", WorkspaceAppSettings)
    assert retrieved is not None
    assert retrieved.theme == "cyberpunk"
    assert retrieved.auto_save_interval_s == 120
    assert retrieved.language == "en"  # default preserved

    # Engine settings
    engine_cfg = BacktestEngineSettings(max_threads=8, precision_mode="ultra")
    service.set_model("engine.backtest", engine_cfg)

    retrieved_engine = service.get_model("engine.backtest", BacktestEngineSettings)
    assert retrieved_engine is not None
    assert retrieved_engine.max_threads == 8
    assert retrieved_engine.precision_mode == "ultra"
    assert retrieved_engine.memory_limit_mb == 8192

    # Non-existent model returns None
    assert service.get_model("missing", WorkspaceAppSettings) is None


def test_sqx_seven_configuration_tabs_models() -> None:
    """Verify strongly-typed Pydantic models for the 7 SQX Configuration tabs."""
    service = SettingsService(SettingsConfig())

    # Tab 1: Global
    glob = GlobalConfigSettings(sounds_off=True, header_custom_text="HaruQuant Pro")
    service.set_model(KEY_CONFIG_GLOBAL, glob)
    retrieved_glob = service.get_model(KEY_CONFIG_GLOBAL, GlobalConfigSettings)
    assert retrieved_glob is not None
    assert retrieved_glob.sounds_off is True
    assert retrieved_glob.header_custom_text == "HaruQuant Pro"
    assert retrieved_glob.default_result_to_display == "Main"

    # Tab 2: CPU
    cpu = CpuConfigSettings(core_usage="custom", custom_cores=16, high_priority=True)
    service.set_model(KEY_CONFIG_CPU, cpu)
    retrieved_cpu = service.get_model(KEY_CONFIG_CPU, CpuConfigSettings)
    assert retrieved_cpu is not None
    assert retrieved_cpu.custom_cores == 16
    assert retrieved_cpu.high_priority is True

    # Tab 3: Performance
    perf = PerformanceConfigSettings(compute_separate_metrics=True)
    service.set_model(KEY_CONFIG_PERFORMANCE, perf)
    retrieved_perf = service.get_model(
        KEY_CONFIG_PERFORMANCE, PerformanceConfigSettings
    )
    assert retrieved_perf is not None
    assert retrieved_perf.compute_separate_metrics is True

    # Tab 4: Memory
    mem = MemoryConfigSettings(memory_limit_gb=16, memory_cleanup=True)
    service.set_model(KEY_CONFIG_MEMORY, mem)
    retrieved_mem = service.get_model(KEY_CONFIG_MEMORY, MemoryConfigSettings)
    assert retrieved_mem is not None
    assert retrieved_mem.memory_limit_gb == 16
    assert retrieved_mem.cleanup_interval_mins == 60

    # Tab 5: Databanks
    db_cfg = DatabanksConfigSettings(databank_sync_interval_mins=5)
    service.set_model(KEY_CONFIG_DATABANKS, db_cfg)
    retrieved_db = service.get_model(KEY_CONFIG_DATABANKS, DatabanksConfigSettings)
    assert retrieved_db is not None
    assert retrieved_db.databank_sync_interval_mins == 5

    # Tab 6: Optimizations
    opt = OptimizationsConfigSettings(dont_store_op_3d_charts_data=False)
    service.set_model(KEY_CONFIG_OPTIMIZATIONS, opt)
    retrieved_opt = service.get_model(
        KEY_CONFIG_OPTIMIZATIONS, OptimizationsConfigSettings
    )
    assert retrieved_opt is not None
    assert retrieved_opt.dont_store_op_3d_charts_data is False

    # Tab 7: Troubleshooting
    trouble = TroubleshootingConfigSettings(debug_level_active=True)
    service.set_model(KEY_CONFIG_TROUBLESHOOTING, trouble)
    retrieved_trouble = service.get_model(
        KEY_CONFIG_TROUBLESHOOTING, TroubleshootingConfigSettings
    )
    assert retrieved_trouble is not None
    assert retrieved_trouble.debug_level_active is True
    assert retrieved_trouble.memory_protection_threshold_pct == 85


def test_user_access_and_password_hashing() -> None:
    """Verify cryptographic password hashing, verification, and UserAccessSettings."""
    # 1. Hashing and verification invariants
    raw_pass = "SuperSecret123!"
    pw_hash, pw_salt = hash_password(raw_pass)
    assert len(pw_hash) == 64  # sha256 hex string length
    assert len(pw_salt) == 32  # 16 bytes hex

    # Correct password verifies True
    assert verify_password(raw_pass, pw_hash, pw_salt) is True

    # Incorrect password verifies False
    assert verify_password("WrongPassword", pw_hash, pw_salt) is False

    # Corrupted hash or salt verifies False gracefully
    assert verify_password(raw_pass, "corrupted_hash", pw_salt) is False
    assert verify_password(raw_pass, pw_hash, "invalid_hex_salt!") is False

    # 2. Service CRUD with UserAccessSettings model
    service = SettingsService(SettingsConfig())
    user_access = UserAccessSettings(
        username="trader_bob",
        password_hash=pw_hash,
        password_salt=pw_salt,
        require_auth=True,
        session_timeout_mins=720,
        allow_remember_me=False,
    )
    service.set_model(KEY_USER_ACCESS, user_access)

    retrieved = service.get_model(KEY_USER_ACCESS, UserAccessSettings)
    assert retrieved is not None
    assert retrieved.username == "trader_bob"
    assert retrieved.password_hash == pw_hash
    assert retrieved.session_timeout_mins == 720
    assert retrieved.allow_remember_me is False


def test_mcp_and_notification_settings() -> None:
    """Verify Model Context Protocol (MCP) and multi-channel notification models."""
    service = SettingsService(SettingsConfig())

    # 1. AI Integration via MCP
    mcp_cfg = McpConnectSettings(
        enabled=True,
        port=5060,
        transport="sse",
        auth_token="mcp-secret-token",
    )
    service.set_model(KEY_CONNECT_MCP, mcp_cfg)
    retrieved_mcp = service.get_model(KEY_CONNECT_MCP, McpConnectSettings)
    assert retrieved_mcp is not None
    assert retrieved_mcp.port == 5060
    assert retrieved_mcp.transport == "sse"
    assert "strategies" in retrieved_mcp.allowed_tools

    # 2. Desktop Notifications
    desktop_cfg = DesktopNotificationSettings(
        enabled=True,
        sound_enabled=False,
        duration_seconds=10,
        min_priority="high",
    )
    service.set_model(KEY_NOTIFY_DESKTOP, desktop_cfg)
    retrieved_desk = service.get_model(KEY_NOTIFY_DESKTOP, DesktopNotificationSettings)
    assert retrieved_desk is not None
    assert retrieved_desk.sound_enabled is False
    assert retrieved_desk.duration_seconds == 10

    # 3. Email (SMTP) Notifications
    email_cfg = EmailNotificationSettings(
        enabled=True,
        smtp_server="smtp.office365.com",
        smtp_port=587,
        use_tls=True,
        from_address="reports@quantfund.com",
        recipient_addresses=["lead@quantfund.com", "ops@quantfund.com"],
    )
    service.set_model(KEY_NOTIFY_EMAIL, email_cfg)
    retrieved_email = service.get_model(KEY_NOTIFY_EMAIL, EmailNotificationSettings)
    assert retrieved_email is not None
    assert retrieved_email.smtp_server == "smtp.office365.com"
    assert len(retrieved_email.recipient_addresses) == 2

    # 4. Telegram Bot Notifications
    telegram_cfg = TelegramNotificationSettings(
        enabled=True,
        bot_token="123456789:ABCdefGHIjklMNOpqr",
        chat_id="-1001234567890",
        parse_mode="HTML",
    )
    service.set_model(KEY_NOTIFY_TELEGRAM, telegram_cfg)
    retrieved_tele = service.get_model(
        KEY_NOTIFY_TELEGRAM, TelegramNotificationSettings
    )
    assert retrieved_tele is not None
    assert retrieved_tele.chat_id == "-1001234567890"


def test_json_preset_file_io_and_user_overrides(tmp_path: Path) -> None:
    """Verify exporting/importing JSON preset files and user override files."""
    service = SettingsService(SettingsConfig())
    service.set_model("app", WorkspaceAppSettings(theme="light"))

    # Export to .json file
    preset_file = tmp_path / "light_theme_preset.json"
    exported_path = service.export_preset_file("light_preset", preset_file)
    assert exported_path.is_file()

    # Import into fresh service
    fresh_service = SettingsService(SettingsConfig())
    fresh_service.import_preset_file(preset_file)
    imported = fresh_service.get_model("app", WorkspaceAppSettings)
    assert imported is not None
    assert imported.theme == "light"

    # Missing file error
    with pytest.raises(SettingsValidationError, match="Preset file not found"):
        fresh_service.import_preset_file(tmp_path / "non_existent.json")

    # User override file (optional)
    override_file = tmp_path / "custom_override.json"
    override_file.write_text('{"app": {"theme": "solarized"}}', encoding="utf-8")
    assert fresh_service.load_user_override_file(override_file) is True

    overridden = fresh_service.get_model("app", WorkspaceAppSettings)
    assert overridden is not None
    assert overridden.theme == "solarized"

    # Non-existent override file returns False gracefully
    assert fresh_service.load_user_override_file(tmp_path / "no_file.json") is False


def test_default_settings_and_presets_paths() -> None:
    """Verify canonical default directories point to data/user/presets."""
    config = SettingsConfig()
    assert config.presets_dir == Path("data/user/presets")
    assert config.settings_dir == Path("data/user/presets")
    assert config.user_override_file is None
    assert DEFAULT_PRESETS_DIR == Path("data/user/presets")
    assert DEFAULT_SETTINGS_DIR == Path("data/user/presets")
    assert DEFAULT_USER_OVERRIDE_FILE is None


def test_broker_and_agent_settings() -> None:
    """Verify MetaTrader 5, cTrader, and multi-provider AI Agent settings."""
    service = SettingsService(SettingsConfig())

    # 1. MetaTrader 5 Configuration
    mt5_cfg = MetaTrader5ConfigSettings(
        enabled=True,
        terminal_path="C:/Trading/MT5/terminal64.exe",
        account_id=12345678,
        server="ICMarkets-SC",
        timeout_ms=30000,
        portable=True,
        use_ticks=True,
    )
    service.set_model(KEY_CONFIG_MT5, mt5_cfg)
    retrieved_mt5 = service.get_model(KEY_CONFIG_MT5, MetaTrader5ConfigSettings)
    assert retrieved_mt5 is not None
    assert retrieved_mt5.enabled is True
    assert retrieved_mt5.account_id == 12345678
    assert retrieved_mt5.server == "ICMarkets-SC"
    assert retrieved_mt5.timeout_ms == 30000
    assert retrieved_mt5.portable is True
    assert retrieved_mt5.use_ticks is True

    # 2. cTrader Open API Configuration
    ctrader_cfg = CTraderConfigSettings(
        enabled=True,
        client_id="cid_app_999",
        client_secret="csec_test_secret",
        environment="live",
        account_id="ct_live_777",
        gateway_port=5035,
    )
    service.set_model(KEY_CONFIG_CTRADER, ctrader_cfg)
    retrieved_ctrader = service.get_model(KEY_CONFIG_CTRADER, CTraderConfigSettings)
    assert retrieved_ctrader is not None
    assert retrieved_ctrader.enabled is True
    assert retrieved_ctrader.client_id == "cid_app_999"
    assert retrieved_ctrader.environment == "live"
    assert retrieved_ctrader.gateway_port == 5035

    # 3. AI Agent Configuration Defaults
    default_agents = AgentsConfigSettings()
    assert default_agents.active_provider == "gemini"
    assert default_agents.gemini.model == "gemini-3.6-flash"
    assert default_agents.openai.model == "gpt-4o"
    assert default_agents.ollama.base_url == "http://127.0.0.1:11434"

    # 4. Custom Multi-Provider Configuration
    custom_agents = AgentsConfigSettings(
        active_provider="ollama",
        gemini=GeminiProviderConfig(
            api_key="ai-test-key",
            model="gemini-2.5-flash",
            temperature=0.4,
        ),
        openai=OpenAiProviderConfig(
            api_key="sk-openai-test",
            model="gpt-4o-mini",
        ),
        ollama=OllamaProviderConfig(
            base_url="http://localhost:11434",
            model="deepseek-r1:14b",
            timeout_seconds=90,
        ),
    )
    service.set_model(KEY_CONFIG_AGENTS, custom_agents)
    retrieved_agents = service.get_model(KEY_CONFIG_AGENTS, AgentsConfigSettings)
    assert retrieved_agents is not None
    assert retrieved_agents.active_provider == "ollama"
    assert retrieved_agents.gemini.model == "gemini-2.5-flash"
    assert retrieved_agents.gemini.temperature == 0.4
    assert retrieved_agents.openai.model == "gpt-4o-mini"
    assert retrieved_agents.ollama.model == "deepseek-r1:14b"
    assert retrieved_agents.ollama.timeout_seconds == 90


def test_export_preset_redacts_secrets() -> None:
    """Verify export_preset redacts secrets and omits user access credentials (FR-WORKSPACE-001)."""
    service = SettingsService(SettingsConfig())

    service.set_model(
        KEY_USER_ACCESS,
        UserAccessSettings(
            username="admin",
            password_hash="hashed_pw",
            password_salt="salt123",
        ),
    )
    service.set_model(
        KEY_NOTIFY_TELEGRAM,
        TelegramNotificationSettings(
            enabled=True,
            bot_token="7364825288:AAGA-secret-token",
            chat_id="5398524142",
        ),
    )

    preset = service.export_preset("safe_preset")
    settings = preset["settings"]

    # user.access must never be exported in portable presets
    assert KEY_USER_ACCESS not in settings

    # Secrets inside settings must be redacted
    tg_settings = settings[KEY_NOTIFY_TELEGRAM]
    assert tg_settings["bot_token"] == "[REDACTED]"
    assert tg_settings["chat_id"] == "5398524142"
