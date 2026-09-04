"""SQLite database helpers for system settings persistence in haruquantai.db.

Serves the workstation's administrator settings surface using the boundary's
authoritative manifest: fifty editable non-secret system-setting definitions
(key, label, description, value kind, allowed values, bounds, activation)
plus five write-only credential slots.

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

_DEFAULT_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
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


_DEFINITIONS: Final[tuple[_SettingDefinition, ...]] = (
    _SettingDefinition(
        "APP_NAME",
        "Application name",
        "Display name presented by the application.",
    ),
    _SettingDefinition(
        "LOG_LEVEL",
        "Log level",
        "Minimum application log severity.",
        allowed_values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    ),
    _SettingDefinition(
        "ACCOUNT_MODE",
        "Account mode",
        "Application-wide trading context: sim executes virtually against "
        "the Simulator, while demo and live both relay to the connected MT5 "
        "terminal and differ only by the credentials the operator supplies.",
        allowed_values=("sim", "demo", "live"),
        activation="hot",
    ),
    _SettingDefinition(
        "RUNTIME_BROKER",
        "Runtime broker",
        "Provider selected for composed broker operations.",
        allowed_values=("binance", "ctrader", "dukascopy", "mt5", "yahoo"),
    ),
    _SettingDefinition(
        "TIMEZONE",
        "Display timezone",
        "Operator-facing display timezone (UTC offset label).",
    ),
    _SettingDefinition(
        "MT5_ENABLED",
        "Enable MT5",
        "Allow composition of the MT5 provider when bootstrap policy permits it.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "MT5_TERMINAL_PATH",
        "MT5 terminal path",
        "Local MT5 terminal executable path.",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_HOST",
        "MT5 snapshot host",
        "Local interface used by the authenticated MT5 snapshot listener.",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_PORT",
        "MT5 snapshot port",
        "TCP port used by the authenticated MT5 snapshot listener.",
        value_kind="integer",
        minimum=1,
        maximum=65_535,
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_CONNECT_TIMEOUT_MS",
        "MT5 connection timeout",
        "EA connection timeout in milliseconds.",
        value_kind="integer",
        minimum=100,
        maximum=60_000,
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_INTERVAL_SECONDS",
        "MT5 snapshot interval",
        "Expected interval between complete multi-symbol snapshots.",
        value_kind="integer",
        minimum=1,
        maximum=3_600,
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_SOURCE_ID",
        "MT5 snapshot source",
        "Exact source identity declared by the bridge EA.",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_SYMBOLS",
        "MT5 bootstrap symbols",
        "Comma-separated broker-native fallback used before runtime demand is applied.",
    ),
    _SettingDefinition(
        "MT5_PIP_SIZES",
        "MT5 pip sizes",
        "Comma-separated broker-symbol pip sizes, for example "
        "EURUSD=0.0001,XAUUSD=0.1.",
    ),
    _SettingDefinition(
        "MT5_SNAPSHOT_LOG_SNAPSHOTS",
        "Log MT5 snapshots",
        "Enable bounded snapshot lifecycle logging without quote or secret payloads.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "CTRADER_ENABLED",
        "Enable cTrader",
        "Allow composition of the cTrader provider when bootstrap policy permits it.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "CTRADER_REDIRECT_URL",
        "cTrader redirect URL",
        "Registered non-secret cTrader OAuth redirect URL.",
    ),
    _SettingDefinition(
        "BINANCE_ENABLED",
        "Enable Binance",
        "Allow composition of the Binance provider when bootstrap policy permits it.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "DUKASCOPY_ENABLED",
        "Enable Dukascopy",
        "Allow read-only Dukascopy provider composition.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "YAHOO_ENABLED",
        "Enable Yahoo Finance",
        "Allow read-only Yahoo Finance provider composition.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "AI_MODEL_AGENT",
        "Agent model",
        "Default model for agent workloads.",
    ),
    _SettingDefinition(
        "AI_MODEL_FAST",
        "Fast model",
        "Model selected for latency-sensitive workloads.",
    ),
    _SettingDefinition(
        "AI_MODEL_PREMIUM",
        "Premium model",
        "Model selected for highest-quality workloads.",
    ),
    _SettingDefinition(
        "AI_MODEL_FALLBACK",
        "Fallback model",
        "Explicit fallback model selected by policy.",
    ),
    _SettingDefinition(
        "AI_TEMPERATURE",
        "Temperature",
        "Sampling temperature for configured AI workloads.",
        value_kind="decimal",
        minimum=0.0,
        maximum=2.0,
    ),
    _SettingDefinition(
        "AI_MAX_TOKENS",
        "Maximum tokens",
        "Maximum generated tokens for configured AI workloads.",
        value_kind="integer",
        minimum=1,
        maximum=1_000_000,
    ),
    _SettingDefinition(
        "AI_TOP_P",
        "Top-p",
        "Nucleus sampling probability for configured AI workloads.",
        value_kind="decimal",
        minimum=0.0,
        maximum=1.0,
    ),
    _SettingDefinition(
        "AI_TOP_K",
        "Top-k",
        "Token candidate bound for providers that support top-k sampling.",
        value_kind="integer",
        minimum=1,
        maximum=1_000_000,
    ),
    _SettingDefinition(
        "GOOGLE_USE_VERTEXAI",
        "Use Vertex AI",
        "Select Vertex AI rather than the direct Google GenAI endpoint.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "GOOGLE_AGENT_MODEL",
        "Google agent model",
        "Google model used by agent workloads.",
    ),
    _SettingDefinition(
        "OPENAI_AGENT_MODEL",
        "OpenAI agent model",
        "OpenAI model used by agent workloads.",
    ),
    _SettingDefinition(
        "OPENAI_AGENT_MID",
        "OpenAI mid model",
        "OpenAI model used for balanced workloads.",
    ),
    _SettingDefinition(
        "OPENAI_AGENT_LIGHT",
        "OpenAI light model",
        "OpenAI model used for lightweight workloads.",
    ),
    _SettingDefinition(
        "OLLAMA_BASE_URL",
        "Ollama URL",
        "Base URL of the configured Ollama service.",
    ),
    _SettingDefinition(
        "OLLAMA_AGENT_MODEL",
        "Ollama agent model",
        "Ollama model used by agent workloads.",
    ),
    _SettingDefinition(
        "SMTP_HOST",
        "SMTP host",
        "SMTP server host name.",
    ),
    _SettingDefinition(
        "SMTP_PORT",
        "SMTP port",
        "SMTP server TCP port.",
        value_kind="integer",
        minimum=1,
        maximum=65_535,
    ),
    _SettingDefinition(
        "SMTP_TLS_MODE",
        "SMTP TLS mode",
        "SMTP transport security mode.",
        allowed_values=("ssl", "starttls", "none"),
    ),
    _SettingDefinition(
        "NOTIFICATIONS_ENABLED",
        "Enable notifications",
        "Master switch for all outbound notification channels.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "NOTIFICATION_DEFAULT_CHANNELS",
        "Default notification channels",
        "Comma-separated subset of desktop, email, telegram, and sms.",
    ),
    _SettingDefinition(
        "NOTIFICATION_RATE_LIMIT",
        "Notification rate limit",
        "Maximum messages per channel within one rate window.",
        value_kind="integer",
        minimum=1,
        maximum=10_000,
    ),
    _SettingDefinition(
        "NOTIFICATION_RATE_WINDOW_SECONDS",
        "Notification rate window",
        "Per-channel rate-limit window in seconds.",
        value_kind="decimal",
        minimum=0.1,
        maximum=86_400,
    ),
    _SettingDefinition(
        "NOTIFICATION_TIMEOUT_SECONDS",
        "Notification timeout",
        "External channel request timeout in seconds.",
        value_kind="decimal",
        minimum=0.1,
        maximum=60,
    ),
    *(
        _SettingDefinition(
            f"{channel.upper()}_NOTIFICATIONS_ENABLED",
            f"Enable {channel} notifications",
            f"Allow outbound {channel} notifications when the master switch "
            "is enabled.",
            value_kind="boolean",
        )
        for channel in ("desktop", "email", "telegram", "sms")
    ),
    _SettingDefinition(
        "LANGCHAIN_TRACING_V2",
        "LangChain tracing",
        "Enable LangChain v2 tracing.",
        value_kind="boolean",
    ),
    _SettingDefinition(
        "LANGCHAIN_PROJECT",
        "LangChain project",
        "Non-secret LangChain tracing project name.",
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
    "CTRADER_REDIRECT_URL": ("https://api.spotware.com/connect/tradingaccounts/token"),
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


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = _resolve_db_path(db_path)
    if not target.exists():
        msg = f"Database not found at {target}"
        raise FileNotFoundError(msg)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


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
        "version": 1,
        "updated_at": str(latest) if latest else _utc_now_iso(),
        "restart_required": False,
    }


def update_system_settings(
    settings_delta: dict[str, Any],
    changed_by: str = "system",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Update settings rows and record settings_history audit entries.

    Args:
        settings_delta: Wire-key to value mapping to persist.
        changed_by: Audit identity for the change record.
        db_path: Optional explicit database path.

    Returns:
        Updated system settings projection.
    """
    now = _utc_now_iso()
    conn = _get_connection(db_path)
    try:
        with conn:
            cur = conn.cursor()
            for wire_key, val in settings_delta.items():
                str_val = str(val) if val is not None else ""
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
        minimum, maximum, activation).
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
