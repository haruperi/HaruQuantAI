"""Unit tests for HTTP and Event Contracts configuration."""

import pytest

from app.services.interfaces.api_events.config import ApiEventsConfig


def test_api_events_config_defaults() -> None:
    """Verify default values of ApiEventsConfig."""
    config = ApiEventsConfig()
    assert config.title == "HaruQuantAI API"
    assert config.api_version == "v1"
    assert config.event_buffer_size == 1000
    assert config.max_artifact_download_bytes == 100 * 1024 * 1024


def test_api_events_config_from_dict_valid() -> None:
    """Verify parsing from valid dictionary."""
    data = {
        "title": "Custom API Gateway",
        "api_version": "v1.2",
        "event_buffer_size": 500,
        "max_artifact_download_bytes": 50 * 1024 * 1024,
    }
    config = ApiEventsConfig.from_dict(data)
    assert config.title == "Custom API Gateway"
    assert config.api_version == "v1.2"
    assert config.event_buffer_size == 500
    assert config.max_artifact_download_bytes == 50 * 1024 * 1024


def test_api_events_config_from_dict_none_or_empty() -> None:
    """Verify parsing from None or empty dictionary returns defaults."""
    assert ApiEventsConfig.from_dict(None) == ApiEventsConfig()
    assert ApiEventsConfig.from_dict({}) == ApiEventsConfig()


def test_api_events_config_unknown_keys_rejected() -> None:
    """Verify unknown keys raise ValueError."""
    with pytest.raises(ValueError, match="Unknown ApiEvents configuration keys: foo"):
        ApiEventsConfig.from_dict({"foo": "bar"})


def test_api_events_config_invalid_bounds() -> None:
    """Verify out-of-bounds numbers raise ValueError."""
    with pytest.raises(ValueError, match="event_buffer_size must be positive"):
        ApiEventsConfig.from_dict({"event_buffer_size": 0})

    with pytest.raises(ValueError, match="event_buffer_size must be positive"):
        ApiEventsConfig.from_dict({"event_buffer_size": -10})

    with pytest.raises(
        ValueError, match="max_artifact_download_bytes must be positive"
    ):
        ApiEventsConfig.from_dict({"max_artifact_download_bytes": 0})
