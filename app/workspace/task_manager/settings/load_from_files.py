"""Load from files settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Load from files"
    automation settings. Configures directory path, pattern, and destination databank.

Purpose:
    FEAT-TASK-MANAGER: Support strategy loading task configuration workflows.

Key Capabilities:
    - FR-settings-load-from-files: Read and write LoadFromFiles configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.load_from_files import (
        LoadFromFilesConfig,
        LoadFromFilesSettings,
    )

    config = LoadFromFilesSettings.load({"directoryPath": "strategies/"})
    target = {}
    LoadFromFilesSettings.write(target, config)
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

__all__ = ["LoadFromFilesConfig", "LoadFromFilesSettings"]


@dataclass(frozen=True, slots=True)
class LoadFromFilesConfig:
    """Immutable configuration for Load from files task."""

    directory_path: str = ""
    file_pattern: str = "*.sqx"
    target_databank: str = "Results"
    clear_before_load: bool = False


class LoadFromFilesSettings:
    """Serialization and deserialization helper for LoadFromFiles configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: LoadFromFilesConfig | None = None,
    ) -> LoadFromFilesConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else LoadFromFilesConfig()

        base = current or LoadFromFilesConfig()
        dir_path = str(
            payload.get("directory_path")
            or payload.get("directoryPath")
            or payload.get("directory")
            or base.directory_path
        )
        pattern = str(
            payload.get("file_pattern")
            or payload.get("filePattern")
            or base.file_pattern
        )
        bank = str(
            payload.get("target_databank")
            or payload.get("targetDatabank")
            or base.target_databank
        )
        clear = bool(
            payload.get("clear_before_load")
            if "clear_before_load" in payload
            else payload.get("clearBeforeLoad", base.clear_before_load)
        )

        return LoadFromFilesConfig(
            directory_path=dir_path,
            file_pattern=pattern,
            target_databank=bank,
            clear_before_load=clear,
        )

    @staticmethod
    def write(target: dict[str, Any], config: LoadFromFilesConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["directoryPath"] = config.directory_path
        target["filePattern"] = config.file_pattern
        target["targetDatabank"] = config.target_databank
        target["clearBeforeLoad"] = config.clear_before_load

    @staticmethod
    def to_dict(config: LoadFromFilesConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
