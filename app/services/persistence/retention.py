"""Reference-safe retention graph checking and audited purge management.

Feature:
    FEAT-PERSISTENCE-RETENTION

Purpose:
    Evaluates reference dependency graphs (databank memberships, lineage DAGs,
    and external references) to safeguard active artifacts while allowing
    safe, audited purging of orphan artifacts with dry-run verification.
    Corresponds to StrategyQuant X databank purge and storage cleanup rules.

Invariants:
    * An artifact cannot be purged if it has active databank memberships or
      is referenced as a parent by any other cataloged artifact.
    * Every physical purge records an audit trail in `persistence_retention_audit`.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from app.contracts.persistence import (
    ARTIFACT_STORE,
    DATABASE_SERVICE,
    RETENTION_SERVICE,
    ArtifactStore,
    DatabaseService,
    RetentionPlan,
    RetentionPurgeReport,
    RetentionReferenceBlockedError,
)
from app.contracts.persistence import (
    RetentionService as IRetentionService,
)
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger
from app.services.persistence.persistence import PersistenceDatabaseManager

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RetentionConfig:
    """Configuration for retention management.

    Attributes:
        artifacts_dir: Directory where physical artifact binary files reside.
    """

    artifacts_dir: Path = Path("data/artifacts")


class RetentionServiceImpl(IRetentionService):
    """Concrete implementation of RetentionService."""

    def __init__(
        self,
        db_service: DatabaseService,
        artifact_store: ArtifactStore,
        config: RetentionConfig | None = None,
    ) -> None:
        """Initialize retention service with database, artifact store, and config.

        Args:
            db_service: Database service provider.
            artifact_store: Artifact store capability provider.
            config: Optional retention configuration.
        """
        self._db_service = db_service
        self._artifact_store = artifact_store
        self._config = config or RetentionConfig()
        self._manager = PersistenceDatabaseManager(db_service.database_path)

    def _collect_blocking_reasons(
        self,
        artifact_id: str,
        active_refs: Mapping[str, Sequence[str]],
    ) -> list[str]:
        """Collect all blocking reasons for an artifact candidate."""
        reasons: list[str] = []

        # 1. Check external references
        if active_refs.get(artifact_id):
            reasons.extend(
                f"Active external reference: {ref}" for ref in active_refs[artifact_id]
            )

        # 2. Check databank memberships
        member_rows = self._manager.execute_query(
            "SELECT project_name, databank_name "
            "FROM persistence_databank_members WHERE artifact_id = ?;",
            (artifact_id,),
        )
        reasons.extend(
            f"Active databank membership: {m['project_name']}/{m['databank_name']}"
            for m in member_rows
        )

        # 3. Check lineage child dependencies (is this artifact a parent?)
        children = self._manager.get_artifact_children(artifact_id)
        reasons.extend(
            f"Referenced as parent by artifact {child_id}" for child_id in children
        )

        # 4. Check if artifact actually exists in catalog
        art_rec = self._artifact_store.get_artifact(artifact_id)
        if art_rec is None:
            reasons.append("Artifact does not exist in catalog")

        return reasons

    @override
    def plan_purge(
        self,
        target_artifact_ids: Sequence[str],
        active_references: Mapping[str, Sequence[str]] | None = None,
    ) -> RetentionPlan:
        """Evaluate purge candidates against reference graph without mutating.

        Args:
            target_artifact_ids: Artifact IDs nominated for deletion.
            active_references: Optional external references map (e.g. active jobs).

        Returns:
            RetentionPlan detailing eligible vs blocked artifacts.
        """
        active_refs = active_references or {}
        eligible: list[str] = []
        blocked: list[str] = []
        blocking_reasons: dict[str, tuple[str, ...]] = {}

        for aid in target_artifact_ids:
            reasons = self._collect_blocking_reasons(aid, active_refs)
            if reasons:
                blocked.append(aid)
                blocking_reasons[aid] = tuple(reasons)
            else:
                eligible.append(aid)

        logger.info(
            "retention_purge_planned",
            target_count=len(target_artifact_ids),
            eligible_count=len(eligible),
            blocked_count=len(blocked),
        )

        return RetentionPlan(
            target_artifact_ids=tuple(target_artifact_ids),
            eligible_artifact_ids=tuple(eligible),
            blocked_artifact_ids=tuple(blocked),
            blocking_reasons=blocking_reasons,
        )

    @override
    def execute_purge(
        self, plan: RetentionPlan, dry_run: bool = False
    ) -> RetentionPurgeReport:
        """Purge eligible artifacts and record audit trail.

        Args:
            plan: Validated RetentionPlan.
            dry_run: If True, simulate deletion without touching disk or DB.

        Returns:
            RetentionPurgeReport with operation details.

        Raises:
            RetentionReferenceBlockedError: If an eligible artifact became referenced
                or invalid since the plan was created.
        """
        # Re-validate all eligible artifacts at execution time against stale plans
        for aid in plan.eligible_artifact_ids:
            reasons = self._collect_blocking_reasons(aid, {})
            if reasons:
                msg = (
                    f"Stale retention plan: artifact {aid} is now blocked by active "
                    f"references: {reasons}"
                )
                raise RetentionReferenceBlockedError(msg)

        operation_id = f"purge_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)
        reclaimed_bytes = 0
        purged_ids: list[str] = []

        for aid in plan.eligible_artifact_ids:
            rec = self._artifact_store.get_artifact(aid)
            size = rec.size_bytes if rec else 0
            reclaimed_bytes += size

            if not dry_run:
                # 1. Remove physical binary payload file
                payload_file = self._config.artifacts_dir / f"{aid}.bin"
                payload_file.unlink(missing_ok=True)

                # 2. Remove catalog entry and lineage edges
                self._manager.delete_artifact_record(aid)

                # 3. Record audit trail
                self._manager.record_purge_audit(
                    operation_id,
                    aid,
                    "retention_policy",
                    now,
                )

            purged_ids.append(aid)

        logger.info(
            "retention_purge_executed",
            operation_id=operation_id,
            purged_count=len(purged_ids),
            reclaimed_bytes=reclaimed_bytes,
            dry_run=dry_run,
        )

        return RetentionPurgeReport(
            operation_id=operation_id,
            purged_count=len(purged_ids),
            reclaimed_bytes=reclaimed_bytes,
            purged_artifact_ids=tuple(purged_ids),
            executed_at_utc=now,
        )

    @override
    def get_audit_history(
        self, operation_id: str | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Retrieve historical purge audit records.

        Args:
            operation_id: Optional filter for specific operation.
            limit: Maximum records to return.

        Returns:
            List of audit dictionary records.
        """
        return self._manager.get_purge_audit(operation_id, limit)


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.retention",
    provides=frozenset({RETENTION_SERVICE}),
    requires=frozenset({DATABASE_SERVICE, ARTIFACT_STORE}),
    optional=frozenset(),
    description="Reference-safe retention graph checking and audited purge.",
)


class RetentionFeature:
    """Wire retention service into kernel composition lifecycle."""

    def __init__(self, config: RetentionConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional retention configuration.
        """
        self._config = config or RetentionConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve dependencies and register retention service.

        Args:
            context: Kernel feature context.
        """
        db_service = context.require(DATABASE_SERVICE)
        artifact_store = context.require(ARTIFACT_STORE)
        service = RetentionServiceImpl(db_service, artifact_store, self._config)
        context.provide(RETENTION_SERVICE, service)
        logger.info("persistence_retention_feature_started")


def feature() -> RetentionFeature:
    """Return a zero-argument factory instance of RetentionFeature."""
    return RetentionFeature()
