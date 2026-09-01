"""Strict configuration for immutable run-data bindings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_DEFAULT_DATABASE_PATH = Path(".haruquant") / "data-run-bindings.sqlite3"
_ALLOWED_KEYS = frozenset({"database_path"})


@dataclass(frozen=True, slots=True)
class BindRunDataConfig:
    """Trusted configuration for run-data binding persistence."""

    database_path: Path = _DEFAULT_DATABASE_PATH

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> BindRunDataConfig:
        """Validate and normalize raw feature configuration.

        Args:
            values: Raw feature configuration.

        Returns:
            Frozen validated configuration.

        Raises:
            ValueError: If keys or path are invalid.
        """
        unknown = set(values) - _ALLOWED_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        raw = values.get("database_path", str(_DEFAULT_DATABASE_PATH))
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("database_path must be a non-empty string")
        return cls(database_path=Path(raw).expanduser())
