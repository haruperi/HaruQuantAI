"""Automatic retest settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Automatic Retest"
    automation settings. Configures databank targeting, retest profiles, and
    result filtering.

Purpose:
    FEAT-TASK-MANAGER: Support automated strategy retest configuration workflows.

Key Capabilities:
    - FR-settings-auto-retest: Read and write AutoRetest configuration dictionaries
      with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.automatic_retest import (
        AutoRetestConfig,
        AutoRetestSettings,
    )

    config = AutoRetestSettings.load({"databank": "Results"})
    target = {}
    AutoRetestSettings.write(target, config)
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/test_settings.py -q
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["AutoRetestConfig", "AutoRetestSettings"]


@dataclass(frozen=True, slots=True)
class AutoRetestConfig:
    """Immutable configuration for Automatic Retest task."""

    databank: str = "Results"
    retest_profile: str = "Default"
    filter_results: bool = True
    save_to_target_databank: bool = False
    target_databank: str = ""


class AutoRetestSettings:
    """Serialization and deserialization helper for AutoRetest configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: AutoRetestConfig | None = None,
    ) -> AutoRetestConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else AutoRetestConfig()

        base = current or AutoRetestConfig()
        bank = str(payload.get("databank") or base.databank)
        profile = str(
            payload.get("retest_profile")
            or payload.get("retestProfile")
            or base.retest_profile
        )
        filter_res = bool(
            payload.get("filter_results")
            if "filter_results" in payload
            else payload.get("filterResults", base.filter_results)
        )
        save_target = bool(
            payload.get("save_to_target_databank")
            if "save_to_target_databank" in payload
            else payload.get("saveToTargetDatabank", base.save_to_target_databank)
        )
        target_bank = str(
            payload.get("target_databank")
            or payload.get("targetDatabank")
            or base.target_databank
        )

        return AutoRetestConfig(
            databank=bank,
            retest_profile=profile,
            filter_results=filter_res,
            save_to_target_databank=save_target,
            target_databank=target_bank,
        )

    @staticmethod
    def write(target: dict[str, Any], config: AutoRetestConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["databank"] = config.databank
        target["retestProfile"] = config.retest_profile
        target["filterResults"] = config.filter_results
        target["saveToTargetDatabank"] = config.save_to_target_databank
        target["targetDatabank"] = config.target_databank

    @staticmethod
    def to_dict(config: AutoRetestConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
