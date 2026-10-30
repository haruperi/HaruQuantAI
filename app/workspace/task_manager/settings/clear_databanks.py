"""Clear databanks settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Clear Databanks"
    automation settings. Supports target databank lists (or 'all') and reset view flags.

Purpose:
    FEAT-TASK-MANAGER: Support ClearDatabanks task settings serialization.

Key Capabilities:
    - FR-settings-clear-databanks: Read and write ClearDatabanks configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.clear_databanks import (
        ClearDatabanksConfig,
        ClearDatabanksSettings,
    )

    config = ClearDatabanksSettings.load({"databanks": ["Results", "Portfolio"]})
    target = {}
    ClearDatabanksSettings.write(target, config)
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

__all__ = ["ClearDatabanksConfig", "ClearDatabanksSettings"]


@dataclass(frozen=True, slots=True)
class ClearDatabanksConfig:
    """Immutable configuration for Clear Databanks task."""

    databanks: list[str] = field(default_factory=lambda: ["Results"])
    reset_view: bool = True


class ClearDatabanksSettings:
    """Serialization and deserialization helper for ClearDatabanks configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: ClearDatabanksConfig | None = None,
    ) -> ClearDatabanksConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else ClearDatabanksConfig()

        base = current or ClearDatabanksConfig()
        raw_banks = payload.get("databanks", base.databanks)
        if isinstance(raw_banks, Sequence) and not isinstance(raw_banks, (str, bytes)):
            banks = [str(b) for b in raw_banks]
        elif isinstance(raw_banks, str):
            banks = [raw_banks]
        else:
            banks = list(base.databanks)

        reset = bool(
            payload.get("reset_view")
            if "reset_view" in payload
            else payload.get("resetView", base.reset_view)
        )

        return ClearDatabanksConfig(databanks=banks, reset_view=reset)

    @staticmethod
    def write(target: dict[str, Any], config: ClearDatabanksConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["databanks"] = list(config.databanks)
        target["resetView"] = config.reset_view

    @staticmethod
    def to_dict(config: ClearDatabanksConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
