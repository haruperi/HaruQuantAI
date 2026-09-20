"""Forward schema migrations management for Persistence domain.

Feature:
    FEAT-PERSISTENCE-MIGRATIONS

Purpose:
    Provides automated discovery, SHA-256 checksum verification, and transactional
    execution of forward schema migrations for the SQLite control-plane database.
    Corresponds to StrategyQuant X project schema upgrades.

Invariants:
    * All migration steps execute inside immediate transactions.
    * SHA-256 checksums of SQL scripts are verified before application;
      checksum discrepancies on previously applied migrations fail closed.
    * Migrations are applied in strict ascending version order.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from app.contracts.persistence import (
    DATABASE_SERVICE,
    MIGRATION_SERVICE,
    DatabaseService,
    MigrationError,
    MigrationRecord,
)
from app.contracts.persistence import (
    MigrationService as IMigrationService,
)
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger
from app.services.persistence.persistence import SCHEMA_SQL

logger = get_logger(__name__)

EXPECTED_FILENAME_PARTS_COUNT: int = 2

BUILTIN_MIGRATIONS: tuple[tuple[int, str, str], ...] = (
    (
        1,
        "0001_initial_schema",
        SCHEMA_SQL,
    ),
    (
        2,
        "0002_secondary_indexes",
        (
            "CREATE INDEX IF NOT EXISTS idx_persistence_views_scope "
            "ON persistence_databank_views(scope);\n"
            "CREATE INDEX IF NOT EXISTS idx_persistence_lineage_parent "
            "ON persistence_artifact_lineage(parent_artifact_id);\n"
        ),
    ),
)


def _compute_checksum(content: str) -> str:
    """Compute SHA-256 checksum string for a SQL script.

    Args:
        content: SQL script text.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class MigrationConfig:
    """Configuration for schema migrations discovery.

    Attributes:
        migrations_dir: Optional filesystem directory containing `.sql` files.
        custom_migrations: Optional sequence of (version, name, sql) tuples.
    """

    migrations_dir: Path | None = None
    custom_migrations: tuple[tuple[int, str, str], ...] = ()


class MigrationServiceImpl(IMigrationService):
    """Concrete implementation of MigrationService."""

    def __init__(
        self,
        db_service: DatabaseService,
        config: MigrationConfig | None = None,
    ) -> None:
        """Initialize migration service with database service and config.

        Args:
            db_service: Database service provider.
            config: Optional migration configuration.
        """
        self._db_service = db_service
        self._config = config or MigrationConfig()

    def _discover_available_migrations(self) -> list[tuple[int, str, str, str]]:
        """Discover and validate all migrations from built-in and directory sources.

        Returns:
            List of (version, name, sql, checksum) sorted by version.

        Raises:
            MigrationError: If duplicate versions are discovered.
        """
        migrations: dict[int, tuple[str, str, str]] = {}

        # 1. Built-in migrations
        for version, name, sql in BUILTIN_MIGRATIONS:
            checksum = _compute_checksum(sql)
            migrations[version] = (name, sql, checksum)

        # 2. Configured custom migrations
        for version, name, sql in self._config.custom_migrations:
            if version in migrations:
                msg = f"Duplicate migration version {version} in custom_migrations"
                raise MigrationError(msg)
            checksum = _compute_checksum(sql)
            migrations[version] = (name, sql, checksum)

        # 3. Filesystem directory if configured
        if self._config.migrations_dir and self._config.migrations_dir.is_dir():
            for sql_file in sorted(self._config.migrations_dir.glob("*.sql")):
                stem = sql_file.stem
                parts = stem.split("_", 1)
                if len(parts) == EXPECTED_FILENAME_PARTS_COUNT and parts[0].isdigit():
                    version = int(parts[0])
                    name = stem
                    sql = sql_file.read_text(encoding="utf-8")
                    if version in migrations:
                        msg = f"Duplicate migration version {version} from {sql_file}"
                        raise MigrationError(msg)
                    checksum = _compute_checksum(sql)
                    migrations[version] = (name, sql, checksum)

        sorted_items = sorted(migrations.items(), key=lambda x: x[0])
        return [(ver, item[0], item[1], item[2]) for ver, item in sorted_items]

    @override
    def get_applied_migrations(self) -> list[MigrationRecord]:
        """Return list of applied schema migrations in version order.

        Returns:
            List of applied MigrationRecord objects.
        """
        rows = self._db_service.execute_query(
            "SELECT version, name, checksum, applied_at_utc "
            "FROM persistence_schema_migrations "
            "ORDER BY version ASC;"
        )
        return [
            MigrationRecord(
                version=int(r["version"]),
                name=str(r["name"]),
                checksum=str(r["checksum"]),
                applied_at_utc=datetime.fromisoformat(r["applied_at_utc"]),
            )
            for r in rows
        ]

    @override
    def get_pending_migrations(self) -> list[MigrationRecord]:
        """Return list of pending unapplied schema migrations.

        Returns:
            List of unapplied migrations formatted as MigrationRecord.

        Raises:
            MigrationError: If an applied migration has a checksum mismatch.
        """
        applied = {m.version: m for m in self.get_applied_migrations()}
        available = self._discover_available_migrations()
        pending: list[MigrationRecord] = []

        now_utc = datetime.now(UTC)
        for ver, name, _sql, checksum in available:
            if ver in applied:
                applied_rec = applied[ver]
                if applied_rec.checksum != checksum:
                    msg = (
                        f"Checksum mismatch for migration {ver} ({name}): "
                        f"recorded {applied_rec.checksum} != current {checksum}"
                    )
                    logger.error("migration_checksum_mismatch", version=ver, name=name)
                    raise MigrationError(msg)
            else:
                pending.append(
                    MigrationRecord(
                        version=ver,
                        name=name,
                        checksum=checksum,
                        applied_at_utc=now_utc,
                    )
                )

        return pending

    @override
    def apply_all(self) -> list[MigrationRecord]:
        """Apply all pending migrations sequentially within transactions.

        Returns:
            List of newly applied MigrationRecord objects.

        Raises:
            MigrationError: If migration execution fails.
        """
        # Validate checksums of previously applied migrations
        self.get_pending_migrations()

        applied_versions = {m.version for m in self.get_applied_migrations()}
        available = self._discover_available_migrations()
        newly_applied: list[MigrationRecord] = []

        for ver, name, sql, checksum in available:
            if ver in applied_versions:
                continue

            applied_at = datetime.now(UTC)
            logger.info("applying_schema_migration", version=ver, name=name)
            try:
                with self._db_service.transaction() as con:
                    con.executescript(sql)
                    con.execute(
                        "INSERT INTO persistence_schema_migrations "
                        "(version, name, checksum, applied_at_utc) "
                        "VALUES (?, ?, ?, ?);",
                        (ver, name, checksum, applied_at.isoformat()),
                    )
            except Exception as exc:
                msg = f"Failed to apply migration {ver} ({name}): {exc}"
                logger.exception("migration_apply_failed", version=ver, name=name)
                raise MigrationError(msg) from exc

            record = MigrationRecord(
                version=ver,
                name=name,
                checksum=checksum,
                applied_at_utc=applied_at,
            )
            newly_applied.append(record)
            logger.info("applied_schema_migration", version=ver, name=name)

        return newly_applied

    @override
    def current_version(self) -> int:
        """Return the current schema version integer.

        Returns:
            Max applied version integer, or 0 if no migrations have been applied.
        """
        applied = self.get_applied_migrations()
        if not applied:
            return 0
        return max(m.version for m in applied)


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.migrations",
    provides=frozenset({MIGRATION_SERVICE}),
    requires=frozenset({DATABASE_SERVICE}),
    optional=frozenset(),
    description="Automated forward schema migrations with checksum verification.",
)


class MigrationFeature:
    """Wire schema migrations service into kernel composition lifecycle."""

    def __init__(self, config: MigrationConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional migration configuration.
        """
        self._config = config or MigrationConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve database capability and register migration service.

        Args:
            context: Kernel feature context.
        """
        db_service = context.require(DATABASE_SERVICE)
        service = MigrationServiceImpl(db_service, self._config)
        context.provide(MIGRATION_SERVICE, service)
        logger.info(
            "persistence_migrations_feature_started",
            current_version=service.current_version(),
        )


def feature() -> MigrationFeature:
    """Return a zero-argument factory instance of MigrationFeature."""
    return MigrationFeature()
