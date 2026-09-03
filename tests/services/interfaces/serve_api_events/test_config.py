"""Unit tests for serve-api-events configuration parsing."""

import pytest
from app.services.interfaces.serve_api_events.config import ServeApiEventsConfig


def test_config_defaults() -> None:
    """Verify default configuration values."""
    config = ServeApiEventsConfig()
    assert config.supported_api_versions == ("v1",)
    assert config.server_prefixes == ("/api/v1",)
    assert config.stream_retention_events == 1_000
    assert config.stream_replay_batch_limit == 100
    assert config.event_payload_max_bytes == 65_536


def test_config_from_dict_none_returns_defaults() -> None:
    """Verify None maps to defaults."""
    config = ServeApiEventsConfig.from_dict(None)
    assert config == ServeApiEventsConfig()


def test_config_from_dict_valid_values() -> None:
    """Verify valid overrides are accepted and normalized to tuples."""
    config = ServeApiEventsConfig.from_dict(
        {
            "supported_api_versions": ["v1", "v2"],
            "server_prefixes": ["/api/v1", "/api/v2"],
            "stream_retention_events": 250,
            "stream_replay_batch_limit": 25,
            "event_payload_max_bytes": 1_024,
        }
    )
    assert config.supported_api_versions == ("v1", "v2")
    assert config.server_prefixes == ("/api/v1", "/api/v2")
    assert config.stream_retention_events == 250
    assert config.stream_replay_batch_limit == 25
    assert config.event_payload_max_bytes == 1_024


def test_config_from_dict_rejects_unknown_keys() -> None:
    """Verify unknown configuration keys fail closed."""
    with pytest.raises(ValueError, match="Unknown serve-api-events"):
        ServeApiEventsConfig.from_dict({"request_timeout_seconds": 30})


def test_config_from_dict_rejects_invalid_types() -> None:
    """Verify non-integer and non-list values raise TypeError."""
    with pytest.raises(TypeError, match="stream_retention_events"):
        ServeApiEventsConfig.from_dict({"stream_retention_events": "many"})
    with pytest.raises(TypeError, match="stream_retention_events"):
        ServeApiEventsConfig.from_dict({"stream_retention_events": True})
    with pytest.raises(TypeError, match="supported_api_versions"):
        ServeApiEventsConfig.from_dict({"supported_api_versions": "v1"})


def test_config_rejects_invalid_constructor_values() -> None:
    """Verify direct construction bounds and formats."""
    with pytest.raises(ValueError, match="supported_api_versions"):
        ServeApiEventsConfig(supported_api_versions=())
    with pytest.raises(ValueError, match="v<N>"):
        ServeApiEventsConfig(supported_api_versions=("1",))
    with pytest.raises(ValueError, match="server_prefixes"):
        ServeApiEventsConfig(server_prefixes=("api/v1",))
    with pytest.raises(ValueError, match="stream_retention_events"):
        ServeApiEventsConfig(stream_retention_events=0)
    with pytest.raises(ValueError, match="stream_replay_batch_limit"):
        ServeApiEventsConfig(stream_replay_batch_limit=10_001)
    with pytest.raises(ValueError, match="event_payload_max_bytes"):
        ServeApiEventsConfig(event_payload_max_bytes=0)
