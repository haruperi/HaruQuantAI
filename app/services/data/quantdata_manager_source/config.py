"""Configuration for QuantDataManager Source feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QuantDataManagerConfig:
    """Runtime configuration for the QuantDataManager source feature.

    Attributes:
        allowed_root: Optional filesystem root directory constraining all discovery
            and decoding operations. If None, default root must be passed per spec.
        database_path: Path to internal persistence database (SQLite) for version
            lineage and state storage.
        auto_migrate: Whether to automatically apply database schema migrations.
    """

    allowed_root: Path | str | None = None
    database_path: Path | str | None = None
    auto_migrate: bool = True

    def get_allowed_root_path(self) -> Path | None:
        """Return the resolved Path for allowed_root if configured.

        Returns:
            Resolved Path object, or None if not configured.
        """
        if self.allowed_root is None:
            return None
        return Path(self.allowed_root).expanduser().resolve()

    def get_database_path(self) -> Path | None:
        """Return the resolved Path for the internal database if configured.

        Returns:
            Resolved Path object, or None if in-memory or unconfigured.
        """
        if self.database_path is None:
            return None
        return Path(self.database_path).expanduser().resolve()

    def is_path_allowed(
        self, target_path: Path | str, base_root: Path | str | None = None
    ) -> bool:
        """Verify that target_path is strictly within the allowed root directory.

        Args:
            target_path: Path to test.
            base_root: Optional root override. If None, uses configured allowed_root.

        Returns:
            True if target_path resolves inside the allowed root, False otherwise.
        """
        root = Path(base_root).resolve() if base_root else self.get_allowed_root_path()
        if root is None:
            return False
        try:
            resolved_target = Path(target_path).resolve()
            resolved_target.relative_to(root)
            return True
        except ValueError:
            return False
