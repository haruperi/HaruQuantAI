from __future__ import annotations

import base64

import pytest
from app.services.api.composition.runtime_settings import build_credential_key_set
from app.services.api.identity import (
    IdentityError,
    get_credential_manifest,
    get_legacy_settings_classification,
    get_system_settings_manifest,
    validate_credential_material,
    validate_system_settings,
)
from app.services.api.workstation.settings.bootstrap import ApiSettings
from pydantic import SecretStr

_LEGACY_PATHS = {
    "settings.ai_model.agent",
    "settings.ai_model.fallback",
    "settings.ai_model.fast",
    "settings.ai_model.max_tokens",
    "settings.ai_model.premium",
    "settings.ai_model.temperature",
    "settings.ai_model.top_k",
    "settings.ai_model.top_p",
    "settings.binance.enabled",
    "settings.binance.environment",
    "settings.brave.answers",
    "settings.brave.search",
    "settings.cline.devkey",
    "settings.ctrader.access_token",
    "settings.ctrader.account_id",
    "settings.ctrader.client_id",
    "settings.ctrader.client_secret",
    "settings.ctrader.enabled",
    "settings.ctrader.environment",
    "settings.ctrader.redirect_url",
    "settings.ctrader.refresh_token",
    "settings.data.data_usage_live_providers",
    "settings.database.database_url",
    "settings.database.sqlite_busy_timeout_seconds",
    "settings.database.write_lock_lease_seconds",
    "settings.dukascopy.enabled",
    "settings.environment.api_host",
    "settings.environment.api_port",
    "settings.environment.app_name",
    "settings.environment.current",
    "settings.environment.log_level",
    "settings.environment.runtime_broker",
    "settings.environment.trading_usage_allow_provider_mutations",
    "settings.environment.ui_origin",
    "settings.firecrawl.firecrawl",
    "settings.github.api",
    "settings.google_genai.agent_model",
    "settings.google_genai.api_key",
    "settings.google_genai.use_vertexai",
    "settings.langchain.api_key",
    "settings.langchain.project",
    "settings.langchain.tracing_v2",
    "settings.mt5.enabled",
    "settings.mt5.environment",
    "settings.mt5.login",
    "settings.mt5.password",
    "settings.mt5.server",
    "settings.mt5.terminal_path",
    "settings.nvidia.build_autogen_19",
    "settings.ollama.agent_model",
    "settings.ollama.base_url",
    "settings.openai.agent_light",
    "settings.openai.agent_mid",
    "settings.openai.agent_model",
    "settings.openai.api_key",
    "settings.openrouter.openrouter",
    "settings.paths.audit_dir",
    "settings.paths.cache_dir",
    "settings.paths.data_dir",
    "settings.paths.home_dir",
    "settings.paths.timezone",
    "settings.security.data_encryption_key",
    "settings.security.jwt_algorithm",
    "settings.security.jwt_secret_key",
    "settings.smtp.host",
    "settings.smtp.password",
    "settings.smtp.port",
    "settings.smtp.username",
    "settings.telegram.bot_token",
    "settings.telegram.chat_id",
    "settings.twilio.account_sid",
    "settings.twilio.auth_token",
    "settings.twilio.from_phone",
    "settings.yahoo.enabled",
    "settings.zai.zai",
    "settings.zcode.zcode",
}


def test_legacy_configuration_paths_are_exhaustively_classified() -> None:
    classification = get_legacy_settings_classification()

    assert set(classification) >= _LEGACY_PATHS
    assert {item["classification"] for item in classification.values()} <= {
        "bootstrap",
        "credential",
        "system",
    }


def test_system_manifest_is_unique_and_secret_free() -> None:
    manifest = get_system_settings_manifest()
    keys = [str(item["key"]) for item in manifest]
    assert "MT5_SNAPSHOT_HOST" in keys
    assert "MT5_SNAPSHOT_SYMBOLS" in keys

    assert len(keys) == len(set(keys))
    assert "DATABASE_URL" not in keys
    assert all("secret" not in key.casefold() for key in keys)


def test_system_settings_reject_unknown_and_invalid_values() -> None:
    with pytest.raises(IdentityError, match="SYSTEM_SETTING_KEY_UNKNOWN"):
        validate_system_settings({"DATABASE_URL": "sqlite:///forbidden.db"})
    with pytest.raises(IdentityError, match="SYSTEM_SETTING_VALUE_INVALID"):
        validate_system_settings({"MT5_ENABLED": "yes"})


def test_credential_slots_require_the_exact_write_only_field_set() -> None:
    slots = {str(item["slot"]): item for item in get_credential_manifest()}
    assert slots["mt5_snapshot_bridge"]["fields"] == ("auth_token",)

    assert "openai" in slots
    assert validate_credential_material(
        "openai",
        {"api_key": "bounded-value"},  # pragma: allowlist secret
    )
    with pytest.raises(IdentityError, match="CREDENTIAL_INPUT_INVALID"):
        validate_credential_material("openai", {"token": "bounded-value"})


def test_external_credential_key_must_decode_to_256_bits() -> None:
    key = b"k" * 32
    encoded = base64.urlsafe_b64encode(key).decode("ascii")
    settings = ApiSettings(
        active_credential_key_id="bootstrap-v1",
        credential_key_refs=("bootstrap-v1",),
        credential_encryption_key=SecretStr(encoded),
    )

    assert build_credential_key_set(settings) == {"bootstrap-v1": key}
