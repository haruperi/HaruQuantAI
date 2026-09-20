"""Broker profile catalog and symbol postfix translation service.

Feature:
    FEAT-BROKERS-CATALOG

Purpose:
    Provides broker profile discovery, system broker querying, server timezone
    resolution, and reversible symbol postfix translation matching StrategyQuant X
    BrokerManager architecture.

Invariants:
    * Reversible symbol translation: symbol + postfix <-> canonical symbol
      (FR-BROKERS-SYMBOL_TRANSLATION).
    * System broker profiles cannot be deleted.
    * Server timezones (e.g. EET, EETUS) are explicitly preserved
      (FR-BROKERS-SERVER_TIMEZONE).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from app.contracts.brokers import (
    BROKER_CATALOG,
    BROKER_PERSISTENCE,
    BrokerPersistenceService,
    BrokerProfile,
)
from app.contracts.brokers import (
    BrokerCatalogService as IBrokerCatalogService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(slots=True)
class BrokerCatalogConfig:
    """Slotted immutable configuration for the broker catalog feature."""

    schema_version: int = 1
    default_timezone: str = "UTC"


class BrokerCatalog(IBrokerCatalogService):
    """Implementation of the broker catalog and symbol translation service."""

    def __init__(
        self,
        persistence: BrokerPersistenceService,
        config: BrokerCatalogConfig | None = None,
    ) -> None:
        self._persistence = persistence
        self._config = config or BrokerCatalogConfig()
        self._cache: dict[int, BrokerProfile] = {}

    async def _refresh_cache(self) -> None:
        profiles = await self._persistence.list_profiles()
        self._cache = {p.id: p for p in profiles}

    async def initialize_cache(self) -> None:
        """Populate initial cache from persistence store."""
        await self._refresh_cache()

    @override
    async def get_profiles(self) -> list[BrokerProfile]:
        profiles = await self._persistence.list_profiles()
        self._cache = {p.id: p for p in profiles}
        return profiles

    @override
    async def get_profile(self, broker_id: int) -> BrokerProfile | None:
        if broker_id in self._cache:
            return self._cache[broker_id]
        profile = await self._persistence.get_profile(broker_id)
        if profile:
            self._cache[profile.id] = profile
        return profile

    @override
    async def get_profile_by_name(self, name: str) -> BrokerProfile | None:
        for p in self._cache.values():
            if p.name.lower() == name.lower():
                return p
        profile = await self._persistence.get_profile_by_name(name)
        if profile:
            self._cache[profile.id] = profile
        return profile

    @override
    async def create_profile(self, profile: BrokerProfile) -> BrokerProfile:
        saved = await self._persistence.save_profile(profile)
        self._cache[saved.id] = saved
        logger.info("broker_profile_created", broker_id=saved.id, name=saved.name)
        return saved

    @override
    async def delete_profile(self, broker_id: int) -> bool:
        profile = await self.get_profile(broker_id)
        if profile is None:
            return False
        if profile.is_system:
            logger.warning(
                "rejection_delete_system_broker",
                broker_id=broker_id,
                name=profile.name,
            )
            return False
        deleted = await self._persistence.delete_profile(broker_id)
        if deleted:
            self._cache.pop(broker_id, None)
            logger.info("broker_profile_deleted", broker_id=broker_id)
        return deleted

    @override
    def resolve_broker_symbol(self, symbol: str, broker_id: int) -> str:
        """Apply broker postfix to canonical symbol (e.g. EURUSD -> EURUSD_roboforex).

        Args:
            symbol: Canonical market symbol.
            broker_id: Integer identifier of the target broker profile.

        Returns:
            Broker-specific symbol with postfix applied if defined.
        """
        profile = self._cache.get(broker_id)
        if not profile or not profile.postfix:
            return symbol
        if symbol.endswith(profile.postfix):
            return symbol
        return f"{symbol}{profile.postfix}"

    @override
    def strip_broker_postfix(self, broker_symbol: str, broker_id: int) -> str:
        """Strip broker postfix to retrieve canonical symbol.

        Args:
            broker_symbol: Broker-specific symbol string.
            broker_id: Integer identifier of the target broker profile.

        Returns:
            Canonical symbol without postfix.
        """
        profile = self._cache.get(broker_id)
        if not profile or not profile.postfix:
            return broker_symbol
        if broker_symbol.endswith(profile.postfix):
            return broker_symbol[: -len(profile.postfix)]
        return broker_symbol

    @override
    def get_broker_timezone(self, broker_id: int) -> str:
        """Return the declared server timezone for the broker."""
        profile = self._cache.get(broker_id)
        if profile and profile.server_timezone:
            return profile.server_timezone
        return self._config.default_timezone


SPEC: FeatureSpec = FeatureSpec(
    name="brokers.catalog",
    provides=frozenset({BROKER_CATALOG}),
    requires=frozenset({BROKER_PERSISTENCE}),
    optional=frozenset(),
    description="Provider profiles, capability discovery, postfix/timezone mapping",
)


class BrokerCatalogFeature:
    """Wire BrokerCatalog into the application runtime lifecycle."""

    def __init__(self, config: BrokerCatalogConfig | None = None) -> None:
        self._config = config or BrokerCatalogConfig()
        self._service: BrokerCatalog | None = None

    @property
    def spec(self) -> FeatureSpec:
        """Return the feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the feature and provide BrokerCatalog capability."""
        persistence = context.require(BROKER_PERSISTENCE)
        self._service = BrokerCatalog(persistence, self._config)
        await self._service.initialize_cache()
        context.provide(BROKER_CATALOG, self._service)
        logger.info("brokers_catalog_feature_started")

    async def stop(self, _context: FeatureContext) -> None:
        """Stop the feature and release resources."""
        self._service = None
        logger.info("brokers_catalog_feature_stopped")


def feature(config: BrokerCatalogConfig | None = None) -> BrokerCatalogFeature:
    """Return a zero-argument factory instance of BrokerCatalogFeature."""
    return BrokerCatalogFeature(config)
