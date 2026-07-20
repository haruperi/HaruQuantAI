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
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def example_key_classification() -> None:
    """Classify separator-equivalent sensitive keys."""
    _header("Example 1: Key Classification")
    print("Sensitive key:", is_sensitive_key("Client-Secret"))


def example_redaction() -> None:
    """Redact text and mapping values without exposing source secrets."""
    _header("Example 2: Redaction")
    text = redact_text_value("api_key=synthetic-value")
    mapping = redact_mapping_value({"nested": {"token": "synthetic-value"}})
    print("Text redaction:", text.value)
    print("Mapping redaction:", mapping.value)


def example_policy_validation() -> None:
    """Demonstrate protected-field allowlist rejection."""
    _header("Example 3: Policy Validation")
    try:
        RedactionPolicy(allowlisted_paths=frozenset({"provider.api_key"}))
    except SecurityError:
        print("Redaction policy: protected credential allowlist rejected")


def main() -> None:
    """Run all redaction examples."""
    example_key_classification()
    example_redaction()
    example_policy_validation()


if __name__ == "__main__":
    main()
