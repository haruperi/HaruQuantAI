"""Unit tests for External Series Alignment configuration."""

import pytest
from app.services.data.external_series_alignment.config import (
    ExternalSeriesAlignmentConfig,
)


def test_default_config() -> None:
    """Verify default configuration attributes."""
    cfg = ExternalSeriesAlignmentConfig()
    assert cfg.max_series_points_per_request == 100_000
    assert cfg.default_timezone == "UTC"
    assert cfg.default_max_age_seconds == 86_400
    assert cfg.default_missing_policy == "NULL"


def test_custom_config() -> None:
    """Verify custom configuration attributes."""
    cfg = ExternalSeriesAlignmentConfig(
        max_series_points_per_request=50_000,
        default_timezone="America/New_York",
        default_max_age_seconds=3600,
        default_missing_policy="CARRY_FORWARD",
    )
    assert cfg.max_series_points_per_request == 50_000
    assert cfg.default_timezone == "America/New_York"
    assert cfg.default_max_age_seconds == 3600
    assert cfg.default_missing_policy == "CARRY_FORWARD"


def test_invalid_max_points() -> None:
    """Verify ValueError on non-positive max_series_points_per_request."""
    with pytest.raises(
        ValueError, match="max_series_points_per_request must be a positive integer"
    ):
        ExternalSeriesAlignmentConfig(max_series_points_per_request=0)


def test_invalid_timezone() -> None:
    """Verify ValueError on empty default_timezone."""
    with pytest.raises(ValueError, match="default_timezone must be a non-empty string"):
        ExternalSeriesAlignmentConfig(default_timezone="")


def test_invalid_max_age() -> None:
    """Verify ValueError on non-positive default_max_age_seconds."""
    with pytest.raises(
        ValueError, match="default_max_age_seconds must be a positive integer"
    ):
        ExternalSeriesAlignmentConfig(default_max_age_seconds=0)


def test_invalid_missing_policy() -> None:
    """Verify ValueError on invalid default_missing_policy."""
    with pytest.raises(
        ValueError,
        match="default_missing_policy must be one of: NULL, CARRY_FORWARD, FAIL",
    ):
        ExternalSeriesAlignmentConfig(default_missing_policy="INVALID")
