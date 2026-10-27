"""Data Manager datasets catalog and overview metrics package.

Description:
    Provides high-level dataset metrics, Parquet market storage,
    coverage analysis, and partition file recovery.
"""

from __future__ import annotations

from . import coverage, partition_files, storage
from ._cli import main
from ._helpers import (
    DATASETS_CATALOG_FR,
    OVERVIEW_FR,
    DataCLI,
    format_data_dashboard,
    format_dataset_table,
    persistence,
)
from .coverage import (
    RangeProgress,
    add_completed_range,
    missing_ranges,
    observation_coverage,
    record_checked_ranges,
)
from .feature import Data
from .http import register_data_routes
from .partition_files import (
    FilePublication,
    canonical_target,
    dataset_lock,
    recover_catalog_publications,
    recover_publications,
)
from .storage import (
    PART_ROWS,
    dataset_root,
    publish_frame,
    require_data,
)

__all__ = [
    "DATASETS_CATALOG_FR",
    "OVERVIEW_FR",
    "PART_ROWS",
    "Data",
    "DataCLI",
    "FilePublication",
    "RangeProgress",
    "add_completed_range",
    "canonical_target",
    "coverage",
    "dataset_lock",
    "dataset_root",
    "format_data_dashboard",
    "format_dataset_table",
    "main",
    "missing_ranges",
    "observation_coverage",
    "partition_files",
    "persistence",
    "publish_frame",
    "record_checked_ranges",
    "recover_catalog_publications",
    "recover_publications",
    "register_data_routes",
    "require_data",
    "storage",
]
