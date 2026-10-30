"""Custom analysis settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Custom Analysis"
    automation settings. Configures custom analysis snippet names, target databank,
    and parameter mappings.

Purpose:
    FEAT-TASK-MANAGER: Support custom analysis task configuration workflows.

Key Capabilities:
    - FR-settings-custom-analysis: Read and write CustomAnalysis configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.custom_analysis import (
        CustomAnalysisConfig,
        CustomAnalysisSettings,
    )

    config = CustomAnalysisSettings.load({"snippetName": "monte_carlo"})
    target = {}
    CustomAnalysisSettings.write(target, config)
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

__all__ = ["CustomAnalysisConfig", "CustomAnalysisSettings"]


@dataclass(frozen=True, slots=True)
class CustomAnalysisConfig:
    """Immutable configuration for Custom Analysis task."""

    snippet_name: str = ""
    target_databank: str = "Results"
    parameters: dict[str, Any] = field(default_factory=dict)


class CustomAnalysisSettings:
    """Serialization and deserialization helper for CustomAnalysis configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: CustomAnalysisConfig | None = None,
    ) -> CustomAnalysisConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else CustomAnalysisConfig()

        base = current or CustomAnalysisConfig()
        snippet = str(
            payload.get("snippet_name")
            or payload.get("snippetName")
            or base.snippet_name
        )
        bank = str(
            payload.get("target_databank")
            or payload.get("targetDatabank")
            or base.target_databank
        )
        params_raw = payload.get("parameters", base.parameters)
        params = (
            dict(params_raw)
            if isinstance(params_raw, Mapping)
            else dict(base.parameters)
        )

        return CustomAnalysisConfig(
            snippet_name=snippet,
            target_databank=bank,
            parameters=params,
        )

    @staticmethod
    def write(target: dict[str, Any], config: CustomAnalysisConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["snippetName"] = config.snippet_name
        target["targetDatabank"] = config.target_databank
        target["parameters"] = dict(config.parameters)

    @staticmethod
    def to_dict(config: CustomAnalysisConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
