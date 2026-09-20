"""Project-scoped databanks, ranking, similarity filtering, and column views.

Feature:
    FEAT-PERSISTENCE-DATABANKS

Purpose:
    Provides project-scoped databanks matching StrategyQuant X databank architecture,
    including capacity-bounded storage with deterministic ranking eviction, metric
    similarity evaluation and dismissal (Net Profit, Trade Count, Max Drawdown ±5%),
    non-duplicating copy/move semantics, and persistent column projection views.

Invariants:
    * Artifacts stored in databanks are referenced by artifact_id without duplicating
      physical payload files.
    * When databank capacity is reached, members with lower ranking are evicted
      deterministically to make room for superior candidates.
    * Similar strategies with inferior fitness are dismissed per DEC-PERSISTENCE-003.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

from app.contracts.persistence import (
    ARTIFACT_STORE,
    DATABANK_STORE,
    DATABASE_SERVICE,
    ArtifactNotFoundError,
    ArtifactStore,
    AutoSyncPolicy,
    DatabankMemberRecord,
    DatabankNotFoundError,
    DatabankRecord,
    DatabankViewConfig,
    DatabaseService,
    DuplicateMemberError,
    SimilarityMatchResult,
    SimilarityProfile,
)
from app.contracts.persistence import (
    DatabankStore as IDatabankStore,
)
from app.kernel.context import FeatureContext
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger
from app.services.persistence.persistence import PersistenceDatabaseManager

logger = get_logger(__name__)

EPSILON_DENOMINATOR: float = 1e-9


def _get_metric_val(metrics: Mapping[str, float], key: str) -> float | None:
    """Retrieve metric value with fallback aliases."""
    val = metrics.get(key)
    if val is None and key == "trade_count":
        return metrics.get("trades")
    if val is None and key == "drawdown":
        return metrics.get("max_drawdown")
    return val


def _check_metrics_similarity(
    candidate_metrics: Mapping[str, float],
    member_metrics: Mapping[str, float],
    profile: SimilarityProfile,
) -> bool:
    """Check if all active metrics fall within profile tolerance percentage."""
    metric_checks: list[tuple[str, bool]] = [
        ("net_profit", profile.compare_net_profit),
        ("trade_count", profile.compare_trade_count),
        ("drawdown", profile.compare_drawdown),
    ]

    tested_any = False
    for metric_key, is_enabled in metric_checks:
        if not is_enabled:
            continue

        cand_val = _get_metric_val(candidate_metrics, metric_key)
        mem_val = _get_metric_val(member_metrics, metric_key)

        if cand_val is not None and mem_val is not None:
            tested_any = True
            denom = max(abs(mem_val), EPSILON_DENOMINATOR)
            diff_pct = (abs(cand_val - mem_val) / denom) * 100.0
            if diff_pct > profile.tolerance_pct:
                return False
        else:
            return False

    return tested_any


@dataclass(frozen=True, slots=True)
class DatabankConfig:
    """Configuration for databank service.

    Attributes:
        default_capacity: Default capacity limit for newly created databanks.
    """

    default_capacity: int = 1000


class DatabankServiceImpl(IDatabankStore):
    """Concrete implementation of DatabankStore protocol."""

    def __init__(
        self,
        db_service: DatabaseService,
        artifact_store: ArtifactStore,
        config: DatabankConfig | None = None,
    ) -> None:
        """Initialize databank service.

        Args:
            db_service: Database service provider.
            artifact_store: Artifact catalog provider.
            config: Optional databank configuration.
        """
        self._db_service = db_service
        self._artifact_store = artifact_store
        self._config = config or DatabankConfig()
        self._manager = PersistenceDatabaseManager(db_service.database_path)

    @override
    def create_databank(
        self,
        project_name: str,
        databank_name: str,
        capacity: int = 1000,
        default_view: str = "Default",
        auto_sync_policy: AutoSyncPolicy = AutoSyncPolicy.NEVER,
    ) -> DatabankRecord:
        """Create a new project databank.

        Args:
            project_name: Project scope identifier.
            databank_name: Name of databank (e.g. 'Results').
            capacity: Maximum number of strategies held.
            default_view: Name of default column view.
            auto_sync_policy: Interval for auto synchronization.

        Returns:
            Created DatabankRecord.
        """
        now = datetime.now(UTC)
        record = self._manager.upsert_databank(
            project_name,
            databank_name,
            capacity=capacity,
            default_view=default_view,
            auto_sync_policy=auto_sync_policy,
            created_at_utc=now,
        )
        logger.info(
            "databank_created",
            project=project_name,
            databank=databank_name,
            capacity=capacity,
        )
        return record

    @override
    def get_databank(
        self, project_name: str, databank_name: str
    ) -> DatabankRecord | None:
        """Get databank configuration by project and databank name.

        Args:
            project_name: Project name.
            databank_name: Databank name.

        Returns:
            DatabankRecord if found, None otherwise.
        """
        return self._manager.get_databank(project_name, databank_name)

    @override
    def list_databanks(self, project_name: str) -> list[DatabankRecord]:
        """List all databanks within a project.

        Args:
            project_name: Project name.

        Returns:
            List of DatabankRecord objects.
        """
        return self._manager.list_databanks(project_name)

    @override
    def delete_databank(self, project_name: str, databank_name: str) -> bool:
        """Delete a databank and all its memberships.

        Args:
            project_name: Project name.
            databank_name: Databank name.

        Returns:
            True if databank was deleted, False if it did not exist.
        """
        deleted = self._manager.delete_databank(project_name, databank_name)
        if deleted:
            logger.info(
                "databank_deleted",
                project=project_name,
                databank=databank_name,
            )
        return deleted

    @override
    def clear_databank(self, project_name: str, databank_name: str) -> int:
        """Clear all memberships from a databank without deleting the databank.

        Args:
            project_name: Project name.
            databank_name: Databank name.

        Returns:
            Number of cleared strategy members.

        Raises:
            DatabankNotFoundError: If databank does not exist.
        """
        if self.get_databank(project_name, databank_name) is None:
            msg = f"Databank {project_name}/{databank_name} not found"
            raise DatabankNotFoundError(msg)

        cleared_count = self._manager.clear_databank_members(
            project_name, databank_name
        )
        logger.info(
            "databank_cleared",
            project=project_name,
            databank=databank_name,
            cleared_count=cleared_count,
        )
        return cleared_count

    @override
    def evaluate_similarity(
        self,
        project_name: str,
        databank_name: str,
        candidate_metrics: Mapping[str, float],
        profile: SimilarityProfile,
    ) -> SimilarityMatchResult:
        """Check candidate strategy against databank members for metric similarity.

        Args:
            project_name: Project name.
            databank_name: Databank name.
            candidate_metrics: Dictionary of candidate performance metrics.
            profile: SimilarityProfile tolerance and comparison configuration.

        Returns:
            SimilarityMatchResult detailing match status and admission verdict.
        """
        members = self.get_members(project_name, databank_name)
        candidate_fitness = float(candidate_metrics.get("fitness", 0.0))

        if not members:
            return SimilarityMatchResult(
                is_similar=False,
                matched_artifact_id=None,
                candidate_fitness=candidate_fitness,
                matched_fitness=0.0,
                should_admit_candidate=True,
            )

        for member in members:
            if _check_metrics_similarity(candidate_metrics, member.metrics, profile):
                should_admit = candidate_fitness > member.fitness
                logger.info(
                    "strategy_similarity_detected",
                    matched_artifact=member.artifact_id,
                    cand_fitness=candidate_fitness,
                    mem_fitness=member.fitness,
                    should_admit=should_admit,
                )
                return SimilarityMatchResult(
                    is_similar=True,
                    matched_artifact_id=member.artifact_id,
                    candidate_fitness=candidate_fitness,
                    matched_fitness=member.fitness,
                    should_admit_candidate=should_admit,
                )

        return SimilarityMatchResult(
            is_similar=False,
            matched_artifact_id=None,
            candidate_fitness=candidate_fitness,
            matched_fitness=0.0,
            should_admit_candidate=True,
        )

    def _evaluate_similarity_gate(
        self,
        project_name: str,
        databank_name: str,
        *,
        artifact_id: str,
        fitness: float,
        metrics: Mapping[str, float],
        profile: SimilarityProfile,
    ) -> bool:
        """Evaluate similarity against existing members and return admission status."""
        metrics_with_fitness = dict(metrics)
        metrics_with_fitness["fitness"] = fitness
        sim_res = self.evaluate_similarity(
            project_name, databank_name, metrics_with_fitness, profile
        )
        if sim_res.is_similar:
            if not sim_res.should_admit_candidate:
                logger.info(
                    "candidate_strategy_dismissed_similar",
                    artifact_id=artifact_id,
                    matched=sim_res.matched_artifact_id,
                )
                return False
            if sim_res.matched_artifact_id:
                self.remove_member(
                    project_name, databank_name, sim_res.matched_artifact_id
                )
        return True

    def _ensure_capacity(
        self,
        project_name: str,
        databank_name: str,
        capacity: int,
        ranking_value: float,
    ) -> bool:
        """Evict lowest ranked member if at capacity; return True if candidate fits."""
        count = self._manager.count_databank_members(project_name, databank_name)
        if count < capacity:
            return True

        members = self.get_members(project_name, databank_name)
        if not members:
            return True

        lowest = members[-1]
        if ranking_value > lowest.ranking_value:
            self.remove_member(project_name, databank_name, lowest.artifact_id)
            logger.info(
                "member_evicted_capacity",
                evicted_artifact=lowest.artifact_id,
                evicted_rank=lowest.ranking_value,
                candidate_rank=ranking_value,
            )
            return True

        logger.info(
            "candidate_rejected_capacity",
            candidate_rank=ranking_value,
            lowest_rank=lowest.ranking_value,
        )
        return False

    @override
    def add_member(
        self,
        project_name: str,
        databank_name: str,
        artifact_id: str,
        *,
        fitness: float,
        ranking_value: float,
        metrics: Mapping[str, float],
        annotations: Mapping[str, Any] | None = None,
        similarity_profile: SimilarityProfile | None = None,
    ) -> DatabankMemberRecord | None:
        """Add member with capacity gating, ranking, and similarity evaluation.

        Args:
            project_name: Project name.
            databank_name: Databank name.
            artifact_id: ID of cataloged strategy artifact.
            fitness: Strategy fitness score.
            ranking_value: Normalized ranking score.
            metrics: Map of performance metrics.
            annotations: Optional user or system annotations.
            similarity_profile: Optional profile for similarity dismissal.

        Returns:
            Created DatabankMemberRecord, or None if candidate was dismissed.

        Raises:
            DatabankNotFoundError: If databank does not exist.
            ArtifactNotFoundError: If artifact does not exist in catalog.
            DuplicateMemberError: If artifact is already in this databank.
        """
        databank = self.get_databank(project_name, databank_name)
        if databank is None:
            msg = f"Databank {project_name}/{databank_name} not found"
            raise DatabankNotFoundError(msg)

        if self._artifact_store.get_artifact(artifact_id) is None:
            msg = f"Artifact {artifact_id} does not exist in artifact catalog"
            raise ArtifactNotFoundError(msg)

        # Check duplicate
        existing = self._manager.execute_query(
            "SELECT artifact_id FROM persistence_databank_members "
            "WHERE project_name = ? AND databank_name = ? AND artifact_id = ?;",
            (project_name, databank_name, artifact_id),
        )
        if existing:
            msg = (
                f"Artifact {artifact_id} is already a member of "
                f"{project_name}/{databank_name}"
            )
            raise DuplicateMemberError(msg)

        # Metric similarity evaluation
        if similarity_profile is not None:
            admitted = self._evaluate_similarity_gate(
                project_name,
                databank_name,
                artifact_id=artifact_id,
                fitness=fitness,
                metrics=metrics,
                profile=similarity_profile,
            )
            if not admitted:
                return None

        # Capacity gating and eviction
        if not self._ensure_capacity(
            project_name, databank_name, databank.capacity, ranking_value
        ):
            return None

        # Insert member
        record = self._manager.insert_member(
            project_name,
            databank_name,
            artifact_id,
            fitness=fitness,
            ranking_value=ranking_value,
            metrics=metrics,
            annotations=annotations or {},
            added_at_utc=datetime.now(UTC),
        )
        logger.info(
            "databank_member_added",
            project=project_name,
            databank=databank_name,
            artifact=artifact_id,
            ranking=ranking_value,
        )
        return record

    @override
    def remove_member(
        self, project_name: str, databank_name: str, artifact_id: str
    ) -> bool:
        """Remove a strategy member from a databank.

        Args:
            project_name: Project name.
            databank_name: Databank name.
            artifact_id: Strategy artifact ID to remove.

        Returns:
            True if removed, False if not found.
        """
        return self._manager.remove_member(project_name, databank_name, artifact_id)

    @override
    def copy_member(
        self,
        source_project: str,
        source_databank: str,
        *,
        target_project: str,
        target_databank: str,
        artifact_id: str,
    ) -> DatabankMemberRecord:
        """Copy a member to target databank without duplicating artifact content.

        Args:
            source_project: Source project.
            source_databank: Source databank.
            target_project: Target project.
            target_databank: Target databank.
            artifact_id: Strategy artifact ID.

        Returns:
            Created DatabankMemberRecord in target databank.

        Raises:
            DatabankNotFoundError: If source or target databank does not exist,
                or member is not found in source databank.
        """
        if self.get_databank(target_project, target_databank) is None:
            msg = f"Target databank {target_project}/{target_databank} not found"
            raise DatabankNotFoundError(msg)

        members = self.get_members(source_project, source_databank)
        source_member = next((m for m in members if m.artifact_id == artifact_id), None)
        if source_member is None:
            msg = (
                f"Member {artifact_id} not found in source databank "
                f"{source_project}/{source_databank}"
            )
            raise DatabankNotFoundError(msg)

        return self._manager.insert_member(
            target_project,
            target_databank,
            artifact_id,
            fitness=source_member.fitness,
            ranking_value=source_member.ranking_value,
            metrics=source_member.metrics,
            annotations=source_member.annotations,
            added_at_utc=datetime.now(UTC),
        )

    @override
    def move_member(
        self,
        source_project: str,
        source_databank: str,
        *,
        target_project: str,
        target_databank: str,
        artifact_id: str,
    ) -> DatabankMemberRecord:
        """Atomically move member from source to target databank.

        Args:
            source_project: Source project.
            source_databank: Source databank.
            target_project: Target project.
            target_databank: Target databank.
            artifact_id: Strategy artifact ID.

        Returns:
            Created DatabankMemberRecord in target databank.

        Raises:
            DatabankNotFoundError: If source or target databank does not exist,
                or member is not found in source databank.
            DuplicateMemberError: If member already exists in target databank.
        """
        return self._manager.move_member_between_databanks(
            source_project,
            source_databank,
            target_project,
            target_databank,
            artifact_id,
        )

    @override
    def get_members(
        self,
        project_name: str,
        databank_name: str,
        limit: int | None = None,
    ) -> list[DatabankMemberRecord]:
        """Return databank members ordered by ranking value descending.

        Args:
            project_name: Project name.
            databank_name: Databank name.
            limit: Optional maximum number of members to retrieve.

        Returns:
            List of DatabankMemberRecord objects.
        """
        return self._manager.get_databank_members(project_name, databank_name, limit)

    @override
    def save_view(self, view_config: DatabankViewConfig) -> None:
        """Save a databank column projection view.

        Args:
            view_config: DatabankViewConfig specifying columns and projection.
        """
        self._manager.upsert_view(view_config)
        logger.info("databank_view_saved", view_name=view_config.view_name)

    @override
    def get_view(self, view_name: str) -> DatabankViewConfig | None:
        """Retrieve a databank column view by name.

        Args:
            view_name: View name.

        Returns:
            DatabankViewConfig if found, None otherwise.
        """
        return self._manager.get_view(view_name)

    @override
    def list_views(self) -> list[DatabankViewConfig]:
        """List all saved databank views.

        Returns:
            List of all saved DatabankViewConfig objects.
        """
        return self._manager.list_views()


SPEC: FeatureSpec = FeatureSpec(
    name="persistence.databanks",
    provides=frozenset({DATABANK_STORE}),
    requires=frozenset({DATABASE_SERVICE, ARTIFACT_STORE}),
    optional=frozenset(),
    description=("Project databanks, ranking, similarity dismissal, and column views."),
)


class DatabankFeature:
    """Wire databank store service into kernel composition lifecycle."""

    def __init__(self, config: DatabankConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional databank configuration.
        """
        self._config = config or DatabankConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve dependencies and register databank service.

        Args:
            context: Kernel feature context.
        """
        db_service = context.require(DATABASE_SERVICE)
        artifact_store = context.require(ARTIFACT_STORE)
        service = DatabankServiceImpl(db_service, artifact_store, self._config)
        context.provide(DATABANK_STORE, service)
        logger.info("persistence_databanks_feature_started")


def feature() -> DatabankFeature:
    """Return a zero-argument factory instance of DatabankFeature."""
    return DatabankFeature()
