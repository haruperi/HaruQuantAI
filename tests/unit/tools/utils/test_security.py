"""Unit tests for tools.utils.security."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from tools.utils.security import (
    REDACTED,
    SecretRef,
    SecretRotationPolicy,
    decrypt_data_value,
    encrypt_data_value,
    generate_encryption_key,
    hash_password_value,
    is_sensitive_key,
    redact_mapping,
    redact_text,
    rotation_policy_to_dict,
    secret_ref_to_dict,
    select_active_secret_version,
    verify_password_value,
)


def assert_tool_schema(result: dict) -> None:
    assert set(result) == {"status", "message", "data", "error", "metadata"}
    assert result["metadata"]["tool_category"] == "utils"
    assert isinstance(result["metadata"]["execution_ms"], float)


def test_is_sensitive_key_true_and_false() -> None:
    yes = is_sensitive_key("MT5_PASSWORD", request_id="req-sec")
    no = is_sensitive_key("symbol")

    assert_tool_schema(yes)
    assert yes["data"]["sensitive"] is True
    assert yes["metadata"]["request_id"] == "req-sec"
    assert no["data"]["sensitive"] is False


def test_is_sensitive_key_invalid_input() -> None:
    result = is_sensitive_key("")

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_redact_text_common_patterns() -> None:
    text = (
        '{"password":"abc","api_key":"xyz"} '
        "token=123 Bearer abc.def.ghi "
        "Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ== "
        "x-api-key: secret-key AKIAABCDEFGHIJKLMNOP"
    )

    result = redact_text(text)

    redacted = result["data"]["redacted_text"]
    assert "abc" not in redacted
    assert "xyz" not in redacted
    assert "123" not in redacted
    assert "QWxhZGRpbjpvcGVuIHNlc2FtZQ==" not in redacted
    assert "AKIAABCDEFGHIJKLMNOP" not in redacted
    assert REDACTED in redacted


def test_redact_text_invalid_input() -> None:
    result = redact_text(123)  # type: ignore[arg-type]

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_redact_mapping_nested_dict_and_list() -> None:
    payload = {
        "username": "haru",
        "password": "secret",
        "nested": {"api_key": "abc", "visible": "ok"},
        "items": [{"token": "tok"}, {"name": "safe"}],
    }

    result = redact_mapping(payload)

    redacted = result["data"]["redacted_mapping"]
    assert redacted["password"] == REDACTED
    assert redacted["nested"]["api_key"] == REDACTED
    assert redacted["nested"]["visible"] == "ok"
    assert redacted["items"][0]["token"] == REDACTED
    assert redacted["items"][1]["name"] == "safe"


def test_redact_mapping_invalid_input() -> None:
    result = redact_mapping([])  # type: ignore[arg-type]

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_INPUT"


def test_secret_ref_and_policy_serialization() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ref = SecretRef("mt5-password", "v1", created_at)
    policy = SecretRotationPolicy("mt5-password", max_age_days=30)

    assert secret_ref_to_dict(ref)["created_at"] == "2026-01-01T00:00:00+00:00"
    assert rotation_policy_to_dict(policy)["overlap_versions"] == 2


def test_select_active_secret_version_newest_active() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    refs = [
        SecretRef("mt5-password", "v1", now - timedelta(days=1), active=True),
        SecretRef("mt5-password", "v2", now, active=True),
        SecretRef("other", "v1", now, active=True),
    ]
    policy = SecretRotationPolicy("mt5-password", max_age_days=30)

    result = select_active_secret_version(refs, policy)

    assert_tool_schema(result)
    assert result["status"] == "success"
    assert result["data"]["secret_ref"]["version"] == "v2"


def test_select_active_secret_version_no_active_returns_data_not_found() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    refs = [SecretRef("mt5-password", "v1", now, active=False)]
    policy = SecretRotationPolicy("mt5-password", max_age_days=30)

    result = select_active_secret_version(refs, policy)

    assert result["status"] == "error"
    assert result["error"]["code"] == "DATA_NOT_FOUND"


def test_internal_crypto_round_trip() -> None:
    key = generate_encryption_key()
    token = encrypt_data_value("secret-value", key)

    assert decrypt_data_value(token, key) == "secret-value"


def test_internal_password_hash_and_verify() -> None:
    hashed = hash_password_value("strong-password")

    assert hashed != "strong-password"
    assert verify_password_value("strong-password", hashed) is True
    assert verify_password_value("wrong-password", hashed) is False
