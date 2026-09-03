"""Configuration for Data Quality and Resolution feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataQualityResolutionConfig:
    """Runtime configuration for Data Quality and Resolution feature.

    Attributes:
        database_path: Optional path to SQLite persistence database for lineage
            and lock state.
        auto_migrate: Whether to initialize/migrate database tables automatically.
        max_findings: Maximum number of findings to retain per quality detection run.
    """

    database_path: Path | str | None = None
    auto_migrate: bool = True
    max_findings: int = 10000

    def get_database_path(self) -> Path | None:
        """Return the resolved Path for database if configured.

        Returns:
            Resolved Path object, or None if in-memory or unconfigured.
        """
        if self.database_path is None:
            return None
        return Path(self.database_path).expanduser().resolve()
