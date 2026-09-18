"""Unit tests for Gateway API server configuration."""

import pytest
from app.services.gateway.api_server import ApiServerConfig


def test_config_defaults() -> None:
    """Verify default configuration attributes."""
    config = ApiServerConfig()
    assert config.host == "127.0.0.1"
    assert config.port == 8000
    assert config.log_level == "INFO"
    assert config.enable_docs is True


def test_config_custom_values() -> None:
    """Verify custom configuration initialization."""
    config = ApiServerConfig(
        host="0.0.0.0",
        port=9000,
        log_level="DEBUG",
        enable_docs=False,
    )
    assert config.host == "0.0.0.0"
    assert config.port == 9000
    assert config.log_level == "DEBUG"
    assert config.enable_docs is False


def test_config_invalid_port() -> None:
    """Verify out-of-range port raises ValueError."""
    with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
        ApiServerConfig(port=0)

    with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
        ApiServerConfig(port=70000)


def test_config_empty_host() -> None:
    """Verify empty or whitespace host raises ValueError."""
    with pytest.raises(ValueError, match="Host cannot be empty"):
        ApiServerConfig(host="")

    with pytest.raises(ValueError, match="Host cannot be empty"):
        ApiServerConfig(host="   ")
