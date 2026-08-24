"""Configuration model and parser for test greeting feature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"default_salutation", "max_name_length"})
_DEFAULT_SALUTATION = "Hello"
_DEFAULT_MAX_NAME_LENGTH = 100


@dataclass(frozen=True, slots=True)
class GreetingConfig:
    """Configuration for greeting generation.

    Attributes:
        default_salutation: Default salutation prefix when none is provided in request.
        max_name_length: Maximum allowed length for caller names.
    """

    default_salutation: str = _DEFAULT_SALUTATION
    max_name_length: int = _DEFAULT_MAX_NAME_LENGTH

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> GreetingConfig:
        """Parse and strictly validate configuration dictionary.

        Args:
            data: Raw configuration dictionary or None.

        Returns:
            Validated GreetingConfig instance.

        Raises:
            ValueError: If unknown keys are present, or values violate constraints.
        """
        if not data:
            return cls()

        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            raise ValueError(
                "Unknown Greeting configuration keys: " + ", ".join(sorted(unknown))
            )

        salutation = data.get("default_salutation", _DEFAULT_SALUTATION)
        if not isinstance(salutation, str) or not salutation.strip():
            raise ValueError("default_salutation must be a non-empty string")

        max_length = data.get("max_name_length", _DEFAULT_MAX_NAME_LENGTH)
        if (
            not isinstance(max_length, int)
            or isinstance(max_length, bool)
            or max_length <= 0
        ):
            raise ValueError("max_name_length must be a positive integer")

        return cls(
            default_salutation=salutation.strip(),
            max_name_length=max_length,
        )
