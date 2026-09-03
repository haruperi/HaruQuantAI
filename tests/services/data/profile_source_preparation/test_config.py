"""Unit tests for Volume Profile Source Preparation configuration."""

from decimal import Decimal

import pytest
from app.services.data.profile_source_preparation.config import (
    ProfileSourcePreparationConfig,
)


def test_default_config() -> None:
    """Verify default configuration attributes."""
    cfg = ProfileSourcePreparationConfig()
    assert cfg.default_price_step == Decimal("0.01")
    assert cfg.default_bin_count is None
    assert cfg.min_price_step == Decimal("0.00000001")
    assert cfg.max_bin_count == 10_000
    assert cfg.require_session_alignment is True


def test_custom_config() -> None:
    """Verify custom configuration attributes."""
    cfg = ProfileSourcePreparationConfig(
        default_price_step=Decimal("0.05"),
        default_bin_count=200,
        min_price_step=Decimal("0.0001"),
        max_bin_count=5000,
        require_session_alignment=False,
    )
    assert cfg.default_price_step == Decimal("0.05")
    assert cfg.default_bin_count == 200
    assert cfg.min_price_step == Decimal("0.0001")
    assert cfg.max_bin_count == 5000
    assert cfg.require_session_alignment is False


def test_invalid_default_price_step() -> None:
    """Verify ValueError on non-positive default_price_step."""
    with pytest.raises(
        ValueError, match="default_price_step must be a positive decimal"
    ):
        ProfileSourcePreparationConfig(default_price_step=Decimal(0))


def test_invalid_min_price_step() -> None:
    """Verify ValueError on non-positive min_price_step."""
    with pytest.raises(ValueError, match="min_price_step must be a positive decimal"):
        ProfileSourcePreparationConfig(min_price_step=Decimal("-0.01"))


def test_invalid_default_bin_count() -> None:
    """Verify ValueError on non-positive default_bin_count."""
    with pytest.raises(
        ValueError, match="default_bin_count must be a positive integer if provided"
    ):
        ProfileSourcePreparationConfig(default_bin_count=0)


def test_invalid_max_bin_count() -> None:
    """Verify ValueError on non-positive max_bin_count."""
    with pytest.raises(ValueError, match="max_bin_count must be a positive integer"):
        ProfileSourcePreparationConfig(max_bin_count=0)


def test_default_bin_count_exceeds_max() -> None:
    """Verify ValueError when default_bin_count exceeds max_bin_count."""
    with pytest.raises(
        ValueError, match="default_bin_count cannot exceed max_bin_count"
    ):
        ProfileSourcePreparationConfig(default_bin_count=500, max_bin_count=100)
