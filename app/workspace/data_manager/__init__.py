"""Data Manager workspace package facade."""

from __future__ import annotations

from .home import Home, HomeCLI
from .routes import AppDataManager, create_data_manager_router

__all__ = [
    "AppDataManager",
    "Home",
    "HomeCLI",
    "create_data_manager_router",
]
