"""Strict configuration for the artifact custody feature.

Purpose:
    Parse and validate the bounded configuration accepted by
    FEAT-WS-MANAGE_ARTIFACTS.

Key capabilities:
    * Reject unknown configuration keys deterministically.
    * Carry the shared workspace database path and derived custody root.
    * Pin finite operational limits for payload size, staging expiry,
      cleanup batches, and download-grant TTL.

Python API usage:
    config = ManageArtifactsConfig.from_dict({})
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {
        "database_path",
        "custody_root",
        "max_artifact_bytes",
        "staging_max_age_seconds",
        "cleanup_batch_limit",
        "grant_max_ttl_seconds",
    }
)

_DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "database" / "haruquantai.db"
)

# 64 MiB default artifact cap; every accepted publication is bounded by
# this finite limit so staging never assumes unbounded disk or memory.
DEFAULT_MAX_ARTIFACT_BYTES = 64 * 1024 * 1024

_MAX_CLEANUP_BATCH_LIMIT = 10_000
_MAX_GRANT_TTL_SECONDS = 86_400


def _validated_int(
    data: dict[str, Any],
    key: str,
    default: int,
    maximum: int | None = None,
) -> int:
    """Parse one bounded integer configuration value.

    Args:
        data: Configuration mapping.
        key: Configuration key to read.
        default: Default when the key is absent.
        maximum: Optional inclusive upper bound.

    Returns:
        The validated integer value.

    Raises:
        TypeError: If the value is not an integer.
        ValueError: If the value is outside its bounded range.
    """
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"{key} must be an integer"
        raise TypeError(message)
    if value < 1 or (maximum is not None and value > maximum):
        message = f"{key} is outside its bounded range"
        raise ValueError(message)
    return value


def from_dict(data: dict[str, Any] | None) -> ManageArtifactsConfig:
    """Build a configuration from a mapping, rejecting unknown keys.

    Args:
        data: Configuration mapping or None for defaults.

    Returns:
        Parsed immutable configuration.

    Raises:
        ValueError: If an unknown key or an out-of-range value is present.
        TypeError: If a value has an unexpected type.
    """
    if not data:
        return ManageArtifactsConfig()
    unknown = set(data) - _ALLOWED_CONFIG_KEYS
    if unknown:
        message = "Unknown manage-artifacts configuration keys: " + ", ".join(
            sorted(unknown)
        )
        raise ValueError(message)
    for key in ("database_path", "custody_root"):
        value = data.get(key)
        if value is not None and not isinstance(value, str | Path):
            message = f"{key} must be a string or Path"
            raise TypeError(message)
    return ManageArtifactsConfig(
        database_path=(
            Path(data["database_path"])
            if data.get("database_path") is not None
            else _DEFAULT_DATABASE_PATH
        ),
        custody_root=(
            Path(data["custody_root"]) if data.get("custody_root") is not None else None
        ),
        max_artifact_bytes=_validated_int(data, "max_artifact_bytes", 64 * 1024 * 1024),
        staging_max_age_seconds=_validated_int(data, "staging_max_age_seconds", 3600),
        cleanup_batch_limit=_validated_int(
            data, "cleanup_batch_limit", 100, maximum=_MAX_CLEANUP_BATCH_LIMIT
        ),
        grant_max_ttl_seconds=_validated_int(
            data, "grant_max_ttl_seconds", 600, maximum=_MAX_GRANT_TTL_SECONDS
        ),
    )


@dataclass(frozen=True, slots=True)
class ManageArtifactsConfig:
    """Runtime configuration for the artifact custody feature.

    Attributes:
        database_path: Shared workspace SQLite database path holding the
            feature-owned ``workspace.manage_artifacts`` namespace tables.
        custody_root: Optional explicit custody root for artifact bytes;
            defaults to an ``artifacts`` directory beside the workspace
            database.
        max_artifact_bytes: Finite maximum accepted payload size.
        staging_max_age_seconds: Age after which incomplete staging
            objects become eligible for admitted cleanup.
        cleanup_batch_limit: Maximum objects examined or removed by one
            reconciliation run.
        grant_max_ttl_seconds: Maximum download-grant lifetime.
    """

    database_path: Path = _DEFAULT_DATABASE_PATH
    custody_root: Path | None = None
    max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES
    staging_max_age_seconds: int = 3600
    cleanup_batch_limit: int = 100
    grant_max_ttl_seconds: int = 600

    def _validate_paths(self) -> None:
        if not isinstance(self.database_path, Path):
            raise TypeError("database_path must be a Path")
        if self.database_path.suffix and self.database_path.name != "haruquantai.db":
            raise ValueError(
                "database_path must name haruquantai.db or a database directory"
            )
        if self.custody_root is not None and not isinstance(self.custody_root, Path):
            raise TypeError("custody_root must be a Path")

    def _validate_limits(self) -> None:
        if isinstance(self.max_artifact_bytes, bool) or not isinstance(
            self.max_artifact_bytes, int
        ):
            raise TypeError("max_artifact_bytes must be an integer")
        if self.max_artifact_bytes < 1:
            raise ValueError("max_artifact_bytes must be at least 1")
        if isinstance(self.staging_max_age_seconds, bool) or not isinstance(
            self.staging_max_age_seconds, int
        ):
            raise TypeError("staging_max_age_seconds must be an integer")
        if self.staging_max_age_seconds < 1:
            raise ValueError("staging_max_age_seconds must be at least 1")
        if isinstance(self.cleanup_batch_limit, bool) or not isinstance(
            self.cleanup_batch_limit, int
        ):
            raise TypeError("cleanup_batch_limit must be an integer")
        if not 1 <= self.cleanup_batch_limit <= _MAX_CLEANUP_BATCH_LIMIT:
            raise ValueError("cleanup_batch_limit is outside its bounded range")
        if isinstance(self.grant_max_ttl_seconds, bool) or not isinstance(
            self.grant_max_ttl_seconds, int
        ):
            raise TypeError("grant_max_ttl_seconds must be an integer")
        if not 1 <= self.grant_max_ttl_seconds <= _MAX_GRANT_TTL_SECONDS:
            raise ValueError("grant_max_ttl_seconds is outside its bounded range")

    def __post_init__(self) -> None:
        """Validate the compatibility paths and finite limits.

        Raises:
            TypeError: If a path is not a Path or a limit is not an
                integer.
            ValueError: If the database file is not canonical or a limit
                is outside its bounded range.
        """
        self._validate_paths()
        self._validate_limits()

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ManageArtifactsConfig:
        """Build a strict configuration from a mapping.

        Args:
            data: Configuration mapping or None.

        Returns:
            Validated immutable configuration.
        """
        return from_dict(data)

    @property
    def workspace_path(self) -> Path:
        """Return the canonical database path used by persistence.

        Returns:
            Central database path or directory.
        """
        return self.database_path

    @property
    def effective_custody_root(self) -> Path:
        """Return the custody root for immutable artifact bytes.

        The default places the custody root in an ``artifacts`` directory
        beside the canonical workspace database file (or inside the
        configured database directory), keeping staging and published
        objects on one filesystem so publication uses an atomic
        same-volume rename.

        Returns:
            Explicit custody root when configured, otherwise the derived
            default.
        """
        if self.custody_root is not None:
            return self.custody_root
        if self.database_path.suffix == ".db":
            return self.database_path.parent / "artifacts"
        return self.database_path / "artifacts"
