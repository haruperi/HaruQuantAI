"""Unit tests for kernel secret redaction."""

from __future__ import annotations

from app.kernel.redaction import (
    is_sensitive_key,
    redact_mapping_value,
    redact_text_value,
)


def test_is_sensitive_key() -> None:
    """Verify is_sensitive_key detects credential keys."""
    assert is_sensitive_key("password") is True
    assert is_sensitive_key("api_key") is True
    assert is_sensitive_key("secret_token") is True
    assert is_sensitive_key("public_symbol") is False


def test_redact_mapping_value() -> None:
    """Verify sensitive keys in mappings are replaced with redaction marker."""
    raw = {
        "username": "trader1",
        "password": "supersecretpassword",  # pragma: allowlist secret
        "amount": 100,
    }
    res = redact_mapping_value(raw)
    assert res.value == {
        "username": "trader1",
        "password": "[REDACTED]",
        "amount": 100,
    }
    assert "password" in res.redacted_paths


def test_redact_text_value() -> None:
    """Verify Bearer tokens and key-values are redacted from strings."""
    text = "Authorization: Bearer my_secret_token_12345"  # pragma: allowlist secret
    res = redact_text_value(text)
    assert "my_secret_token_12345" not in str(res.value)
    assert "[REDACTED]" in str(res.value)
