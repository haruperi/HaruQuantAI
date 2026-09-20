"""Scoped Pydantic settings and snapshots feature module.

Purpose:
    Provides hierarchical settings management, validation, snapshots, and
    JSON preset interchange for HaruQuantAI with optional SQLite persistence.

Key capabilities:
    * Hierarchical resolution order: run > project > application.
    * JSON preset export and import.
    * Atomic SQLite WAL backing when `persistence.workspace@1` is available.
    * In-memory isolated fallback when running unpersisted.

Python API usage:
    settings = ctx.require(WORKSPACE_SETTINGS)
    snapshot = settings.resolve_effective(("engine.max_threads",))

CLI usage:
    uv run python -m tests.examples.01_workspace
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar, override

from pydantic import BaseModel, Field

from app.contracts.workspace import (
    WORKSPACE_PERSISTENCE,
    WORKSPACE_SETTINGS,
    SettingsEntry,
    SettingsScope,
    SettingsSnapshot,
    SettingsValidationError,
    WorkspacePersistenceService,
)
from app.contracts.workspace import (
    SettingsService as ISettingsService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


T = TypeVar("T", bound=BaseModel)

# Canonical Keys for 7 StrategyQuant X Configuration Tabs
KEY_CONFIG_GLOBAL: str = "config.global"
KEY_CONFIG_CPU: str = "config.cpu"
KEY_CONFIG_PERFORMANCE: str = "config.performance"
KEY_CONFIG_MEMORY: str = "config.memory"
KEY_CONFIG_DATABANKS: str = "config.databanks"
KEY_CONFIG_OPTIMIZATIONS: str = "config.optimizations"
KEY_CONFIG_TROUBLESHOOTING: str = "config.troubleshooting"

# Canonical Keys for Companion System & Integration Settings
KEY_USER_ACCESS: str = "user.access"
KEY_CONNECT_MCP: str = "connect.mcp"
KEY_NOTIFY_DESKTOP: str = "notify.desktop"
KEY_NOTIFY_EMAIL: str = "notify.email"
KEY_NOTIFY_TELEGRAM: str = "notify.telegram"

# Canonical Keys for External Brokers & AI Agent Integration
KEY_CONFIG_MT5: str = "config.metatrader5"
KEY_CONFIG_CTRADER: str = "config.ctrader"
KEY_CONFIG_AGENTS: str = "config.agents"


class WorkspaceAppSettings(BaseModel):
    """Application-wide environment and UI settings."""

    theme: str = Field(default="dark", description="UI theme skin")
    language: str = Field(default="en", description="Localization language")
    auto_save_interval_s: int = Field(default=60, ge=5, le=3600)
    confirm_on_exit: bool = Field(default=True)


class BacktestEngineSettings(BaseModel):
    """Quantitative backtest execution settings."""

    max_threads: int = Field(default=4, ge=1)
    memory_limit_mb: int = Field(default=8192, ge=512)
    enable_caching: bool = Field(default=True)
    precision_mode: str = Field(default="high")


class GlobalConfigSettings(BaseModel):
    """Global user interface and environment configuration (Tab 1)."""

    sounds_off: bool = Field(default=False, description="Mute notification sounds")
    advanced_file_chooser: bool = Field(
        default=True, description="Persist view type and sorting in file dialogs"
    )
    show_control_orders: bool = Field(
        default=False, description="Show control orders in netting engines"
    )
    header_custom_text: str = Field(
        default="", description="Custom title text in window header"
    )
    footer_custom_text: str = Field(
        default="", description="Custom status text in window footer"
    )
    default_result_to_display: str = Field(
        default="Main", description="Default databank result tab to display"
    )
    language: str = Field(default="en", description="Application locale language")
    theme: str = Field(default="dark", description="Visual theme skin")


class CpuConfigSettings(BaseModel):
    """CPU allocation and process priority configuration (Tab 2)."""

    core_usage: str = Field(
        default="all", description="CPU allocation mode ('all' or 'custom')"
    )
    custom_cores: int = Field(
        default=8, ge=1, le=256, description="Worker core count when custom"
    )
    high_priority: bool = Field(
        default=False, description="Execute engine tasks with high OS process priority"
    )
    thread_affinity: bool = Field(
        default=False, description="Bind worker threads to specific physical CPU cores"
    )


class PerformanceConfigSettings(BaseModel):
    """Execution performance and metric calculation configuration (Tab 3)."""

    compute_pips_metrics: bool = Field(
        default=False, description="Calculate trade statistics in pips"
    )
    compute_pcts_metrics: bool = Field(
        default=False, description="Calculate trade statistics in percentages"
    )
    compute_separate_metrics: bool = Field(
        default=True, description="Compute separate long and short sub-metrics"
    )
    benchmark_time_per_tick_ms: float = Field(
        default=1.7188e-05, ge=0.0, description="Reference benchmark timing per tick"
    )


class MemoryConfigSettings(BaseModel):
    """Memory ceiling and garbage collection configuration (Tab 4)."""

    gc_type: str = Field(
        default="ParallelGC", description="Garbage collection strategy reference"
    )
    memory_limit_gb: int = Field(
        default=8,
        ge=1,
        le=1024,
        description="Maximum heap/RAM allocation ceiling in GB",
    )
    dont_store_pending_orders: bool = Field(
        default=True, description="Discard non-executed pending orders to save RAM"
    )
    memory_cleanup: bool = Field(
        default=False, description="Perform periodic forced garbage collection"
    )
    cleanup_interval_mins: int = Field(
        default=60, ge=1, le=1440, description="Forced cleanup interval in minutes"
    )


class DatabanksConfigSettings(BaseModel):
    """Databank synchronization and persistence configuration (Tab 5)."""

    databank_sync_interval_mins: int = Field(
        default=10, ge=0, le=1440, description="Auto-sync interval in minutes"
    )
    sync_databanks_after_task_done: bool = Field(
        default=True, description="Flush strategies to disk immediately on task finish"
    )
    store_chart_data: bool = Field(
        default=False, description="Save full chart OHLCV data within strategy archives"
    )


class OptimizationsConfigSettings(BaseModel):
    """Optimization profile and surface calculation configuration (Tab 6)."""

    dont_store_op_3d_charts_data: bool = Field(
        default=True,
        description="Skip 3D optimization surface cache to conserve memory",
    )


class TroubleshootingConfigSettings(BaseModel):
    """Diagnostics, protection, and display troubleshooting configuration (Tab 7)."""

    gpu_accelerated: bool = Field(
        default=True, description="Enable hardware acceleration for user interface"
    )
    memory_protection: bool = Field(
        default=True,
        description="Halt background pipelines when memory exceeds threshold",
    )
    memory_protection_threshold_pct: int = Field(
        default=85, ge=50, le=99, description="Memory protection trigger percentage"
    )
    debug_level_active: bool = Field(
        default=False, description="Enable detailed debug-level logging"
    )


def hash_password(
    password: str,
    salt: str | None = None,
    iterations: int = 100_000,
) -> tuple[str, str]:
    """Hash a password securely using PBKDF2-HMAC-SHA256.

    Args:
        password: Plaintext password.
        salt: Optional hexadecimal salt string (generated if None).
        iterations: Number of PBKDF2 iterations.

    Returns:
        Tuple of (hex_hash, hex_salt).
    """
    effective_salt = salt if salt is not None else secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(effective_salt),
        iterations,
    )
    return derived.hex(), effective_salt


def verify_password(
    password: str,
    password_hash: str,
    salt: str,
    iterations: int = 100_000,
) -> bool:
    """Verify a plaintext password against a stored PBKDF2-HMAC-SHA256 hash.

    Args:
        password: Plaintext candidate password.
        password_hash: Stored hexadecimal hash.
        salt: Stored hexadecimal salt.
        iterations: Number of PBKDF2 iterations.

    Returns:
        True if candidate password matches hash, False otherwise.
    """
    try:
        candidate_hash, _ = hash_password(password, salt=salt, iterations=iterations)
        return hmac.compare_digest(candidate_hash, password_hash)
    except ValueError, TypeError:
        return False


class UserAccessSettings(BaseModel):
    """Web dashboard and API access authentication configuration."""

    username: str = Field(default="admin", description="Login username")
    password_hash: str = Field(
        default="", description="Cryptographic PBKDF2-HMAC-SHA256 password hash"
    )
    password_salt: str = Field(
        default="", description="Cryptographic salt for password hashing"
    )
    require_auth: bool = Field(
        default=True, description="Enforce authentication on web dashboard and API"
    )
    session_timeout_mins: int = Field(
        default=1440, ge=5, le=43200, description="Session expiration in minutes"
    )
    allow_remember_me: bool = Field(
        default=True, description="Allow persistent login sessions"
    )


class McpConnectSettings(BaseModel):
    """AI Integration via Model Context Protocol (MCP) server configuration."""

    enabled: bool = Field(
        default=True, description="Enable Model Context Protocol server"
    )
    host: str = Field(default="127.0.0.1", description="MCP server binding host")
    port: int = Field(
        default=5055, ge=1024, le=65535, description="MCP server listening port"
    )
    transport: str = Field(
        default="sse", description="MCP transport protocol ('sse', 'stdio', 'http')"
    )
    auth_token: str = Field(
        default="", description="Bearer token for MCP authentication"
    )
    allowed_tools: list[str] = Field(
        default_factory=lambda: [
            "strategies",
            "projects",
            "databanks",
            "backtest",
            "optimizer",
        ],
        description="Exposed tool modules accessible to AI agents",
    )
    max_context_items: int = Field(
        default=50, ge=1, le=500, description="Max strategies/items per MCP query"
    )


class DesktopNotificationSettings(BaseModel):
    """Desktop push notification and sound chime configuration."""

    enabled: bool = Field(
        default=True, description="Enable desktop notification popups"
    )
    sound_enabled: bool = Field(
        default=True, description="Play audio chime alongside desktop notifications"
    )
    duration_seconds: int = Field(
        default=5, ge=1, le=60, description="Notification popup display duration"
    )
    min_priority: str = Field(
        default="normal", description="Minimum priority threshold"
    )


class EmailNotificationSettings(BaseModel):
    """Outbound SMTP email dispatch configuration."""

    enabled: bool = Field(
        default=False, description="Enable email alerts for completed jobs or warnings"
    )
    smtp_server: str = Field(
        default="smtp.gmail.com", description="Outbound SMTP server hostname"
    )
    smtp_port: int = Field(
        default=587, ge=1, le=65535, description="SMTP server port (e.g. 587 or 465)"
    )
    use_ssl: bool = Field(
        default=False, description="Connect using direct SSL/TLS wrapper"
    )
    use_tls: bool = Field(default=True, description="Upgrade connection using STARTTLS")
    username: str = Field(
        default="", description="SMTP account username or login address"
    )
    password: str = Field(
        default="", description="SMTP account password or application password"
    )
    from_address: str = Field(
        default="alerts@haruquant.ai", description="Sender email address in header"
    )
    recipient_addresses: list[str] = Field(
        default_factory=list, description="Default recipient email addresses"
    )


class TelegramNotificationSettings(BaseModel):
    """Telegram bot alert dispatch configuration."""

    enabled: bool = Field(
        default=False, description="Enable Telegram bot notifications"
    )
    bot_token: str = Field(
        default="", description="Telegram Bot API token issued by @BotFather"
    )
    chat_id: str = Field(default="", description="Target Telegram chat or channel ID")
    parse_mode: str = Field(
        default="HTML", description="Telegram text parse mode ('HTML' or 'MarkdownV2')"
    )
    disable_notification: bool = Field(
        default=False, description="Send silent messages without sound"
    )


class MetaTrader5ConfigSettings(BaseModel):
    """MetaTrader 5 broker terminal and IPC bridge configuration."""

    enabled: bool = Field(
        default=False, description="Enable MetaTrader 5 adapter connection"
    )
    terminal_path: str = Field(
        default="", description="Path to terminal64.exe (blank for auto-detect)"
    )
    account_id: int | None = Field(
        default=None, description="MetaTrader 5 trading account identifier"
    )
    password: str = Field(
        default="", description="Trading account password or auth token"
    )
    server: str = Field(
        default="MetaQuotes-Demo", description="Broker trade server name"
    )
    environment: str = Field(
        default="demo", description="Trading environment ('demo' or 'live')"
    )
    timeout_ms: int = Field(
        default=60_000,
        ge=1000,
        le=300_000,
        description="IPC connection timeout in milliseconds",
    )
    portable: bool = Field(
        default=False, description="Launch terminal in portable mode"
    )
    use_ticks: bool = Field(
        default=True,
        description="Enable tick-level execution and order book subscriptions",
    )


class CTraderConfigSettings(BaseModel):
    """Spotware cTrader Open API and FIX trading connection configuration."""

    enabled: bool = Field(
        default=False, description="Enable cTrader Open API connection"
    )
    client_id: str = Field(
        default="", description="cTrader Open API application client ID"
    )
    client_secret: str = Field(
        default="", description="cTrader Open API application client secret"
    )
    access_token: str = Field(default="", description="OAuth2 account access token")
    refresh_token: str = Field(
        default="", description="OAuth2 refresh token for session maintenance"
    )
    redirect_url: str = Field(
        default="https://api.spotware.com/connect/tradingaccounts/token",
        description="cTrader OAuth2 redirect URI",
    )
    environment: str = Field(
        default="demo", description="cTrader environment ('demo' or 'live')"
    )
    account_id: str = Field(default="", description="Target cTrader trading account ID")
    gateway_host: str = Field(
        default="live.ctraderapi.com", description="cTrader protobuf gateway host"
    )
    gateway_port: int = Field(
        default=5035, ge=1024, le=65535, description="cTrader gateway SSL/TLS port"
    )


class GeminiProviderConfig(BaseModel):
    """Google Gemini AI model provider configuration."""

    api_key: str = Field(default="", description="Google AI Studio or Vertex API key")
    use_vertex_ai: bool = Field(
        default=False, description="Use Vertex AI instead of Google AI Studio"
    )
    model: str = Field(
        default="gemini-3.6-flash", description="Default Gemini model name"
    )
    fast_model: str = Field(
        default="gemini-3.6-flash", description="Fast inference model tier"
    )
    premium_model: str = Field(
        default="gemini-3.6-pro", description="Premium reasoning model tier"
    )
    fallback_model: str = Field(
        default="gemini-3.6-flash", description="Fallback inference model tier"
    )
    temperature: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=8192, ge=128, le=65536, description="Maximum token generation limit"
    )


class OpenAiProviderConfig(BaseModel):
    """OpenAI compatible AI model provider configuration."""

    api_key: str = Field(default="", description="OpenAI API secret key")
    base_url: str = Field(
        default="https://api.openai.com/v1", description="API endpoint base URL"
    )
    model: str = Field(default="gpt-4o", description="Default OpenAI model name")
    temperature: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=4096, ge=128, le=32768, description="Maximum token generation limit"
    )


class OllamaProviderConfig(BaseModel):
    """Local Ollama AI model provider configuration."""

    base_url: str = Field(
        default="http://127.0.0.1:11434", description="Local Ollama instance URL"
    )
    model: str = Field(default="llama3.1:8b", description="Local LLM model tag")
    temperature: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Sampling temperature"
    )
    timeout_seconds: int = Field(
        default=120, ge=5, le=600, description="HTTP request timeout in seconds"
    )


class AgentsConfigSettings(BaseModel):
    """Multi-provider AI agent synthesis and reasoning configuration."""

    active_provider: str = Field(
        default="gemini",
        description="Active AI provider ('gemini', 'openai', 'ollama')",
    )
    gemini: GeminiProviderConfig = Field(
        default_factory=GeminiProviderConfig,
        description="Google Gemini provider configuration",
    )
    openai: OpenAiProviderConfig = Field(
        default_factory=OpenAiProviderConfig,
        description="OpenAI provider configuration",
    )
    ollama: OllamaProviderConfig = Field(
        default_factory=OllamaProviderConfig,
        description="Local Ollama provider configuration",
    )
    system_prompt_preset: str = Field(
        default="quant_researcher",
        description="Default agent persona system prompt preset",
    )
    agent_timeout_seconds: int = Field(
        default=180,
        ge=10,
        le=1800,
        description="Maximum timeout for agentic reasoning cycles",
    )


DEFAULT_PRESETS_DIR: Path = Path("data/user/presets")
DEFAULT_SETTINGS_DIR: Path = Path("data/user/presets")
DEFAULT_USER_OVERRIDE_FILE: Path | None = None


@dataclass(frozen=True, slots=True)
class SettingsConfig:
    """Runtime configuration for settings service."""

    default_scope: str = SettingsScope.APPLICATION.value
    allow_preset_override: bool = True
    presets_dir: Path = DEFAULT_PRESETS_DIR
    settings_dir: Path = DEFAULT_PRESETS_DIR
    user_override_file: Path | None = DEFAULT_USER_OVERRIDE_FILE

    def __post_init__(self) -> None:
        """Validate settings configuration."""
        if hasattr(self.default_scope, "value"):
            object.__setattr__(self, "default_scope", str(self.default_scope.value))
        if not self.default_scope or not self.default_scope.strip():
            msg = "default_scope cannot be empty"
            raise ValueError(msg)


_SECRET_KEYS: frozenset[str] = frozenset(
    {"token", "secret", "password", "key", "api_key", "auth"}
)


def _sanitize_preset_payload(data: Any) -> Any:
    """Recursively redact secrets and credentials from exported presets."""
    if isinstance(data, dict):
        sanitized: dict[str, Any] = {}
        for k, v in data.items():
            is_secret = any(term in k.lower() for term in _SECRET_KEYS)
            if is_secret and isinstance(v, str) and v:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = _sanitize_preset_payload(v)
        return sanitized
    if isinstance(data, list):
        return [_sanitize_preset_payload(item) for item in data]
    return data


class SettingsService(ISettingsService):
    """Implement scoped settings management with hierarchical resolution."""

    def __init__(
        self,
        config: SettingsConfig,
        persistence: WorkspacePersistenceService | None = None,
    ) -> None:
        """Initialize settings service with in-memory cache and optional database.

        Args:
            config: Runtime settings configuration.
            persistence: Optional database persistence capability.
        """
        self._config = config
        self._persistence = persistence
        # In-memory storage: (scope, key) -> SettingsEntry
        self._store: dict[tuple[str, str], SettingsEntry] = {}

        if self._persistence is not None:
            self._load_from_database()

    def _load_from_database(self) -> None:
        """Hydrate in-memory cache from the SQLite persistence table."""
        if self._persistence is None:
            return
        rows = self._persistence.load_all_settings()
        for scope, key, val_json, ver, updated_str in rows:
            try:
                val = json.loads(val_json)
                updated_at = datetime.fromisoformat(updated_str)
                self._store[(scope, key)] = SettingsEntry(
                    scope=scope,
                    key=key,
                    value=val,
                    schema_version=ver,
                    updated_at_utc=updated_at,
                )
            except (json.JSONDecodeError, ValueError) as err:
                logger.warning(
                    "settings_load_entry_error",
                    scope=scope,
                    key=key,
                    error=str(err),
                )

    @override
    def get_setting(
        self, key: str, scope: str = SettingsScope.APPLICATION
    ) -> dict[str, Any] | None:
        """Retrieve setting value by scope and key.

        Args:
            key: Unique key.
            scope: Target scope.

        Returns:
            Setting value dictionary or None.
        """
        entry = self._store.get((scope, key))
        return entry.value if entry else None

    @override
    def set_setting(
        self,
        key: str,
        value: dict[str, Any],
        scope: str = SettingsScope.APPLICATION,
        schema_version: int = 1,
    ) -> None:
        """Store or update setting value.

        Args:
            key: Setting key.
            value: Setting dictionary.
            scope: Target scope.
            schema_version: Schema version integer.

        Raises:
            SettingsValidationError: If inputs are invalid.
        """
        if not key or not key.strip():
            msg = "Setting key cannot be empty"
            raise SettingsValidationError(msg)

        now = datetime.now(UTC)
        entry = SettingsEntry(
            scope=scope,
            key=key,
            value=value,
            schema_version=schema_version,
            updated_at_utc=now,
        )
        self._store[(scope, key)] = entry

        if self._persistence is not None:
            self._persistence.save_setting(
                scope=scope,
                key=key,
                value_json=json.dumps(value),
                schema_version=schema_version,
                updated_at_utc=now.isoformat(),
            )

    @override
    def resolve_effective(
        self,
        keys: tuple[str, ...],
        project_id: str | None = None,
        run_id: str | None = None,
    ) -> SettingsSnapshot:
        """Resolve settings with precedence: run > project > application.

        Args:
            keys: Tuple of setting keys.
            project_id: Optional project scope identifier.
            run_id: Optional run scope identifier.

        Returns:
            SettingsSnapshot containing resolved entries.
        """
        now = datetime.now(UTC)
        resolved: list[SettingsEntry] = []

        for key in keys:
            entry: SettingsEntry | None = None

            # 1. Check run scope
            if run_id:
                entry = self._store.get((f"run:{run_id}", key))

            # 2. Check project scope
            if entry is None and project_id:
                entry = self._store.get((f"project:{project_id}", key))

            # 3. Check application scope
            if entry is None:
                entry = self._store.get((SettingsScope.APPLICATION, key))

            if entry is not None:
                resolved.append(entry)

        return SettingsSnapshot(entries=tuple(resolved), resolved_at_utc=now)

    @override
    def export_preset(self, preset_name: str) -> dict[str, Any]:
        """Export current settings as a JSON preset dictionary with secrets redacted.

        Args:
            preset_name: Target preset name.

        Returns:
            Preset payload dictionary with credentials redacted.
        """
        app_settings = {
            k: _sanitize_preset_payload(entry.value)
            for (scope, k), entry in self._store.items()
            if scope == SettingsScope.APPLICATION and k != KEY_USER_ACCESS
        }
        return {
            "preset_name": preset_name,
            "exported_at_utc": datetime.now(UTC).isoformat(),
            "settings": app_settings,
        }

    @override
    def import_preset(self, preset_data: dict[str, Any]) -> None:
        """Import a JSON preset into application settings.

        Args:
            preset_data: Validated preset payload dictionary.

        Raises:
            SettingsValidationError: If preset payload format is invalid.
        """
        if "settings" not in preset_data or not isinstance(
            preset_data["settings"], dict
        ):
            msg = "Invalid preset data: missing 'settings' object"
            raise SettingsValidationError(msg)

        for key, val in preset_data["settings"].items():
            if isinstance(val, dict):
                self.set_setting(key=key, value=val, scope=SettingsScope.APPLICATION)

    @override
    def get_model(
        self,
        key: str,
        model_cls: type[T],
        scope: str = SettingsScope.APPLICATION,
    ) -> T | None:
        """Retrieve and parse setting value using a strongly-typed Pydantic model.

        Args:
            key: Setting identifier.
            model_cls: Target Pydantic model class.
            scope: Target hierarchy scope.

        Returns:
            Validated Pydantic model instance or None if not set.
        """
        data = self.get_setting(key, scope=scope)
        if data is None:
            return None
        return model_cls.model_validate(data)

    @override
    def set_model(
        self,
        key: str,
        model: BaseModel,
        scope: str = SettingsScope.APPLICATION,
        schema_version: int = 1,
    ) -> None:
        """Store a strongly-typed Pydantic model into the settings store.

        Args:
            key: Setting identifier.
            model: Pydantic model instance.
            scope: Target hierarchy scope.
            schema_version: Version of the payload schema.
        """
        self.set_setting(
            key=key,
            value=model.model_dump(mode="json"),
            scope=scope,
            schema_version=schema_version,
        )

    @override
    def export_preset_file(
        self, preset_name: str, file_path: Path | str | None = None
    ) -> Path:
        """Export current settings to a JSON preset file on disk.

        Args:
            preset_name: Preset label.
            file_path: Output file path
                (defaults to config.presets_dir / '<preset_name>.json').

        Returns:
            Resolved Path of the written file.
        """
        path = (
            Path(file_path)
            if file_path is not None
            else Path(self._config.presets_dir) / f"{preset_name}.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.export_preset(preset_name)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("preset_file_exported", preset_name=preset_name, path=str(path))
        return path

    @override
    def import_preset_file(self, file_path: Path | str) -> None:
        """Import settings from a JSON preset file on disk.

        Args:
            file_path: Path to existing preset JSON file.

        Raises:
            SettingsValidationError: If file is missing or invalid JSON.
        """
        path = Path(file_path)
        if not path.is_file():
            msg = f"Preset file not found: {path}"
            raise SettingsValidationError(msg)
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as err:
            msg = f"Failed to read preset file: {err}"
            raise SettingsValidationError(msg) from err
        self.import_preset(content)

    @override
    def load_user_override_file(self, file_path: Path | str | None = None) -> bool:
        """Optionally load user overrides from a JSON file if provided.

        Args:
            file_path: Optional path to user override file.

        Returns:
            True if file existed and was loaded; False otherwise.
        """
        target = file_path or self._config.user_override_file
        if target is None:
            return False
        path = Path(target)
        if not path.is_file():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                items = data.get("settings", data) if "settings" in data else data
                if isinstance(items, dict):
                    for k, v in items.items():
                        if isinstance(v, dict):
                            self.set_setting(k, v, scope=SettingsScope.APPLICATION)
                    logger.info("user_override_file_loaded", path=str(path))
                    return True
        except json.JSONDecodeError, OSError:
            logger.warning("failed_to_load_user_override_file", path=str(path))
        return False


SPEC: FeatureSpec = FeatureSpec(
    name="workspace.settings",
    provides=frozenset({WORKSPACE_SETTINGS}),
    requires=frozenset(),
    optional=frozenset({WORKSPACE_PERSISTENCE}),
    description="Scoped settings with SQLite and JSON persistence.",
)


class SettingsFeature:
    """Lifecycle-managed runtime feature providing hierarchical scoped settings.

    Mounts SettingsService, connects to persistence for SQLite WAL storage,
    optionally loads user override JSON presets, and publishes WORKSPACE_SETTINGS.
    """

    def __init__(self, config: SettingsConfig | None = None) -> None:
        """Initialize settings feature with storage paths and scoping config.

        Args:
            config: Settings configuration specifying directories, scopes, and
                overrides. If None, default SettingsConfig is used.
        """
        self._config = config or SettingsConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable specification declaring capabilities and dependencies."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the settings service and publish WORKSPACE_SETTINGS capability.

        Args:
            context: Runtime feature context used for capability provision and
                resolution.
        """
        persistence = context.optional(WORKSPACE_PERSISTENCE)
        service = SettingsService(self._config, persistence=persistence)
        if self._config.allow_preset_override:
            service.load_user_override_file()
        context.provide(WORKSPACE_SETTINGS, service)
        logger.info("workspace_settings_started", scope=self._config.default_scope)


def feature() -> SettingsFeature:
    """Construct an unmounted SettingsFeature instance for bootstrapping.

    Returns:
        Configured SettingsFeature instance ready for registration.
    """
    return SettingsFeature()


__all__ = [
    "DEFAULT_PRESETS_DIR",
    "DEFAULT_SETTINGS_DIR",
    "DEFAULT_USER_OVERRIDE_FILE",
    "KEY_CONFIG_AGENTS",
    "KEY_CONFIG_CPU",
    "KEY_CONFIG_CTRADER",
    "KEY_CONFIG_DATABANKS",
    "KEY_CONFIG_GLOBAL",
    "KEY_CONFIG_MEMORY",
    "KEY_CONFIG_MT5",
    "KEY_CONFIG_OPTIMIZATIONS",
    "KEY_CONFIG_PERFORMANCE",
    "KEY_CONFIG_TROUBLESHOOTING",
    "KEY_CONNECT_MCP",
    "KEY_NOTIFY_DESKTOP",
    "KEY_NOTIFY_EMAIL",
    "KEY_NOTIFY_TELEGRAM",
    "KEY_USER_ACCESS",
    "SPEC",
    "AgentsConfigSettings",
    "BacktestEngineSettings",
    "CTraderConfigSettings",
    "CpuConfigSettings",
    "DatabanksConfigSettings",
    "DesktopNotificationSettings",
    "EmailNotificationSettings",
    "GeminiProviderConfig",
    "GlobalConfigSettings",
    "McpConnectSettings",
    "MemoryConfigSettings",
    "MetaTrader5ConfigSettings",
    "OllamaProviderConfig",
    "OpenAiProviderConfig",
    "OptimizationsConfigSettings",
    "PerformanceConfigSettings",
    "SettingsConfig",
    "SettingsFeature",
    "SettingsService",
    "TelegramNotificationSettings",
    "TroubleshootingConfigSettings",
    "UserAccessSettings",
    "WorkspaceAppSettings",
    "feature",
    "hash_password",
    "verify_password",
]
