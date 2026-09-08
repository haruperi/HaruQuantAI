"""System settings store for the administer-settings capability.

Persists the workstation's administrator settings using the authoritative
manifest: editable non-secret system-setting definitions (key, label,
description, value kind, allowed values, bounds, activation, owner,
effective default, narrower policy, remount effect, secret reference slots)
plus the write-only credential slots.

Values are persisted in the ``settings`` table under dotted lowercase keys.
The wire contract uses the legacy uppercase key names the workstation reads
(for example ``MT5_SNAPSHOT_SYMBOLS``); :data:`_KEY_ALIASES` maps each wire
key to its storage key, and :data:`_LEGACY_DEFAULTS` supplies the value for
definitions whose storage row does not exist yet.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from app.composition.logging import get_logger
from app.contracts.workspace.administer_settings import (
    SettingsConflictError,
    SettingsValidationError,
)

logger = get_logger(__name__)

_DEFAULT_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)

ORCHESTRATION_MAX_WORKER_CPU_PERCENT: Final[int] = 80
ORCHESTRATION_MAX_CPU_CORES: Final[int] = 4
ORCHESTRATION_CPU_ENVELOPE_REASON: Final[str] = (
    "Host orchestration envelope caps worker CPU allocation at 80% and 4 cores "
    "(orchestration.host_envelope_cap)"
)


@dataclass(frozen=True, slots=True)
class _SettingDefinition:
    """Manifest definition for one editable non-secret system setting."""

    key: str
    label: str
    description: str
    value_kind: str = "string"
    allowed_values: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    activation: str = "restart_required"
    owner: str = "workspace"
    effective_default: str = ""
    narrower_policy: str | None = None
    remount_effect: str | None = None
    secret_reference_slots: tuple[str, ...] = ()


_DEFINITIONS: Final[tuple[_SettingDefinition, ...]] = (
    _SettingDefinition(
        "APP_NAME",
        "Application name",
        "Display name presented by the application.",
        owner="workspace",
        effective_default="haruquantai",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "LOG_LEVEL",
        "Log level",
        "Minimum application log severity.",
        allowed_values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        owner="workspace",
        effective_default="INFO",
        activation="hot",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "ACCOUNT_MODE",
        "Account mode",
        "Application-wide trading context: sim executes virtually against "
        "the Simulator, while demo and live both relay to the connected MT5 "
        "terminal and differ only by the credentials the operator supplies.",
        allowed_values=("sim", "demo", "live"),
        activation="hot",
        owner="broker",
        effective_default="sim",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "RUNTIME_BROKER",
        "Runtime broker",
        "Provider selected for composed broker operations.",
        allowed_values=("binance", "ctrader", "dukascopy", "mt5", "yahoo"),
        owner="broker",
        effective_default="mt5",
        activation="hot",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "TIMEZONE",
        "Display timezone",
        "Operator-facing display timezone (UTC offset label).",
        owner="workspace",
        effective_default="UTC+3",
        activation="hot",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "MT5_ENABLED",
        "Enable MT5",
        "Allow composition of the MT5 provider when bootstrap policy permits it.",
        value_kind="boolean",
        owner="broker",
        effective_default="true",
        remount_effect="restart_required",
        secret_reference_slots=("mt5_live", "mt5_demo"),
    ),
    _SettingDefinition(
        "MT5_TERMINAL_PATH",
        "MT5 terminal path",
        "Local MT5 terminal executable path.",
        owner="broker",
        effective_default="",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_HOST",
        "MT5 snapshot host",
        "Local interface used by the authenticated MT5 snapshot listener.",
        owner="broker",
        effective_default="127.0.0.1",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_PORT",
        "MT5 snapshot port",
        "TCP port used by the authenticated MT5 snapshot listener.",
        value_kind="integer",
        minimum=1,
        maximum=65_535,
        owner="broker",
        effective_default="9001",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_CONNECT_TIMEOUT_MS",
        "MT5 connection timeout",
        "EA connection timeout in milliseconds.",
        value_kind="integer",
        minimum=100,
        maximum=60_000,
        owner="broker",
        effective_default="1000",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_INTERVAL_SECONDS",
        "MT5 snapshot interval",
        "Expected interval between complete multi-symbol snapshots.",
        value_kind="integer",
        minimum=1,
        maximum=3_600,
        owner="broker",
        effective_default="1",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_SOURCE_ID",
        "MT5 snapshot source",
        "Exact source identity declared by the bridge EA.",
        owner="broker",
        effective_default="mt5-terminal-1",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_SYMBOLS",
        "MT5 bootstrap symbols",
        "Comma-separated broker-native fallback used before runtime demand is applied.",
        owner="broker",
        effective_default="EURUSD,GBPUSD,USDJPY,XAUUSD",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MT5_PIP_SIZES",
        "MT5 pip sizes",
        "Comma-separated broker-symbol pip sizes, for example "
        "EURUSD=0.0001,XAUUSD=0.1.",
        owner="broker",
        effective_default="EURUSD=0.0001,XAUUSD=0.1",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_LOG_SNAPSHOTS",
        "Log MT5 snapshots",
        "Enable bounded snapshot lifecycle logging without quote or secret payloads.",
        value_kind="boolean",
        owner="broker",
        effective_default="true",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "CTRADER_ENABLED",
        "Enable cTrader",
        "Allow composition of the cTrader provider when bootstrap policy permits it.",
        value_kind="boolean",
        owner="broker",
        effective_default="true",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "CTRADER_REDIRECT_URL",
        "cTrader redirect URL",
        "Registered non-secret cTrader OAuth redirect URL.",
        owner="broker",
        effective_default="https://api.spotware.com/connect/tradingaccounts/token",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "BINANCE_ENABLED",
        "Enable Binance",
        "Allow composition of the Binance provider when bootstrap policy permits it.",
        value_kind="boolean",
        owner="broker",
        effective_default="true",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "DUKASCOPY_ENABLED",
        "Enable Dukascopy",
        "Allow read-only Dukascopy provider composition.",
        value_kind="boolean",
        owner="broker",
        effective_default="true",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "YAHOO_ENABLED",
        "Enable Yahoo Finance",
        "Allow read-only Yahoo Finance provider composition.",
        value_kind="boolean",
        owner="broker",
        effective_default="true",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "AI_MODEL_AGENT",
        "Agent model",
        "Default model for agent workloads.",
        owner="ai",
        effective_default="gemini-3.6-flash",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "AI_MODEL_FAST",
        "Fast model",
        "Model selected for latency-sensitive workloads.",
        owner="ai",
        effective_default="gemini-3.6-flash",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "AI_MODEL_PREMIUM",
        "Premium model",
        "Model selected for highest-quality workloads.",
        owner="ai",
        effective_default="gpt-5.6-sol",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "AI_MODEL_FALLBACK",
        "Fallback model",
        "Explicit fallback model selected by policy.",
        owner="ai",
        effective_default="glm-5.2",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "AI_TEMPERATURE",
        "Temperature",
        "Sampling temperature for configured AI workloads.",
        value_kind="decimal",
        minimum=0.0,
        maximum=2.0,
        owner="ai",
        effective_default="0.2",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "AI_MAX_TOKENS",
        "Maximum tokens",
        "Maximum generated tokens for configured AI workloads.",
        value_kind="integer",
        minimum=1,
        maximum=1_000_000,
        owner="ai",
        effective_default="4096",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "AI_TOP_P",
        "Top-p",
        "Nucleus sampling probability for configured AI workloads.",
        value_kind="decimal",
        minimum=0.0,
        maximum=1.0,
        owner="ai",
        effective_default="0.95",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "AI_TOP_K",
        "Top-k",
        "Token candidate bound for providers that support top-k sampling.",
        value_kind="integer",
        minimum=1,
        maximum=1_000_000,
        owner="ai",
        effective_default="40",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "GOOGLE_USE_VERTEXAI",
        "Use Vertex AI",
        "Select Vertex AI rather than the direct Google GenAI endpoint.",
        value_kind="boolean",
        owner="ai",
        effective_default="false",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "GOOGLE_AGENT_MODEL",
        "Google agent model",
        "Google model used by agent workloads.",
        owner="ai",
        effective_default="gemini-3.6-flash",
        remount_effect="hot",
        secret_reference_slots=("google",),
    ),
    _SettingDefinition(
        "OPENAI_AGENT_MODEL",
        "OpenAI agent model",
        "OpenAI model used by agent workloads.",
        owner="ai",
        effective_default="gpt-5.6-sol",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "OPENAI_AGENT_MID",
        "OpenAI mid model",
        "OpenAI model used for balanced workloads.",
        owner="ai",
        effective_default="gpt-5.6-terra",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "OPENAI_AGENT_LIGHT",
        "OpenAI light model",
        "OpenAI model used for lightweight workloads.",
        owner="ai",
        effective_default="gpt-5.6-luna",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "OLLAMA_BASE_URL",
        "Ollama URL",
        "Base URL of the configured Ollama service.",
        owner="ai",
        effective_default="http://localhost:11434",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "OLLAMA_AGENT_MODEL",
        "Ollama agent model",
        "Ollama model used by agent workloads.",
        owner="ai",
        effective_default="ollama/llama3.1:70b",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "SMTP_HOST",
        "SMTP host",
        "SMTP server host name.",
        owner="notification",
        effective_default="smtp.gmail.com",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "SMTP_PORT",
        "SMTP port",
        "SMTP server TCP port.",
        value_kind="integer",
        minimum=1,
        maximum=65_535,
        owner="notification",
        effective_default="587",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "SMTP_TLS_MODE",
        "SMTP TLS mode",
        "SMTP transport security mode.",
        allowed_values=("ssl", "starttls", "none"),
        owner="notification",
        effective_default="starttls",
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "NOTIFICATIONS_ENABLED",
        "Enable notifications",
        "Master switch for all outbound notification channels.",
        value_kind="boolean",
        owner="notification",
        effective_default="true",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "NOTIFICATION_DEFAULT_CHANNELS",
        "Default notification channels",
        "Comma-separated subset of desktop, email, telegram, and sms.",
        owner="notification",
        effective_default="desktop,telegram",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "NOTIFICATION_RATE_LIMIT",
        "Notification rate limit",
        "Maximum messages per channel within one rate window.",
        value_kind="integer",
        minimum=1,
        maximum=10_000,
        owner="notification",
        effective_default="60",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "NOTIFICATION_RATE_WINDOW_SECONDS",
        "Notification rate window",
        "Per-channel rate-limit window in seconds.",
        value_kind="decimal",
        minimum=0.1,
        maximum=86_400,
        owner="notification",
        effective_default="60",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "NOTIFICATION_TIMEOUT_SECONDS",
        "Notification timeout",
        "External channel request timeout in seconds.",
        value_kind="decimal",
        minimum=0.1,
        maximum=60,
        owner="notification",
        effective_default="60",
        remount_effect="hot",
    ),
    *(
        _SettingDefinition(
            f"{channel.upper()}_NOTIFICATIONS_ENABLED",
            f"Enable {channel} notifications",
            f"Allow outbound {channel} notifications when the master switch "
            "is enabled.",
            value_kind="boolean",
            owner="notification",
            effective_default="true" if channel in ("desktop", "telegram") else "false",
            remount_effect="hot",
        )
        for channel in ("desktop", "email", "telegram", "sms")
    ),
    _SettingDefinition(
        "LANGCHAIN_TRACING_V2",
        "LangChain tracing",
        "Enable LangChain v2 tracing.",
        value_kind="boolean",
        owner="ai",
        effective_default="true",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "LANGCHAIN_PROJECT",
        "LangChain project",
        "Non-secret LangChain tracing project name.",
        owner="ai",
        effective_default="HaruQuant",
        remount_effect="hot",
    ),
    # User interaction, UI, and layout preferences (FR-TRC-WS-ADMINISTER_SETTINGS-003)
    _SettingDefinition(
        "LOCALE",
        "Display Locale",
        "User-visible display locale for formatting and presentation "
        "without altering stored IDs or hashes.",
        value_kind="string",
        allowed_values=("en_US", "de_DE", "ja_JP", "fr_FR", "es_ES"),
        activation="hot",
        owner="ui",
        effective_default="en_US",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "THEME",
        "UI Theme",
        "Visual theme mode for the workstation interface.",
        value_kind="string",
        allowed_values=("dark", "light", "system"),
        activation="hot",
        owner="ui",
        effective_default="dark",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "SOUND_ENABLED",
        "Sound Effects",
        "Auditory feedback for events, order execution, and alarms.",
        value_kind="boolean",
        activation="hot",
        owner="ui",
        effective_default="true",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "UNITS_SYSTEM",
        "Units System",
        "Measurement units conventions for financial and charting display.",
        value_kind="string",
        allowed_values=("metric", "imperial", "native"),
        activation="hot",
        owner="ui",
        effective_default="metric",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "DEFAULT_RESULT_VIEW",
        "Default Result View",
        "Initial view presented when opening backtest or optimization results.",
        value_kind="string",
        allowed_values=("overview", "trades", "equity", "analytics"),
        activation="hot",
        owner="ui",
        effective_default="overview",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "REPORT_HEADER",
        "Report Header",
        "User-visible header text included on exported reports and summaries.",
        value_kind="string",
        activation="hot",
        owner="ui",
        effective_default="",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "REPORT_FOOTER",
        "Report Footer",
        "User-visible footer text included on exported reports and summaries.",
        value_kind="string",
        activation="hot",
        owner="ui",
        effective_default="",
        remount_effect="hot",
    ),
    _SettingDefinition(
        "PICKER_SORTING",
        "Picker Sorting",
        "Sorting preference for modal instrument, strategy, and dataset pickers.",
        value_kind="string",
        allowed_values=("alphabetical", "recent", "popularity"),
        activation="hot",
        owner="ui",
        effective_default="recent",
        remount_effect="hot",
    ),
    # Orchestration and CPU bounds (FR-TRC-WS-ADMINISTER_SETTINGS-002)
    _SettingDefinition(
        "WORKER_CPU_PERCENT",
        "Worker CPU Allocation %",
        "Per-worker CPU execution envelope percentage.",
        value_kind="integer",
        minimum=1,
        maximum=100,
        activation="restart_required",
        owner="orchestration",
        effective_default="80",
        narrower_policy=(
            "Host orchestration envelope caps worker CPU allocation at 80% "
            "(orchestration.host_envelope_cap); higher UI values cannot override "
            "this envelope."
        ),
        remount_effect="restart_required",
    ),
    _SettingDefinition(
        "MAX_CPU_CORES",
        "Maximum CPU Cores",
        "Maximum CPU cores admitted across worker jobs.",
        value_kind="integer",
        minimum=1,
        maximum=64,
        activation="restart_required",
        owner="orchestration",
        effective_default="4",
        narrower_policy=(
            "Host orchestration envelope limits allocation to at most 4 cores "
            "on this host; higher UI values are clamped."
        ),
        remount_effect="restart_required",
    ),
)

_DEFINITION_BY_KEY: Final[Mapping[str, _SettingDefinition]] = {
    definition.key: definition for definition in _DEFINITIONS
}

#: Wire (legacy uppercase) key -> storage (dotted lowercase) key.
_KEY_ALIASES: Final[Mapping[str, str]] = {
    "APP_NAME": "system.app_name",
    "LOG_LEVEL": "system.log_level",
    "ACCOUNT_MODE": "system.account_mode",
    "RUNTIME_BROKER": "broker.runtime_broker",
    "TIMEZONE": "system.timezone",
    "MT5_ENABLED": "broker.mt5.enabled",
    "MT5_TERMINAL_PATH": "broker.mt5.terminal_path",
    "MT5_SNAPSHOT_HOST": "broker.mt5.snapshot_host",
    "MT5_SNAPSHOT_PORT": "broker.mt5.snapshot_port",
    "MT5_SNAPSHOT_CONNECT_TIMEOUT_MS": "broker.mt5.snapshot_connect_timeout_ms",
    "MT5_SNAPSHOT_INTERVAL_SECONDS": "broker.mt5.snapshot_interval_seconds",
    "MT5_SNAPSHOT_SOURCE_ID": "broker.mt5.snapshot_source_id",
    "MT5_SNAPSHOT_SYMBOLS": "broker.mt5.snapshot_symbols",
    "MT5_SNAPSHOT_LOG_SNAPSHOTS": "broker.mt5.snapshot_log_snapshots",
    "CTRADER_ENABLED": "broker.ctrader.enabled",
    "CTRADER_REDIRECT_URL": "broker.ctrader.redirect_url",
    "BINANCE_ENABLED": "broker.binance.enabled",
    "DUKASCOPY_ENABLED": "broker.dukascopy.enabled",
    "YAHOO_ENABLED": "broker.yahoo.enabled",
    "AI_MODEL_AGENT": "ai.model_agent",
    "AI_MODEL_FAST": "ai.model_fast",
    "AI_MODEL_PREMIUM": "ai.model_premium",
    "AI_MODEL_FALLBACK": "ai.model_fallback",
    "AI_TEMPERATURE": "ai.temperature",
    "AI_MAX_TOKENS": "ai.max_tokens",
    "AI_TOP_P": "ai.top_p",
    "AI_TOP_K": "ai.top_k",
    "GOOGLE_USE_VERTEXAI": "ai.google.use_vertexai",
    "GOOGLE_AGENT_MODEL": "ai.google.agent_model",
    "OPENAI_AGENT_MODEL": "ai.openai.agent_model",
    "OPENAI_AGENT_MID": "ai.openai.agent_mid",
    "OPENAI_AGENT_LIGHT": "ai.openai.agent_light",
    "OLLAMA_BASE_URL": "ai.ollama.base_url",
    "OLLAMA_AGENT_MODEL": "ai.ollama.agent_model",
    "SMTP_HOST": "notification.smtp_host",
    "SMTP_PORT": "notification.smtp_port",
    "NOTIFICATIONS_ENABLED": "notification.enabled",
    "NOTIFICATION_DEFAULT_CHANNELS": "notification.default_channels",
    "NOTIFICATION_RATE_WINDOW_SECONDS": "notification.rate_window_seconds",
    "NOTIFICATION_TIMEOUT_SECONDS": "notification.timeout_seconds",
    "DESKTOP_NOTIFICATIONS_ENABLED": "notification.desktop_enabled",
    "EMAIL_NOTIFICATIONS_ENABLED": "notification.email_enabled",
    "TELEGRAM_NOTIFICATIONS_ENABLED": "notification.telegram_enabled",
    "LANGCHAIN_TRACING_V2": "ai.langchain.tracing_v2",
    "LANGCHAIN_PROJECT": "ai.langchain.project",
    "LOCALE": "ui.locale",
    "THEME": "ui.theme",
    "SOUND_ENABLED": "ui.sound_enabled",
    "UNITS_SYSTEM": "ui.units_system",
    "DEFAULT_RESULT_VIEW": "ui.default_result_view",
    "REPORT_HEADER": "ui.report_header",
    "REPORT_FOOTER": "ui.report_footer",
    "PICKER_SORTING": "ui.picker_sorting",
    "WORKER_CPU_PERCENT": "orchestration.worker_cpu_percent",
    "MAX_CPU_CORES": "orchestration.max_cpu_cores",
}

#: Default value per wire key for definitions with no storage row. Values
#: mirror the reference deployment's persisted system settings document.
_LEGACY_DEFAULTS: Final[Mapping[str, str]] = {
    "ACCOUNT_MODE": "sim",
    "AI_MAX_TOKENS": "4096",
    "AI_MODEL_AGENT": "gemini-3.6-flash",
    "AI_MODEL_FALLBACK": "glm-5.2",
    "AI_MODEL_FAST": "gemini-3.6-flash",
    "AI_MODEL_PREMIUM": "gpt-5.6-sol",
    "AI_TEMPERATURE": "0.2",
    "AI_TOP_K": "40",
    "AI_TOP_P": "0.95",
    "APP_NAME": "haruquantai",
    "BINANCE_ENABLED": "true",
    "CTRADER_ENABLED": "true",
    "CTRADER_REDIRECT_URL": "https://api.spotware.com/connect/tradingaccounts/token",
    "DESKTOP_NOTIFICATIONS_ENABLED": "true",
    "DUKASCOPY_ENABLED": "true",
    "EMAIL_NOTIFICATIONS_ENABLED": "false",
    "GOOGLE_AGENT_MODEL": "gemini-3.6-flash",
    "GOOGLE_USE_VERTEXAI": "false",
    "LANGCHAIN_PROJECT": "HaruQuant",
    "LANGCHAIN_TRACING_V2": "true",
    "LOG_LEVEL": "INFO",
    "MT5_ENABLED": "true",
    "MT5_PIP_SIZES": "EURUSD=0.0001,XAUUSD=0.1",
    "MT5_SNAPSHOT_CONNECT_TIMEOUT_MS": "1000",
    "MT5_SNAPSHOT_HOST": "127.0.0.1",
    "MT5_SNAPSHOT_INTERVAL_SECONDS": "1",
    "MT5_SNAPSHOT_LOG_SNAPSHOTS": "true",
    "MT5_SNAPSHOT_PORT": "9001",
    "MT5_SNAPSHOT_SOURCE_ID": "mt5-terminal-1",
    "MT5_SNAPSHOT_SYMBOLS": "EURUSD,GBPUSD,USDJPY,XAUUSD",
    "MT5_TERMINAL_PATH": "",
    "NOTIFICATIONS_ENABLED": "true",
    "NOTIFICATION_DEFAULT_CHANNELS": "desktop,telegram",
    "NOTIFICATION_RATE_LIMIT": "60",
    "NOTIFICATION_RATE_WINDOW_SECONDS": "60",
    "NOTIFICATION_TIMEOUT_SECONDS": "60",
    "OLLAMA_AGENT_MODEL": "ollama/llama3.1:70b",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "OPENAI_AGENT_LIGHT": "gpt-5.6-luna",
    "OPENAI_AGENT_MID": "gpt-5.6-terra",
    "OPENAI_AGENT_MODEL": "gpt-5.6-sol",
    "RUNTIME_BROKER": "mt5",
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": "587",
    "SMTP_TLS_MODE": "starttls",
    "SMS_NOTIFICATIONS_ENABLED": "false",
    "TELEGRAM_NOTIFICATIONS_ENABLED": "true",
    "TIMEZONE": "UTC+3",
    "YAHOO_ENABLED": "true",
    "LOCALE": "en_US",
    "THEME": "dark",
    "SOUND_ENABLED": "true",
    "UNITS_SYSTEM": "metric",
    "DEFAULT_RESULT_VIEW": "overview",
    "REPORT_HEADER": "",
    "REPORT_FOOTER": "",
    "PICKER_SORTING": "recent",
    "WORKER_CPU_PERCENT": "80",
    "MAX_CPU_CORES": "4",
}

_CREDENTIAL_SLOTS: Final[dict[str, dict[str, Any]]] = {
    "mt5_snapshot_bridge": {
        "label": "MT5 Snapshot Bridge (TickBridge EA)",
        "fields": ["credentials.mt5_snapshot_auth_token"],
    },
    "mt5_live": {
        "label": "MetaTrader 5 (Live)",
        "fields": ["mt5.live.login", "mt5.live.password", "mt5.live.server"],
    },
    "mt5_demo": {
        "label": "MetaTrader 5 (Demo)",
        "fields": ["mt5.demo.login", "mt5.demo.password", "mt5.demo.server"],
    },
    "market_data_primary": {
        "label": "Primary Market Data Provider",
        "fields": ["market_data.primary.api_key", "market_data.primary.endpoint"],
    },
    "market_data_secondary": {
        "label": "Secondary Market Data Provider",
        "fields": [
            "market_data.secondary.api_key",
            "market_data.secondary.endpoint",
        ],
    },
    "google": {
        "label": "Google AI / Gemini Platform",
        "fields": ["credentials.google_api_key"],
    },
}


def _resolve_db_path(db_path: Path | str | None) -> Path:
    if db_path is None:
        return _DEFAULT_DB_PATH
    return Path(db_path)


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def init_settings_db(db_path: Path | str | None = None) -> None:
    """Initialize settings and settings_history tables in the target database.

    Args:
        db_path: Path to database file or None for default path.
    """
    target = _resolve_db_path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(target)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                value_type TEXT NOT NULL,
                category TEXT NOT NULL,
                label TEXT NOT NULL,
                description TEXT NOT NULL,
                is_secret INTEGER NOT NULL DEFAULT 0,
                is_readonly INTEGER NOT NULL DEFAULT 0,
                default_value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT NOT NULL,
                changed_by TEXT NOT NULL DEFAULT 'system',
                changed_at TEXT NOT NULL
            );
            """
        )


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = _resolve_db_path(db_path)
    if not target.exists():
        msg = f"Database not found at {target}"
        raise FileNotFoundError(msg)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def _validate_setting_value(  # noqa: C901
    definition: _SettingDefinition, val: str
) -> None:
    """Validate one setting candidate against its definition constraints.

    Args:
        definition: Setting definition containing constraints and value kind.
        val: Candidate string value.

    Raises:
        SettingsValidationError: If value fails allowed_values, type, or bounds.
    """
    if definition.allowed_values and val not in definition.allowed_values:
        msg = (
            f"Invalid value '{val}' for setting '{definition.key}': "
            f"must be one of {definition.allowed_values}"
        )
        raise SettingsValidationError(msg, key=definition.key, value=val)
    if definition.value_kind == "boolean":
        if val.lower() not in ("true", "false", "1", "0"):
            msg = f"Invalid boolean value '{val}' for setting '{definition.key}'"
            raise SettingsValidationError(msg, key=definition.key, value=val)
    elif definition.value_kind == "integer":
        try:
            int_val = int(val)
        except ValueError as err:
            msg = f"Invalid integer value '{val}' for setting '{definition.key}'"
            raise SettingsValidationError(msg, key=definition.key, value=val) from err
        if definition.minimum is not None and int_val < definition.minimum:
            msg = (
                f"Value {int_val} for '{definition.key}' is below minimum "
                f"{definition.minimum}"
            )
            raise SettingsValidationError(msg, key=definition.key, value=val)
        if definition.maximum is not None and int_val > definition.maximum:
            msg = (
                f"Value {int_val} for '{definition.key}' is above maximum "
                f"{definition.maximum}"
            )
            raise SettingsValidationError(msg, key=definition.key, value=val)
    elif definition.value_kind == "decimal":
        try:
            float_val = float(val)
        except ValueError as err:
            msg = f"Invalid decimal value '{val}' for setting '{definition.key}'"
            raise SettingsValidationError(msg, key=definition.key, value=val) from err
        if definition.minimum is not None and float_val < definition.minimum:
            msg = (
                f"Value {float_val} for '{definition.key}' is below minimum "
                f"{definition.minimum}"
            )
            raise SettingsValidationError(msg, key=definition.key, value=val)
        if definition.maximum is not None and float_val > definition.maximum:
            msg = (
                f"Value {float_val} for '{definition.key}' is above maximum "
                f"{definition.maximum}"
            )
            raise SettingsValidationError(msg, key=definition.key, value=val)


def _validate_incompatible_combinations(settings: dict[str, str]) -> None:
    """Validate that combined setting values form a valid system state.

    Args:
        settings: Map of wire setting keys to string values.

    Raises:
        SettingsValidationError: If settings combinations are incompatible.
    """
    broker = settings.get("RUNTIME_BROKER", "mt5")
    mt5_enabled = settings.get("MT5_ENABLED", "true").lower() in ("true", "1")
    ctrader_enabled = settings.get("CTRADER_ENABLED", "true").lower() in ("true", "1")
    binance_enabled = settings.get("BINANCE_ENABLED", "true").lower() in ("true", "1")
    account_mode = settings.get("ACCOUNT_MODE", "sim")

    if broker == "mt5" and not mt5_enabled:
        msg = (
            "Incompatible configuration: RUNTIME_BROKER is 'mt5' but "
            "MT5_ENABLED is false"
        )
        raise SettingsValidationError(msg, key="RUNTIME_BROKER", value=broker)
    if broker == "ctrader" and not ctrader_enabled:
        msg = (
            "Incompatible configuration: RUNTIME_BROKER is 'ctrader' but "
            "CTRADER_ENABLED is false"
        )
        raise SettingsValidationError(msg, key="RUNTIME_BROKER", value=broker)
    if broker == "binance" and not binance_enabled:
        msg = (
            "Incompatible configuration: RUNTIME_BROKER is 'binance' but "
            "BINANCE_ENABLED is false"
        )
        raise SettingsValidationError(msg, key="RUNTIME_BROKER", value=broker)
    if account_mode == "live" and broker == "yahoo":
        msg = (
            "Incompatible configuration: ACCOUNT_MODE 'live' cannot use "
            "read-only broker 'yahoo'"
        )
        raise SettingsValidationError(msg, key="ACCOUNT_MODE", value=account_mode)


def _get_current_version(conn: sqlite3.Connection) -> int:
    """Read the monotonic system settings revision version from storage.

    Args:
        conn: Open SQLite connection.

    Returns:
        Monotonically increasing version integer.
    """
    row = conn.execute(
        "SELECT value FROM settings WHERE key = 'system._version'"
    ).fetchone()
    if row is not None:
        try:
            return int(row["value"])
        except ValueError, TypeError:
            return 1
    # Fallback: distinct change timestamps in history or default 1
    hist = conn.execute(
        "SELECT COUNT(DISTINCT changed_at) FROM settings_history"
    ).fetchone()[0]
    return int(hist) + 1 if hist else 1


def get_system_settings(
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Retrieve the system settings projection under wire (legacy) keys.

    Args:
        db_path: Optional explicit database path.

    Returns:
        System settings projection payload matching the SettingsReadResponse
        contract: one value per manifest key, resolved from the storage row
        when present and from the legacy default otherwise.
    """
    conn = _get_connection(db_path)
    try:
        rows = {
            str(row["key"]): str(row["value"])
            for row in conn.execute("SELECT key, value FROM settings")
        }
        latest = conn.execute("SELECT max(updated_at) FROM settings").fetchone()[0]
        version = _get_current_version(conn)
    finally:
        conn.close()

    settings_dict = {
        definition.key: rows.get(
            _KEY_ALIASES.get(definition.key, definition.key),
            _LEGACY_DEFAULTS.get(definition.key, ""),
        )
        for definition in _DEFINITIONS
    }
    return {
        "scope": "system",
        "subject_id": "system",
        "user_id": None,
        "settings": settings_dict,
        "version": version,
        "updated_at": str(latest) if latest else _utc_now_iso(),
        "restart_required": False,
    }


def update_system_settings(  # noqa: C901, PLR0912, PLR0915
    settings_delta: dict[str, Any],
    changed_by: str = "system",
    expected_revision: int | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Update settings rows and record settings_history audit entries.

    Validates that:
    1. All keys exist in the authoritative manifest.
    2. Values satisfy value_kind, bounds, and allowed_values.
    3. Combined settings do not introduce incompatible states.
    4. Expected revision matches current version (optimistic concurrency).
    5. Orchestration CPU envelope is not exceeded (values are clamped).

    Args:
        settings_delta: Wire-key to value mapping to persist.
        changed_by: Audit identity for the change record.
        expected_revision: Expected current revision for optimistic concurrency.
        db_path: Optional explicit database path.

    Returns:
        Updated system settings projection.

    Raises:
        SettingsConflictError: When expected_revision does not match.
        SettingsValidationError: When keys, values, or combinations are invalid.
    """
    # 1. Reject unknown keys
    for wire_key in settings_delta:
        if wire_key not in _DEFINITION_BY_KEY:
            logger.warning(
                "Rejected unknown setting key",
                key=wire_key,
                changed_by=changed_by,
                event="settings.key.unknown",
            )
            msg = f"Unknown setting key '{wire_key}'"
            raise SettingsValidationError(msg, key=str(wire_key))

    conn = _get_connection(db_path)
    try:
        current_version = _get_current_version(conn)
        if expected_revision is not None and expected_revision != current_version:
            logger.warning(
                "Stale settings update rejected",
                expected_revision=expected_revision,
                current_revision=current_version,
                changed_by=changed_by,
                event="settings.concurrency.conflict",
            )
            msg = (
                f"Stale update conflict: expected revision {expected_revision}, "
                f"but current revision is {current_version}"
            )
            raise SettingsConflictError(
                msg,
                expected_revision=expected_revision,
                current_revision=current_version,
            )

        # 2. Value validation and CPU envelope clamping
        validated_delta: dict[str, str] = {}
        for wire_key, raw_val in settings_delta.items():
            definition = _DEFINITION_BY_KEY[str(wire_key)]
            str_val = str(raw_val) if raw_val is not None else ""

            # AT-WS-ADMINISTER_SETTINGS-002: Enforce Orchestration CPU envelope
            if wire_key == "WORKER_CPU_PERCENT":
                try:
                    int_val = int(str_val)
                    if int_val > ORCHESTRATION_MAX_WORKER_CPU_PERCENT:
                        logger.info(
                            "Selecting a larger UI CPU value cannot override "
                            "the effective Orchestration envelope; "
                            "clamping to stricter value",
                            setting=wire_key,
                            requested=int_val,
                            clamped=ORCHESTRATION_MAX_WORKER_CPU_PERCENT,
                            reason=ORCHESTRATION_CPU_ENVELOPE_REASON,
                            event="settings.cpu_envelope.clamped",
                        )
                        str_val = str(ORCHESTRATION_MAX_WORKER_CPU_PERCENT)
                except ValueError as err:
                    msg = f"Invalid integer value '{str_val}' for 'WORKER_CPU_PERCENT'"
                    raise SettingsValidationError(
                        msg,
                        key="WORKER_CPU_PERCENT",
                        value=str_val,
                    ) from err
            elif wire_key == "MAX_CPU_CORES":
                try:
                    int_val = int(str_val)
                    if int_val > ORCHESTRATION_MAX_CPU_CORES:
                        logger.info(
                            "Selecting a larger UI CPU core count cannot override "
                            "the effective Orchestration envelope; "
                            "clamping to stricter value",
                            setting=wire_key,
                            requested=int_val,
                            clamped=ORCHESTRATION_MAX_CPU_CORES,
                            reason=ORCHESTRATION_CPU_ENVELOPE_REASON,
                            event="settings.cpu_envelope.clamped",
                        )
                        str_val = str(ORCHESTRATION_MAX_CPU_CORES)
                except ValueError as err:
                    msg = f"Invalid integer value '{str_val}' for 'MAX_CPU_CORES'"
                    raise SettingsValidationError(
                        msg,
                        key="MAX_CPU_CORES",
                        value=str_val,
                    ) from err

            _validate_setting_value(definition, str_val)
            validated_delta[str(wire_key)] = str_val

        # 3. Incompatible combinations check against combined candidate state
        current_rows = {
            str(row["key"]): str(row["value"])
            for row in conn.execute("SELECT key, value FROM settings")
        }
        candidate_settings = {
            definition.key: validated_delta.get(
                definition.key,
                current_rows.get(
                    _KEY_ALIASES.get(definition.key, definition.key),
                    _LEGACY_DEFAULTS.get(definition.key, ""),
                ),
            )
            for definition in _DEFINITIONS
        }
        _validate_incompatible_combinations(candidate_settings)

        # 4. Atomic transaction update
        now = _utc_now_iso()
        new_version = current_version + 1
        with conn:
            cur = conn.cursor()
            for wire_key, str_val in validated_delta.items():
                storage_key = _KEY_ALIASES.get(str(wire_key), str(wire_key))
                existing = cur.execute(
                    "SELECT value FROM settings WHERE key = ?", (storage_key,)
                ).fetchone()
                old_val = str(existing["value"]) if existing is not None else None
                if existing is not None:
                    cur.execute(
                        "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
                        (str_val, now, storage_key),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO settings (
                            key, value, value_type, category, label,
                            description, is_secret, is_readonly, default_value,
                            updated_at, created_at
                        ) VALUES (?, ?, 'string', 'custom', ?, '', 0, 0, ?, ?, ?)
                        """,
                        (storage_key, str_val, str(wire_key), str_val, now, now),
                    )
                cur.execute(
                    """
                    INSERT INTO settings_history (
                        key, old_value, new_value, changed_by, changed_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (storage_key, old_val, str_val, changed_by, now),
                )

            # Persist version bump
            version_existing = cur.execute(
                "SELECT 1 FROM settings WHERE key = 'system._version'"
            ).fetchone()
            if version_existing is not None:
                cur.execute(
                    "UPDATE settings SET value = ?, updated_at = ? "
                    "WHERE key = 'system._version'",
                    (str(new_version), now),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO settings (
                        key, value, value_type, category, label,
                        description, is_secret, is_readonly, default_value,
                        updated_at, created_at
                    ) VALUES (
                        'system._version', ?, 'integer', 'system',
                        'Settings Version', 'Monotonically increasing version',
                        0, 1, '1', ?, ?
                    )
                    """,
                    (str(new_version), now, now),
                )

            logger.info(
                "Committed system settings revision",
                new_version=new_version,
                changed_by=changed_by,
                keys=list(validated_delta.keys()),
                event="settings.revision.updated",
            )
    finally:
        conn.close()

    return get_system_settings(db_path=db_path)


def get_settings_manifest(
    db_path: Path | str | None = None,  # noqa: ARG001 - uniform helper signature
) -> list[dict[str, Any]]:
    """Return the authoritative manifest of editable system settings.

    Args:
        db_path: Unused; accepted for signature uniformity with the
            persistence-backed helpers.

    Returns:
        Secret-free definition list matching the SystemSettingDefinition
        contract (key, label, description, value_kind, allowed_values,
        minimum, maximum, activation, owner, effective_default,
        narrower_policy, remount_effect, secret_reference_slots).
    """
    return [
        {
            "key": definition.key,
            "label": definition.label,
            "description": definition.description,
            "value_kind": definition.value_kind,
            "allowed_values": list(definition.allowed_values),
            "minimum": definition.minimum,
            "maximum": definition.maximum,
            "activation": definition.activation,
            "owner": definition.owner,
            "effective_default": definition.effective_default,
            "narrower_policy": definition.narrower_policy,
            "remount_effect": definition.remount_effect,
            "secret_reference_slots": list(definition.secret_reference_slots),
        }
        for definition in _DEFINITIONS
    ]


def get_credentials_status(
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Return status of credential slots.

    Args:
        db_path: Optional explicit database path.

    Returns:
        List of credential slot statuses.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT key, value, updated_at FROM settings WHERE category = 'credentials'"
        )
        cred_rows = {
            str(row["key"]): (str(row["value"]), str(row["updated_at"]))
            for row in cur.fetchall()
        }

        statuses: list[dict[str, Any]] = []
        for slot, info in _CREDENTIAL_SLOTS.items():
            fields = info["fields"]
            configured = any(bool(cred_rows.get(f, ("", ""))[0]) for f in fields)
            updated_times = [
                cred_rows[f][1] for f in fields if f in cred_rows and cred_rows[f][0]
            ]
            latest_update = max(updated_times) if updated_times else None
            statuses.append(
                {
                    "slot": slot,
                    "label": info["label"],
                    "fields": fields,
                    "activation": "restart_required",
                    "configured": configured,
                    "version": 1,
                    "updated_at": latest_update,
                }
            )
        return statuses
    finally:
        conn.close()


def update_credential_slot(
    slot: str,
    material: dict[str, Any],
    changed_by: str = "system",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Update credentials for a specific slot.

    Args:
        slot: Credential slot identifier.
        material: Field-to-secret mapping to persist.
        changed_by: Audit identity for the change record.
        db_path: Optional explicit database path.

    Returns:
        Updated slot status payload.
    """
    now = _utc_now_iso()
    conn = _get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            for key, val in material.items():
                str_val = str(val) if val is not None else ""
                existing = cur.execute(
                    "SELECT value FROM settings WHERE key = ?", (key,)
                ).fetchone()
                old_val = str(existing["value"]) if existing is not None else None
                if existing is not None:
                    cur.execute(
                        "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?",
                        (str_val, now, key),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO settings (
                            key, value, value_type, category, label,
                            description, is_secret, is_readonly, default_value,
                            updated_at, created_at
                        ) VALUES (?, ?, 'string', 'credentials', ?, '', 1, 0, '', ?, ?)
                        """,
                        (key, str_val, key, now, now),
                    )
                cur.execute(
                    """
                    INSERT INTO settings_history (
                        key, old_value, new_value, changed_by, changed_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (key, old_val, str_val, changed_by, now),
                )
        return {
            "slot": slot,
            "configured": True,
            "version": 1,
            "updated_at": now,
            "activation": "restart_required",
        }
    finally:
        conn.close()


#: Settings-table key -> bridge runtime parameter name, with the TickBridge
#: EA's documented defaults for absent rows.
_BRIDGE_RUNTIME_SETTINGS: Final[Mapping[str, tuple[str, str]]] = {
    "broker.mt5.snapshot_host": ("host", "127.0.0.1"),
    "broker.mt5.snapshot_port": ("port", "9001"),
    "broker.mt5.snapshot_source_id": ("source_id", "mt5-terminal-1"),
    "credentials.mt5_snapshot_auth_token": ("auth_token", ""),
    "broker.mt5.snapshot_symbols": ("symbols", "EURUSD,GBPUSD,USDJPY,XAUUSD"),
}


def get_mt5_snapshot_bridge_runtime(
    db_path: Path | str | None = None,
) -> dict[str, str]:
    """Read the MT5 snapshot bridge runtime settings from the settings table.

    Args:
        db_path: Optional explicit database path.

    Returns:
        Mapping with host, port, source_id, auth_token, and symbols values;
        absent rows fall back to the TickBridge EA's documented defaults.
    """
    conn = _get_connection(db_path)
    try:
        rows = {
            str(row["key"]): str(row["value"])
            for row in conn.execute("SELECT key, value FROM settings")
        }
    finally:
        conn.close()
    return {
        name: rows.get(key, default)
        for key, (name, default) in _BRIDGE_RUNTIME_SETTINGS.items()
    }
