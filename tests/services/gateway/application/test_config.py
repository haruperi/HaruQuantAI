"""Tests for gateway application configuration."""

from __future__ import annotations

import pytest
from app.services.gateway.application import ApplicationConfig


def test_application_config_defaults() -> None:
    """Verify default application configuration values."""
    config = ApplicationConfig()
    assert config.host == "127.0.0.1"
    assert config.port == 8000
    assert config.enable_gzip is True
    assert config.gzip_minimum_size == 500
    assert config.enable_docs is True
    assert config.static_ui_dir is None
    assert config.allowed_origins == (
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    )


def test_application_config_validation() -> None:
    """Verify configuration boundary validation."""
    with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
        ApplicationConfig(port=0)

    with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
        ApplicationConfig(port=70000)

    with pytest.raises(ValueError, match="Host cannot be empty"):
        ApplicationConfig(host="")

    with pytest.raises(ValueError, match="gzip_minimum_size must be >= 0"):
        ApplicationConfig(gzip_minimum_size=-1)

    with pytest.raises(ValueError, match="allowed_origins cannot be empty"):
        ApplicationConfig(allowed_origins=())
