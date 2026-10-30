"""Filtering settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Filtering"
    automation settings. Configures source databank, target databank, and filters.

Purpose:
    FEAT-TASK-MANAGER: Support strategy filtering task configuration workflows.

Key Capabilities:
    - FR-settings-filtering: Read and write Filtering configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.filtering import (
        FilteringConfig,
        FilteringSettings,
    )

    config = FilteringSettings.load({"sourceDatabank": "Results"})
    target = {}
    FilteringSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["FilteringCondition", "FilteringConfig", "FilteringSettings"]


@dataclass(frozen=True, slots=True)
class FilteringCondition:
    """Single filtering condition criterion."""

    metric: str = "NetProfit"
    comparator: str = ">"
    value: float = 0.0


@dataclass(frozen=True, slots=True)
class FilteringConfig:
    """Immutable configuration for Filtering task."""

    source_databank: str = "Results"
    target_databank: str = "Filtered"
    filter_conditions: list[FilteringCondition] = field(default_factory=list)


class FilteringSettings:
    """Serialization and deserialization helper for Filtering configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: FilteringConfig | None = None,
    ) -> FilteringConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else FilteringConfig()

        base = current or FilteringConfig()
        src = str(
            payload.get("source_databank")
            or payload.get("sourceDatabank")
            or base.source_databank
        )
        dst = str(
            payload.get("target_databank")
            or payload.get("targetDatabank")
            or base.target_databank
        )

        conds: list[FilteringCondition] = []
        raw_conds = payload.get("filter_conditions") or payload.get("filterConditions")
        if isinstance(raw_conds, Sequence) and not isinstance(raw_conds, (str, bytes)):
            conds.extend(
                FilteringCondition(
                    metric=str(c.get("metric", "NetProfit")),
                    comparator=str(c.get("comparator", ">")),
                    value=float(c.get("value", 0.0)),
                )
                for c in raw_conds
                if isinstance(c, Mapping)
            )
        else:
            conds = list(base.filter_conditions)

        return FilteringConfig(
            source_databank=src,
            target_databank=dst,
            filter_conditions=conds,
        )

    @staticmethod
    def write(target: dict[str, Any], config: FilteringConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["sourceDatabank"] = config.source_databank
        target["targetDatabank"] = config.target_databank
        target["filterConditions"] = [asdict(c) for c in config.filter_conditions]

    @staticmethod
    def to_dict(config: FilteringConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
