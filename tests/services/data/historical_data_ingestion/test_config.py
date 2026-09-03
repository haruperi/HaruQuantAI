"""Tests for Historical Data Ingestion configuration."""

from __future__ import annotations

from pathlib import Path

from app.services.data.historical_data_ingestion.config import (
    HistoricalDataIngestionConfig,
)


def test_config_defaults() -> None:
    """Test HistoricalDataIngestionConfig default field values."""
    cfg = HistoricalDataIngestionConfig()
    assert cfg.database_path is None
    assert cfg.auto_migrate is True


def test_config_custom_values(tmp_path: Path) -> None:
    """Test HistoricalDataIngestionConfig with custom parameters."""
    db_file = tmp_path / "custom_test.db"
    cfg = HistoricalDataIngestionConfig(
        database_path=db_file,
        auto_migrate=False,
    )
    assert cfg.database_path == db_file
    assert cfg.auto_migrate is False
