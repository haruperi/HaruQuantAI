"""Data Manager baskets (stock groups) catalog service package.

Description:
    Provides baskets (stock groups), constituent stock memberships, and
    market data synchronization for the Data Manager workspace, reading
    catalog entries from the authoritative SQLite database (datamgr_stock_group table).
"""

from __future__ import annotations

from app.workspace.data_manager.cli_formatters import (
    BasketsCLI,
    format_basket_table,
)

from ._cli import (
    register_basket_commands,
    run_basket_command,
)
from ._helpers import (
    BASKETS_CATALOG_FR,
    BasketInfo,
    BasketStockItem,
    BasketTargets,
    persistence,
)
from .feature import Baskets
from .http import register_basket_routes

__all__ = [
    "BASKETS_CATALOG_FR",
    "BasketInfo",
    "BasketStockItem",
    "BasketTargets",
    "Baskets",
    "BasketsCLI",
    "format_basket_table",
    "persistence",
    "register_basket_commands",
    "register_basket_routes",
    "run_basket_command",
]
