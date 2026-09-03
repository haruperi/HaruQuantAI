"""Unit tests for Synthetic Scenario Series configuration."""

import pytest
from app.services.data.synthetic_scenario_series.config import (
    SyntheticScenarioSeriesConfig,
)


def test_default_config() -> None:
    """Test default configuration values."""
    cfg = SyntheticScenarioSeriesConfig()
    assert cfg.max_records == 250_000
    assert cfg.default_model == "gbm"
    assert cfg.default_rounding == "ROUND_HALF_EVEN"
    assert "SHOCK" in cfg.supported_transform_types
    assert "GAP" in cfg.supported_transform_types


def test_custom_config() -> None:
    """Test valid custom configuration."""
    cfg = SyntheticScenarioSeriesConfig(
        max_records=50_000,
        default_model="constant",
        default_rounding="ROUND_HALF_EVEN",
        supported_transform_types=frozenset({"SHOCK", "GAP"}),
    )
    assert cfg.max_records == 50_000
    assert cfg.default_model == "constant"
    assert cfg.supported_transform_types == frozenset({"SHOCK", "GAP"})


def test_invalid_max_records() -> None:
    """Test rejection of non-positive max_records."""
    with pytest.raises(ValueError, match="max_records must be a positive integer"):
        SyntheticScenarioSeriesConfig(max_records=0)


def test_invalid_default_model() -> None:
    """Test rejection of unsupported default model."""
    with pytest.raises(ValueError, match="default_model must be one of"):
        SyntheticScenarioSeriesConfig(default_model="unsupported_model")


def test_invalid_supported_transforms() -> None:
    """Test rejection of invalid transform kinds."""
    with pytest.raises(
        ValueError, match="supported_transform_types contains invalid transforms"
    ):
        SyntheticScenarioSeriesConfig(
            supported_transform_types=frozenset({"INVALID_KIND"})
        )
