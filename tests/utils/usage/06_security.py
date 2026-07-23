"""Executable secret-redaction examples."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    RedactionPolicy,
    SecurityError,
    is_sensitive_key,
    redact_mapping_value,
    redact_text_value,
    to_json_safe,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_utils_016_redaction_policy() -> None:
    """FR-UTL-016: immutable denylist-first redaction policy."""
    _header("Example 1: Redaction Policy")
    policy = RedactionPolicy()
    print("Redaction policy:", bool(policy))
    print("Sample redacted:", to_json_safe(sorted(policy.sensitive_keys)))


def fr_utils_017_key_classification() -> None:
    """FR-UTL-017: Classify separator-equivalent sensitive keys."""
    _header("Example 1: Key Classification")
    print("Sensitive key:", is_sensitive_key("Client-Secret"))


def fr_utils_018_redaction_text() -> None:
    """FR-UTL-018: Redact text without exposing source secrets."""
    _header("Example 2: Redaction")
    text = redact_text_value("api_key=synthetic-value")
    print("Text redaction:", text.value)


def fr_utils_019_redaction_mapping() -> None:
    """FR-UTL-019: Recursively redact a JSON-safe mapping without mutating it."""
    _header("Example 2: Mapping Redaction")
    mapping = redact_mapping_value({"nested": {"token": "synthetic-value"}})
    print("Mapping redaction:", mapping.value)


def fr_utils_020_redaction_result() -> None:
    """FR-UTL-020: Return redaction diagnostics without secret values."""
    _header("Example 2: Redaction Diagnostics")
    result = redact_mapping_value({"nested": {"token": "synthetic-value"}})
    print("Redaction result:", result.truncated, result.redacted_paths)


def fr_utils_021_policy_validation() -> None:
    """FR-UTL-021: Demonstrate protected-field allowlist rejection."""
    _header("Example 3: Policy Validation")
    try:
        RedactionPolicy(allowlisted_paths=frozenset({"provider.api_key"}))
    except SecurityError:
        print("Redaction policy: protected credential allowlist rejected")


def main() -> None:
    """Run all redaction examples."""
    fr_utils_016_redaction_policy()
    fr_utils_017_key_classification()
    fr_utils_018_redaction_text()
    fr_utils_019_redaction_mapping()
    fr_utils_020_redaction_result()
    fr_utils_021_policy_validation()


if __name__ == "__main__":
    main()
