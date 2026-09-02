"""Configuration dataclass for Broker Operations feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"database_path"})


@dataclass(frozen=True, slots=True)
class BrokerOperationsConfig:
    """Configuration options for Broker Operations.

    Attributes:
        database_path: Optional custom path to SQLite central database.
    """

    database_path: Path | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> BrokerOperationsConfig:
        """Parse configuration mapping.

        Args:
            data: Raw feature configuration mapping.

        Returns:
            Validated immutable BrokerOperationsConfig instance.

        Raises:
            TypeError: If database_path is not a string or Path.
            ValueError: If unknown keys are provided or database_path is empty string.
        """
        if not data:
            return cls()

        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            msg = f"Unknown Broker Operations configuration keys: {', '.join(sorted(unknown))}"
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
