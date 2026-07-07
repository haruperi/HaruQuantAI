"""Recursive key and token redaction boundary helper for Analytics.

All functions are stateless pure functions.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from app.utils.logger import logger


class RedactionPolicy(StrEnum):
    """Policies for level of redaction coverage."""

    STANDARD = "standard"
    STRICT = "strict"


def redact(
    value: object,
    policy: RedactionPolicy = RedactionPolicy.STANDARD,
) -> object:
    """Recursively redact secrets and credentials from data payloads.

    Args:
        value (object): Input parameter `value`.
        policy (RedactionPolicy): Input parameter `policy`.

    Returns:
        Calculated object value.
    """
    logger.debug("redact: executed.")
    sensitive_keys = {
        "secret",
        "token",
        "password",
        "key",
        "credential",
        "auth",
        "authorization",
        "broker_token",
        "private_key",
    }

    if isinstance(value, dict):
        redacted_dict: dict[Any, Any] = {}
        for k, v in value.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in sensitive_keys):
                redacted_dict[k] = "[REDACTED]"
            else:
                redacted_dict[k] = redact(v, policy)
        return redacted_dict

    if isinstance(value, list):
        return [redact(item, policy) for item in value]

    if isinstance(value, str):
        val_lower = value.lower()
        if val_lower.startswith(("bearer ", "basic ")):
            return "[REDACTED]"

    return value
