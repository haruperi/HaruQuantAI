from dataclasses import FrozenInstanceError

import pytest
from app.utils import (
    RedactionPolicy,
    SecurityError,
    is_sensitive_key,
    redact_mapping_value,
    redact_text_value,
)


def test_redaction_policy_is_immutable() -> None:
    policy = RedactionPolicy()
    with pytest.raises(FrozenInstanceError):
        policy.max_items = 2  # type: ignore[misc]


def test_is_sensitive_key_is_case_insensitive() -> None:
    assert is_sensitive_key("API_KEY")
    assert is_sensitive_key("Client-Secret")


def test_redact_text_value_does_not_mutate_input() -> None:
    source = "token=abc123"
    result = redact_text_value(source)
    assert source == "token=abc123"
    assert "abc123" not in str(result.value)


def test_redact_mapping_value_is_recursive() -> None:
    source = {"nested": {"password": "abc123"}}  # pragma: allowlist secret
    result = redact_mapping_value(source)
    assert source["nested"]["password"] == "abc123"  # pragma: allowlist secret
    assert result.value == {"nested": {"password": "[REDACTED]"}}


def test_redaction_result_omits_secret_values() -> None:
    result = redact_mapping_value({"token": "abc123"})
    assert result.redacted_paths == ("token",)
    assert "abc123" not in repr(result)


def test_policy_rejects_protected_credential_field() -> None:
    with pytest.raises(SecurityError):
        RedactionPolicy(allowlisted_paths=frozenset({"provider.api_key"}))
