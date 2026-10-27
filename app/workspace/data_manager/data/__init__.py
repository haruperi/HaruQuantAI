"""Data Manager datasets catalog and overview metrics package.

Description:
    Provides high-level dataset metrics for the Data Manager workspace,
    reading saved datasets catalog entries from the authoritative SQLite database
    (datamgr_datasets table). Exposes saved datasets catalog and summaries.
"""

from __future__ import annotations

from app.workspace.data_manager.cli_formatters import (
    DataCLI,
    format_data_dashboard,
    format_dataset_table,
)

from ._cli import main
from ._helpers import (
    DATASETS_CATALOG_FR,
    OVERVIEW_FR,
    persistence,
)
from .feature import Data
from .http import register_data_routes

__all__ = [
    "DATASETS_CATALOG_FR",
    "OVERVIEW_FR",
    "Data",
    "DataCLI",
    "format_data_dashboard",
    "format_dataset_table",
    "main",
    "persistence",
    "register_data_routes",
]
