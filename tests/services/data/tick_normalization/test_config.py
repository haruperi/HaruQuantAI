"""Unit tests for Tick Normalization config."""

import pytest
from app.services.data.tick_normalization.config import TickNormalizationConfig


def test_config_defaults() -> None:
    """Verify default configuration limits."""
    cfg = TickNormalizationConfig()
    assert cfg.max_batch_size == 1_000_000


def test_config_custom_values() -> None:
    """Verify custom valid configuration limits."""
    cfg = TickNormalizationConfig(max_batch_size=500_000)
    assert cfg.max_batch_size == 500_000


def test_config_invalid_batch_size() -> None:
    """Verify ValueError on non-positive max_batch_size."""
    with pytest.raises(ValueError, match="max_batch_size must be a positive integer"):
        TickNormalizationConfig(max_batch_size=0)

    with pytest.raises(ValueError, match="max_batch_size must be a positive integer"):
        TickNormalizationConfig(max_batch_size=-100)
