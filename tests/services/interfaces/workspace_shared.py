"""Shared fixture helpers for watchlist boundary tests."""

from __future__ import annotations

from app.contracts.interfaces.capabilities import OPERATE_WATCHLISTS_CAPABILITY
from app.contracts.workspace.capabilities import MANAGE_WATCHLISTS_CAPABILITY
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.operate_watchlists.config import OperateWatchlistsConfig
from app.services.interfaces.operate_watchlists.gateway import WatchlistGateway
from app.services.workspace.manage_watchlists.config import ManageWatchlistsConfig
from app.services.workspace.manage_watchlists.manage_watchlists import WatchlistService


async def mount_watchlist_stack() -> tuple[
    ServiceRegistry,
    FeatureScope,
    FeatureScope,
]:
    """Mount the store and gateway capabilities into one registry.

    Returns:
        Registry, store scope, and gateway scope for removal tests.
    """
    registry = ServiceRegistry()
    store = WatchlistService(ManageWatchlistsConfig())
    store_scope = FeatureScope(owner_id="FEAT-WS-MANAGE_WATCHLISTS")
    registry.register(
        MANAGE_WATCHLISTS_CAPABILITY,
        store,
        owner_id="FEAT-WS-MANAGE_WATCHLISTS",
        scope=store_scope,
    )
    gateway = WatchlistGateway(store, OperateWatchlistsConfig())
    gateway_scope = FeatureScope(owner_id="FEAT-IFACE-OPERATE_WATCHLISTS")
    registry.register(
        OPERATE_WATCHLISTS_CAPABILITY,
        gateway,
        owner_id="FEAT-IFACE-OPERATE_WATCHLISTS",
        scope=gateway_scope,
    )
    return registry, store_scope, gateway_scope
