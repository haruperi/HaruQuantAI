"""Configuration validation for Persistent Storage feature."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class StorageConfig:
    """Configuration options for persistent storage.

    Satisfies:
        FR-SYS-VALIDATE_STORAGE_CONFIG: Validates database and storage paths.

    Attributes:
        db_path: Path to SQLite database file.
        base_path: Filesystem path to root data directory.
        driver: Storage engine driver type ('sqlite' or 'disk').
    """

    db_path: str = "data/db/haruquantai.db"
    base_path: str = "data/storage"
    driver: str = "sqlite"

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> StorageConfig:
        """Parse and validate configuration dictionary.

        Args:
            data: Raw dictionary from application configuration.

        Returns:
            Validated StorageConfig instance.

        Raises:
            ValueError: If db_path or base_path is empty.
        """
        if not data:
            return cls()

        db_path_str = str(data.get("db_path", "data/db/haruquantai.db")).strip()
        if not db_path_str:
            msg = "db_path must not be empty"
            raise ValueError(msg)

        base_path_str = str(data.get("base_path", "data/storage")).strip()
        if not base_path_str:
            msg = "base_path must not be empty"
            raise ValueError(msg)

        driver_str = str(data.get("driver", "sqlite")).strip().lower()
        if driver_str not in {"sqlite", "disk"}:
            msg = f"driver must be 'sqlite' or 'disk', got '{driver_str}'"
            raise ValueError(msg)

        return cls(
            db_path=db_path_str,
            base_path=base_path_str,
            driver=driver_str,
        )

    @property
    def database_file(self) -> Path:
        """Return Path object for SQLite database file."""
        return Path(self.db_path)

    @property
    def root_directory(self) -> Path:
        """Return Path object for base storage directory."""
        return Path(self.base_path)
