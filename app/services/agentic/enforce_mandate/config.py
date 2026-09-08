"""Strict configuration for mandate enforcement."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnforceMandateConfig:
    """Task 1.15 intentionally owns no feature-local configuration keys."""


def from_dict(raw: dict[str, object] | None) -> EnforceMandateConfig:
    """Validate the empty feature configuration."""
    raw = {} if raw is None else raw
    if raw:
        raise ValueError(f"unknown enforce-mandate config keys: {sorted(raw)}")
    return EnforceMandateConfig()
