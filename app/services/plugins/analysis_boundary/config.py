"""Strict configuration for the plugin analysis boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.plugins.analysis_boundary.manifest import SPEC

_DEFAULT_MAX_INPUT_HANDLES: int = 50
_DEFAULT_ENFORCE_SCHEMA: bool = True
_DEFAULT_MAX_PARAMETER_BYTES: int = 1_048_576
_MIN_PARAMETER_BYTES: int = 256


@dataclass(frozen=True, slots=True)
class IsolateAnalysisConfig:
    """Immutable configuration limits for the analysis boundary."""

    max_input_handles: int = _DEFAULT_MAX_INPUT_HANDLES
    enforce_staged_output_schema: bool = _DEFAULT_ENFORCE_SCHEMA
    max_parameter_bytes: int = _DEFAULT_MAX_PARAMETER_BYTES

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> IsolateAnalysisConfig:
        """Parse and validate configuration dictionary against allowed schema keys.

        Args:
            data: Raw configuration dictionary or None.

        Returns:
            Validated IsolateAnalysisConfig instance.

        Raises:
            TypeError: If data is not a mapping.
            ValueError: If unknown keys or invalid numeric values are provided.
        """
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise TypeError("Isolate Analysis configuration must be a mapping")

        unknown = set(data) - SPEC.config_keys
        if unknown:
            joined = ", ".join(sorted(unknown))
            msg = f"Unknown Isolate Analysis configuration keys: {joined}"
            raise ValueError(msg)

        max_handles = data.get("max_input_handles", _DEFAULT_MAX_INPUT_HANDLES)
        if (
            not isinstance(max_handles, int)
            or isinstance(max_handles, bool)
            or max_handles <= 0
        ):
            raise ValueError("max_input_handles must be a positive integer")

        enforce_schema = data.get(
            "enforce_staged_output_schema", _DEFAULT_ENFORCE_SCHEMA
        )
        if not isinstance(enforce_schema, bool):
            raise TypeError("enforce_staged_output_schema must be boolean")

        param_bytes = data.get("max_parameter_bytes", _DEFAULT_MAX_PARAMETER_BYTES)
        if (
            not isinstance(param_bytes, int)
            or isinstance(param_bytes, bool)
            or param_bytes < _MIN_PARAMETER_BYTES
        ):
            msg = (
                f"max_parameter_bytes must be an integer of at least "
                f"{_MIN_PARAMETER_BYTES}"
            )
            raise ValueError(msg)

        return cls(
            max_input_handles=max_handles,
            enforce_staged_output_schema=enforce_schema,
            max_parameter_bytes=param_bytes,
        )
