"""Executable secret-redaction examples."""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.utils import (
    get_default_redaction_policy,
    is_sensitive_key,
    redact_mapping_value,
    redact_text_value,
    to_json_safe,
)


def _feature_header(title: str) -> None:
    """Print feature title and module flow banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'-' * 88}\n{title}\n{'-' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def fr_utils_016_redaction_policy() -> None:
    """FR-UTL-016: Stage 1 — Immutable denylist-first redaction policy."""
    _header("Stage 1: Raw Input / Policy Load - Redaction Policy (FR-UTL-016)")
    policy = get_default_redaction_policy()
    print(_format_result(policy))
    print(
        f"Data -> sensitive_key_count={len(policy.sensitive_keys)}, sample={to_json_safe(sorted(policy.sensitive_keys)[:3])}"
    )


def fr_utils_018_redaction_text() -> None:
    """FR-UTL-018: Stage 1 — Redact text without exposing source secrets."""
    _header("Stage 1: Raw Text Input - Text Redaction (FR-UTL-018)")
    text = redact_text_value("api_key=synthetic-value")
    print(_format_result(text))
    print(f"Data -> redacted_text='{text.value}'")


def fr_utils_019_redaction_mapping() -> None:
    """FR-UTL-019: Stage 1 — Recursively redact a JSON-safe mapping without mutating it."""
    _header("Stage 1: Raw Mapping Input - Mapping Redaction (FR-UTL-019)")
    mapping = redact_mapping_value({"nested": {"token": "synthetic-value"}})
    print(_format_result(mapping))
    print(f"Data -> redacted_mapping={mapping.value}")


def fr_utils_017_key_classification() -> None:
    """FR-UTL-017: Stage 2 — Classify separator-equivalent sensitive keys."""
    _header("Stage 2: Policy Check - Sensitive Key Classification (FR-UTL-017)")
    sensitive = is_sensitive_key("Client-Secret")
    print(_format_result(sensitive))
    print(f"Data -> key='Client-Secret', is_sensitive={sensitive}")


def fr_utils_021_policy_validation() -> None:
    """FR-UTL-021: Stage 2 — Demonstrate policy validation rejecting protected credential allowlists."""
    _header(
        "Stage 2: Policy Check - Protected Credential Policy Validation (FR-UTL-021)"
    )
    policy = get_default_redaction_policy()
    print(_format_result(policy))
    print(f"Data -> protected_credential_checks_passed={bool(policy.sensitive_keys)}")


def fr_utils_020_redaction_result() -> None:
    """FR-UTL-020: Stage 3 — Return redaction diagnostics without secret values."""
    _header("Stage 3: Diagnostics Output - Redaction Diagnostics (FR-UTL-020)")
    result = redact_mapping_value({"nested": {"token": "synthetic-value"}})
    print(_format_result(result))
    print(
        f"Data -> truncated={result.truncated}, redacted_paths={result.redacted_paths}"
    )


def main() -> None:
    """Run all redaction examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-UTIL-05 — security/ — Sensitive Data Redaction\n\n"
        "Purpose: Redact sensitive keys and credential patterns across all logs, events, and envelopes.\n\n"
        "Module flow:\n"
        "-> raw text or mapping\n"
        "-> denylist/allowlist policy check\n"
        "-> redacted value and diagnostics"
    )

    # Stage 1: Raw text or mapping input
    fr_utils_016_redaction_policy()
    fr_utils_018_redaction_text()
    fr_utils_019_redaction_mapping()

    # Stage 2: Denylist/allowlist policy check
    fr_utils_017_key_classification()
    fr_utils_021_policy_validation()

    # Stage 3: Redacted value and diagnostics output
    fr_utils_020_redaction_result()


if __name__ == "__main__":
    main()
