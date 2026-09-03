"""Unit tests for Run Data Binding configuration."""

import pytest
from app.services.data.run_data_binding.config import RunDataBindingConfig


def test_config_defaults() -> None:
    """Verify default configuration settings."""
    cfg = RunDataBindingConfig()
    assert cfg.strict_precision_check is True
    assert cfg.allow_synthetic_sources is True
    assert cfg.require_committed_status is True
    assert len(cfg.supported_precisions) == 4


def test_config_custom_values() -> None:
    """Verify custom configuration values."""
    cfg = RunDataBindingConfig(
        strict_precision_check=False,
        allow_synthetic_sources=False,
        require_committed_status=False,
        supported_precisions=("SELECTED_TIMEFRAME",),
    )
    assert cfg.strict_precision_check is False
    assert cfg.allow_synthetic_sources is False
    assert cfg.require_committed_status is False
    assert cfg.supported_precisions == ("SELECTED_TIMEFRAME",)


def test_config_empty_precisions_raises() -> None:
    """Verify ValueError on empty supported_precisions."""
    with pytest.raises(ValueError, match="supported_precisions cannot be empty"):
        RunDataBindingConfig(supported_precisions=())
