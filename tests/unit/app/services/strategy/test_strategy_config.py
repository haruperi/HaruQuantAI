"""Unit tests for StrategyConfig parsing, validation, type, and bounds checks."""

import tempfile
from pathlib import Path
from typing import Any

import pytest
from app.services.strategy.config import (
    ConfigurationError,
    StrategyConfig,
    load_strategy_config,
    validate_strategy_config,
)


def get_valid_base_config() -> dict[str, Any]:
    """Helper to return a minimum valid configuration dictionary."""
    return {
        "schema_version": "1.0.0",
        "strategy_manifest": {
            "identity": {
                "strategy_id": "test",
                "strategy_type": "trend",
                "description": "desc",
                "author": "auth",
                "created_at": "2026-06-23",
            },
            "version": "1.0.0",
            "chart_requirements": {
                "main": {"symbol": "EURUSD", "timeframe": "M5"},
                "other": {},
            },
            "supported_runtime_modes": ["SIMULATOR"],
            "strategy_capabilities": [],
            "permissions": {
                "lifecycle_status": "RESEARCH",
                "permitted_environments": ["SIMULATOR"],
                "risk_profile": {},
            },
        },
        "trading_profile": {},
        "parameters": {"definitions": {}, "values": {}, "generation_metadata": {}},
        "risk_management": {},
        "trading_options": {},
        "signal_rules": {},
        "action_rules": {},
        "protection_rules": {},
        "state_contract": {},
        "required": [],
    }


def test_validate_non_mapping() -> None:
    """Verify validate_strategy_config raises ConfigurationError for non-mapping input."""
    with pytest.raises(
        ConfigurationError, match="Strategy configuration must be a JSON object"
    ):
        validate_strategy_config([])  # type: ignore[arg-type]


def test_validate_missing_top_level_keys() -> None:
    """Verify validate_strategy_config enforces required top-level keys."""
    with pytest.raises(ConfigurationError, match="missing top-level keys"):
        validate_strategy_config({"schema_version": "1.0.0"})


def test_validate_unknown_top_level_keys() -> None:
    """Verify validate_strategy_config rejects unknown top-level keys."""
    base = get_valid_base_config()
    base["extra_unknown_key"] = 123
    with pytest.raises(ConfigurationError, match="Unknown top-level config keys"):
        validate_strategy_config(base)


def test_validate_schema_version() -> None:
    """Verify schema version is validated."""
    base = get_valid_base_config()
    base["schema_version"] = "2.0.0"
    with pytest.raises(ConfigurationError, match=r"schema_version must be '1\.0\.0'"):
        validate_strategy_config(base)


def test_validate_manifest_identity() -> None:
    """Verify strategy manifest identity checks."""
    base = get_valid_base_config()
    base["strategy_manifest"]["identity"]["strategy_id"] = ""
    with pytest.raises(
        ConfigurationError, match="strategy_id must be a non-empty string"
    ):
        validate_strategy_config(base)


def test_validate_manifest_version() -> None:
    """Verify version is checked."""
    base = get_valid_base_config()
    base["strategy_manifest"]["version"] = "   "
    with pytest.raises(ConfigurationError, match="version must be a non-empty string"):
        validate_strategy_config(base)


def test_validate_manifest_runtime_modes() -> None:
    """Verify supported runtime modes checks."""
    base = get_valid_base_config()
    base["strategy_manifest"]["supported_runtime_modes"] = ["INVALID_MODE"]
    with pytest.raises(
        ConfigurationError, match="supported_runtime_modes has unsupported values"
    ):
        validate_strategy_config(base)


def test_validate_manifest_permissions() -> None:
    """Verify permission lifecycle and environment subset rules."""
    base = get_valid_base_config()
    base["strategy_manifest"]["permissions"]["lifecycle_status"] = "INVALID_STATUS"
    with pytest.raises(ConfigurationError, match="lifecycle_status must be one of"):
        validate_strategy_config(base)

    base = get_valid_base_config()
    base["strategy_manifest"]["permissions"]["permitted_environments"] = ["LIVE"]
    with pytest.raises(
        ConfigurationError,
        match="permitted_environments must be a subset of supported_runtime_modes",
    ):
        validate_strategy_config(base)


def test_validate_parameters_definition_value() -> None:
    """Verify parameters value validation checks."""
    base = get_valid_base_config()
    base["parameters"] = {
        "definitions": {
            "period": {
                "type": "integer",
                "default": 14,
                "description": "Period length",
            }
        },
        "values": {"period": "invalid_string_instead_of_int"},
        "generation_metadata": {},
    }
    with pytest.raises(ConfigurationError, match="Parameter 'period' must be integer"):
        validate_strategy_config(base)


def test_validate_parameter_bounds() -> None:
    """Verify parameters numeric constraints (min, max, step)."""
    base = get_valid_base_config()
    base["parameters"] = {
        "definitions": {
            "period": {
                "type": "integer",
                "default": 14,
                "description": "Period length",
                "minimum": 10,
                "maximum": 20,
                "step": 2,
            }
        },
        "values": {"period": 15},
        "generation_metadata": {},
    }
    with pytest.raises(ConfigurationError, match="does not align to step"):
        validate_strategy_config(base)


def test_validate_required_paths() -> None:
    """Verify required paths list dots verification."""
    base = get_valid_base_config()
    base["required"] = ["trading_options.timezone"]
    with pytest.raises(
        ConfigurationError, match="Required configuration path is missing"
    ):
        validate_strategy_config(base)


def test_strategy_config_helper_methods() -> None:
    """Verify StrategyConfig helper methods and fallback defaults."""
    raw = get_valid_base_config()
    raw["parameters"] = {
        "definitions": {
            "period": {
                "type": "integer",
                "default": 14,
                "description": "Period length",
            }
        },
        "values": {},
        "generation_metadata": {},
    }
    raw["trading_options"] = {"timezone": "UTC"}
    config = StrategyConfig(raw)
    assert config.strategy_id == "test"
    assert config.version == "1.0.0"
    assert config.permitted_environments == frozenset(["SIMULATOR"])

    assert config.section("trading_options") == {"timezone": "UTC"}
    with pytest.raises(
        ConfigurationError, match="Expected section 'schema_version' to be an object"
    ):
        config.section("schema_version")

    assert config.parameter("period") == 14
    with pytest.raises(ConfigurationError, match="No parameter definition exists for"):
        config.parameter("unknown_param")

    assert config.option("timezone") == "UTC"
    assert config.option("nested", "missing", default="default_val") == "default_val"


def test_load_strategy_config() -> None:
    """Verify load_strategy_config file parsing exceptions."""
    with pytest.raises(ConfigurationError, match="Strategy config does not exist"):
        load_strategy_config(Path("non_existent_file.json"))

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, encoding="utf-8"
    ) as temp_file:
        temp_file.write("{invalid_json}")
        temp_file_path = Path(temp_file.name)

    try:
        with pytest.raises(
            ConfigurationError, match="Strategy config is not valid JSON"
        ):
            load_strategy_config(temp_file_path)
    finally:
        temp_file_path.unlink()


def test_validate_manifest_runtime_modes_not_list() -> None:
    """Verify validate_strategy_config rejects non-list supported runtime modes."""
    base = get_valid_base_config()
    base["strategy_manifest"]["supported_runtime_modes"] = "not_a_list"
    with pytest.raises(
        ConfigurationError, match="supported_runtime_modes must be a non-empty list"
    ):
        validate_strategy_config(base)


def test_validate_manifest_permitted_environments_not_list() -> None:
    """Verify validate_strategy_config rejects non-list permitted environments."""
    base = get_valid_base_config()
    base["strategy_manifest"]["permissions"]["permitted_environments"] = "not_a_list"
    with pytest.raises(
        ConfigurationError, match="permitted_environments must be a non-empty list"
    ):
        validate_strategy_config(base)


def test_validate_unknown_parameter_value() -> None:
    """Verify validate_strategy_config rejects values without definitions."""
    base = get_valid_base_config()
    base["parameters"]["values"] = {"extra_param": 10}
    with pytest.raises(
        ConfigurationError,
        match=r"parameters\.values contains values without definitions",
    ):
        validate_strategy_config(base)


def test_validate_parameter_invalid_type() -> None:
    """Verify validate_strategy_config rejects invalid parameter types."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "period": {"type": "invalid_type", "default": 10, "description": "desc"}
    }
    with pytest.raises(ConfigurationError, match="type must be one of"):
        validate_strategy_config(base)


def test_validate_parameter_allowed_values_not_list() -> None:
    """Verify validate_strategy_config rejects non-list allowed_values."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "period": {
            "type": "integer",
            "default": 10,
            "description": "desc",
            "allowed_values": "not_a_list",
        }
    }
    with pytest.raises(ConfigurationError, match="allowed_values must be a list"):
        validate_strategy_config(base)


def test_validate_parameter_string_early_return() -> None:
    """Verify validate_strategy_config skips bounds checks for string parameter type."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "mode": {"type": "string", "default": "fast", "description": "desc"}
    }
    config = validate_strategy_config(base)
    assert config.parameter("mode") == "fast"


def test_validate_parameter_min_max_violation() -> None:
    """Verify validate_strategy_config enforces minimum and maximum bounds."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "period": {
            "type": "integer",
            "default": 10,
            "description": "desc",
            "minimum": 5,
            "maximum": 15,
        }
    }

    # Violation of min
    base["parameters"]["values"] = {"period": 4}
    with pytest.raises(ConfigurationError, match="must be >= 5"):
        validate_strategy_config(base)

    # Violation of max
    base["parameters"]["values"] = {"period": 16}
    with pytest.raises(ConfigurationError, match="must be <= 15"):
        validate_strategy_config(base)


def test_validate_parameter_min_greater_than_max() -> None:
    """Verify validate_strategy_config rejects minimum > maximum."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "period": {
            "type": "number",
            "default": float("nan"),
            "description": "desc",
            "minimum": 15,
            "maximum": 5,
        }
    }
    with pytest.raises(ConfigurationError, match="has minimum greater than maximum"):
        validate_strategy_config(base)


def test_validate_parameter_step_non_positive() -> None:
    """Verify validate_strategy_config rejects step <= 0."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "period": {
            "type": "integer",
            "default": 10,
            "description": "desc",
            "minimum": 5,
            "step": -1,
        }
    }
    with pytest.raises(ConfigurationError, match="step must be > 0"):
        validate_strategy_config(base)


def test_validate_required_path_is_null() -> None:
    """Verify validate_strategy_config rejects required paths that evaluate to null."""
    base = get_valid_base_config()
    base["required"] = ["trading_options"]
    base["trading_options"] = None
    with pytest.raises(ConfigurationError, match="Required configuration path is null"):
        validate_strategy_config(base)


def test_validate_numeric_constraints_non_numeric() -> None:
    """Verify validate_strategy_config rejects non-numeric bounds."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "period": {
            "type": "integer",
            "default": 10,
            "description": "desc",
            "minimum": "not_numeric",
        }
    }
    with pytest.raises(ConfigurationError, match="minimum must be numeric"):
        validate_strategy_config(base)


def test_validate_runtime_modes_non_string() -> None:
    """Verify validate_strategy_config rejects non-string members in supported runtime modes."""
    base = get_valid_base_config()
    base["strategy_manifest"]["supported_runtime_modes"] = [123]
    with pytest.raises(
        ConfigurationError, match="supported_runtime_modes must contain strings only"
    ):
        validate_strategy_config(base)


def test_validate_runtime_modes_duplicates() -> None:
    """Verify validate_strategy_config rejects duplicate members in supported runtime modes."""
    base = get_valid_base_config()
    base["strategy_manifest"]["supported_runtime_modes"] = ["SIMULATOR", "SIMULATOR"]
    with pytest.raises(
        ConfigurationError, match="supported_runtime_modes cannot contain duplicates"
    ):
        validate_strategy_config(base)


def test_validate_parameter_value_not_in_allowed_values() -> None:
    """Verify validate_strategy_config rejects parameter values that violate allowed_values."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "period": {
            "type": "integer",
            "default": 10,
            "description": "desc",
            "allowed_values": [5, 10, 15],
        }
    }
    base["parameters"]["values"] = {"period": 12}
    with pytest.raises(ConfigurationError, match="must be one of"):
        validate_strategy_config(base)


def test_validate_permitted_environments_non_string() -> None:
    """Verify validate_strategy_config rejects non-string members in permitted environments."""
    base = get_valid_base_config()
    base["strategy_manifest"]["permissions"]["permitted_environments"] = [123]
    with pytest.raises(
        ConfigurationError, match="permitted_environments must contain strings only"
    ):
        validate_strategy_config(base)


def test_validate_permitted_environments_duplicates() -> None:
    """Verify validate_strategy_config rejects duplicate members in permitted environments."""
    base = get_valid_base_config()
    base["strategy_manifest"]["permissions"]["permitted_environments"] = [
        "SIMULATOR",
        "SIMULATOR",
    ]
    with pytest.raises(
        ConfigurationError, match="permitted_environments cannot contain duplicates"
    ):
        validate_strategy_config(base)


def test_validate_minimum_boolean() -> None:
    """Verify validate_strategy_config rejects boolean values for minimum check."""
    base = get_valid_base_config()
    base["parameters"]["definitions"] = {
        "period": {
            "type": "integer",
            "default": 10,
            "description": "desc",
            "minimum": True,
        }
    }
    with pytest.raises(ConfigurationError, match="minimum must be numeric"):
        validate_strategy_config(base)


def test_validate_required_non_string() -> None:
    """Verify validate_strategy_config rejects non-string entries in required dot paths."""
    base = get_valid_base_config()
    base["required"] = [123]
    with pytest.raises(
        ConfigurationError, match="required must be a list of configuration dot paths"
    ):
        validate_strategy_config(base)


def test_validate_parameter_various_types() -> None:
    """Verify type checking for number, boolean, list, and dict parameters."""
    base = get_valid_base_config()
    from collections.abc import Mapping

    base["parameters"]["definitions"] = {
        "p1": {"type": "number", "default": 1.5, "description": "desc"},
        "p2": {"type": "boolean", "default": True, "description": "desc"},
        "p3": {"type": "list", "default": [1, 2], "description": "desc"},
        "p4": {"type": "dict", "default": {"key": "val"}, "description": "desc"},
    }
    config = validate_strategy_config(base)
    assert config.parameter("p1") == 1.5
    assert config.parameter("p2") is True
    assert config.parameter("p3") == [1, 2]
    assert isinstance(config.parameter("p4"), Mapping)
    assert config.parameter("p4")["key"] == "val"
