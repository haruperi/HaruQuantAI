"""Apply mass config settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Apply Mass Config"
    automation settings. Supports target databank selection, config templates,
    and parameter overrides.

Purpose:
    FEAT-TASK-MANAGER: Support task automation settings for mass configuration.

Key Capabilities:
    - FR-settings-apply-mass-config: Read and write ApplyMassConfig configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.apply_mass_config import (
        ApplyMassConfigConfig,
        ApplyMassConfigSettings,
    )

    config = ApplyMassConfigSettings.load({"targetDatabank": "Results"})
    target = {}
    ApplyMassConfigSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["ApplyMassConfigConfig", "ApplyMassConfigSettings"]


@dataclass(frozen=True, slots=True)
class ApplyMassConfigConfig:
    """Immutable configuration for task ApplyMassConfig setting."""

    target_databank: str = "Results"
    config_type: str = "default"
    parameters: dict[str, Any] = field(default_factory=dict)


class ApplyMassConfigSettings:
    """Serialization and deserialization helper for ApplyMassConfig configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: ApplyMassConfigConfig | None = None,
    ) -> ApplyMassConfigConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else ApplyMassConfigConfig()

        base = current or ApplyMassConfigConfig()
        target_bank = str(
            payload.get("target_databank")
            or payload.get("targetDatabank")
            or base.target_databank
        )
        cfg_type = str(
            payload.get("config_type") or payload.get("configType") or base.config_type
        )
        params_raw = payload.get("parameters", base.parameters)
        params = (
            dict(params_raw)
            if isinstance(params_raw, Mapping)
            else dict(base.parameters)
        )

        return ApplyMassConfigConfig(
            target_databank=target_bank,
            config_type=cfg_type,
            parameters=params,
        )

    @staticmethod
    def write(target: dict[str, Any], config: ApplyMassConfigConfig) -> None:
        """Write configuration to a target dictionary, preserving other keys."""
        target["targetDatabank"] = config.target_databank
        target["configType"] = config.config_type
        target["parameters"] = dict(config.parameters)

    @staticmethod
    def to_dict(config: ApplyMassConfigConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
