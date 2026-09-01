"""Lifecycle adapter for Data retention management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import MANAGE_RETENTION_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_RETENTION_COLLECTOR_CAPABILITY
from app.services.data.manage_retention.config import ManageRetentionConfig
from app.services.data.manage_retention.manage_retention import ManageRetentionService
from app.services.data.manage_retention.manifest import SPEC
from app.services.data.manage_retention.policy_store import RetentionPolicyStore

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class ManageRetentionFeature:
    """Composable Data retention-management feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve physical collection, construct policy storage, and publish."""
        if isinstance(config, ManageRetentionConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = ManageRetentionConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or ManageRetentionConfig")
        collector = context.require(DATA_SERIES_RETENTION_COLLECTOR_CAPABILITY)
        service = ManageRetentionService(
            parsed,
            RetentionPolicyStore(parsed.database_path),
            collector,
        )
        context.provide(MANAGE_RETENTION_CAPABILITY, service)


def create_feature() -> ManageRetentionFeature:
    """Create a fresh retention-management feature."""
    return ManageRetentionFeature()
