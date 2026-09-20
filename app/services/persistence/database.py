"""Transactional SQLite persistence feature for the control plane.

Purpose:
    Provides durable storage, parameterized SQL execution, and transactional
    invariants for the application control plane, artifacts catalog, databanks,
    and migrations under namespace `persistence.v1`.

Key capabilities:
    * WAL-mode SQLite metadata management with bounded busy timeout.
    * Parameterized queries, mutations, and managed transaction context.
    * Atomic SQLite hot snapshots via VACUUM INTO.
    * Connection lifecycle cleanup and WAL checkpointing.

Python API usage:
    db = ctx.require(DATABASE_SERVICE)
    db.execute_query("SELECT * FROM persistence_artifacts WHERE ...", params)

CLI usage:
    uv run python -m tests.examples.02_persistence
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

from app.contracts.persistence import (
    DATABASE_SERVICE,
    DatabaseConnectionError,
)
from app.contracts.persistence import (
    DatabaseService as IDatabaseService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger
from app.services.persistence.persistence import PersistenceDatabaseManager

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

DEFAULT_DB_PATH: str = "data/database/haruquantai.db"


def _default_db_path() -> Path:
    """Resolve default database path honoring environment variable override.

    Returns:
        Resolved Path to SQLite database file.
    """
    env_path = os.getenv("HARUQUANTAI_DB_PATH")
    if env_path:
        return Path(env_path)
    return Path(DEFAULT_DB_PATH)


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """Slotted immutable configuration for SQLite database service."""

    database_path: Path = field(default_factory=_default_db_path)
    timeout_s: float = 5.0
    busy_timeout_ms: int = 5000
    wal_mode: bool = True

    def __post_init__(self) -> None:
        """Validate configuration invariants."""
        if self.timeout_s <= 0:
            msg = f"timeout_s must be positive, got {self.timeout_s}"
            raise ValueError(msg)
        if self.busy_timeout_ms <= 0:
            msg = f"busy_timeout_ms must be positive, got {self.busy_timeout_ms}"
            raise ValueError(msg)


class DatabaseServiceImpl(IDatabaseService):
    """Concrete implementation of DatabaseService protocol."""

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize service with configuration.

        Args:
            config: Database configuration parameters.

        Raises:
            DatabaseConnectionError: If database initialization fails.
        """
        self._config = config
        try:
            self._manager = PersistenceDatabaseManager(config.database_path)
            logger.info(
                "persistence_database_initialized",
                db_path=str(config.database_path),
                wal_mode=config.wal_mode,
            )
        except Exception as exc:
            msg = (
                f"Failed to initialize SQLite database at {config.database_path}: {exc}"
            )
            raise DatabaseConnectionError(msg) from exc

    @property
    @override
    def database_path(self) -> Path:
        """Return the active SQLite database path."""
        return self._config.database_path

    @override
    def execute_query(
        self, sql: str, params: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        """Execute a read query and return row dictionaries."""
        return self._manager.execute_query(sql, params)

    @override
    def execute_mutation(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        """Execute an insert, update, or delete and return rows affected."""
        return self._manager.execute_mutation(sql, params)

    @override
    def execute_script(self, sql_script: str) -> None:
        """Execute multiple semicolon-delimited SQL statements."""
        self._manager.execute_script(sql_script)

    @override
    def transaction(self) -> AbstractContextManager[Any]:
        """Enter a managed transactional context."""
        return self._manager.transaction()

    @override
    def checkpoint(self) -> None:
        """Force a WAL checkpoint to truncate wal journal and commit pages."""
        self._manager.checkpoint()

    @override
    def hot_snapshot(self, destination_path: Path) -> None:
        """Create an atomic SQLite point-in-time snapshot using VACUUM INTO.

        Args:
            destination_path: Path where the hot snapshot database will be created.
        """
        self._manager.hot_snapshot(destination_path)

    def close(self) -> None:
        """Close database and flush WAL journal."""
        try:
            self.checkpoint()
            logger.info(
                "persistence_database_closed",
                db_path=str(self._config.database_path),
            )
        except sqlite3.Error as exc:
            logger.warning("persistence_database_close_error", error=str(exc))


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.database",
    provides=frozenset({DATABASE_SERVICE}),
    requires=frozenset(),
    optional=frozenset(),
    description=(
        "SQLite WAL control-plane lifecycle, transactions, and connection management."
    ),
)


class DatabaseFeature:
    """Wire SQLite database service into kernel composition lifecycle."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional database configuration.
        """
        self._config = config or DatabaseConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the database service and publish capability.

        Args:
            context: Lifecycle feature context.
        """
        service = DatabaseServiceImpl(self._config)
        context.on_close(service.close)
        context.provide(DATABASE_SERVICE, service)


def feature() -> DatabaseFeature:
    """Return an unmounted DatabaseFeature instance.

    Returns:
        New DatabaseFeature instance.
    """
    return DatabaseFeature()


__all__ = [
    "DEFAULT_DB_PATH",
    "SPEC",
    "DatabaseConfig",
    "DatabaseFeature",
    "DatabaseServiceImpl",
    "feature",
]
