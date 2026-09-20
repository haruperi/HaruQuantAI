"""Explicit feature registry and profile mappings.

This module serves as the application's declarative feature factory registry.
Adding or removing a domain feature from the runtime is accomplished by adding
or removing its factory callable in `FEATURES`.

Key Design Principles:
- Pure Declarations: Importing this module executes no business logic, opens no
  database connections, and performs no I/O.
- Deterministic Composition: All feature factories are explicitly enumerated in
  `FEATURES`. The runtime performs topological dependency sorting over this
  collection to determine valid startup order.
- Role Profiles: The `PROFILES` mapping enables named deployment roles (e.g.,
  'api', 'worker', 'all') that activate predefined subsets of features.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.kernel.bootstrapper import FeatureFactory
from app.services.brokers.catalog import feature as brokers_catalog
from app.services.brokers.crypto import feature as brokers_crypto
from app.services.brokers.ctrader import feature as brokers_ctrader
from app.services.brokers.darwinex import feature as brokers_darwinex
from app.services.brokers.dukascopy import feature as brokers_dukascopy
from app.services.brokers.equity import feature as brokers_equity
from app.services.brokers.futures import feature as brokers_futures
from app.services.brokers.isolation_fencing import feature as brokers_fencing
from app.services.brokers.mt5 import feature as brokers_mt5
from app.services.brokers.reconciliation import feature as brokers_reconciliation
from app.services.brokers.yahoo import feature as brokers_yahoo
from app.services.gateway.api_server import feature as gateway_api_server
from app.services.persistence.artifacts import feature as persistence_artifacts
from app.services.persistence.brokers import feature as persistence_brokers
from app.services.persistence.databanks import feature as persistence_databanks
from app.services.persistence.database import feature as persistence_database
from app.services.persistence.migrations import feature as persistence_migrations
from app.services.persistence.parquet_store import feature as persistence_parquet
from app.services.persistence.retention import feature as persistence_retention
from app.services.persistence.snapshots import feature as persistence_snapshots
from app.services.persistence.workspace import feature as persistence_workspace
from app.services.workspace.diagnostics import feature as workspace_diagnostics
from app.services.workspace.jobs import feature as workspace_jobs
from app.services.workspace.notifications import feature as workspace_notifications
from app.services.workspace.plugin_host import feature as workspace_plugins
from app.services.workspace.remote_workers import feature as workspace_workers
from app.services.workspace.resource_governor import feature as workspace_resources
from app.services.workspace.scheduler import feature as workspace_scheduler
from app.services.workspace.settings import feature as workspace_settings

# Enumerate all domain feature factory callables here.
# Features will be topologically sorted by Runtime before startup.
FEATURES: tuple[FeatureFactory, ...] = (
    gateway_api_server,
    persistence_database,
    persistence_workspace,
    persistence_migrations,
    persistence_snapshots,
    persistence_artifacts,
    persistence_retention,
    persistence_databanks,
    persistence_parquet,
    persistence_brokers,
    brokers_catalog,
    brokers_mt5,
    brokers_ctrader,
    brokers_dukascopy,
    brokers_equity,
    brokers_futures,
    brokers_darwinex,
    brokers_crypto,
    brokers_yahoo,
    brokers_reconciliation,
    brokers_fencing,
    workspace_settings,
    workspace_notifications,
    workspace_diagnostics,
    workspace_resources,
    workspace_plugins,
    workspace_jobs,
    workspace_scheduler,
    workspace_workers,
)

# Named deployment profiles mapping a profile name to its active feature set.
PROFILES: Mapping[str, frozenset[str]] = {
    "all": frozenset(
        {
            "gateway.api_server",
            "persistence.workspace",
            "persistence.database",
            "persistence.migrations",
            "persistence.snapshots",
            "persistence.artifacts",
            "persistence.retention",
            "persistence.databanks",
            "persistence.parquet",
            "persistence.brokers",
            "brokers.catalog",
            "brokers.mt5",
            "brokers.ctrader",
            "brokers.dukascopy",
            "brokers.equity",
            "brokers.futures",
            "brokers.darwinex",
            "brokers.crypto",
            "brokers.yahoo",
            "brokers.reconciliation",
            "brokers.fencing",
            "workspace.settings",
            "workspace.notifications",
            "workspace.diagnostics",
            "workspace.resources",
            "workspace.plugins",
            "workspace.jobs",
            "workspace.scheduler",
            "workspace.workers",
        }
    ),
    "api": frozenset({"gateway.api_server"}),
    "persistence": frozenset(
        {
            "persistence.database",
            "persistence.migrations",
            "persistence.snapshots",
            "persistence.artifacts",
            "persistence.retention",
            "persistence.databanks",
            "persistence.parquet",
            "persistence.brokers",
        }
    ),
    "brokers": frozenset(
        {
            "persistence.database",
            "persistence.brokers",
            "brokers.catalog",
            "brokers.mt5",
            "brokers.ctrader",
            "brokers.dukascopy",
            "brokers.equity",
            "brokers.futures",
            "brokers.darwinex",
            "brokers.crypto",
            "brokers.yahoo",
            "brokers.reconciliation",
            "brokers.fencing",
        }
    ),
    "workspace": frozenset(
        {
            "persistence.workspace",
            "workspace.settings",
            "workspace.notifications",
            "workspace.diagnostics",
            "workspace.resources",
            "workspace.plugins",
            "workspace.jobs",
            "workspace.scheduler",
            "workspace.workers",
        }
    ),
    "default": frozenset(),
}


def available_profiles() -> tuple[str, ...]:
    """Return an alphabetically sorted tuple of all configured profile names.

    Returns:
        Sorted tuple of profile name strings.
    """
    return tuple(sorted(PROFILES.keys()))


def get_features(
    profile: str | None = None,
    enabled: Sequence[str] | None = None,
) -> tuple[tuple[FeatureFactory, ...], frozenset[str] | None]:
    """Resolve active feature factories and optional enabled name filter.

    Args:
        profile: Named role profile mapping to a predefined set of feature names.
        enabled: Explicit feature names to activate.

    Returns:
        A tuple of (factories, enabled_names_or_none).

    Raises:
        ValueError: If both profile and enabled are specified simultaneously,
            or if the requested profile name is not found in `PROFILES`.

    Example:
        >>> factories, enabled = get_features(profile="default")
        >>> factories, enabled = get_features(enabled=["auth", "database"])
    """
    if profile is not None and enabled is not None:
        raise ValueError("Cannot specify both profile and explicit enabled names")
    if profile is not None:
        if profile not in PROFILES:
            valid = ", ".join(available_profiles())
            raise ValueError(f"Unknown profile {profile!r}; valid profiles: {valid}")
        return FEATURES, PROFILES[profile]
    if enabled is not None:
        return FEATURES, frozenset(enabled)
    return FEATURES, None


__all__ = ("FEATURES", "PROFILES", "available_profiles", "get_features")
