"""Shared fixture helpers for workspace-backed boundary tests."""

from __future__ import annotations

from pathlib import Path

from app.contracts.interfaces.capabilities import (
    OPERATE_IDENTITY_CAPABILITY,
    OPERATE_SETTINGS_CAPABILITY,
    OPERATE_WATCHLISTS_CAPABILITY,
)
from app.contracts.workspace.capabilities import (
    ADMINISTER_SETTINGS_CAPABILITY,
    MANAGE_ACCOUNTS_CAPABILITY,
    MANAGE_WATCHLISTS_CAPABILITY,
)
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.interfaces.operate_identity.config import OperateIdentityConfig
from app.services.interfaces.operate_identity.gateway import IdentityGateway
from app.services.interfaces.operate_settings.config import OperateSettingsConfig
from app.services.interfaces.operate_settings.gateway import SettingsGateway
from app.services.interfaces.operate_watchlists.config import OperateWatchlistsConfig
from app.services.interfaces.operate_watchlists.gateway import WatchlistGateway
from app.services.workspace.administer_settings.administer_settings import (
    SettingsService,
)
from app.services.workspace.administer_settings.config import AdministerSettingsConfig
from app.services.workspace.manage_accounts.accounts import AccountService
from app.services.workspace.manage_accounts.config import ManageAccountsConfig
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


async def mount_identity_stack(
    db_path: Path | str | None = None,
) -> tuple[
    ServiceRegistry,
    FeatureScope,
    FeatureScope,
]:
    """Mount the account store and identity gateway capabilities into one registry.

    Returns:
        Registry, store scope, and gateway scope.
    """
    registry = ServiceRegistry()
    config = (
        ManageAccountsConfig(database_path=db_path)
        if db_path is not None
        else ManageAccountsConfig()
    )
    store = AccountService(config)
    store_scope = FeatureScope(owner_id="FEAT-WS-MANAGE_ACCOUNTS")
    registry.register(
        MANAGE_ACCOUNTS_CAPABILITY,
        store,
        owner_id="FEAT-WS-MANAGE_ACCOUNTS",
        scope=store_scope,
    )
    gateway = IdentityGateway(store, OperateIdentityConfig())
    gateway_scope = FeatureScope(owner_id="FEAT-IFACE-OPERATE_IDENTITY")
    registry.register(
        OPERATE_IDENTITY_CAPABILITY,
        gateway,
        owner_id="FEAT-IFACE-OPERATE_IDENTITY",
        scope=gateway_scope,
    )
    return registry, store_scope, gateway_scope


def init_settings_db(db_path: Path | str) -> None:
    """Ensure settings and settings_history tables exist in the target database."""
    import sqlite3

    target = Path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                value_type TEXT NOT NULL DEFAULT 'string',
                category TEXT NOT NULL DEFAULT 'general',
                label TEXT NOT NULL DEFAULT '',
                description TEXT,
                is_secret INTEGER NOT NULL DEFAULT 0,
                is_readonly INTEGER NOT NULL DEFAULT 0,
                default_value TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT NOT NULL,
                changed_by TEXT NOT NULL DEFAULT 'system',
                changed_at TEXT NOT NULL
            );
            """
        )
    conn.close()


async def mount_settings_stack(
    db_path: Path | str | None = None,
) -> tuple[
    ServiceRegistry,
    FeatureScope,
    FeatureScope,
]:
    """Mount the settings store and settings gateway capabilities into one registry.

    Returns:
        Registry, store scope, and gateway scope.
    """
    registry = ServiceRegistry()
    if db_path is not None:
        init_settings_db(db_path)
    config = (
        AdministerSettingsConfig(database_path=db_path)
        if db_path is not None
        else AdministerSettingsConfig()
    )
    store = SettingsService(config)
    store_scope = FeatureScope(owner_id="FEAT-WS-ADMINISTER_SETTINGS")
    registry.register(
        ADMINISTER_SETTINGS_CAPABILITY,
        store,
        owner_id="FEAT-WS-ADMINISTER_SETTINGS",
        scope=store_scope,
    )
    gateway = SettingsGateway(store, OperateSettingsConfig())
    gateway_scope = FeatureScope(owner_id="FEAT-IFACE-OPERATE_SETTINGS")
    registry.register(
        OPERATE_SETTINGS_CAPABILITY,
        gateway,
        owner_id="FEAT-IFACE-OPERATE_SETTINGS",
        scope=gateway_scope,
    )
    return registry, store_scope, gateway_scope


async def mount_trading_stack(
    db_path: Path | str | None = None,
) -> tuple[
    ServiceRegistry,
    FeatureScope,
    FeatureScope,
]:
    """Mount the execution sessions store and trading gateway capabilities into one registry.

    Returns:
        Registry, store scope, and gateway scope.
    """
    from app.contracts.interfaces.capabilities import OPERATE_TRADING_CAPABILITY
    from app.contracts.trading.capabilities import (
        MANAGE_EXECUTION_SESSIONS_CAPABILITY,
    )
    from app.services.interfaces.operate_trading.config import (
        OperateTradingConfig,
    )
    from app.services.interfaces.operate_trading.gateway import TradingGateway
    from app.services.trading.manage_execution_sessions.config import (
        ManageExecutionSessionsConfig,
    )
    from app.services.trading.manage_execution_sessions.execution_sessions import (
        ExecutionSessionsService,
    )

    registry = ServiceRegistry()
    config = (
        ManageExecutionSessionsConfig(database_path=db_path)
        if db_path is not None
        else ManageExecutionSessionsConfig()
    )
    store = ExecutionSessionsService(config)
    store_scope = FeatureScope(owner_id="FEAT-TRD-MANAGE_EXECUTION_SESSIONS")
    registry.register(
        MANAGE_EXECUTION_SESSIONS_CAPABILITY,
        store,
        owner_id="FEAT-TRD-MANAGE_EXECUTION_SESSIONS",
        scope=store_scope,
    )
    gateway = TradingGateway(
        config=OperateTradingConfig(),
        execution_sessions=store,
    )
    gateway_scope = FeatureScope(owner_id="FEAT-IFACE-OPERATE_TRADING")
    registry.register(
        OPERATE_TRADING_CAPABILITY,
        gateway,
        owner_id="FEAT-IFACE-OPERATE_TRADING",
        scope=gateway_scope,
    )
    return registry, store_scope, gateway_scope
