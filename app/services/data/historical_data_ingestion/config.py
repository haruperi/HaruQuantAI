"""Configuration models for Historical Data Ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HistoricalDataIngestionConfig:
    """Runtime configuration for Historical Data Ingestion service.

    Attributes:
        database_path: Optional SQLite database path for persistent storage;
            defaults to in-memory SQLite.
        auto_migrate: Automatically run database migrations on initialization.
    """

    database_path: str | Path | None = None
    auto_migrate: bool = True
