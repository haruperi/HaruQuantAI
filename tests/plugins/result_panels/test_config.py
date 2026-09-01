"""Unit tests for ResultPanelsConfig."""

from __future__ import annotations

import pytest
from app.services.plugins.result_panels.config import ResultPanelsConfig


def test_default_config() -> None:
    config = ResultPanelsConfig.from_dict(None)
    assert config.allowed_bridge_operations == (
        "READ_RESULTS",
        "QUERY_DATA",
        "RECEIVE_MESSAGES",
    )
    assert config.enforce_secure_content_source is True
    assert config.max_panels_per_query == 100


def test_custom_valid_config() -> None:
    data = {
        "allowed_bridge_operations": ["READ_RESULTS"],
        "enforce_secure_content_source": False,
        "max_panels_per_query": 25,
    }
    config = ResultPanelsConfig.from_dict(data)
    assert config.allowed_bridge_operations == ("READ_RESULTS",)
    assert config.enforce_secure_content_source is False
    assert config.max_panels_per_query == 25


def test_unknown_config_key_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown Result Panels configuration keys"):
        ResultPanelsConfig.from_dict({"unknown_key": 123})


def test_invalid_type_rejected() -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        ResultPanelsConfig.from_dict("invalid")  # type: ignore[arg-type]


def test_invalid_allowed_bridge_operations_rejected() -> None:
    with pytest.raises(TypeError, match="must be a list or tuple"):
        ResultPanelsConfig.from_dict({"allowed_bridge_operations": "READ_RESULTS"})

    with pytest.raises(TypeError, match="must be strings"):
        ResultPanelsConfig.from_dict({"allowed_bridge_operations": [123]})

    with pytest.raises(ValueError, match="Invalid bridge operation: 'INVALID_OP'"):
        ResultPanelsConfig.from_dict({"allowed_bridge_operations": ["INVALID_OP"]})


def test_invalid_enforce_secure_rejected() -> None:
    with pytest.raises(
        TypeError, match="enforce_secure_content_source must be boolean"
    ):
        ResultPanelsConfig.from_dict({"enforce_secure_content_source": "yes"})


def test_invalid_max_panels_rejected() -> None:
    with pytest.raises(
        ValueError, match="max_panels_per_query must be a positive integer"
    ):
        ResultPanelsConfig.from_dict({"max_panels_per_query": 0})

    with pytest.raises(
        ValueError, match="max_panels_per_query must be a positive integer"
    ):
        ResultPanelsConfig.from_dict({"max_panels_per_query": True})
