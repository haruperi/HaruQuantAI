"""Behavior tests for FEAT-DATA-MANAGE_RETENTION."""

from pathlib import Path

import pytest

from app.contracts.data.models import ManageRetentionRequest, RetentionPolicy
from app.kernel.identity import generate_uuid7
from app.services.data.manage_retention.config import ManageRetentionConfig
from app.services.data.manage_retention.manage_retention import ManageRetentionService
from app.services.data.manage_retention.policy_store import RetentionPolicyStore


class _Collector:
    def __init__(self) -> None:
        self.limit: int | None = None

    async def collect_unpinned_before(
        self,
        *,
        created_before: str,
        limit: int,
    ) -> tuple[str, ...]:
        assert created_before.endswith("Z")
        self.limit = limit
        return (generate_uuid7(), generate_uuid7())


@pytest.mark.asyncio
async def test_collection_requires_defined_policy(tmp_path: Path) -> None:
    config = ManageRetentionConfig(database_path=tmp_path / "retention.sqlite3")
    service = ManageRetentionService(
        config,
        RetentionPolicyStore(config.database_path),
        _Collector(),  # type: ignore[arg-type]
    )

    result = await service.manage_retention(
        ManageRetentionRequest(
            request_id=generate_uuid7(),
            capability_snapshot_id=generate_uuid7(),
            operation="COLLECT",
        )
    )

    assert result.outcome == "FAILURE"
    assert result.code == "DATA_NOT_FOUND"


@pytest.mark.asyncio
async def test_collection_is_bounded_by_feature_configuration(tmp_path: Path) -> None:
    collector = _Collector()
    config = ManageRetentionConfig(
        database_path=tmp_path / "retention.sqlite3",
        collection_limit=7,
    )
    service = ManageRetentionService(
        config,
        RetentionPolicyStore(config.database_path),
        collector,  # type: ignore[arg-type]
    )
    policy = RetentionPolicy(
        policy_id=generate_uuid7(),
        retention_days=30,
        quarantine_days=5,
    )
    await service.manage_retention(
        ManageRetentionRequest(
            request_id=generate_uuid7(),
            capability_snapshot_id=generate_uuid7(),
            operation="DEFINE_POLICY",
            policy=policy,
        )
    )

    result = await service.manage_retention(
        ManageRetentionRequest(
            request_id=generate_uuid7(),
            capability_snapshot_id=generate_uuid7(),
            operation="COLLECT",
        )
    )

    assert result.outcome == "SUCCESS"
    assert result.collected_count == 2
    assert collector.limit == 7
