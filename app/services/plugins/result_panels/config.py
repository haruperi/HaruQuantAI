"""Strict configuration for plugin result panels."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.services.plugins.result_panels.manifest import SPEC

if TYPE_CHECKING:
    from app.contracts.plugins.models import PanelBridgeOperation

_DEFAULT_ALLOWED_OPERATIONS: tuple[PanelBridgeOperation, ...] = (
    "READ_RESULTS",
    "QUERY_DATA",
    "RECEIVE_MESSAGES",
)
_VALID_OPERATIONS: frozenset[str] = frozenset(
    {"READ_RESULTS", "QUERY_DATA", "RECEIVE_MESSAGES"}
)
_DEFAULT_ENFORCE_SECURE_ORIGIN: bool = True
_DEFAULT_MAX_PANELS: int = 100


@dataclass(frozen=True, slots=True)
class ResultPanelsConfig:
    """Immutable configuration limits and rules for result panels."""

    allowed_bridge_operations: tuple[PanelBridgeOperation, ...] = (
        _DEFAULT_ALLOWED_OPERATIONS
    )
    enforce_secure_content_source: bool = _DEFAULT_ENFORCE_SECURE_ORIGIN
    max_panels_per_query: int = _DEFAULT_MAX_PANELS

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None = None) -> ResultPanelsConfig:
        """Parse and validate configuration dictionary against allowed schema keys.

        Args:
            data: Raw configuration dictionary or None.

        Returns:
            Validated ResultPanelsConfig instance.

        Raises:
            TypeError: If data or nested values have invalid types.
            ValueError: If unknown keys or invalid values are provided.
        """
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise TypeError("Result Panels configuration must be a mapping")

        unknown = set(data) - SPEC.config_keys
        if unknown:
            joined = ", ".join(sorted(unknown))
            msg = f"Unknown Result Panels configuration keys: {joined}"
            raise ValueError(msg)

        allowed_ops_raw = data.get(
            "allowed_bridge_operations", _DEFAULT_ALLOWED_OPERATIONS
        )
        if not isinstance(allowed_ops_raw, (list, tuple)):
            raise TypeError("allowed_bridge_operations must be a list or tuple")

        parsed_ops: list[PanelBridgeOperation] = []
        for op in allowed_ops_raw:
            if not isinstance(op, str):
                raise TypeError("bridge operation names must be strings")
            if op not in _VALID_OPERATIONS:
                msg = f"Invalid bridge operation: '{op}'"
                raise ValueError(msg)
            parsed_ops.append(op)  # type: ignore[arg-type]

        enforce_secure = data.get(
            "enforce_secure_content_source", _DEFAULT_ENFORCE_SECURE_ORIGIN
        )
        if not isinstance(enforce_secure, bool):
            raise TypeError("enforce_secure_content_source must be boolean")

        max_panels = data.get("max_panels_per_query", _DEFAULT_MAX_PANELS)
        if (
            not isinstance(max_panels, int)
            or isinstance(max_panels, bool)
            or max_panels <= 0
        ):
            raise ValueError("max_panels_per_query must be a positive integer")

        return cls(
            allowed_bridge_operations=tuple(parsed_ops),
            enforce_secure_content_source=enforce_secure,
            max_panels_per_query=max_panels,
        )
