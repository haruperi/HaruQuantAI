"""Watchlists-owned immutable schema definitions."""

from app.services.api.widgets.watchlists.migrations.definitions import (
    get_watchlist_migration_steps,
)

__all__ = ("get_watchlist_migration_steps",)
