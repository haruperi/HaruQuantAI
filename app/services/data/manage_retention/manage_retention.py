"""Reachability-safe Data retention for ``FEAT-DATA-MANAGE_RETENTION``.

Policy is durable and independent of the immutable-series implementation. Physical
series deletion is delegated through a narrow owner-provided capability, so this
feature never imports a sibling implementation or reads another feature's tables.
Pinned versions are structurally excluded by the series owner.
"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING

from app.contracts.common.models import ProblemDetails, UtcTimestamp, Uuid7
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import ManageRetentionRequest, ManageRetentionSuccess
from app.kernel.time import format_utc_timestamp, utc_now
from app.services.data.manage_retention.config import ManageRetentionConfig
from app.services.data.manage_retention.policy_store import RetentionPolicyStore

if TYPE_CHECKING:
    from app.contracts.data.internal import DataSeriesRetentionCollectorCapability


def _failure(request_id: str, detail: str) -> DataFailure:
    """Build a deterministic retention-management failure.

    Args:
        request_id: Public request identity.
        detail: Safe human-readable failure detail.

    Returns:
        Contract-native Data failure.
    """
    return DataFailure(
        request_id=request_id,
        code="DATA_NOT_FOUND",
        problem=ProblemDetails(
            status=404,
            code="DATA_NOT_FOUND",
            detail=detail,
            request_id=request_id,
        ),
    )


class ManageRetentionService:
    """Capability implementation for durable policy and bounded collection."""

    def __init__(
        self,
        config: ManageRetentionConfig,
        store: RetentionPolicyStore,
        collector: DataSeriesRetentionCollectorCapability,
    ) -> None:
        """Initialize retention policy and physical collection collaborators.

        Args:
            config: Trusted feature configuration.
            store: Feature-owned durable policy store.
            collector: Owner-provided physical series collection capability.
        """
        self._config = config
        self._store = store
        self._collector = collector

    async def manage_retention(
        self,
        request: ManageRetentionRequest,
    ) -> ManageRetentionSuccess | DataFailure:
        """Define policy or collect unreachable Data series after quarantine.

        Args:
            request: Operation-discriminated retention request.

        Returns:
            Contract-native success or deterministic failure.
        """
        if request.operation == "DEFINE_POLICY":
            assert request.policy is not None
            await self._store.define(request.policy)
            return ManageRetentionSuccess(
                request_id=request.request_id,
                policy=request.policy,
            )

        policy = await self._store.latest()
        if policy is None:
            return _failure(
                request.request_id,
                "Retention collection requires a previously defined policy",
            )
        retained_days = policy.retention_days or 0
        age_days = retained_days + policy.quarantine_days
        cutoff = format_utc_timestamp(utc_now() - timedelta(days=age_days))
        collected = await self._collector.collect_unpinned_before(
            created_before=cutoff,
            limit=self._config.collection_limit,
        )
        return ManageRetentionSuccess(
            request_id=request.request_id,
            policy=policy,
            collected_count=len(collected),
        )


async def _demo() -> None:
    """Demonstrate durable retention-policy definition without collecting data."""
    import tempfile
    from pathlib import Path

    from app.contracts.data.models import RetentionPolicy
    from app.kernel.identity import generate_uuid7

    class _NoopCollector:
        async def collect_unpinned_before(
            self,
            *,
            created_before: UtcTimestamp,
            limit: int,
        ) -> tuple[Uuid7, ...]:
            """Return no collected versions for the standalone demonstration."""
            del created_before, limit
            return ()

    with tempfile.TemporaryDirectory() as temporary_directory:
        config = ManageRetentionConfig(
            database_path=Path(temporary_directory) / "retention.sqlite3"
        )
        service = ManageRetentionService(
            config,
            RetentionPolicyStore(config.database_path),
            _NoopCollector(),
        )
        result = await service.manage_retention(
            ManageRetentionRequest(
                request_id=generate_uuid7(),
                capability_snapshot_id=generate_uuid7(),
                operation="DEFINE_POLICY",
                policy=RetentionPolicy(
                    policy_id=generate_uuid7(),
                    retention_days=30,
                    quarantine_days=7,
                ),
            )
        )
        print(result.model_dump(mode="json"))


if __name__ == "__main__":
    asyncio.run(_demo())
