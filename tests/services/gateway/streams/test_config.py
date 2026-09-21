"""Tests for gateway streams configuration."""

from __future__ import annotations

import pytest
from app.services.gateway.streams import StreamsConfig


def test_streams_config_defaults() -> None:
    """Verify default streams configuration values."""
    config = StreamsConfig()
    assert config.max_connections == 100
    assert config.client_buffer_size == 256
    assert config.heartbeat_interval_s == 15.0
    assert config.websocket_path == "/websocket/updates"
    assert config.sse_path == "/api/v1/stream"


def test_streams_config_validation() -> None:
    """Verify streams configuration bounds validation."""
    with pytest.raises(ValueError, match="max_connections must be > 0"):
        StreamsConfig(max_connections=0)

    with pytest.raises(ValueError, match="client_buffer_size must be > 0"):
        StreamsConfig(client_buffer_size=0)

    with pytest.raises(ValueError, match="heartbeat_interval_s must be > 0"):
        StreamsConfig(heartbeat_interval_s=0.0)
