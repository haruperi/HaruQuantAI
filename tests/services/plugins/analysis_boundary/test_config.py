"""Unit tests for IsolateAnalysisConfig."""

from __future__ import annotations

import pytest
from app.services.plugins.analysis_boundary.config import IsolateAnalysisConfig


def test_default_config() -> None:
    config = IsolateAnalysisConfig.from_dict(None)
    assert config.max_input_handles == 50
    assert config.enforce_staged_output_schema is True
    assert config.max_parameter_bytes == 1_048_576


def test_custom_valid_config() -> None:
    data = {
        "max_input_handles": 20,
        "enforce_staged_output_schema": False,
        "max_parameter_bytes": 65536,
    }
    config = IsolateAnalysisConfig.from_dict(data)
    assert config.max_input_handles == 20
    assert config.enforce_staged_output_schema is False
    assert config.max_parameter_bytes == 65536


def test_unknown_config_key_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown Isolate Analysis configuration keys"):
        IsolateAnalysisConfig.from_dict({"unknown_key": 123})


def test_invalid_type_rejected() -> None:
    with pytest.raises(TypeError, match="must be a mapping"):
        IsolateAnalysisConfig.from_dict("invalid")  # type: ignore[arg-type]


def test_invalid_max_input_handles_rejected() -> None:
    with pytest.raises(
        ValueError, match="max_input_handles must be a positive integer"
    ):
        IsolateAnalysisConfig.from_dict({"max_input_handles": 0})

    with pytest.raises(
        ValueError, match="max_input_handles must be a positive integer"
    ):
        IsolateAnalysisConfig.from_dict({"max_input_handles": True})


def test_invalid_enforce_schema_rejected() -> None:
    with pytest.raises(TypeError, match="enforce_staged_output_schema must be boolean"):
        IsolateAnalysisConfig.from_dict({"enforce_staged_output_schema": "yes"})


def test_invalid_max_parameter_bytes_rejected() -> None:
    with pytest.raises(
        ValueError, match="max_parameter_bytes must be an integer of at least 256"
    ):
        IsolateAnalysisConfig.from_dict({"max_parameter_bytes": 100})
