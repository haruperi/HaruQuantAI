"""Strict configuration for the Data series-store feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_DEFAULT_DATABASE_PATH = Path(".haruquant") / "data-series.sqlite3"
_ALLOWED_KEYS = frozenset({"database_path"})


@dataclass(frozen=True, slots=True)
class ManageSeriesConfig:
    """Trusted configuration for immutable Data series storage."""

    database_path: Path = _DEFAULT_DATABASE_PATH

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> ManageSeriesConfig:
        """Validate and normalize one raw feature configuration mapping.

        Args:
            values: Raw feature configuration.

        Returns:
            Frozen validated configuration.

        Raises:
            ValueError: If an unknown key or invalid path is supplied.
        """
        unknown = set(values) - _ALLOWED_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        raw_path = values.get("database_path", str(_DEFAULT_DATABASE_PATH))
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError("database_path must be a non-empty string")
        return cls(database_path=Path(raw_path).expanduser())
