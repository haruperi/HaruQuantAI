"""
Security helpers for HaruQuantAI utility modules.

This module contains internal redaction helpers used by logging infrastructure.
It does not expose official AI tools.
"""

from __future__ import annotations

from typing import Any, Dict

SENSITIVE_KEYWORDS = (
    "api_key",
    "apikey",
    "auth",
    "broker_password",
    "credential",
    "password",
    "secret",
    "token",
)
REDACTED_VALUE = "[REDACTED]"


def _is_sensitive_key(key: str) -> bool:
    """Return True when a mapping key is likely to contain sensitive data."""
    normalized_key = key.lower().replace("-", "_")
    return any(keyword in normalized_key for keyword in SENSITIVE_KEYWORDS)


def _redact_mapping(value: Dict[str, Any]) -> Dict[str, Any]:
    """Return a shallow copy of a mapping with sensitive values redacted."""
    redacted: Dict[str, Any] = {}
    for key, item in value.items():
        text_key = str(key)
        if _is_sensitive_key(text_key):
            redacted[text_key] = REDACTED_VALUE
        else:
            redacted[text_key] = item
    return redacted


def _redact_text(value: str) -> str:
    """Redact obvious key-value secrets from a text message."""
    redacted = str(value)
    separators = ("=", ":")
    for keyword in SENSITIVE_KEYWORDS:
        for separator in separators:
            marker = f"{keyword}{separator}"
            lower_redacted = redacted.lower()
            start = lower_redacted.find(marker)
            while start != -1:
                value_start = start + len(marker)
                value_end = value_start
                while value_end < len(redacted) and not redacted[value_end].isspace():
                    value_end += 1
                redacted = (
                    redacted[:value_start] + REDACTED_VALUE + redacted[value_end:]
                )
                lower_redacted = redacted.lower()
                start = lower_redacted.find(marker, value_start + len(REDACTED_VALUE))
    return redacted


__all__: list[str] = []
