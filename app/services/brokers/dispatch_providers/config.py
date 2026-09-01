"""Strict configuration for explicit provider dispatch."""

from __future__ import annotations

from dataclasses import dataclass

_ALLOWED_KEYS = frozenset({"reject_duplicate_profiles"})


@dataclass(frozen=True, slots=True)
class DispatchProvidersConfig:
    """Configuration for deterministic provider routing."""

    reject_duplicate_profiles: bool = True

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> "DispatchProvidersConfig":
        """Validate raw dispatcher configuration.

        Args:
            values: Raw feature configuration mapping.

        Returns:
            Validated immutable configuration.

        Raises:
            ValueError: An unknown key or non-boolean value is supplied.
        """
        unknown = set(values) - _ALLOWED_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        raw = values.get("reject_duplicate_profiles", True)
        if not isinstance(raw, bool):
            raise ValueError("reject_duplicate_profiles must be a boolean")
        return cls(reject_duplicate_profiles=raw)
