"""Unit tests for External Indicator Series configuration."""

import pytest
from app.services.data.external_indicator_series.config import (
    ExternalIndicatorSeriesConfig,
)


def test_default_config() -> None:
    """Verify default configuration attributes."""
    cfg = ExternalIndicatorSeriesConfig()
    assert cfg.default_timezone == "UTC"
    assert cfg.max_points_per_series == 1_000_000
    assert cfg.require_deterministic_reimport is True
    assert cfg.allow_future_timestamps is False
    assert cfg.default_missing_policy == "FORWARD_FILL"


def test_custom_config() -> None:
    """Verify custom configuration attributes."""
    cfg = ExternalIndicatorSeriesConfig(
        default_timezone="America/New_York",
        max_points_per_series=500_000,
        require_deterministic_reimport=False,
        allow_future_timestamps=True,
        default_missing_policy="ZERO_FILL",
    )
    assert cfg.default_timezone == "America/New_York"
    assert cfg.max_points_per_series == 500_000
    assert cfg.require_deterministic_reimport is False
    assert cfg.allow_future_timestamps is True
    assert cfg.default_missing_policy == "ZERO_FILL"


def test_invalid_max_points_per_series() -> None:
    """Verify ValueError on non-positive max_points_per_series."""
    with pytest.raises(
        ValueError, match="max_points_per_series must be a positive integer"
    ):
        ExternalIndicatorSeriesConfig(max_points_per_series=0)


def test_invalid_timezone() -> None:
    """Verify ValueError on invalid timezone string."""
    with pytest.raises(ValueError, match="not a valid IANA timezone"):
        ExternalIndicatorSeriesConfig(default_timezone="Invalid/NonExistentZone_123")


def test_invalid_missing_policy() -> None:
    """Verify ValueError on unsupported missing policy."""
    with pytest.raises(ValueError, match="default_missing_policy must be one of"):
        ExternalIndicatorSeriesConfig(default_missing_policy="INVALID_POLICY")
