from dataclasses import FrozenInstanceError

import pytest
from app.utils import (
    RedactionPolicy,
    SecurityError,
    ValidationError,
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


@pytest.mark.parametrize(
    "source",
    [
        "token=abc123",
        "API_KEY=abc123",
        "client-secret: abc123",
        "Private_Key=abc123",
        "ACCESS-KEY=abc123",
        "authorization: Bearer abc123",
        "Bearer abc123",
    ],
)
def test_redact_text_value_does_not_mutate_input(source: str) -> None:
    result = redact_text_value(source)
    assert "abc123" not in str(result.value)
    assert source != result.value


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


@pytest.mark.parametrize(
    "arguments",
    [
        {"sensitive_keys": frozenset()},
        {"sensitive_keys": frozenset({" invalid"})},
        {"replacement": " "},
        {"max_text_length": 0},
        {"allowlisted_paths": frozenset({"nested..value"})},
    ],
)
def test_redaction_policy_rejects_invalid_definitions(
    arguments: dict[str, object],
) -> None:
    """Reject malformed keys, replacements, limits, and field paths."""
    with pytest.raises(ValidationError):
        RedactionPolicy(**arguments)  # type: ignore[arg-type]


def test_redaction_honors_safe_allowlist_and_text_limit() -> None:
    """Honor a reviewed non-credential path and report bounded truncation."""
    policy = RedactionPolicy(
        allowlisted_paths=frozenset({"metadata.token"}),
        max_text_length=5,
    )
    result = redact_mapping_value(
        {"metadata": {"token": "public", "message": "longer-than-five"}},
        policy,
    )
    assert result.value == {"metadata": {"token": "publi", "message": "longe"}}
    assert result.truncated


def test_redaction_supports_json_scalars_and_sequences() -> None:
    """Preserve safe JSON scalars and redact secret-shaped sequence text."""
    result = redact_mapping_value(
        {
            "none": None,
            "flag": True,
            "count": 2,
            "ratio": 1.5,
            "items": ("token=value", "safe"),
        }
    )
    assert result.value == {
        "none": None,
        "flag": True,
        "count": 2,
        "ratio": 1.5,
        "items": ["token=[REDACTED]", "safe"],
    }


@pytest.mark.parametrize(
    ("value", "policy"),
    [
        ({"number": float("nan")}, RedactionPolicy()),
        ({"items": [1, 2]}, RedactionPolicy(max_items=1)),
        ({"nested": {"value": 1}}, RedactionPolicy(max_depth=1)),
        ({"invalid": object()}, RedactionPolicy()),
        ({"": "value"}, RedactionPolicy()),
    ],
)
def test_redaction_rejects_unsafe_or_unbounded_values(
    value: dict[str, object],
    policy: RedactionPolicy,
) -> None:
    """Reject non-finite, oversized, over-deep, or unsupported mapping values."""
    with pytest.raises(ValidationError):
        redact_mapping_value(value, policy)
