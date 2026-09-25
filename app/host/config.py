"""Host runtime settings: typed models, database loader, and singleton."""

# ruff: noqa: INP001 -- the reset host package has no initializer yet.

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

from app.host.logging import get_logger
from app.persistence.host import (
    HostPersistenceSchemaError,
    HostSettingRecord,
    read_settings,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

logger = get_logger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATABASE_PATH = Path("data") / "database" / "haruquantai.db"


class HostConfigurationError(ValueError):
    """A host runtime setting could not be safely loaded or validated."""


# ---------------------------------------------------------------------------
# Typed configuration sections from table `host_settings`
# ---------------------------------------------------------------------------


class GeneralSettings(BaseModel):
    """General application settings from app.general."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    theme: str = Field(default="dark", strict=True)
    language: str = Field(default="en", strict=True)
    auto_save_interval_s: int = Field(default=60, ge=1, strict=True)
    confirm_on_exit: bool = Field(default=True, strict=True)
    web_server_port: int = Field(default=8080, ge=1, le=65535, strict=True)
    gpu_accelerated: bool = Field(default=True, strict=True)


class CalibrationIndicatorsSettings(BaseModel):
    """Indicator calibration parameters from calibration.indicators."""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True
    )

    qqe_rsi_period: tuple[int, ...] = Field(
        default=(10, 20, 50, 100, 200), alias="QQE.RSIPeriod"
    )
    qqe_sf: tuple[int, ...] = Field(default=(5, 10, 20, 40), alias="QQE.sF")
    qqe_value1: str = Field(default="disabled", alias="QQE.Value1", strict=True)


class GeminiAgentSettings(BaseModel):
    """Gemini agent model provider configuration."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    api_key: str = Field(default="", repr=False, strict=True)
    use_vertex_ai: bool = Field(default=False, strict=True)
    model: str = Field(default="gemini-3.6-flash", strict=True)
    fast_model: str = Field(default="gemini-3.6-flash", strict=True)
    premium_model: str = Field(default="gemini-3.6-pro", strict=True)
    fallback_model: str = Field(default="gemini-3.6-flash", strict=True)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8192, ge=1, strict=True)


class OpenAiAgentSettings(BaseModel):
    """OpenAI agent model provider configuration."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    api_key: str = Field(default="", repr=False, strict=True)
    base_url: str = Field(default="https://api.openai.com/v1", strict=True)
    model: str = Field(default="gpt-5.4-mini", strict=True)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, strict=True)


class OllamaAgentSettings(BaseModel):
    """Local Ollama agent model provider configuration."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    base_url: str = Field(default="http://127.0.0.1:11434", strict=True)
    model: str = Field(default="llama3.1:8b", strict=True)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    timeout_seconds: int = Field(default=120, ge=1, strict=True)


class AgentsSettings(BaseModel):
    """LLM agent orchestration settings from config.agents."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    active_provider: str = Field(default="gemini", strict=True)
    gemini: GeminiAgentSettings = Field(default_factory=GeminiAgentSettings)
    openai: OpenAiAgentSettings = Field(default_factory=OpenAiAgentSettings)
    ollama: OllamaAgentSettings = Field(default_factory=OllamaAgentSettings)
    system_prompt_preset: str = Field(default="quant_researcher", strict=True)
    agent_timeout_seconds: int = Field(default=180, ge=1, strict=True)


class CpuSettings(BaseModel):
    """CPU topology and allocation settings from config.cpu."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    core_usage: str = Field(default="all", strict=True)
    custom_cores: int = Field(default=8, ge=1, strict=True)
    high_priority: bool = Field(default=False, strict=True)
    thread_affinity: bool = Field(default=False, strict=True)


class CtraderSettings(BaseModel):
    """cTrader Open API connection settings from config.ctrader."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, strict=True)
    client_id: str = Field(default="", strict=True)
    client_secret: str = Field(default="", repr=False, strict=True)
    access_token: str = Field(default="", repr=False, strict=True)
    refresh_token: str = Field(default="", repr=False, strict=True)
    redirect_url: str = Field(
        default="https://api.spotware.com/connect/tradingaccounts/token",
        strict=True,
    )
    environment: str = Field(default="demo", strict=True)
    account_id: str = Field(default="", strict=True)
    gateway_host: str = Field(default="live.ctraderapi.com", strict=True)
    gateway_port: int = Field(default=5035, ge=1, le=65535, strict=True)


class DatabanksSettings(BaseModel):
    """Databank synchronization and persistence settings from config.databanks."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    databank_sync_interval_mins: int = Field(default=10, ge=1, strict=True)
    sync_databanks_after_task_done: bool = Field(default=True, strict=True)
    store_chart_data: bool = Field(default=False, strict=True)


class GlobalSettings(BaseModel):
    """Global UI and system options from config.global."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    advanced_file_chooser: bool = Field(default=True, strict=True)
    default_result_to_display: str = Field(default="Main", strict=True)
    footer_custom_text: str = Field(default="", strict=True)
    header_custom_text: str = Field(default="", strict=True)
    language: str = Field(default="en", strict=True)
    show_control_orders: bool = Field(default=False, strict=True)
    sounds_off: bool = Field(default=True, strict=True)
    theme: str = Field(default="dark", strict=True)


class MemorySettings(BaseModel):
    """Memory and garbage collection settings from config.memory."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    gc_type: str = Field(default="ParallelGC", strict=True)
    memory_limit_gb: int = Field(default=8, ge=1, strict=True)
    dont_store_pending_orders: bool = Field(default=True, strict=True)
    memory_cleanup: bool = Field(default=False, strict=True)
    cleanup_interval_mins: int = Field(default=60, ge=1, strict=True)


class Metatrader5Settings(BaseModel):
    """MetaTrader 5 terminal integration settings from config.metatrader5."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, strict=True)
    terminal_path: str = Field(default="", strict=True)
    account_id: int | str = Field(default=0)
    password: str = Field(default="", repr=False, strict=True)
    server: str = Field(default="", strict=True)
    environment: str = Field(default="demo", strict=True)
    timeout_ms: int = Field(default=60000, ge=1, strict=True)
    portable: bool = Field(default=False, strict=True)
    use_ticks: bool = Field(default=True, strict=True)


class OptimizationsSettings(BaseModel):
    """Strategy optimization settings from config.optimizations."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    dont_store_op_3d_charts_data: bool = Field(default=True, strict=True)


class PerformanceSettings(BaseModel):
    """Performance evaluation settings from config.performance."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    compute_pips_metrics: bool = Field(default=False, strict=True)
    compute_pcts_metrics: bool = Field(default=False, strict=True)
    compute_separate_metrics: bool = Field(default=True, strict=True)
    benchmark_time_per_tick_ms: float = Field(default=1.7188e-05, ge=0.0)


class TroubleshootingSettings(BaseModel):
    """Troubleshooting and diagnostic settings from config.troubleshooting."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    gpu_accelerated: bool = Field(default=True, strict=True)
    memory_protection: bool = Field(default=True, strict=True)
    memory_protection_threshold_pct: int = Field(default=85, ge=1, le=100, strict=True)
    debug_level_active: bool = Field(default=False, strict=True)


class McpSettings(BaseModel):
    """Model Context Protocol server settings from connect.mcp."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, strict=True)
    host: str = Field(default="127.0.0.1", strict=True)
    port: int = Field(default=5055, ge=1, le=65535, strict=True)
    transport: str = Field(default="sse", strict=True)
    auth_token: str = Field(default="", repr=False, strict=True)
    allowed_tools: tuple[str, ...] = Field(
        default=("strategies", "projects", "databanks", "backtest", "optimizer")
    )
    max_context_items: int = Field(default=50, ge=1, strict=True)


class BacktestEngineSettings(BaseModel):
    """Backtesting engine tuning from engine.backtest."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    max_threads: int = Field(default=4, ge=1, strict=True)
    memory_limit_mb: int = Field(default=8192, ge=256, strict=True)
    enable_caching: bool = Field(default=True, strict=True)
    precision_mode: str = Field(default="high", strict=True)
    benchmark_time_per_tick_ms: float = Field(default=1.7188e-05, ge=0.0)
    dont_store_pending_orders: bool = Field(default=True, strict=True)
    dont_store_op3d_charts: bool = Field(default=True, strict=True)
    compute_separate_metrics: bool = Field(default=True, strict=True)
    compute_pcts_metrics: bool = Field(default=False, strict=True)
    compute_pips_metrics: bool = Field(default=False, strict=True)
    source_code_constants_params: bool = Field(default=True, strict=True)


class DesktopNotifySettings(BaseModel):
    """Desktop notification settings from notify.desktop."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, strict=True)
    sound_enabled: bool = Field(default=True, strict=True)
    duration_seconds: int = Field(default=5, ge=1, strict=True)
    min_priority: str = Field(default="normal", strict=True)


class EmailNotifySettings(BaseModel):
    """Email notification credentials and delivery settings from notify.email."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, strict=True)
    smtp_server: str = Field(default="smtp.gmail.com", strict=True)
    smtp_port: int = Field(default=587, ge=1, le=65535, strict=True)
    use_ssl: bool = Field(default=False, strict=True)
    use_tls: bool = Field(default=True, strict=True)
    username: str = Field(default="", strict=True)
    password: str = Field(default="", repr=False, strict=True)
    from_address: str = Field(default="", strict=True)
    recipient_addresses: tuple[str, ...] = Field(default_factory=tuple)


class TelegramNotifySettings(BaseModel):
    """Telegram notification bot settings from notify.telegram."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    enabled: bool = Field(default=True, strict=True)
    bot_token: str = Field(default="", repr=False, strict=True)
    chat_id: str = Field(default="", strict=True)
    parse_mode: str = Field(default="HTML", strict=True)
    disable_notification: bool = Field(default=False, strict=True)


class UserAccessSettings(BaseModel):
    """Authentication and operator credentials from user.access."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    username: str = Field(default="admin", strict=True)
    password_hash: str = Field(default="", repr=False, strict=True)
    password_salt: str = Field(default="", repr=False, strict=True)
    require_auth: bool = Field(default=True, strict=True)
    session_timeout_mins: int = Field(default=1440, ge=1, strict=True)
    allow_remember_me: bool = Field(default=True, strict=True)


class WorkspacePathsSettings(BaseModel):
    """User workspaces and presets directory mapping from workspace.paths."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    configs_dir: str = Field(default="data/user/presets", strict=True)
    projects_dir: str = Field(default="data/user/projects", strict=True)
    strategies_dir: str = Field(default="data/user/strategies", strict=True)
    customdata_dir: str = Field(default="data/user/customdata", strict=True)


# ---------------------------------------------------------------------------
# HostSettings Aggregate Model
# ---------------------------------------------------------------------------


class HostSettings(BaseModel):
    """Every host runtime setting: product, networking, layout, and sections.

    The model is pure: construction performs no database, environment, or
    filesystem access. records carries the parsed snapshot of every
    host_settings row (scope -> key -> JSON value) and is hidden from repr
    because stored records include credential fields. The directory layout
    is derived from data_dir; ensure_directories is the only side-effecting
    operation and is never invoked at import time.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    # Product metadata
    product_name: str = Field(default="HaruQuantAI", strict=True)
    app_version: str = Field(default="2.1.0", strict=True)

    # Product architecture defaults; the authoritative bind is host/port
    control_host: str = Field(default="127.0.0.1", strict=True)
    control_port: int = Field(default=5050, ge=1, le=65535, strict=True)
    api_host: str = Field(default="127.0.0.1", strict=True)
    api_port: int = Field(default=8080, ge=1, le=65535, strict=True)

    # Effective bind configuration (B02)
    host: str = Field(default="127.0.0.1", strict=True)
    port: int = Field(default=8000, ge=1, le=65535, strict=True)
    gpu_accelerated: bool = Field(default=True, strict=True)

    # Runtime tuning
    min_memory_gb: int = Field(default=4, strict=True)
    prefer_ipv4: bool = Field(default=True, strict=True)
    use_system_proxies: bool = Field(default=True, strict=True)
    parallel_gc_enabled: bool = Field(default=True, strict=True)
    disable_attach_mechanism: bool = Field(default=True, strict=True)

    # Layout root and the boot-time snapshot of every stored record
    data_dir: Path = Path("data")
    records: Mapping[str, Mapping[str, object]] = Field(
        default_factory=dict, repr=False
    )

    # Concrete typed settings sections populated from table host_settings
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    calibration: CalibrationIndicatorsSettings = Field(
        default_factory=CalibrationIndicatorsSettings
    )
    agents: AgentsSettings = Field(default_factory=AgentsSettings)
    cpu: CpuSettings = Field(default_factory=CpuSettings)
    ctrader: CtraderSettings = Field(default_factory=CtraderSettings)
    databanks: DatabanksSettings = Field(default_factory=DatabanksSettings)
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    metatrader5: Metatrader5Settings = Field(default_factory=Metatrader5Settings)
    optimizations: OptimizationsSettings = Field(default_factory=OptimizationsSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    troubleshooting: TroubleshootingSettings = Field(
        default_factory=TroubleshootingSettings
    )
    mcp: McpSettings = Field(default_factory=McpSettings)
    backtest: BacktestEngineSettings = Field(default_factory=BacktestEngineSettings)
    notify_desktop: DesktopNotifySettings = Field(default_factory=DesktopNotifySettings)
    notify_email: EmailNotifySettings = Field(default_factory=EmailNotifySettings)
    notify_telegram: TelegramNotifySettings = Field(
        default_factory=TelegramNotifySettings
    )
    user_access: UserAccessSettings = Field(default_factory=UserAccessSettings)
    workspace_paths: WorkspacePathsSettings = Field(
        default_factory=WorkspacePathsSettings
    )
    revision: int = Field(default=1, strict=True)

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        """Require a nonblank bind host."""
        host = value.strip()
        if not host:
            raise ValueError("host must not be empty")
        return host

    @field_validator("data_dir", mode="before")
    @classmethod
    def validate_data_dir(cls, value: object) -> object:
        """Reject blank text before Pydantic converts it to a path."""
        if isinstance(value, (str, Path)) and not str(value).strip():
            raise ValueError("data directory must not be empty")
        return value

    @property
    def database_path(self) -> Path:
        """Return the host database path without accessing the filesystem."""
        return self.data_dir / "database" / "haruquantai.db"

    @property
    def database_dir(self) -> Path:
        """Return the database directory derived from the data directory."""
        return self.data_dir / "database"

    @property
    def log_dir(self) -> Path:
        """Return the log directory, matching the telemetry default."""
        return self.data_dir / "logs"

    @property
    def market_dir(self) -> Path:
        """Return the market data directory derived from the data directory."""
        return self.data_dir / "market"

    @property
    def strategies_dir(self) -> Path:
        """Return the strategies directory derived from the data directory."""
        return self.data_dir / "strategies"

    @property
    def databank_dir(self) -> Path:
        """Return the databank directory derived from the data directory."""
        return self.data_dir / "databank"

    @property
    def projects_dir(self) -> Path:
        """Return the projects directory derived from the data directory."""
        return self.data_dir / "projects"

    @property
    def ui_dir(self) -> Path:
        """Return the bundled UI directory."""
        return ROOT_DIR / "app" / "ui"

    @property
    def plugins_dir(self) -> Path:
        """Return the repository plugins directory."""
        return ROOT_DIR / "plugins"

    def ensure_directories(self) -> None:
        """Create the runtime data tree under the data directory.

        Only data-owned directories are created; repository directories
        such as ui_dir and plugins_dir are never touched.
        """
        for directory in (
            self.data_dir,
            self.database_dir,
            self.log_dir,
            self.market_dir,
            self.strategies_dir,
            self.databank_dir,
            self.projects_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Strict JSON parser helpers
# ---------------------------------------------------------------------------


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant {value}")


_SETTINGS_SECTION_MAP: Mapping[tuple[str, str], tuple[str, type[BaseModel]]] = {
    ("application", "app.general"): ("general", GeneralSettings),
    ("application", "calibration.indicators"): (
        "calibration",
        CalibrationIndicatorsSettings,
    ),
    ("application", "config.agents"): ("agents", AgentsSettings),
    ("application", "config.cpu"): ("cpu", CpuSettings),
    ("application", "config.ctrader"): ("ctrader", CtraderSettings),
    ("application", "config.databanks"): ("databanks", DatabanksSettings),
    ("application", "config.global"): ("global_settings", GlobalSettings),
    ("application", "config.memory"): ("memory", MemorySettings),
    ("application", "config.metatrader5"): ("metatrader5", Metatrader5Settings),
    ("application", "config.optimizations"): (
        "optimizations",
        OptimizationsSettings,
    ),
    ("application", "config.performance"): ("performance", PerformanceSettings),
    ("application", "config.troubleshooting"): (
        "troubleshooting",
        TroubleshootingSettings,
    ),
    ("application", "connect.mcp"): ("mcp", McpSettings),
    ("application", "engine.backtest"): ("backtest", BacktestEngineSettings),
    ("application", "notify.desktop"): ("notify_desktop", DesktopNotifySettings),
    ("application", "notify.email"): ("notify_email", EmailNotifySettings),
    ("application", "notify.telegram"): ("notify_telegram", TelegramNotifySettings),
    ("application", "user.access"): ("user_access", UserAccessSettings),
    ("application", "workspace.paths"): (
        "workspace_paths",
        WorkspacePathsSettings,
    ),
}


# ---------------------------------------------------------------------------
# Database settings loader (uses app.persistence.host exclusively)
# ---------------------------------------------------------------------------


def _parse_row_document(row: HostSettingRecord) -> object:
    """Parse and validate JSON payload from a single host_settings row."""
    if row.schema_version != 1:
        raise HostConfigurationError("Incompatible host settings schema version")
    try:
        return json.loads(
            row.value_json,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (TypeError, ValueError) as error:
        raise HostConfigurationError("Malformed host settings record") from error


def _populate_section(
    scope: str,
    key: str,
    document: object,
    values: dict[str, object],
) -> None:
    """Populate typed section models from a parsed document."""
    target = _SETTINGS_SECTION_MAP.get((scope, key))
    if target is not None:
        field_name, model_cls = target
        if not isinstance(document, dict):
            raise HostConfigurationError(
                f"Invalid {key} settings record: expected object"
            )
        try:
            values[field_name] = model_cls.model_validate(document)
        except ValidationError as error:
            raise HostConfigurationError(
                f"Failed validating {key} settings: {error}"
            ) from error
    elif (scope, key) == ("host", "__revision__") and isinstance(document, int):
        values["revision"] = document


def load_host_settings(
    database_path: Path | None = None,
    *,
    data_dir: Path | None = None,
) -> HostSettings:
    """Load settings from the host database into a typed HostSettings model.

    Database access is routed exclusively through
    ``app.persistence.host.read_settings``. If the database file does not
    exist, a default HostSettings instance is returned.
    """
    effective_data_dir = data_dir or Path("data")
    target_db = database_path or (effective_data_dir / "database" / "haruquantai.db")

    if not target_db.exists():
        return HostSettings(data_dir=effective_data_dir)

    if not target_db.is_file():
        raise HostConfigurationError("Host database path is not a file")

    try:
        rows = read_settings(target_db)
    except HostPersistenceSchemaError as error:
        raise HostConfigurationError("Incompatible host_settings schema") from error

    records: dict[str, dict[str, object]] = {}
    values: dict[str, object] = {"data_dir": effective_data_dir}

    for row in rows:
        document = _parse_row_document(row)
        records.setdefault(row.scope, {})[row.key] = document
        _populate_section(row.scope, row.key, document, values)

    values["records"] = records

    # Derive bind overrides from app.general if explicitly stored
    general_doc = records.get("application", {}).get("app.general")
    if isinstance(general_doc, dict):
        if "web_server_port" in general_doc:
            values["port"] = general_doc["web_server_port"]
        if "gpu_accelerated" in general_doc:
            values["gpu_accelerated"] = general_doc["gpu_accelerated"]

    try:
        return HostSettings.model_validate(values)
    except ValidationError as error:
        raise HostConfigurationError(
            f"Failed constructing HostSettings: {error}"
        ) from error


# ---------------------------------------------------------------------------
# Global singleton configuration instance
# ---------------------------------------------------------------------------


def _initialize_settings() -> HostSettings:
    """Populate default settings, auto-loading from database if it exists."""
    default_db = Path("data") / "database" / "haruquantai.db"
    if default_db.is_file():
        try:
            return load_host_settings(default_db)
        except HostConfigurationError, OSError:
            return HostSettings()
    return HostSettings()


settings = _initialize_settings()
