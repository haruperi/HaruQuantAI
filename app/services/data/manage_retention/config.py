"""Strict configuration for Data retention management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_DEFAULT_DATABASE_PATH = Path(".haruquant") / "data-retention.sqlite3"
_ALLOWED_KEYS = frozenset({"database_path", "collection_limit"})


@dataclass(frozen=True, slots=True)
class ManageRetentionConfig:
    """Trusted retention-policy persistence and collection configuration."""

    database_path: Path = _DEFAULT_DATABASE_PATH
    collection_limit: int = 100

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> ManageRetentionConfig:
        """Validate and normalize raw feature configuration.

        Args:
            values: Raw feature configuration mapping.

        Returns:
            Trusted immutable configuration.

        Raises:
            ValueError: If a key/value is unsupported.
        """
        unknown = set(values) - _ALLOWED_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        raw_path = values.get("database_path", str(_DEFAULT_DATABASE_PATH))
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError("database_path must be a non-empty string")
        raw_limit = values.get("collection_limit", 100)
        if not isinstance(raw_limit, int) or isinstance(raw_limit, bool):
            raise ValueError("collection_limit must be an integer")
        if not 1 <= raw_limit <= 10_000:
            raise ValueError("collection_limit must be between 1 and 10000")
        return cls(
            database_path=Path(raw_path).expanduser(),
            collection_limit=raw_limit,
        )
