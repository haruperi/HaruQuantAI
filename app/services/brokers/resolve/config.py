"""Configuration dataclass for Service-Level Broker Resolver feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"database_path"})


@dataclass(frozen=True, slots=True)
class ResolveConfig:
    """Configuration options for Service-Level Broker Resolver.

    Attributes:
        database_path: Optional custom path to SQLite central database.
    """

    database_path: Path | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ResolveConfig:
        """Parse configuration mapping.

        Args:
            data: Raw feature configuration mapping.

        Returns:
            Validated immutable ResolveConfig instance.

        Raises:
            TypeError: If database_path is not a string or Path.
            ValueError: If unknown keys are provided or database_path is empty string.
        """
        if not data:
            return cls()

        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            msg = f"Unknown Resolve configuration keys: {', '.join(sorted(unknown))}"
            raise ValueError(msg)

        raw_path = data.get("database_path")
        if raw_path is None:
            return cls(database_path=None)

        if not isinstance(raw_path, (str, Path)):
            msg = "database_path must be a string or Path"
            raise TypeError(msg)

        str_path = str(raw_path).strip()
        if not str_path:
            msg = "database_path cannot be an empty string"
            raise ValueError(msg)

        return cls(database_path=Path(str_path))
