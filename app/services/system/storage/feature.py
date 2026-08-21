"""Feature lifecycle implementation for Persistent Storage."""

from typing import TYPE_CHECKING

from app.contracts.system.storage import SYSTEM_STORAGE
from app.services.system.storage.config import StorageConfig
from app.services.system.storage.engine import DiskStorageEngine
from app.services.system.storage.manifest import SPEC
from app.services.system.storage.sqlite_engine import SqliteStorageEngine

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class StorageFeature:
    """Provides durable persistent storage capability via SQLite or filesystem."""

    spec: FeatureSpec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the storage service into runtime.

        Args:
            context: Feature runtime context.
            config: Optional StorageConfig or dict.
        """
        cfg = (
            config
            if isinstance(config, StorageConfig)
            else StorageConfig.from_dict(config if isinstance(config, dict) else None)
        )

        if cfg.driver == "sqlite":
            sqlite_engine = SqliteStorageEngine(cfg.database_file)
            await sqlite_engine.initialize()
            context.provide(SYSTEM_STORAGE, sqlite_engine)
        else:
            disk_engine = DiskStorageEngine(cfg.root_directory)
            context.provide(SYSTEM_STORAGE, disk_engine)


def create_feature() -> StorageFeature:
    """Entry point factory for Persistent Storage feature.

    Returns:
        New StorageFeature instance.
    """
    return StorageFeature()
