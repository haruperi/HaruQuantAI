"""Authoritative classification for operator-managed application settings."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from types import MappingProxyType
from typing import Literal

from app.services.api.identity.errors import IdentityError

type SettingKind = Literal["boolean", "decimal", "integer", "string"]
type SettingClass = Literal["bootstrap", "credential", "static", "system"]
type ActivationMode = Literal["hot", "restart_required"]

_MAX_SETTING_VALUE_LENGTH = 256
_MAX_CREDENTIAL_VALUE_LENGTH = 8_192


@dataclass(frozen=True, slots=True)
class _SystemSettingDefinition:
    """Internal definition for one editable non-secret system setting."""

    key: str
    source_path: str
    label: str
    description: str
    value_kind: SettingKind = "string"
    allowed_values: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    activation: ActivationMode = "restart_required"


@dataclass(frozen=True, slots=True)
class _CredentialDefinition:
    """Internal definition for one write-only encrypted credential slot."""

    slot: str
    label: str
    fields: Mapping[str, str]


_SYSTEM_DEFINITIONS = (
    _SystemSettingDefinition(
        "APP_NAME",
        "settings.environment.app_name",
        "Application name",
        "Display name presented by the application.",
    ),
    _SystemSettingDefinition(
        "LOG_LEVEL",
        "settings.environment.log_level",
        "Log level",
        "Minimum application log severity.",
        allowed_values=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
    ),
    _SystemSettingDefinition(
        "RUNTIME_BROKER",
        "settings.environment.runtime_broker",
        "Runtime broker",
        "Provider selected for composed broker operations.",
        allowed_values=("binance", "ctrader", "dukascopy", "mt5", "yahoo"),
    ),
    _SystemSettingDefinition(
        "TIMEZONE",
        "settings.paths.timezone",
        "Display timezone",
        "IANA timezone used for operator-facing presentation.",
    ),
    _SystemSettingDefinition(
        "MT5_ENABLED",
        "settings.mt5.enabled",
        "Enable MT5",
        "Allow composition of the MT5 provider when bootstrap policy permits it.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "MT5_TERMINAL_PATH",
        "settings.mt5.terminal_path",
        "MT5 terminal path",
        "Local MT5 terminal executable path.",
    ),
    _SystemSettingDefinition(
        "MT5_SNAPSHOT_HOST",
        "settings.mt5.snapshot.host",
        "MT5 snapshot host",
        "Local interface used by the authenticated MT5 snapshot listener.",
    ),
    _SystemSettingDefinition(
        "MT5_SNAPSHOT_PORT",
        "settings.mt5.snapshot.port",
        "MT5 snapshot port",
        "TCP port used by the authenticated MT5 snapshot listener.",
        value_kind="integer",
        minimum=1,
        maximum=65_535,
    ),
    _SystemSettingDefinition(
        "MT5_SNAPSHOT_CONNECT_TIMEOUT_MS",
        "settings.mt5.snapshot.connect_timeout_ms",
        "MT5 connection timeout",
        "EA connection timeout in milliseconds, retained for configuration parity.",
        value_kind="integer",
        minimum=100,
        maximum=60_000,
    ),
    _SystemSettingDefinition(
        "MT5_SNAPSHOT_INTERVAL_SECONDS",
        "settings.mt5.snapshot.interval_seconds",
        "MT5 snapshot interval",
        "Expected interval between complete multi-symbol snapshots.",
        value_kind="integer",
        minimum=1,
        maximum=3_600,
    ),
    _SystemSettingDefinition(
        "MT5_SNAPSHOT_SOURCE_ID",
        "settings.mt5.snapshot.source_id",
        "MT5 snapshot source",
        "Exact source identity declared by the bridge EA.",
    ),
    _SystemSettingDefinition(
        "MT5_SNAPSHOT_SYMBOLS",
        "settings.mt5.snapshot.symbols",
        "MT5 bootstrap symbols",
        "Comma-separated broker-native fallback used before runtime demand is applied.",
    ),
    _SystemSettingDefinition(
        "MT5_PIP_SIZES",
        "settings.mt5.pip_sizes",
        "MT5 pip sizes",
        "Comma-separated broker-symbol pip sizes, for example "
        "EURUSD=0.0001,XAUUSD=0.1.",
    ),
    _SystemSettingDefinition(
        "MT5_SNAPSHOT_LOG_SNAPSHOTS",
        "settings.mt5.snapshot.log_snapshots",
        "Log MT5 snapshots",
        "Enable bounded snapshot lifecycle logging without quote or secret payloads.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "CTRADER_ENABLED",
        "settings.ctrader.enabled",
        "Enable cTrader",
        "Allow composition of the cTrader provider when bootstrap policy permits it.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "CTRADER_REDIRECT_URL",
        "settings.ctrader.redirect_url",
        "cTrader redirect URL",
        "Registered non-secret cTrader OAuth redirect URL.",
    ),
    _SystemSettingDefinition(
        "BINANCE_ENABLED",
        "settings.binance.enabled",
        "Enable Binance",
        "Allow composition of the Binance provider when bootstrap policy permits it.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "DUKASCOPY_ENABLED",
        "settings.dukascopy.enabled",
        "Enable Dukascopy",
        "Allow read-only Dukascopy provider composition.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "YAHOO_ENABLED",
        "settings.yahoo.enabled",
        "Enable Yahoo Finance",
        "Allow read-only Yahoo Finance provider composition.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "AI_MODEL_AGENT",
        "settings.ai_model.agent",
        "Agent model",
        "Default model for agent workloads.",
    ),
    _SystemSettingDefinition(
        "AI_MODEL_FAST",
        "settings.ai_model.fast",
        "Fast model",
        "Model selected for latency-sensitive workloads.",
    ),
    _SystemSettingDefinition(
        "AI_MODEL_PREMIUM",
        "settings.ai_model.premium",
        "Premium model",
        "Model selected for highest-quality workloads.",
    ),
    _SystemSettingDefinition(
        "AI_MODEL_FALLBACK",
        "settings.ai_model.fallback",
        "Fallback model",
        "Explicit fallback model selected by policy.",
    ),
    _SystemSettingDefinition(
        "AI_TEMPERATURE",
        "settings.ai_model.temperature",
        "Temperature",
        "Sampling temperature for configured AI workloads.",
        value_kind="decimal",
        minimum=0.0,
        maximum=2.0,
    ),
    _SystemSettingDefinition(
        "AI_MAX_TOKENS",
        "settings.ai_model.max_tokens",
        "Maximum tokens",
        "Maximum generated tokens for configured AI workloads.",
        value_kind="integer",
        minimum=1,
        maximum=1_000_000,
    ),
    _SystemSettingDefinition(
        "AI_TOP_P",
        "settings.ai_model.top_p",
        "Top-p",
        "Nucleus sampling probability for configured AI workloads.",
        value_kind="decimal",
        minimum=0.0,
        maximum=1.0,
    ),
    _SystemSettingDefinition(
        "AI_TOP_K",
        "settings.ai_model.top_k",
        "Top-k",
        "Token candidate bound for providers that support top-k sampling.",
        value_kind="integer",
        minimum=1,
        maximum=1_000_000,
    ),
    _SystemSettingDefinition(
        "GOOGLE_USE_VERTEXAI",
        "settings.google_genai.use_vertexai",
        "Use Vertex AI",
        "Select Vertex AI rather than the direct Google GenAI endpoint.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "GOOGLE_AGENT_MODEL",
        "settings.google_genai.agent_model",
        "Google agent model",
        "Google model used by agent workloads.",
    ),
    _SystemSettingDefinition(
        "OPENAI_AGENT_MODEL",
        "settings.openai.agent_model",
        "OpenAI agent model",
        "OpenAI model used by agent workloads.",
    ),
    _SystemSettingDefinition(
        "OPENAI_AGENT_MID",
        "settings.openai.agent_mid",
        "OpenAI mid model",
        "OpenAI model used for balanced workloads.",
    ),
    _SystemSettingDefinition(
        "OPENAI_AGENT_LIGHT",
        "settings.openai.agent_light",
        "OpenAI light model",
        "OpenAI model used for lightweight workloads.",
    ),
    _SystemSettingDefinition(
        "OLLAMA_BASE_URL",
        "settings.ollama.base_url",
        "Ollama URL",
        "Base URL of the configured Ollama service.",
    ),
    _SystemSettingDefinition(
        "OLLAMA_AGENT_MODEL",
        "settings.ollama.agent_model",
        "Ollama agent model",
        "Ollama model used by agent workloads.",
    ),
    _SystemSettingDefinition(
        "SMTP_HOST",
        "settings.smtp.host",
        "SMTP host",
        "SMTP server host name.",
    ),
    _SystemSettingDefinition(
        "SMTP_PORT",
        "settings.smtp.port",
        "SMTP port",
        "SMTP server TCP port.",
        value_kind="integer",
        minimum=1,
        maximum=65_535,
    ),
    _SystemSettingDefinition(
        "NOTIFICATIONS_ENABLED",
        "settings.notifications.enabled",
        "Enable notifications",
        "Master switch for all outbound notification channels.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "NOTIFICATION_DEFAULT_CHANNELS",
        "settings.notifications.default_channels",
        "Default notification channels",
        "Comma-separated subset of desktop, email, telegram, and sms.",
    ),
    _SystemSettingDefinition(
        "NOTIFICATION_RATE_LIMIT",
        "settings.notifications.rate_limit",
        "Notification rate limit",
        "Maximum messages per channel within one rate window.",
        value_kind="integer",
        minimum=1,
        maximum=10_000,
    ),
    _SystemSettingDefinition(
        "NOTIFICATION_RATE_WINDOW_SECONDS",
        "settings.notifications.rate_window_seconds",
        "Notification rate window",
        "Per-channel rate-limit window in seconds.",
        value_kind="decimal",
        minimum=0.1,
        maximum=86_400,
    ),
    _SystemSettingDefinition(
        "NOTIFICATION_TIMEOUT_SECONDS",
        "settings.notifications.timeout_seconds",
        "Notification timeout",
        "External channel request timeout in seconds.",
        value_kind="decimal",
        minimum=0.1,
        maximum=60,
    ),
    *(
        _SystemSettingDefinition(
            f"{channel.upper()}_NOTIFICATIONS_ENABLED",
            f"settings.notifications.{channel}.enabled",
            f"Enable {channel} notifications",
            (
                f"Allow outbound {channel} notifications when the master switch "
                "is enabled."
            ),
            value_kind="boolean",
        )
        for channel in ("desktop", "email", "telegram", "sms")
    ),
    _SystemSettingDefinition(
        "SMTP_TLS_MODE",
        "settings.notifications.email.tls_mode",
        "SMTP TLS mode",
        "SMTP transport security mode.",
        allowed_values=("ssl", "starttls", "none"),
    ),
    _SystemSettingDefinition(
        "LANGCHAIN_TRACING_V2",
        "settings.langchain.tracing_v2",
        "LangChain tracing",
        "Enable LangChain v2 tracing.",
        value_kind="boolean",
    ),
    _SystemSettingDefinition(
        "LANGCHAIN_PROJECT",
        "settings.langchain.project",
        "LangChain project",
        "Non-secret LangChain tracing project name.",
    ),
)

_BOOTSTRAP_BINDINGS = MappingProxyType(
    {
        "settings.environment.current": "ENVIRONMENT",
        "settings.environment.api_host": "API_HOST",
        "settings.environment.api_port": "API_PORT",
        "settings.environment.ui_origin": "UI_ORIGINS",
        "settings.environment.trading_usage_allow_provider_mutations": (
            "ALLOW_LIVE_MUTATIONS"
        ),
        "settings.paths.home_dir": "HOME_DIR",
        "settings.paths.data_dir": "DATA_DIR",
        "settings.paths.cache_dir": "CACHE_DIR",
        "settings.paths.audit_dir": "AUDIT_DIR",
        "settings.data.data_usage_live_providers": "DATA_USAGE_LIVE_PROVIDERS",
        "settings.database.database_url": "DATABASE_URL",
        "settings.database.sqlite_busy_timeout_seconds": (
            "SQLITE_BUSY_TIMEOUT_SECONDS"
        ),
        "settings.database.write_lock_lease_seconds": "WRITE_LOCK_LEASE_SECONDS",
        "settings.mt5.environment": "MT5_ENVIRONMENT",
        "settings.ctrader.environment": "CTRADER_ENVIRONMENT",
        "settings.binance.environment": "BINANCE_ENVIRONMENT",
        "settings.security.jwt_secret_key": (
            "JWT_SECRET_KEY"  # pragma: allowlist secret
        ),
        "settings.security.jwt_algorithm": "JWT_ALGORITHM",
        "settings.security.data_encryption_key": "CREDENTIAL_ENCRYPTION_KEY",
        "settings.environment.runtime_profile": "RUNTIME_PROFILE",
        "settings.environment.execution_route": "EXECUTION_ROUTE",
    }
)

_CREDENTIAL_DEFINITIONS = (
    _CredentialDefinition(
        "mt5_snapshot_bridge",
        "MT5 Snapshot Bridge",
        MappingProxyType(
            {"auth_token": "settings.mt5.snapshot.auth_token"}
        ),  # pragma: allowlist secret
    ),
    _CredentialDefinition(
        "mt5",
        "MetaTrader 5",
        MappingProxyType(
            {
                "login": "settings.mt5.login",
                "password": "settings.mt5.password",  # pragma: allowlist secret
                "server": "settings.mt5.server",
            }
        ),
    ),
    _CredentialDefinition(
        "ctrader",
        "cTrader",
        MappingProxyType(
            {
                "account_id": "settings.ctrader.account_id",
                "client_id": "settings.ctrader.client_id",
                "client_secret": (
                    "settings.ctrader.client_secret"  # pragma: allowlist secret
                ),
                "access_token": "settings.ctrader.access_token",
                "refresh_token": "settings.ctrader.refresh_token",
            }
        ),
    ),
    _CredentialDefinition(
        "google_genai",
        "Google GenAI",
        MappingProxyType(
            {"api_key": "settings.google_genai.api_key"}  # pragma: allowlist secret
        ),
    ),
    _CredentialDefinition(
        "openai",
        "OpenAI",
        MappingProxyType(
            {"api_key": "settings.openai.api_key"}  # pragma: allowlist secret
        ),
    ),
    _CredentialDefinition(
        "nvidia",
        "NVIDIA",
        MappingProxyType(
            {"api_key": "settings.nvidia.build_autogen_19"}  # pragma: allowlist secret
        ),
    ),
    _CredentialDefinition(
        "zcode",
        "ZCode",
        MappingProxyType(
            {"api_key": "settings.zcode.zcode"}  # pragma: allowlist secret
        ),
    ),
    _CredentialDefinition(
        "zai",
        "Z.AI",
        MappingProxyType({"api_key": "settings.zai.zai"}),  # pragma: allowlist secret
    ),
    _CredentialDefinition(
        "openrouter",
        "OpenRouter",
        MappingProxyType(
            {"api_key": "settings.openrouter.openrouter"}  # pragma: allowlist secret
        ),
    ),
    _CredentialDefinition(
        "cline",
        "Cline",
        MappingProxyType(
            {"api_key": "settings.cline.devkey"}  # pragma: allowlist secret
        ),
    ),
    _CredentialDefinition(
        "github",
        "GitHub",
        MappingProxyType(
            {"api_key": "settings.github.api"}  # pragma: allowlist secret
        ),
    ),
    _CredentialDefinition(
        "brave",
        "Brave",
        MappingProxyType(
            {
                "search_api_key": "settings.brave.search",  # pragma: allowlist secret
                "answers_api_key": "settings.brave.answers",  # pragma: allowlist secret
            }
        ),
    ),
    _CredentialDefinition(
        "firecrawl",
        "Firecrawl",
        MappingProxyType(
            {"api_key": "settings.firecrawl.firecrawl"}  # pragma: allowlist secret
        ),
    ),
    _CredentialDefinition(
        "smtp",
        "SMTP",
        MappingProxyType(
            {
                "username": "settings.smtp.username",
                "password": "settings.smtp.password",  # pragma: allowlist secret
                "sender_email": "settings.notifications.email.sender_email",
                "recipient_emails": "settings.notifications.email.recipient_emails",
            }
        ),
    ),
    _CredentialDefinition(
        "telegram",
        "Telegram",
        MappingProxyType(
            {
                "bot_token": "settings.telegram.bot_token",
                "chat_id": "settings.telegram.chat_id",
                "chat_ids": "settings.notifications.telegram.chat_ids",
            }
        ),
    ),
    _CredentialDefinition(
        "twilio",
        "Twilio",
        MappingProxyType(
            {
                "account_sid": "settings.twilio.account_sid",
                "auth_token": "settings.twilio.auth_token",
                "from_phone": "settings.twilio.from_phone",
                "recipient_phones": "settings.notifications.sms.recipient_phones",
            }
        ),
    ),
    _CredentialDefinition(
        "langchain",
        "LangChain",
        MappingProxyType(
            {"api_key": "settings.langchain.api_key"}  # pragma: allowlist secret
        ),
    ),
)

_SYSTEM_BY_KEY = MappingProxyType(
    {definition.key: definition for definition in _SYSTEM_DEFINITIONS}
)
_SYSTEM_BY_SOURCE = MappingProxyType(
    {definition.source_path: definition for definition in _SYSTEM_DEFINITIONS}
)
_CREDENTIAL_BY_SLOT = MappingProxyType(
    {definition.slot: definition for definition in _CREDENTIAL_DEFINITIONS}
)


def _parse_numeric_value(
    definition: _SystemSettingDefinition,
    value: str,
) -> Decimal | None:
    """Parse a numeric manifest value without accepting lossy syntax.

    Args:
        definition: Internal setting definition.
        value: Candidate canonical string.

    Returns:
        Parsed numeric value, or None for non-numeric definitions.

    Raises:
        IdentityError: If numeric syntax is invalid.
    """
    if definition.value_kind not in {"decimal", "integer"}:
        return None
    try:
        numeric_value = Decimal(value)
    except InvalidOperation:
        raise IdentityError("SYSTEM_SETTING_VALUE_INVALID") from None
    if not numeric_value.is_finite():
        raise IdentityError("SYSTEM_SETTING_VALUE_INVALID")
    if (
        definition.value_kind == "integer"
        and numeric_value != numeric_value.to_integral()
    ):
        raise IdentityError("SYSTEM_SETTING_VALUE_INVALID")
    return numeric_value


def _validate_typed_value(
    definition: _SystemSettingDefinition,
    value: str,
) -> str:
    """Validate one canonical string against its manifest definition.

    Args:
        definition: Internal setting definition.
        value: Candidate canonical string.

    Returns:
        Validated canonical string.

    Raises:
        IdentityError: If the value violates the manifest.
    """
    if value != value.strip() or len(value) > _MAX_SETTING_VALUE_LENGTH:
        raise IdentityError("SYSTEM_SETTING_VALUE_INVALID")
    if definition.allowed_values and value not in definition.allowed_values:
        raise IdentityError("SYSTEM_SETTING_VALUE_INVALID")
    if definition.value_kind == "boolean" and value not in {"false", "true"}:
        raise IdentityError("SYSTEM_SETTING_VALUE_INVALID")
    numeric_value = _parse_numeric_value(definition, value)
    if numeric_value is not None and (
        (
            definition.minimum is not None
            and numeric_value < Decimal(str(definition.minimum))
        )
        or (
            definition.maximum is not None
            and numeric_value > Decimal(str(definition.maximum))
        )
    ):
        raise IdentityError("SYSTEM_SETTING_VALUE_INVALID")
    return value


def validate_system_settings(settings: Mapping[str, str]) -> Mapping[str, str]:
    """Validate the complete global non-secret settings document.

    Args:
        settings: Candidate canonical string settings.

    Returns:
        Validated settings in deterministic key order.

    Raises:
        IdentityError: If a key or value is not manifest-approved.
    """
    unknown = set(settings) - set(_SYSTEM_BY_KEY)
    if unknown:
        raise IdentityError("SYSTEM_SETTING_KEY_UNKNOWN")
    return MappingProxyType(
        {
            key: _validate_typed_value(_SYSTEM_BY_KEY[key], settings[key])
            for key in sorted(settings)
        }
    )


def system_settings_require_restart(
    previous: Mapping[str, str],
    current: Mapping[str, str],
) -> bool:
    """Report whether a validated replacement requires application restart.

    Args:
        previous: Previously persisted system settings.
        current: Replacement system settings.

    Returns:
        True when any restart-required value changed.
    """
    changed = {
        key
        for key in set(previous) | set(current)
        if previous.get(key) != current.get(key)
    }
    return any(_SYSTEM_BY_KEY[key].activation == "restart_required" for key in changed)


def get_system_settings_manifest() -> tuple[Mapping[str, object], ...]:
    """Return secret-free metadata for frontend system-settings rendering.

    Returns:
        Ordered immutable manifest mappings.
    """
    return tuple(
        MappingProxyType(
            {
                "key": definition.key,
                "label": definition.label,
                "description": definition.description,
                "value_kind": definition.value_kind,
                "allowed_values": definition.allowed_values,
                "minimum": definition.minimum,
                "maximum": definition.maximum,
                "activation": definition.activation,
            }
        )
        for definition in _SYSTEM_DEFINITIONS
    )


def get_credential_manifest() -> tuple[Mapping[str, object], ...]:
    """Return write-only credential-slot metadata without credential values.

    Returns:
        Ordered immutable credential metadata mappings.
    """
    return tuple(
        MappingProxyType(
            {
                "slot": definition.slot,
                "label": definition.label,
                "fields": tuple(definition.fields),
                "activation": "restart_required",
            }
        )
        for definition in _CREDENTIAL_DEFINITIONS
    )


def get_legacy_settings_classification() -> Mapping[str, Mapping[str, str]]:
    """Return the exhaustive legacy JSON-key migration classification.

    Returns:
        Immutable source-path classification used by the one-time migration.
    """
    result: dict[str, Mapping[str, str]] = {
        source_path: MappingProxyType(
            {
                "classification": "system",
                "target": definition.key,
            }
        )
        for source_path, definition in _SYSTEM_BY_SOURCE.items()
    }
    result.update(
        {
            source_path: MappingProxyType(
                {
                    "classification": "bootstrap",
                    "target": target,
                }
            )
            for source_path, target in _BOOTSTRAP_BINDINGS.items()
        }
    )
    for definition in _CREDENTIAL_DEFINITIONS:
        for field, source_path in definition.fields.items():
            result[source_path] = MappingProxyType(
                {
                    "classification": "credential",
                    "target": definition.slot,
                    "field": field,
                }
            )
    return MappingProxyType(dict(sorted(result.items())))


def validate_credential_material(
    slot: str,
    material: Mapping[str, str],
) -> Mapping[str, str]:
    """Validate complete write-only material for one credential slot.

    Args:
        slot: Manifest-approved credential slot.
        material: Candidate field-to-secret mapping.

    Returns:
        Validated credential material.

    Raises:
        IdentityError: If the slot or exact field set is invalid.
    """
    if slot not in _CREDENTIAL_BY_SLOT:
        raise IdentityError("CREDENTIAL_SLOT_UNKNOWN")
    expected = set(_CREDENTIAL_BY_SLOT[slot].fields)
    if set(material) != expected or any(
        not value or value != value.strip() or len(value) > _MAX_CREDENTIAL_VALUE_LENGTH
        for value in material.values()
    ):
        raise IdentityError("CREDENTIAL_INPUT_INVALID")
    return MappingProxyType(dict(material))


__all__ = (
    "get_credential_manifest",
    "get_legacy_settings_classification",
    "get_system_settings_manifest",
    "system_settings_require_restart",
    "validate_credential_material",
    "validate_system_settings",
)
