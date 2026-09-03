"""Tests for Data Inspection, Export, and Retention configuration."""

import pytest
from app.services.data.data_inspection_retention.config import (
    DataInspectionRetentionConfig,
)


def test_config_defaults() -> None:
    """Verify valid default configuration."""
    cfg = DataInspectionRetentionConfig()
    assert cfg.default_preview_limit == 100
    assert cfg.max_preview_limit == 10_000
    assert cfg.default_quarantine_days == 30
    assert "CSV" in cfg.supported_export_formats


def test_config_invalid() -> None:
    """Verify validation of invalid bounds."""
    with pytest.raises(ValueError, match="default_preview_limit"):
        DataInspectionRetentionConfig(default_preview_limit=0)

    with pytest.raises(ValueError, match="max_preview_limit"):
        DataInspectionRetentionConfig(default_preview_limit=500, max_preview_limit=100)

    with pytest.raises(ValueError, match="default_quarantine_days"):
        DataInspectionRetentionConfig(default_quarantine_days=0)
