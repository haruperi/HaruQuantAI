"""Configuration parser and validator for Plugin Contributions feature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.plugins.contributions.manifest import SPEC

_DEFAULT_STRICT_CONTRACT_TESTS: bool = True
_DEFAULT_MAX_CONTRIBUTIONS: int = 100


@dataclass(frozen=True, slots=True)
class PluginContributionsConfig:
    """Configuration limits and behavior for plugin contribution registration."""

    strict_contract_tests: bool = _DEFAULT_STRICT_CONTRACT_TESTS
    max_contributions_per_plugin: int = _DEFAULT_MAX_CONTRIBUTIONS

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> PluginContributionsConfig:
        """Parse and validate configuration dictionary against allowed schema keys.

        Args:
            data: Raw configuration dictionary or None.

        Returns:
            Validated PluginContributionsConfig instance.

        Raises:
            ValueError: If unknown keys or invalid numeric values are provided.
        """
        if data is None:
            return cls()

        unknown_keys = set(data) - SPEC.config_keys
        if unknown_keys:
            joined = ", ".join(sorted(unknown_keys))
            msg = f"Unknown Plugin Contributions configuration keys: {joined}"
            raise ValueError(msg)

        strict_tests = bool(
            data.get("strict_contract_tests", _DEFAULT_STRICT_CONTRACT_TESTS)
        )
        max_contrib = int(
            data.get("max_contributions_per_plugin", _DEFAULT_MAX_CONTRIBUTIONS)
        )

        if max_contrib <= 0:
            msg = "max_contributions_per_plugin must be positive"
            raise ValueError(msg)

        return cls(
            strict_contract_tests=strict_tests,
            max_contributions_per_plugin=max_contrib,
        )
