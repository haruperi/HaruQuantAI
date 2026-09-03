"""Configuration models for Partitioned Parquet Market Data Store."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MarketDataStoreConfig:
    """Runtime configuration for Partitioned Parquet Market Data Store.

    Attributes:
        storage_root: Canonical root path for partitioned market data storage.
        compression: Parquet compression codec (default 'zstd').
        compression_level: Initial compression level for Zstandard (default 6).
        min_rows_per_group: Minimum rows per Parquet row group (default 100,000).
        max_rows_per_group: Maximum rows per Parquet row group (default 500,000).
        max_rows_per_file: Target maximum rows per part file (default 2,000,000).
        manifest_database_path: File path to DuckDB catalog; None uses in-memory.
        staging_dir_name: Name of transient staging directory for atomic promotion.
    """

    storage_root: Path = Path("data/market_data")
    compression: str = "zstd"
    compression_level: int = 6
    min_rows_per_group: int = 100_000
    max_rows_per_group: int = 500_000
    max_rows_per_file: int = 2_000_000
    manifest_database_path: str | Path | None = Path("data/market_data/catalog.duckdb")
    staging_dir_name: str = ".staging"
