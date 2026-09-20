"""Hot point-in-time snapshots management for Persistence domain.

Feature:
    FEAT-PERSISTENCE-SNAPSHOTS

Purpose:
    Provides non-blocking hot point-in-time database backups via SQLite VACUUM INTO,
    snapshot cataloging with SHA-256 verification, and atomic restoration.

Invariants:
    * VACUUM INTO snapshots are created without interrupting active read connections.
    * WAL checkpoints are triggered prior to snapshotting to ensure consistent state.
    * Restorations validate database integrity before applying.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import override

from app.contracts.persistence import (
    DATABASE_SERVICE,
    SNAPSHOT_SERVICE,
    DatabaseService,
    SnapshotError,
    SnapshotRecord,
)
from app.contracts.persistence import (
    SnapshotService as ISnapshotService,
)
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger
from app.services.persistence.persistence import PersistenceDatabaseManager

logger = get_logger(__name__)

HASH_CHUNK_SIZE_BYTES: int = 65536


def _compute_file_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file in streaming chunks.

    Args:
        path: Path to the target file.

    Returns:
        Hex-encoded SHA-256 checksum string.
    """
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(HASH_CHUNK_SIZE_BYTES):
            hasher.update(chunk)
    return hasher.hexdigest()


@dataclass(frozen=True, slots=True)
class SnapshotConfig:
    """Configuration for hot snapshot storage.

    Attributes:
        snapshot_dir: Default directory where generated snapshots are stored.
    """

    snapshot_dir: Path = Path("data/snapshots")


class SnapshotServiceImpl(ISnapshotService):
    """Concrete implementation of SnapshotService."""

    def __init__(
        self,
        db_service: DatabaseService,
        config: SnapshotConfig | None = None,
    ) -> None:
        """Initialize snapshot service.

        Args:
            db_service: Database service provider.
            config: Optional snapshot storage configuration.
        """
        self._db_service = db_service
        self._config = config or SnapshotConfig()
        self._manager = PersistenceDatabaseManager(db_service.database_path)

    @override
    def create_snapshot(
        self, destination_path: Path | None = None, label: str = ""
    ) -> SnapshotRecord:
        """Create an atomic VACUUM INTO hot snapshot.

        Args:
            destination_path: Optional explicit target path. If omitted,
                a generated timestamped path within `snapshot_dir` is used.
            label: Optional descriptive tag for the snapshot.

        Returns:
            SnapshotRecord metadata receipt.

        Raises:
            SnapshotError: If snapshot creation fails.
        """
        now = datetime.now(UTC)
        target_path = destination_path
        if target_path is None:
            self._config.snapshot_dir.mkdir(parents=True, exist_ok=True)
            stamp = now.strftime("%Y%m%d_%H%M%S")
            short_id = uuid.uuid4().hex[:8]
            file_name = f"snapshot_{stamp}_{short_id}.db"
            target_path = self._config.snapshot_dir / file_name

        try:
            # Checkpoint WAL first to flush committed pages to disk
            self._db_service.checkpoint()
            self._db_service.hot_snapshot(target_path)
        except Exception as exc:
            msg = f"Failed to create hot snapshot at {target_path}: {exc}"
            logger.exception("hot_snapshot_failed", path=str(target_path))
            raise SnapshotError(msg) from exc

        if not target_path.exists():
            msg = f"Snapshot file was not created at {target_path}"
            raise SnapshotError(msg)

        size_bytes = target_path.stat().st_size
        checksum = _compute_file_sha256(target_path)
        record = SnapshotRecord(
            snapshot_id=target_path.stem,
            path=target_path,
            size_bytes=size_bytes,
            checksum_sha256=checksum,
            label=label,
            created_at_utc=now,
        )
        logger.info(
            "hot_snapshot_created",
            snapshot_id=record.snapshot_id,
            size_bytes=size_bytes,
            label=label,
        )
        return record

    @override
    def list_snapshots(self) -> list[SnapshotRecord]:
        """List available snapshots ordered by creation timestamp descending.

        Returns:
            List of discovered SnapshotRecord receipts.
        """
        if not self._config.snapshot_dir.exists():
            return []

        snapshots: list[SnapshotRecord] = []
        for file_path in self._config.snapshot_dir.glob("*.db"):
            try:
                stat = file_path.stat()
                created_dt = datetime.fromtimestamp(stat.st_mtime, tz=UTC)
                checksum = _compute_file_sha256(file_path)
                snapshots.append(
                    SnapshotRecord(
                        snapshot_id=file_path.stem,
                        path=file_path,
                        size_bytes=stat.st_size,
                        checksum_sha256=checksum,
                        label="",
                        created_at_utc=created_dt,
                    )
                )
            except OSError as exc:
                logger.warning(
                    "snapshot_stat_failed",
                    path=str(file_path),
                    error=str(exc),
                )

        snapshots.sort(key=lambda s: s.created_at_utc, reverse=True)
        return snapshots

    @override
    def restore_snapshot(
        self, snapshot_path: Path, expected_checksum_sha256: str | None = None
    ) -> None:
        """Restore the database from a validated snapshot file.

        Args:
            snapshot_path: Path to snapshot database file to restore from.
            expected_checksum_sha256: Optional expected SHA-256 checksum to verify.

        Raises:
            SnapshotError: If snapshot is invalid, corrupt, checksum mismatches,
                or restore fails.
        """
        if not snapshot_path.is_file():
            msg = f"Snapshot file does not exist: {snapshot_path}"
            raise SnapshotError(msg)

        # 1. Optional checksum verification
        if expected_checksum_sha256 is not None:
            actual_checksum = _compute_file_sha256(snapshot_path)
            if actual_checksum != expected_checksum_sha256:
                msg = (
                    f"Snapshot checksum verification failed for {snapshot_path}: "
                    f"expected {expected_checksum_sha256}, got {actual_checksum}"
                )
                raise SnapshotError(msg)

        # 2. Validate SQLite database integrity via persistence manager
        try:
            self._manager.verify_sqlite_integrity(snapshot_path)
        except Exception as exc:
            msg = f"Corrupt SQLite snapshot file at {snapshot_path}: {exc}"
            raise SnapshotError(msg) from exc

        # 3. Perform live restoration via persistence manager
        try:
            self._manager.restore_database(snapshot_path)
            logger.info("database_restored_from_snapshot", snapshot=str(snapshot_path))
        except Exception as exc:
            msg = (
                f"Failed to restore database from {snapshot_path} into "
                f"{self._db_service.database_path}: {exc}"
            )
            logger.exception("snapshot_restore_failed", path=str(snapshot_path))
            raise SnapshotError(msg) from exc


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.snapshots",
    provides=frozenset({SNAPSHOT_SERVICE}),
    requires=frozenset({DATABASE_SERVICE}),
    optional=frozenset(),
    description="Hot point-in-time SQLite snapshots and backup sets.",
)


class SnapshotFeature:
    """Wire hot snapshot service into kernel composition lifecycle."""

    def __init__(self, config: SnapshotConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional snapshot configuration.
        """
        self._config = config or SnapshotConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve database capability and register snapshot service.

        Args:
            context: Kernel feature context.
        """
        db_service = context.require(DATABASE_SERVICE)
        service = SnapshotServiceImpl(db_service, self._config)
        context.provide(SNAPSHOT_SERVICE, service)
        logger.info(
            "persistence_snapshots_feature_started",
            snapshot_dir=str(self._config.snapshot_dir),
        )


def feature() -> SnapshotFeature:
    """Return a zero-argument factory instance of SnapshotFeature."""
    return SnapshotFeature()
