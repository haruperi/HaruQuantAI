"""Configuration validation for Persistent Storage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset({"driver", "db_path", "base_path"})


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Configuration for SQLite-backed or disk-backed persistent storage."""

    db_path: str = "data/db/haruquantai.db"
    base_path: str = "data/storage"
    driver: str = "sqlite"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> StorageConfig:
        """Parse and validate a strict storage configuration mapping."""
        if not data:
            return cls()
        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            raise ValueError(
                "Unknown Persistent Storage configuration keys: "
                + ", ".join(sorted(unknown))
            )
        db_path = str(data.get("db_path", "data/db/haruquantai.db")).strip()
        if not db_path:
            raise ValueError("db_path must not be empty")
        base_path = str(data.get("base_path", "data/storage")).strip()
        if not base_path:
            raise ValueError("base_path must not be empty")
        driver = str(data.get("driver", "sqlite")).strip().lower()
        if driver not in {"sqlite", "disk"}:
            raise ValueError(f"driver must be 'sqlite' or 'disk', got '{driver}'")
        return cls(db_path=db_path, base_path=base_path, driver=driver)

    @property
    def database_file(self) -> Path:
        """Return the configured SQLite database path."""
        return Path(self.db_path)

    @property
    def root_directory(self) -> Path:
        """Return the configured disk-storage root directory."""
        return Path(self.base_path)
