"""Unit tests for kernel secret redaction."""

from __future__ import annotations

import pytest
from app.kernel.errors import SecurityError, ValidationError
from app.kernel.redaction import (
    RedactionPolicy,
    get_default_redaction_policy,
    is_sensitive_key,
    redact_contract_mapping,
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
        "nested_list": [
            {"token": "secret_token_1"},
            "plain_text",
        ],  # pragma: allowlist secret
    }
    res = redact_mapping_value(raw)
    assert res.value == {
        "username": "trader1",
        "password": "[REDACTED]",
        "amount": 100,
        "nested_list": [{"token": "[REDACTED]"}, "plain_text"],
    }
    assert "password" in res.redacted_paths
    assert "nested_list.0.token" in res.redacted_paths


def test_redact_text_value_and_truncation() -> None:
    """Verify Bearer tokens and key-values are redacted and truncated from strings."""
    text = "Authorization: Bearer my_secret_token_12345"  # pragma: allowlist secret
    res = redact_text_value(text)
    assert "my_secret_token_12345" not in str(res.value)
    assert "[REDACTED]" in str(res.value)

    # Text truncation
    long_text = "A" * 5000
    policy = RedactionPolicy(max_text_length=100)
    truncated_res = redact_text_value(long_text, policy)
    assert len(str(truncated_res.value)) == 100
    assert "$text" in truncated_res.truncated_paths


def test_redaction_policy_validation_errors() -> None:
    """Verify RedactionPolicy validates input constraints."""
    with pytest.raises(ValidationError, match="REDACTION_POLICY_INVALID"):
        RedactionPolicy(sensitive_keys=frozenset())

    with pytest.raises(ValidationError, match="REDACTION_POLICY_INVALID"):
        RedactionPolicy(replacement="")

    with pytest.raises(ValidationError, match="REDACTION_POLICY_INVALID"):
        RedactionPolicy(max_depth=0)

    with pytest.raises(ValidationError, match="REDACTION_POLICY_INVALID"):
        RedactionPolicy(allowlisted_paths=frozenset({""}))

    # Protected key cannot be allowlisted
    with pytest.raises(SecurityError, match="REDACTION_PROTECTED_ALLOWLIST"):
        RedactionPolicy(allowlisted_paths=frozenset({"config.password"}))


def test_redaction_allowlisted_path_exemption() -> None:
    """Verify allowlisted paths are preserved even if matching sensitive key."""
    policy = RedactionPolicy(
        sensitive_keys=frozenset({"token"}),
        allowlisted_paths=frozenset({"public.token"}),
    )
    data = {
        "public": {"token": "public_token_value"},
        "private": {"token": "secret_token_value"},  # pragma: allowlist secret
    }
    res = redact_mapping_value(data, policy=policy)
    assert res.value["public"]["token"] == "public_token_value"
    assert res.value["private"]["token"] == "[REDACTED]"


def test_redact_mapping_limits_and_validation() -> None:
    """Verify depth, item, and input type validations in redact_mapping_value."""
    with pytest.raises(ValidationError):
        redact_mapping_value("not_a_mapping")  # type: ignore[arg-type]

    # Non-finite numbers
    with pytest.raises(ValidationError):
        redact_mapping_value({"val": float("nan")})

    # Max depth exceeded
    deep_mapping: dict[str, object] = {"a": 1}
    for _ in range(20):
        deep_mapping = {"nested": deep_mapping}
    with pytest.raises(ValidationError, match="REDACTION_DEPTH_EXCEEDED"):
        redact_mapping_value(deep_mapping, policy=RedactionPolicy(max_depth=5))

    # Max items exceeded
    large_mapping = {f"k{i}": i for i in range(50)}
    with pytest.raises(ValidationError, match="REDACTION_ITEMS_EXCEEDED"):
        redact_mapping_value(large_mapping, policy=RedactionPolicy(max_items=10))

    # Invalid empty key
    with pytest.raises(ValidationError, match="REDACTION_MAPPING_INVALID"):
        redact_mapping_value({"": "val"})


def test_redact_contract_mapping_and_default_policy() -> None:
    """Verify redact_contract_mapping and get_default_redaction_policy."""
    pol = get_default_redaction_policy()
    assert isinstance(pol, RedactionPolicy)

    contract = {
        "domain": "risk",
        "api_key": "sensitive123",  # pragma: allowlist secret
    }
    redacted = redact_contract_mapping(contract)
    assert redacted == {"domain": "risk", "api_key": "[REDACTED]"}
