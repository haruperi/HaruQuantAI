"""Feature lifecycle mount implementation for Partitioned Parquet Market Data Store."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from app.contracts.data.capabilities import MARKET_DATA_STORE_CAPABILITY
from app.services.data.market_data_store.config import MarketDataStoreConfig
from app.services.data.market_data_store.manifest import SPEC
from app.services.data.market_data_store.market_data_store import MarketDataStoreService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class MarketDataStoreFeature:
    """Feature package providing Partitioned Parquet Market Data Store."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: MarketDataStoreService | None = None

    @property
    def service(self) -> MarketDataStoreService | None:
        """Return the underlying market data store service instance."""
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the market data store capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or MarketDataStoreConfig object.
        """
        cfg = MarketDataStoreConfig()
        if isinstance(config, dict):
            raw_root = config.get("storage_root", "data/market_data")
            raw_manifest = config.get(
                "manifest_database_path", "data/market_data/catalog.duckdb"
            )
            cfg = MarketDataStoreConfig(
                storage_root=Path(raw_root),
                compression=config.get("compression", "zstd"),
                compression_level=int(config.get("compression_level", 6)),
                min_rows_per_group=int(config.get("min_rows_per_group", 100_000)),
                max_rows_per_group=int(config.get("max_rows_per_group", 500_000)),
                max_rows_per_file=int(config.get("max_rows_per_file", 2_000_000)),
                manifest_database_path=Path(raw_manifest) if raw_manifest else None,
                staging_dir_name=config.get("staging_dir_name", ".staging"),
            )
        elif isinstance(config, MarketDataStoreConfig):
            cfg = config

        self._service = MarketDataStoreService(config=cfg)
        context.provide(MARKET_DATA_STORE_CAPABILITY, self._service)

    async def unmount(self, _context: FeatureContext) -> None:
        """Unmount the feature and release catalog connections."""
        if self._service is not None:
            self._service.close()
            self._service = None


def feature() -> MarketDataStoreFeature:
    """Factory function for discovery via entry points.

    Returns:
        New MarketDataStoreFeature instance.
    """
    return MarketDataStoreFeature()
