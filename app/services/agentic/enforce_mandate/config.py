"""Strict configuration for Mandate Enforcement."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EnforceMandateConfig:
    """Strict configuration for mandate enforcement feature."""


def from_dict(data: dict[str, object] | None) -> EnforceMandateConfig:
    """Parse strict feature configuration and reject unknown keys.

    Args:
        data: Raw configuration mapping or None.

    Returns:
        Validated EnforceMandateConfig instance.

    Raises:
        ValueError: If unknown keys are provided.
    """
    values = dict(data or {})
    unknown = set(values) - set()
    if unknown:
        msg = f"Unknown mandate-enforcement configuration keys: {sorted(unknown)}"
        raise ValueError(msg)
    return EnforceMandateConfig()


__all__ = ["EnforceMandateConfig", "from_dict"]
