"""JSON strategy configuration loading and deterministic validation."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

JsonObject = dict[str, Any]


class ConfigurationError(ValueError):
    """Raised when a strategy configuration violates the canonical contract."""


_REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "strategy_manifest",
    "trading_profile",
    "parameters",
    "risk_management",
    "trading_options",
    "signal_rules",
    "action_rules",
    "protection_rules",
    "state_contract",
    "required",
}

_PARAMETER_TYPES = {"integer", "number", "string", "boolean", "list", "dict"}
_RUNTIME_MODES = {"SIMULATOR", "PAPER", "LIVE"}
_LIFECYCLE_STATUSES = {"RESEARCH", "PAPER", "ACTIVE", "RETIRED"}


@dataclass(frozen=True, slots=True)
class StrategyConfig:
    """Validated wrapper around a deep-copied canonical JSON object."""

    raw: Mapping[str, Any]

    @property
    def strategy_id(self) -> str:
        return str(self.raw["strategy_manifest"]["identity"]["strategy_id"])

    @property
    def version(self) -> str:
        return str(self.raw["strategy_manifest"]["version"])

    @property
    def permitted_environments(self) -> frozenset[str]:
        permissions = self.raw["strategy_manifest"]["permissions"]
        return frozenset(permissions["permitted_environments"])

    def section(self, name: str) -> Mapping[str, Any]:
        """Return a named configuration section."""
        value = self.raw[name]
        if not isinstance(value, Mapping):
            raise ConfigurationError(f"Expected section {name!r} to be an object.")
        return value

    def parameter(self, name: str) -> Any:
        """Return active parameter value, falling back to the declared default."""
        parameters = self.section("parameters")
        values = _as_mapping(parameters.get("values"), "parameters.values")
        definitions = _as_mapping(
            parameters.get("definitions"), "parameters.definitions"
        )
        if name not in definitions:
            raise ConfigurationError(f"No parameter definition exists for {name!r}.")
        if name in values:
            return values[name]
        definition = _as_mapping(definitions[name], f"parameters.definitions.{name}")
        return definition["default"]

    def option(self, *path: str, default: Any = None) -> Any:
        """Read an optional nested value under trading_options."""
        current: Any = self.section("trading_options")
        for segment in path:
            if not isinstance(current, Mapping) or segment not in current:
                return default
            current = current[segment]
        return current


def load_strategy_config(path: str | Path) -> StrategyConfig:
    """Load and validate a UTF-8 JSON strategy config from disk."""
    config_path = Path(path)
    try:
        value = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigurationError(
            f"Strategy config does not exist: {config_path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ConfigurationError(
            f"Strategy config is not valid JSON: {config_path}: {error.msg}"
        ) from error
    return validate_strategy_config(value)


def validate_strategy_config(value: Mapping[str, Any]) -> StrategyConfig:
    """Validate canonical strategy config without a third-party runtime dependency."""
    if not isinstance(value, Mapping):
        raise ConfigurationError("Strategy configuration must be a JSON object.")

    missing = _REQUIRED_TOP_LEVEL_KEYS.difference(value)
    if missing:
        joined = ", ".join(sorted(missing))
        raise ConfigurationError(
            f"Strategy configuration is missing top-level keys: {joined}."
        )

    unexpected = set(value).difference(_REQUIRED_TOP_LEVEL_KEYS)
    if unexpected:
        joined = ", ".join(sorted(unexpected))
        raise ConfigurationError(f"Unknown top-level config keys: {joined}.")

    if value["schema_version"] != "1.0.0":
        raise ConfigurationError("schema_version must be '1.0.0'.")

    _validate_manifest(_as_mapping(value["strategy_manifest"], "strategy_manifest"))
    _validate_parameters(_as_mapping(value["parameters"], "parameters"))
    _validate_required_paths(value, value["required"])

    return StrategyConfig(raw=_copy_json_object(value))


def _validate_manifest(manifest: Mapping[str, Any]) -> None:
    required = {
        "identity",
        "version",
        "chart_requirements",
        "supported_runtime_modes",
        "strategy_capabilities",
        "permissions",
    }
    _require_keys(manifest, required, "strategy_manifest")

    identity = _as_mapping(manifest["identity"], "strategy_manifest.identity")
    _require_keys(
        identity,
        {"strategy_id", "strategy_type", "description", "author", "created_at"},
        "strategy_manifest.identity",
    )
    for key in ("strategy_id", "strategy_type", "description", "author", "created_at"):
        if not isinstance(identity[key], str) or not identity[key].strip():
            raise ConfigurationError(
                f"strategy_manifest.identity.{key} must be a non-empty string."
            )

    if not isinstance(manifest["version"], str) or not manifest["version"].strip():
        raise ConfigurationError(
            "strategy_manifest.version must be a non-empty string."
        )

    runtime_modes = manifest["supported_runtime_modes"]
    if not isinstance(runtime_modes, list) or not runtime_modes:
        raise ConfigurationError(
            "strategy_manifest.supported_runtime_modes must be a non-empty list."
        )
    _validate_members(runtime_modes, _RUNTIME_MODES, "supported_runtime_modes")

    permissions = _as_mapping(manifest["permissions"], "strategy_manifest.permissions")
    _require_keys(
        permissions,
        {"lifecycle_status", "permitted_environments", "risk_profile"},
        "strategy_manifest.permissions",
    )
    lifecycle = permissions["lifecycle_status"]
    if lifecycle not in _LIFECYCLE_STATUSES:
        raise ConfigurationError(
            "strategy_manifest.permissions.lifecycle_status must be one of "
            f"{sorted(_LIFECYCLE_STATUSES)}."
        )
    environments = permissions["permitted_environments"]
    if not isinstance(environments, list) or not environments:
        raise ConfigurationError(
            "strategy_manifest.permissions.permitted_environments must be a "
            "non-empty list."
        )
    _validate_members(environments, _RUNTIME_MODES, "permitted_environments")
    unsupported = set(environments).difference(runtime_modes)
    if unsupported:
        raise ConfigurationError(
            "permitted_environments must be a subset of supported_runtime_modes; "
            f"unsupported: {sorted(unsupported)}."
        )


def _validate_parameters(parameters: Mapping[str, Any]) -> None:
    _require_keys(
        parameters,
        {"definitions", "values", "generation_metadata"},
        "parameters",
    )
    definitions = _as_mapping(parameters["definitions"], "parameters.definitions")
    values = _as_mapping(parameters["values"], "parameters.values")

    unknown_values = set(values).difference(definitions)
    if unknown_values:
        raise ConfigurationError(
            "parameters.values contains values without definitions: "
            f"{sorted(unknown_values)}."
        )

    for name, raw_definition in definitions.items():
        definition = _as_mapping(raw_definition, f"parameters.definitions.{name}")
        _require_keys(
            definition,
            {"type", "default", "description"},
            f"parameters.definitions.{name}",
        )
        parameter_type = definition["type"]
        if parameter_type not in _PARAMETER_TYPES:
            raise ConfigurationError(
                f"parameters.definitions.{name}.type must be one of "
                f"{sorted(_PARAMETER_TYPES)}."
            )
        _validate_parameter_value(name, definition["default"], definition)
        if name in values:
            _validate_parameter_value(name, values[name], definition)


def _validate_parameter_value(
    name: str, parameter_value: Any, definition: Mapping[str, Any]
) -> None:
    parameter_type = definition["type"]
    if not _matches_parameter_type(parameter_value, parameter_type):
        raise ConfigurationError(
            f"Parameter {name!r} must be {parameter_type}; got "
            f"{type(parameter_value).__name__}."
        )

    allowed_values = definition.get("allowed_values")
    if allowed_values is not None:
        if not isinstance(allowed_values, list):
            raise ConfigurationError(
                f"parameters.definitions.{name}.allowed_values must be a list."
            )
        if parameter_value not in allowed_values:
            raise ConfigurationError(
                f"Parameter {name!r} must be one of {allowed_values!r}; got "
                f"{parameter_value!r}."
            )

    if parameter_type not in {"integer", "number"}:
        return

    numeric_value = float(parameter_value)
    minimum = definition.get("minimum")
    maximum = definition.get("maximum")
    step = definition.get("step")
    if minimum is not None:
        _validate_numeric_definition(name, "minimum", minimum)
        if numeric_value < float(minimum):
            raise ConfigurationError(
                f"Parameter {name!r} must be >= {minimum}; got {parameter_value}."
            )
    if maximum is not None:
        _validate_numeric_definition(name, "maximum", maximum)
        if numeric_value > float(maximum):
            raise ConfigurationError(
                f"Parameter {name!r} must be <= {maximum}; got {parameter_value}."
            )
    if minimum is not None and maximum is not None and float(minimum) > float(maximum):
        raise ConfigurationError(
            f"Parameter {name!r} has minimum greater than maximum."
        )
    if step is not None:
        _validate_numeric_definition(name, "step", step)
        if float(step) <= 0:
            raise ConfigurationError(f"Parameter {name!r} step must be > 0.")
        anchor = float(minimum) if minimum is not None else float(definition["default"])
        ratio = (numeric_value - anchor) / float(step)
        if not math.isclose(ratio, round(ratio), abs_tol=1e-9):
            raise ConfigurationError(
                f"Parameter {name!r} value {parameter_value} does not align "
                f"to step {step} from anchor {anchor}."
            )


def _validate_required_paths(value: Mapping[str, Any], required: Any) -> None:
    if not isinstance(required, list) or not all(
        isinstance(path, str) for path in required
    ):
        raise ConfigurationError("required must be a list of configuration dot paths.")
    for path in required:
        current: Any = value
        for segment in path.split("."):
            if not isinstance(current, Mapping) or segment not in current:
                raise ConfigurationError(
                    f"Required configuration path is missing: {path}."
                )
            current = current[segment]
        if current is None:
            raise ConfigurationError(f"Required configuration path is null: {path}.")


def _matches_parameter_type(value: Any, declared_type: str) -> bool:
    match declared_type:
        case "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        case "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        case "string":
            return isinstance(value, str)
        case "boolean":
            return isinstance(value, bool)
        case "list":
            return isinstance(value, list)
        case "dict":
            return isinstance(value, Mapping)
    return False


def _as_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{name} must be a JSON object.")
    return value


def _require_keys(value: Mapping[str, Any], keys: set[str], name: str) -> None:
    missing = keys.difference(value)
    if missing:
        raise ConfigurationError(f"{name} is missing keys: {sorted(missing)}.")


def _validate_members(values: list[Any], allowed: set[str], name: str) -> None:
    if not all(isinstance(item, str) for item in values):
        raise ConfigurationError(f"{name} must contain strings only.")
    unexpected = set(values).difference(allowed)
    if unexpected:
        raise ConfigurationError(
            f"{name} has unsupported values: {sorted(unexpected)}."
        )
    if len(values) != len(set(values)):
        raise ConfigurationError(f"{name} cannot contain duplicates.")


def _validate_numeric_definition(name: str, field: str, value: Any) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigurationError(
            f"parameters.definitions.{name}.{field} must be numeric."
        )


def _copy_json_object(value: Mapping[str, Any]) -> JsonObject:
    """Deep copy through JSON to prevent callers mutating validated config in place."""
    return cast("JsonObject", json.loads(json.dumps(value)))
