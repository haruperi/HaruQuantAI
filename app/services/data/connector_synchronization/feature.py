"""Feature lifecycle mount implementation for Connector Synchronization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import SYNC_CONNECTORS_CAPABILITY
from app.services.data.connector_synchronization.config import ConnectorSyncConfig
from app.services.data.connector_synchronization.connector_synchronization import (
    SyncConnectorsService,
)
from app.services.data.connector_synchronization.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ConnectorSynchronizationFeature:
    """Composable feature package providing Connector Synchronization."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: SyncConnectorsService | None = None

    @property
    def service(self) -> SyncConnectorsService | None:
        """Return the underlying connector synchronization service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the sync connectors capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or ConnectorSyncConfig instance.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = ConnectorSyncConfig()
        if isinstance(config, dict):
            overlap = config.get(
                "default_overlap_window_seconds", cfg.default_overlap_window_seconds
            )
            if not isinstance(overlap, int):
                msg = "default_overlap_window_seconds must be an integer"
                raise TypeError(msg)

            dedup = config.get(
                "default_deduplication_policy", cfg.default_deduplication_policy
            )
            if not isinstance(dedup, str):
                msg = "default_deduplication_policy must be a string"
                raise TypeError(msg)

            rev_pol = config.get("default_revision_policy", cfg.default_revision_policy)
            if not isinstance(rev_pol, str):
                msg = "default_revision_policy must be a string"
                raise TypeError(msg)

            max_recs = config.get("max_records_per_page", cfg.max_records_per_page)
            if not isinstance(max_recs, int):
                msg = "max_records_per_page must be an integer"
                raise TypeError(msg)

            max_rate = config.get(
                "max_rate_limit_per_window", cfg.max_rate_limit_per_window
            )
            if not isinstance(max_rate, int):
                msg = "max_rate_limit_per_window must be an integer"
                raise TypeError(msg)

            rate_win = config.get(
                "rate_limit_window_seconds", cfg.rate_limit_window_seconds
            )
            if not isinstance(rate_win, int):
                msg = "rate_limit_window_seconds must be an integer"
                raise TypeError(msg)

            strict_sec = config.get(
                "strict_secret_isolation", cfg.strict_secret_isolation
            )
            if not isinstance(strict_sec, bool):
                msg = "strict_secret_isolation must be a boolean"
                raise TypeError(msg)

            cfg = ConnectorSyncConfig(
                default_overlap_window_seconds=overlap,
                default_deduplication_policy=dedup,  # type: ignore[arg-type]
                default_revision_policy=rev_pol,  # type: ignore[arg-type]
                max_records_per_page=max_recs,
                max_rate_limit_per_window=max_rate,
                rate_limit_window_seconds=rate_win,
                strict_secret_isolation=strict_sec,
            )
        elif isinstance(config, ConnectorSyncConfig):
            cfg = config

        self._service = SyncConnectorsService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(SYNC_CONNECTORS_CAPABILITY, self._service)


def feature() -> ConnectorSynchronizationFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ConnectorSynchronizationFeature instance.
    """
    return ConnectorSynchronizationFeature()
