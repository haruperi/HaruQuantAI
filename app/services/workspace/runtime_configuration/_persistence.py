"""Central SQLite persistence and unified settings store for HaruQuantAI."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

DEFAULT_CENTRAL_DB_PATH = Path("data/database/haruquantai.db")


def _utc_now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format.

    Returns:
        Formatted UTC timestamp string.
    """
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


CENTRAL_SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    value_type TEXT NOT NULL CHECK(
        value_type IN ('string', 'int', 'float', 'bool', 'json')
    ),
    category TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    is_secret INTEGER NOT NULL DEFAULT 0 CHECK(is_secret IN (0, 1)),
    is_readonly INTEGER NOT NULL DEFAULT 0 CHECK(is_readonly IN (0, 1)),
    default_value TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_settings_category ON settings(category);

CREATE TABLE IF NOT EXISTS settings_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    changed_by TEXT NOT NULL DEFAULT 'system',
    changed_at TEXT NOT NULL,
    FOREIGN KEY(key) REFERENCES settings(key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_settings_history_key ON settings_history(key);

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    roles_json TEXT NOT NULL,
    permissions_json TEXT NOT NULL,
    environment TEXT NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    verified INTEGER NOT NULL CHECK (verified IN (0, 1)),
    created_at TEXT NOT NULL,
    last_login_at TEXT,
    runtime_profile TEXT NOT NULL DEFAULT 'research' CHECK (
        runtime_profile IN ('research', 'simulation', 'demo', 'live')
    )
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS sessions (
    session_digest TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    csrf_digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

CREATE TABLE IF NOT EXISTS permissions (
    permission_id TEXT PRIMARY KEY,
    permission_key TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL,
    action TEXT NOT NULL CHECK (
        action IN ('read', 'write', 'execute', 'approve', 'admin')
    ),
    is_mutating INTEGER NOT NULL CHECK (is_mutating IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (permission_key NOT LIKE '%*%')
);

CREATE INDEX IF NOT EXISTS idx_permissions_domain ON permissions(domain);
"""

DEFAULT_SETTINGS_SEEDS: tuple[dict[str, object], ...] = (
    # 1. Credentials & Secrets (is_secret = 1)
    {
        "key": "credentials.google_api_key",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "Google AI Studio API Key",
        "description": "API key for Gemini models and Google AI endpoints",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.openai_api_key",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "OpenAI API Key",
        "description": "API key for OpenAI GPT models and embeddings",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.anthropic_api_key",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "Anthropic API Key",
        "description": "API key for Claude models",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.telegram_bot_token",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "Telegram Bot Token",
        "description": "Bot authentication token for Telegram alert dispatch",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.telegram_chat_id",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "Telegram Chat ID",
        "description": "Target chat identifier for operational alerts",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.smtp_username",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "SMTP Username",
        "description": "Email service username/address for notifications",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.smtp_password",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "SMTP Password",
        "description": "Email service application password",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.mt5_login",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "MetaTrader 5 Account Login",
        "description": "MT5 trading account login ID",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.mt5_password",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "MetaTrader 5 Account Password",
        "description": "MT5 trading account master password",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.mt5_server",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "MetaTrader 5 Broker Server",
        "description": "MT5 broker server name",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.ctrader_client_id",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "cTrader Open API Client ID",
        "description": "cTrader Open API Application Client ID",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.ctrader_client_secret",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "cTrader Open API Client Secret",
        "description": "cTrader Open API Application Secret",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.binance_api_key",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "Binance API Key",
        "description": "Binance exchange API key for data and execution",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.binance_api_secret",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "Binance API Secret",
        "description": "Binance exchange API secret",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    {
        "key": "credentials.langchain_api_key",
        "value": "",
        "value_type": "string",
        "category": "credentials",
        "label": "LangSmith / LangChain API Key",
        "description": "API key for LangChain / LangSmith tracing",
        "is_secret": 1,
        "is_readonly": 0,
        "default_value": "",
    },
    # 2. AI & Model Settings
    {
        "key": "ai.model_agent",
        "value": "gemini-3.6-flash",
        "value_type": "string",
        "category": "ai",
        "label": "Default Agent Model",
        "description": "Primary AI model used for orchestration and reasoning",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "gemini-3.6-flash",
    },
    {
        "key": "ai.model_fast",
        "value": "gemini-3.6-flash",
        "value_type": "string",
        "category": "ai",
        "label": "Fast AI Model",
        "description": "High-throughput, low-latency model for rapid processing",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "gemini-3.6-flash",
    },
    {
        "key": "ai.model_premium",
        "value": "gpt-5.6-sol",
        "value_type": "string",
        "category": "ai",
        "label": "Premium AI Model",
        "description": "Highest capability model for complex quantitative reasoning",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "gpt-5.6-sol",
    },
    {
        "key": "ai.model_fallback",
        "value": "glm-5.2",
        "value_type": "string",
        "category": "ai",
        "label": "Fallback AI Model",
        "description": "Secondary model used when primary provider is unavailable",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "glm-5.2",
    },
    {
        "key": "ai.temperature",
        "value": "0.2",
        "value_type": "float",
        "category": "ai",
        "label": "AI Temperature",
        "description": "Sampling temperature for model generation",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "0.2",
    },
    {
        "key": "ai.top_p",
        "value": "0.95",
        "value_type": "float",
        "category": "ai",
        "label": "AI Top-P",
        "description": "Nucleus sampling parameter for model generation",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "0.95",
    },
    {
        "key": "ai.top_k",
        "value": "40",
        "value_type": "int",
        "category": "ai",
        "label": "AI Top-K",
        "description": "Top-k vocabulary limit for model generation",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "40",
    },
    {
        "key": "ai.max_tokens",
        "value": "4096",
        "value_type": "int",
        "category": "ai",
        "label": "AI Max Output Tokens",
        "description": "Maximum token generation limit per response",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "4096",
    },
    {
        "key": "ai.google.agent_model",
        "value": "gemini-3.6-flash",
        "value_type": "string",
        "category": "ai",
        "label": "Google Agent Model",
        "description": "Configured Google AI model identifier",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "gemini-3.6-flash",
    },
    {
        "key": "ai.google.use_vertexai",
        "value": "false",
        "value_type": "bool",
        "category": "ai",
        "label": "Use Google Vertex AI",
        "description": "Route Google AI requests via Vertex AI endpoints",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    {
        "key": "ai.openai.agent_model",
        "value": "gpt-5.6-sol",
        "value_type": "string",
        "category": "ai",
        "label": "OpenAI Agent Model",
        "description": "Configured OpenAI model identifier",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "gpt-5.6-sol",
    },
    {
        "key": "ai.openai.agent_mid",
        "value": "gpt-5.6-terra",
        "value_type": "string",
        "category": "ai",
        "label": "OpenAI Mid Model",
        "description": "Medium-tier OpenAI model identifier",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "gpt-5.6-terra",
    },
    {
        "key": "ai.openai.agent_light",
        "value": "gpt-5.6-luna",
        "value_type": "string",
        "category": "ai",
        "label": "OpenAI Light Model",
        "description": "Lightweight OpenAI model identifier",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "gpt-5.6-luna",
    },
    {
        "key": "ai.ollama.agent_model",
        "value": "ollama/llama3.1:70b",
        "value_type": "string",
        "category": "ai",
        "label": "Ollama Agent Model",
        "description": "Local model identifier served via Ollama",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "ollama/llama3.1:70b",
    },
    {
        "key": "ai.ollama.base_url",
        "value": "http://localhost:11434",
        "value_type": "string",
        "category": "ai",
        "label": "Ollama Base URL",
        "description": "HTTP endpoint for local Ollama daemon",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "http://localhost:11434",
    },
    {
        "key": "ai.langchain.project",
        "value": "HaruQuant",
        "value_type": "string",
        "category": "ai",
        "label": "LangChain Project Name",
        "description": "Project workspace for LangChain / LangSmith tracing",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "HaruQuant",
    },
    {
        "key": "ai.langchain.tracing_v2",
        "value": "true",
        "value_type": "bool",
        "category": "ai",
        "label": "LangChain Tracing V2",
        "description": "Enable V2 LangSmith distributed tracing",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    # 3. System & Application Settings
    {
        "key": "system.app_name",
        "value": "haruquant-dev",
        "value_type": "string",
        "category": "system",
        "label": "Application Name",
        "description": "Running HaruQuantAI instance identifier",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "haruquant-dev",
    },
    {
        "key": "system.log_level",
        "value": "INFO",
        "value_type": "string",
        "category": "system",
        "label": "System Log Level",
        "description": "Logging verbosity threshold (DEBUG, INFO, WARNING, ERROR)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "INFO",
    },
    {
        "key": "system.timezone",
        "value": "UTC+3",
        "value_type": "string",
        "category": "system",
        "label": "Default Timezone",
        "description": "Application display and scheduling timezone",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "UTC+3",
    },
    {
        "key": "system.allow_live_mutations",
        "value": "false",
        "value_type": "bool",
        "category": "system",
        "label": "Allow Live Mutations",
        "description": "Safety gate: must be true to allow live broker orders",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    {
        "key": "system.audit_retention_days",
        "value": "90",
        "value_type": "int",
        "category": "system",
        "label": "Audit Retention (Days)",
        "description": "Number of days to keep settings audit records",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "90",
    },
    {
        "key": "system.telemetry_enabled",
        "value": "false",
        "value_type": "bool",
        "category": "system",
        "label": "Telemetry Enabled",
        "description": "Opt-in anonymous system performance telemetry",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    {
        "key": "system.max_memory_mb",
        "value": "8192",
        "value_type": "int",
        "category": "system",
        "label": "Max System Memory (MB)",
        "description": "Maximum memory ceiling allocated for background tasks",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "8192",
    },
    {
        "key": "system.maintenance_mode",
        "value": "false",
        "value_type": "bool",
        "category": "system",
        "label": "Maintenance Mode",
        "description": "When active, rejects new non-admin user requests",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    # 4. Broker Integration Settings
    {
        "key": "broker.runtime_broker",
        "value": "mt5",
        "value_type": "string",
        "category": "broker",
        "label": "Active Runtime Broker",
        "description": "Primary broker interface for execution (mt5, ctrader, binance)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "mt5",
    },
    {
        "key": "broker.mt5.enabled",
        "value": "true",
        "value_type": "bool",
        "category": "broker",
        "label": "MT5 Integration Enabled",
        "description": "Enable MetaTrader 5 gateway connection",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "broker.mt5.terminal_path",
        "value": "C:\\Program Files\\Pepperstone MetaTrader 5\\terminal64.exe",
        "value_type": "string",
        "category": "broker",
        "label": "MT5 Terminal Executable Path",
        "description": "Local filesystem path to MT5 terminal64.exe",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "C:\\Program Files\\Pepperstone MetaTrader 5\\terminal64.exe",
    },
    {
        "key": "broker.mt5.snapshot_host",
        "value": "127.0.0.1",
        "value_type": "string",
        "category": "broker",
        "label": "MT5 Snapshot Bridge Host",
        "description": "Host IP address for local MT5 bridge feed",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "127.0.0.1",
    },
    {
        "key": "broker.mt5.snapshot_port",
        "value": "9001",
        "value_type": "int",
        "category": "broker",
        "label": "MT5 Snapshot Bridge Port",
        "description": "TCP port for MT5 bridge communication",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "9001",
    },
    {
        "key": "broker.mt5.snapshot_symbols",
        "value": "EURUSD,GBPUSD,USDJPY,XAUUSD",
        "value_type": "string",
        "category": "broker",
        "label": "MT5 Monitored Symbols",
        "description": "Comma-delimited list of active trading symbols",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "EURUSD,GBPUSD,USDJPY,XAUUSD",
    },
    {
        "key": "broker.mt5.snapshot_interval_seconds",
        "value": "1",
        "value_type": "int",
        "category": "broker",
        "label": "MT5 Snapshot Interval (Seconds)",
        "description": "Frequency of market quote snapshots from MT5",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "1",
    },
    {
        "key": "broker.mt5.snapshot_connect_timeout_ms",
        "value": "1000",
        "value_type": "int",
        "category": "broker",
        "label": "MT5 Connect Timeout (ms)",
        "description": "Connection timeout in milliseconds for MT5 bridge",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "1000",
    },
    {
        "key": "broker.mt5.snapshot_log_snapshots",
        "value": "true",
        "value_type": "bool",
        "category": "broker",
        "label": "Log MT5 Snapshots",
        "description": "Record quote snapshot metrics to operational logs",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "broker.mt5.snapshot_source_id",
        "value": "mt5-terminal-1",
        "value_type": "string",
        "category": "broker",
        "label": "MT5 Snapshot Source ID",
        "description": "Identifier tag for snapshot telemetry stream",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "mt5-terminal-1",
    },
    {
        "key": "broker.ctrader.enabled",
        "value": "true",
        "value_type": "bool",
        "category": "broker",
        "label": "cTrader Enabled",
        "description": "Enable Spotware cTrader Open API integration",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "broker.ctrader.redirect_url",
        "value": "https://api.spotware.com/connect/tradingaccounts/token",
        "value_type": "string",
        "category": "broker",
        "label": "cTrader OAuth Redirect URL",
        "description": "OAuth token exchange endpoint for cTrader authentication",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "https://api.spotware.com/connect/tradingaccounts/token",
    },
    {
        "key": "broker.binance.enabled",
        "value": "true",
        "value_type": "bool",
        "category": "broker",
        "label": "Binance Enabled",
        "description": "Enable Binance crypto market feed and execution",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "broker.dukascopy.enabled",
        "value": "true",
        "value_type": "bool",
        "category": "broker",
        "label": "Dukascopy Feed Enabled",
        "description": "Enable Dukascopy historical tick and bar downloads",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "broker.yahoo.enabled",
        "value": "true",
        "value_type": "bool",
        "category": "broker",
        "label": "Yahoo Finance Feed Enabled",
        "description": "Enable Yahoo Finance public market data queries",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    # 5. Notification Settings
    {
        "key": "notification.enabled",
        "value": "true",
        "value_type": "bool",
        "category": "notification",
        "label": "Notifications Master Switch",
        "description": "Master switch to enable/disable outbound dispatching",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "notification.default_channels",
        "value": "desktop,telegram",
        "value_type": "string",
        "category": "notification",
        "label": "Default Alert Channels",
        "description": "Comma-delimited default channels (desktop, telegram, email)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "desktop,telegram",
    },
    {
        "key": "notification.desktop_enabled",
        "value": "true",
        "value_type": "bool",
        "category": "notification",
        "label": "Desktop Toast Notifications",
        "description": "Display OS desktop notifications for trade alerts",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "notification.telegram_enabled",
        "value": "true",
        "value_type": "bool",
        "category": "notification",
        "label": "Telegram Notifications",
        "description": "Send trade fills and system alerts to Telegram",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "notification.email_enabled",
        "value": "false",
        "value_type": "bool",
        "category": "notification",
        "label": "Email Notifications",
        "description": "Send periodic summary reports via SMTP email",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    {
        "key": "notification.rate_limit",
        "value": "60",
        "value_type": "int",
        "category": "notification",
        "label": "Notification Rate Limit (Max Count)",
        "description": "Maximum number of messages permitted per rate window",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "60",
    },
    {
        "key": "notification.rate_window_seconds",
        "value": "60",
        "value_type": "int",
        "category": "notification",
        "label": "Rate Limit Window (Seconds)",
        "description": "Sliding time window in seconds for dispatch rate limiting",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "60",
    },
    {
        "key": "notification.timeout_seconds",
        "value": "60",
        "value_type": "int",
        "category": "notification",
        "label": "Notification Dispatch Timeout",
        "description": "Network timeout in seconds for alert delivery requests",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "60",
    },
    {
        "key": "notification.smtp.host",
        "value": "smtp.gmail.com",
        "value_type": "string",
        "category": "notification",
        "label": "SMTP Server Host",
        "description": "Outbound SMTP server hostname",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "smtp.gmail.com",
    },
    {
        "key": "notification.smtp.port",
        "value": "587",
        "value_type": "int",
        "category": "notification",
        "label": "SMTP Server Port",
        "description": "Outbound SMTP server port (587 for STARTTLS, 465 for SSL)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "587",
    },
    # 6. Trading & Order Execution Settings
    {
        "key": "trading.account_mode",
        "value": "sim",
        "value_type": "string",
        "category": "trading",
        "label": "Account Trading Mode",
        "description": "Execution routing mode: sim, demo, or live",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "sim",
    },
    {
        "key": "trading.default_order_type",
        "value": "market",
        "value_type": "string",
        "category": "trading",
        "label": "Default Order Type",
        "description": "Default entry order style (market, limit, stop)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "market",
    },
    {
        "key": "trading.max_slippage_pips",
        "value": "3.0",
        "value_type": "float",
        "category": "trading",
        "label": "Max Allowed Slippage (Pips)",
        "description": "Maximum price tolerance for market execution fills",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "3.0",
    },
    {
        "key": "trading.auto_stop_loss_pips",
        "value": "25.0",
        "value_type": "float",
        "category": "trading",
        "label": "Default Stop Loss (Pips)",
        "description": "Default protective stop distance applied if omitted",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "25.0",
    },
    {
        "key": "trading.auto_take_profit_pips",
        "value": "50.0",
        "value_type": "float",
        "category": "trading",
        "label": "Default Take Profit (Pips)",
        "description": "Default profit target distance applied if omitted",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "50.0",
    },
    {
        "key": "trading.max_open_positions",
        "value": "10",
        "value_type": "int",
        "category": "trading",
        "label": "Max Open Positions",
        "description": "Concurrent position limit across all symbols",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "10",
    },
    {
        "key": "trading.cooldown_seconds_after_loss",
        "value": "300",
        "value_type": "int",
        "category": "trading",
        "label": "Loss Cooldown (Seconds)",
        "description": "Mandatory trading pause after consecutive losses",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "300",
    },
    # 7. Risk Management Settings
    {
        "key": "risk.max_risk_per_trade_pct",
        "value": "1.0",
        "value_type": "float",
        "category": "risk",
        "label": "Max Risk Per Trade (%)",
        "description": "Maximum equity risk allocation per single trade",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "1.0",
    },
    {
        "key": "risk.max_daily_drawdown_pct",
        "value": "4.0",
        "value_type": "float",
        "category": "risk",
        "label": "Max Daily Drawdown (%)",
        "description": "Daily portfolio loss threshold triggering safety halts",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "4.0",
    },
    {
        "key": "risk.max_total_drawdown_pct",
        "value": "10.0",
        "value_type": "float",
        "category": "risk",
        "label": "Max Total Drawdown (%)",
        "description": "Total peak-to-trough equity drawdown limit",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "10.0",
    },
    {
        "key": "risk.max_leverage",
        "value": "30.0",
        "value_type": "float",
        "category": "risk",
        "label": "Max Effective Leverage",
        "description": "Maximum permissible account leverage ratio",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "30.0",
    },
    {
        "key": "risk.kill_switch_active",
        "value": "false",
        "value_type": "bool",
        "category": "risk",
        "label": "Global Kill Switch",
        "description": "Emergency circuit breaker: closes positions, blocks orders",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    {
        "key": "risk.enforce_hard_stop_loss",
        "value": "true",
        "value_type": "bool",
        "category": "risk",
        "label": "Enforce Hard Stop Loss",
        "description": "Require broker-side stop orders for all open positions",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "risk.allowed_trading_hours_utc",
        "value": "00:00-23:59",
        "value_type": "string",
        "category": "risk",
        "label": "Allowed Trading Hours (UTC)",
        "description": "Permitted trading window in UTC (HH:MM-HH:MM)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "00:00-23:59",
    },
    # 8. Workspace & Storage Settings
    {
        "key": "workspace.runtime_profile",
        "value": "research",
        "value_type": "string",
        "category": "workspace",
        "label": "Default Workspace Runtime Profile",
        "description": "Profile for workspaces (research, simulation, demo, live)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "research",
    },
    {
        "key": "workspace.worker_count",
        "value": "4",
        "value_type": "int",
        "category": "workspace",
        "label": "Workspace Worker Count",
        "description": "Concurrent worker processes allocated for background tasks",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "4",
    },
    {
        "key": "workspace.worker_memory_mb",
        "value": "2048",
        "value_type": "int",
        "category": "workspace",
        "label": "Worker Memory Limit (MB)",
        "description": "Memory ceiling in MiB per worker process",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "2048",
    },
    {
        "key": "workspace.max_file_size_bytes",
        "value": "104857600",
        "value_type": "int",
        "category": "workspace",
        "label": "Max Upload File Size (Bytes)",
        "description": "Upload size limit for workspace files (100 MB)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "104857600",
    },
    {
        "key": "workspace.max_total_storage_mb",
        "value": "51200",
        "value_type": "int",
        "category": "workspace",
        "label": "Total Workspace Storage Cap (MB)",
        "description": "Total disk quota per workspace in MiB (50 GB)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "51200",
    },
    {
        "key": "workspace.max_artifact_size_mb",
        "value": "2048",
        "value_type": "int",
        "category": "workspace",
        "label": "Max Artifact Size (MB)",
        "description": "Maximum size per generated artifact file",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "2048",
    },
    {
        "key": "workspace.min_free_space_mb",
        "value": "1024",
        "value_type": "int",
        "category": "workspace",
        "label": "Min Free Disk Space (MB)",
        "description": "Minimum required free disk space before admitting jobs",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "1024",
    },
    {
        "key": "workspace.auto_purge_days",
        "value": "30",
        "value_type": "int",
        "category": "workspace",
        "label": "Artifact Auto-Purge (Days)",
        "description": "Retention lifespan for temporary staging and scratch artifacts",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "30",
    },
    {
        "key": "workspace.enable_distributed_pool",
        "value": "false",
        "value_type": "bool",
        "category": "workspace",
        "label": "Enable Distributed Worker Pool",
        "description": "Allow worker tasks to be dispatched to remote worker nodes",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    {
        "key": "workspace.backup_on_shutdown",
        "value": "true",
        "value_type": "bool",
        "category": "workspace",
        "label": "Backup Workspace on Shutdown",
        "description": "Create automated snapshot checkpoint on clean shutdown",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "workspace.diagnostics_interval_minutes",
        "value": "15",
        "value_type": "int",
        "category": "workspace",
        "label": "Diagnostic Interval (Minutes)",
        "description": "Frequency of workspace health and resource scans",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "15",
    },
    {
        "key": "workspace.default_locale",
        "value": "en-US",
        "value_type": "string",
        "category": "workspace",
        "label": "Workspace Locale",
        "description": "Default regional formatting locale code",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "en-US",
    },
    # 9. Server & Network Settings
    {
        "key": "server.host",
        "value": "127.0.0.1",
        "value_type": "string",
        "category": "server",
        "label": "HTTP Server Bind Host",
        "description": "Network interface address to bind HTTP API server",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "127.0.0.1",
    },
    {
        "key": "server.port",
        "value": "8000",
        "value_type": "int",
        "category": "server",
        "label": "HTTP Server Port",
        "description": "TCP port for HTTP API listener",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "8000",
    },
    {
        "key": "server.headless",
        "value": "false",
        "value_type": "bool",
        "category": "server",
        "label": "Headless Server Mode",
        "description": "Run server without initiating local desktop GUI window",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    {
        "key": "server.allow_non_loopback",
        "value": "false",
        "value_type": "bool",
        "category": "server",
        "label": "Allow External Non-Loopback Traffic",
        "description": "Permit connections from non-127.0.0.1 external IP addresses",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
    {
        "key": "server.cors_origins",
        "value": '["http://localhost:3000", "http://localhost:5173"]',
        "value_type": "json",
        "category": "server",
        "label": "Allowed CORS Origins",
        "description": "List of authorized cross-origin URL origins",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": '["http://localhost:3000", "http://localhost:5173"]',
    },
    {
        "key": "server.request_timeout_seconds",
        "value": "30",
        "value_type": "int",
        "category": "server",
        "label": "HTTP Request Timeout",
        "description": "Maximum seconds to wait before timing out API requests",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "30",
    },
    # 10. Data Ingestion & Market Feeds
    {
        "key": "data.default_timeframe",
        "value": "1h",
        "value_type": "string",
        "category": "data",
        "label": "Default Bar Timeframe",
        "description": "Standard OHLCV bar timeframe (1m, 5m, 15m, 1h, 4h, 1d)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "1h",
    },
    {
        "key": "data.cache_retention_days",
        "value": "30",
        "value_type": "int",
        "category": "data",
        "label": "Market Data Cache (Days)",
        "description": "Number of days cached historical bars remain active on disk",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "30",
    },
    {
        "key": "data.auto_sync_on_launch",
        "value": "true",
        "value_type": "bool",
        "category": "data",
        "label": "Auto Sync Market Data on Startup",
        "description": "Automatically download missing bars upon engine boot",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "true",
    },
    {
        "key": "data.historical_provider",
        "value": "mt5",
        "value_type": "string",
        "category": "data",
        "label": "Historical Data Provider",
        "description": "Preferred primary data provider (mt5, dukascopy, yahoo)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "mt5",
    },
    # 11. UI & Visual Theme Settings
    {
        "key": "ui.theme",
        "value": "dark",
        "value_type": "string",
        "category": "ui",
        "label": "Application Visual Theme",
        "description": "UI appearance theme (dark, light, high-contrast, cyberpunk)",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "dark",
    },
    {
        "key": "ui.chart_default_indicators",
        "value": '["EMA_20", "EMA_50", "RSI_14"]',
        "value_type": "json",
        "category": "ui",
        "label": "Default Chart Indicators",
        "description": "Technical indicators loaded on new symbol charts",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": '["EMA_20", "EMA_50", "RSI_14"]',
    },
    {
        "key": "ui.sidebar_collapsed",
        "value": "false",
        "value_type": "bool",
        "category": "ui",
        "label": "Sidebar Collapsed Default",
        "description": "Whether navigation sidebar is initially minimized",
        "is_secret": 0,
        "is_readonly": 0,
        "default_value": "false",
    },
)

DEFAULT_USERS_SEEDS: tuple[dict[str, object], ...] = (
    {
        "user_id": "user_system",
        "username": "system",
        "password_hash": (  # pragma: allowlist secret
            "argon2id$v=19$m=65536,t=3,p=4$system_internal_placeholder"
        ),
        "roles_json": '["system", "admin"]',
        "permissions_json": '["*"]',
        "environment": "production",
        "active": 1,
        "verified": 1,
        "created_at": "2026-09-02T00:00:00Z",
        "last_login_at": None,
        "runtime_profile": "research",
    },
    {
        "user_id": "user_admin",
        "username": "admin",
        "password_hash": (  # pragma: allowlist secret
            "argon2id$v=19$m=65536,t=3,p=4$admin_default_placeholder"
        ),
        "roles_json": '["admin"]',
        "permissions_json": '["*"]',
        "environment": "development",
        "active": 1,
        "verified": 1,
        "created_at": "2026-09-02T00:00:00Z",
        "last_login_at": None,
        "runtime_profile": "research",
    },
)

DEFAULT_PERMISSIONS_SEEDS: tuple[dict[str, object], ...] = (
    {
        "permission_id": "perm_ws_read",
        "permission_key": "workspace:read",
        "domain": "workspace",
        "action": "read",
        "is_mutating": 0,
    },
    {
        "permission_id": "perm_ws_write",
        "permission_key": "workspace:write",
        "domain": "workspace",
        "action": "write",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_ws_execute",
        "permission_key": "workspace:execute",
        "domain": "workspace",
        "action": "execute",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_ws_approve",
        "permission_key": "workspace:approve",
        "domain": "workspace",
        "action": "approve",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_ws_admin",
        "permission_key": "workspace:admin",
        "domain": "workspace",
        "action": "admin",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_broker_read",
        "permission_key": "broker:read",
        "domain": "broker",
        "action": "read",
        "is_mutating": 0,
    },
    {
        "permission_id": "perm_broker_write",
        "permission_key": "broker:write",
        "domain": "broker",
        "action": "write",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_broker_execute",
        "permission_key": "broker:execute",
        "domain": "broker",
        "action": "execute",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_broker_approve",
        "permission_key": "broker:approve",
        "domain": "broker",
        "action": "approve",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_broker_admin",
        "permission_key": "broker:admin",
        "domain": "broker",
        "action": "admin",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_trading_read",
        "permission_key": "trading:read",
        "domain": "trading",
        "action": "read",
        "is_mutating": 0,
    },
    {
        "permission_id": "perm_trading_write",
        "permission_key": "trading:write",
        "domain": "trading",
        "action": "write",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_trading_execute",
        "permission_key": "trading:execute",
        "domain": "trading",
        "action": "execute",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_trading_approve",
        "permission_key": "trading:approve",
        "domain": "trading",
        "action": "approve",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_trading_admin",
        "permission_key": "trading:admin",
        "domain": "trading",
        "action": "admin",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_risk_read",
        "permission_key": "risk:read",
        "domain": "risk",
        "action": "read",
        "is_mutating": 0,
    },
    {
        "permission_id": "perm_risk_write",
        "permission_key": "risk:write",
        "domain": "risk",
        "action": "write",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_risk_approve",
        "permission_key": "risk:approve",
        "domain": "risk",
        "action": "approve",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_risk_admin",
        "permission_key": "risk:admin",
        "domain": "risk",
        "action": "admin",
        "is_mutating": 1,
    },
    {
        "permission_id": "perm_system_read",
        "permission_key": "system:read",
        "domain": "system",
        "action": "read",
        "is_mutating": 0,
    },
    {
        "permission_id": "perm_system_admin",
        "permission_key": "system:admin",
        "domain": "system",
        "action": "admin",
        "is_mutating": 1,
    },
)


def _resolve_central_db_path(db_path: Path | str | None = None) -> Path:
    """Resolve target central database path to an absolute path.

    Args:
        db_path: Optional custom database path.

    Returns:
        Resolved absolute Path.
    """
    target = Path(db_path) if db_path is not None else DEFAULT_CENTRAL_DB_PATH
    return target.resolve()


def _cast_from_db(value_str: str, value_type: str) -> object:
    """Convert string database representation to native Python type.

    Args:
        value_str: Raw string value from SQLite.
        value_type: Type identifier ('string', 'int', 'float', 'bool', 'json').

    Returns:
        Cast native Python value (str, int, float, bool, or parsed JSON).
    """
    if value_type == "int":
        return int(value_str)
    if value_type == "float":
        return float(value_str)
    if value_type == "bool":
        return value_str.lower() in ("true", "1", "t", "yes")
    if value_type == "json":
        return json.loads(value_str)
    return value_str


def _cast_to_db(value: object, value_type: str) -> str:
    """Convert native Python value to canonical database string representation.

    Args:
        value: Input Python object to serialize.
        value_type: Target database type descriptor.

    Returns:
        Canonical string representation for SQLite storage.
    """
    if value_type == "bool":
        if isinstance(value, str) and value.lower() in ("true", "false"):
            res = value.lower()
        else:
            res = "true" if bool(value) else "false"
    elif value_type == "int":
        res = str(int(cast("Any", value)))
    elif value_type == "float":
        res = str(float(cast("Any", value)))
    elif value_type == "json":
        if isinstance(value, str):
            json.loads(value)
            res = value
        else:
            res = json.dumps(value, sort_keys=True)
    else:
        res = str(value)
    return res


def init_central_database(db_path: Path | str | None = None) -> Path:
    """Initialize the central application SQLite database with all tables and seeds.

    Creates parent directory, applies the 5-table schema, and seeds default
    settings, users, and permissions if not already present.

    Args:
        db_path: Optional custom database path.

    Returns:
        Resolved Path to the initialized database.
    """
    path = _resolve_central_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), timeout=10.0)
    try:
        conn.executescript(CENTRAL_SCHEMA_SQL)
        cursor = conn.cursor()
        now = _utc_now_iso()

        # 1. Seed settings
        for item in DEFAULT_SETTINGS_SEEDS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO settings (
                    key, value, value_type, category, label, description,
                    is_secret, is_readonly, default_value, updated_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    item["key"],
                    item["value"],
                    item["value_type"],
                    item["category"],
                    item["label"],
                    item["description"],
                    item["is_secret"],
                    item["is_readonly"],
                    item["default_value"],
                    now,
                    now,
                ),
            )

        # 2. Seed default users
        for user in DEFAULT_USERS_SEEDS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (
                    user_id, username, password_hash, roles_json,
                    permissions_json, environment, active, verified,
                    created_at, last_login_at, runtime_profile
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    user["user_id"],
                    user["username"],
                    user["password_hash"],
                    user["roles_json"],
                    user["permissions_json"],
                    user["environment"],
                    user["active"],
                    user["verified"],
                    user["created_at"],
                    user["last_login_at"],
                    user["runtime_profile"],
                ),
            )

        # 3. Seed default permissions
        for perm in DEFAULT_PERMISSIONS_SEEDS:
            cursor.execute(
                """
                INSERT OR IGNORE INTO permissions (
                    permission_id, permission_key, domain, action, is_mutating,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    perm["permission_id"],
                    perm["permission_key"],
                    perm["domain"],
                    perm["action"],
                    perm["is_mutating"],
                    now,
                    now,
                ),
            )

        conn.commit()
        return path
    finally:
        conn.close()


def get_setting(
    key: str,
    default: object = None,
    db_path: Path | str | None = None,
) -> object:
    """Retrieve a typed setting value from the central database.

    Args:
        key: Unique setting key identifier.
        default: Fallback value when key is absent.
        db_path: Optional custom database path.

    Returns:
        Properly cast typed value (str, int, float, bool, or json object).
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value, value_type FROM settings WHERE key = ?;", (key,))
        row = cursor.fetchone()
        if row is None:
            return default
        return _cast_from_db(str(row[0]), str(row[1]))
    finally:
        conn.close()


def set_setting(
    key: str,
    value: object,
    changed_by: str = "system",
    db_path: Path | str | None = None,
) -> None:
    """Update or insert a typed setting and record an audit history entry.

    Args:
        key: Unique setting key identifier.
        value: Setting value to validate and store.
        changed_by: Identifier of the user or subsystem performing the update.
        db_path: Optional custom database path.

    Raises:
        ValueError: If the setting is marked as read-only.
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")
        cursor.execute(
            "SELECT value, value_type, is_readonly FROM settings WHERE key = ?;",
            (key,),
        )
        row = cursor.fetchone()
        now = _utc_now_iso()

        if row is not None:
            old_value = str(row[0])
            value_type = str(row[1])
            is_readonly = int(row[2])

            if is_readonly:
                msg = f"Setting '{key}' is read-only and cannot be modified."
                raise ValueError(msg)

            new_value_str = _cast_to_db(value, value_type)
            if old_value != new_value_str:
                cursor.execute(
                    "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?;",
                    (new_value_str, now, key),
                )
                cursor.execute(
                    """
                    INSERT INTO settings_history (
                        key, old_value, new_value, changed_by, changed_at
                    ) VALUES (?, ?, ?, ?, ?);
                    """,
                    (key, old_value, new_value_str, changed_by, now),
                )
        else:
            # Auto-infer type if creating dynamic key
            if isinstance(value, bool):
                vtype = "bool"
            elif isinstance(value, int):
                vtype = "int"
            elif isinstance(value, float):
                vtype = "float"
            elif isinstance(value, (dict, list)):
                vtype = "json"
            else:
                vtype = "string"

            new_value_str = _cast_to_db(value, vtype)
            category = key.split(".", maxsplit=1)[0] if "." in key else "custom"
            cursor.execute(
                """
                INSERT INTO settings (
                    key, value, value_type, category, label, description,
                    is_secret, is_readonly, default_value, updated_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?);
                """,
                (key, new_value_str, vtype, category, key, "", new_value_str, now, now),
            )
            cursor.execute(
                """
                INSERT INTO settings_history (
                    key, old_value, new_value, changed_by, changed_at
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (key, "", new_value_str, changed_by, now),
            )
        conn.commit()
    finally:
        conn.close()


def set_settings(
    items: Mapping[str, object],
    changed_by: str = "system",
    db_path: Path | str | None = None,
) -> None:
    """Batch update multiple settings in a single atomic transaction.

    Args:
        items: Mapping of key to new setting values.
        changed_by: Identifier of the updater.
        db_path: Optional custom database path.

    Raises:
        ValueError: If any setting is marked as read-only.
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")
        now = _utc_now_iso()

        for key, value in items.items():
            cursor.execute(
                "SELECT value, value_type, is_readonly FROM settings WHERE key = ?;",
                (key,),
            )
            row = cursor.fetchone()
            if row is not None:
                old_value = str(row[0])
                value_type = str(row[1])
                if int(row[2]):
                    msg = f"Setting '{key}' is read-only."
                    raise ValueError(msg)
                new_value_str = _cast_to_db(value, value_type)
                if old_value != new_value_str:
                    cursor.execute(
                        "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?;",
                        (new_value_str, now, key),
                    )
                    cursor.execute(
                        """
                        INSERT INTO settings_history (
                            key, old_value, new_value, changed_by, changed_at
                        ) VALUES (?, ?, ?, ?, ?);
                        """,
                        (key, old_value, new_value_str, changed_by, now),
                    )
            else:
                vtype = "string"
                new_value_str = str(value)
                category = key.split(".", maxsplit=1)[0] if "." in key else "custom"
                cursor.execute(
                    """
                    INSERT INTO settings (
                        key, value, value_type, category, label, description,
                        is_secret, is_readonly, default_value, updated_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?);
                    """,
                    (
                        key,
                        new_value_str,
                        vtype,
                        category,
                        key,
                        "",
                        new_value_str,
                        now,
                        now,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO settings_history (
                        key, old_value, new_value, changed_by, changed_at
                    ) VALUES (?, ?, ?, ?, ?);
                    """,
                    (key, "", new_value_str, changed_by, now),
                )
        conn.commit()
    finally:
        conn.close()


def get_category_settings(
    category: str,
    db_path: Path | str | None = None,
) -> dict[str, object]:
    """Return all key-value pairs belonging to a category.

    Args:
        category: Category name (e.g. 'system', 'trading', 'ai', 'broker').
        db_path: Optional custom database path.

    Returns:
        Dictionary of key -> typed value for the category.
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT key, value, value_type FROM settings
            WHERE category = ? ORDER BY key;
            """,
            (category,),
        )
        rows = cursor.fetchall()
        return {str(r[0]): _cast_from_db(str(r[1]), str(r[2])) for r in rows}
    finally:
        conn.close()


def get_all_settings(db_path: Path | str | None = None) -> dict[str, object]:
    """Return all settings as a flat key-value dictionary.

    Args:
        db_path: Optional custom database path.

    Returns:
        Dictionary of key -> typed value across all categories.
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key, value, value_type FROM settings ORDER BY category, key;"
        )
        rows = cursor.fetchall()
        return {str(r[0]): _cast_from_db(str(r[1]), str(r[2])) for r in rows}
    finally:
        conn.close()


def reset_setting_to_default(
    key: str,
    changed_by: str = "system",
    db_path: Path | str | None = None,
) -> None:
    """Reset a setting back to its configured default_value.

    Args:
        key: Unique setting key.
        changed_by: Identifier of the actor resetting the setting.
        db_path: Optional custom database path.

    Raises:
        KeyError: If the setting does not exist.
        ValueError: If the setting is marked as read-only.
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN IMMEDIATE;")
        cursor.execute(
            """
            SELECT value, default_value, value_type, is_readonly
            FROM settings WHERE key = ?;
            """,
            (key,),
        )
        row = cursor.fetchone()
        if row is None:
            msg = f"Setting '{key}' not found."
            raise KeyError(msg)
        if int(row[3]):
            msg = f"Setting '{key}' is read-only."
            raise ValueError(msg)

        old_value = str(row[0])
        default_val = str(row[1])
        now = _utc_now_iso()

        if old_value != default_val:
            cursor.execute(
                "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?;",
                (default_val, now, key),
            )
            cursor.execute(
                """
                INSERT INTO settings_history (
                    key, old_value, new_value, changed_by, changed_at
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (key, old_value, default_val, changed_by, now),
            )
        conn.commit()
    finally:
        conn.close()


def get_setting_record(
    key: str, db_path: Path | str | None = None
) -> dict[str, object] | None:
    """Retrieve full setting metadata record by key.

    Args:
        key: Unique setting key identifier.
        db_path: Optional custom database path.

    Returns:
        Dictionary with full row metadata or None if missing.
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT key, value, value_type, category, label, description,
                   is_secret, is_readonly, default_value, updated_at, created_at
            FROM settings WHERE key = ?;
            """,
            (key,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "key": str(row[0]),
            "value": _cast_from_db(str(row[1]), str(row[2])),
            "raw_value": str(row[1]),
            "value_type": str(row[2]),
            "category": str(row[3]),
            "label": str(row[4]),
            "description": str(row[5]) if row[5] is not None else "",
            "is_secret": bool(row[6]),
            "is_readonly": bool(row[7]),
            "default_value": _cast_from_db(str(row[8]), str(row[2])),
            "updated_at": str(row[9]),
            "created_at": str(row[10]),
        }
    finally:
        conn.close()


def list_settings_records(
    category: str | None = None, db_path: Path | str | None = None
) -> list[dict[str, object]]:
    """List setting metadata records, optionally filtered by category.

    Args:
        category: Optional category filter.
        db_path: Optional custom database path.

    Returns:
        List of setting records dictionaries.
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        if category:
            cursor.execute(
                """
                SELECT key, value, value_type, category, label, description,
                       is_secret, is_readonly, default_value, updated_at, created_at
                FROM settings WHERE category = ? ORDER BY key;
                """,
                (category,),
            )
        else:
            cursor.execute(
                """
                SELECT key, value, value_type, category, label, description,
                       is_secret, is_readonly, default_value, updated_at, created_at
                FROM settings ORDER BY category, key;
                """
            )
        rows = cursor.fetchall()
        return [
            {
                "key": str(r[0]),
                "value": _cast_from_db(str(r[1]), str(r[2])),
                "raw_value": str(r[1]),
                "value_type": str(r[2]),
                "category": str(r[3]),
                "label": str(r[4]),
                "description": str(r[5]) if r[5] is not None else "",
                "is_secret": bool(r[6]),
                "is_readonly": bool(r[7]),
                "default_value": _cast_from_db(str(r[8]), str(r[2])),
                "updated_at": str(r[9]),
                "created_at": str(r[10]),
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_settings_history(
    key: str | None = None,
    limit: int = 100,
    db_path: Path | str | None = None,
) -> list[dict[str, object]]:
    """Retrieve audit history entries for settings.

    Args:
        key: Optional specific key to filter history for.
        limit: Maximum history rows to return.
        db_path: Optional custom database path.

    Returns:
        List of audit log dictionaries in reverse chronological order.
    """
    path = _resolve_central_db_path(db_path)
    if not path.exists():
        init_central_database(path)

    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        cursor = conn.cursor()
        if key:
            cursor.execute(
                """
                SELECT id, key, old_value, new_value, changed_by, changed_at
                FROM settings_history WHERE key = ?
                ORDER BY id DESC LIMIT ?;
                """,
                (key, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, key, old_value, new_value, changed_by, changed_at
                FROM settings_history
                ORDER BY id DESC LIMIT ?;
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        return [
            {
                "id": int(r[0]),
                "key": str(r[1]),
                "old_value": str(r[2]),
                "new_value": str(r[3]),
                "changed_by": str(r[4]),
                "changed_at": str(r[5]),
            }
            for r in rows
        ]
    finally:
        conn.close()
