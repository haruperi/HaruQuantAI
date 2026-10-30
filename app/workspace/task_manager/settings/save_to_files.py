"""Save to files settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Save to files"
    automation settings. Configures source databank, output folder, and file formats.

Purpose:
    FEAT-TASK-MANAGER: Support strategy file export task configuration workflows.

Key Capabilities:
    - FR-settings-save-to-files: Read and write SaveToFiles configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.save_to_files import (
        SaveToFilesConfig,
        SaveToFilesSettings,
    )

    config = SaveToFilesSettings.load({"outputDirectory": "exports/"})
    target = {}
    SaveToFilesSettings.write(target, config)
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

__all__ = ["SaveToFilesConfig", "SaveToFilesSettings"]


@dataclass(frozen=True, slots=True)
class SaveToFilesConfig:
    """Immutable configuration for Save to files task."""

    source_databank: str = "Results"
    output_directory: str = ""
    file_format: str = "sqx"
    save_all: bool = True


class SaveToFilesSettings:
    """Serialization and deserialization helper for SaveToFiles configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: SaveToFilesConfig | None = None,
    ) -> SaveToFilesConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else SaveToFilesConfig()

        base = current or SaveToFilesConfig()
        src = str(
            payload.get("source_databank")
            or payload.get("sourceDatabank")
            or base.source_databank
        )
        out_dir = str(
            payload.get("output_directory")
            or payload.get("outputDirectory")
            or payload.get("directory")
            or base.output_directory
        )
        fmt = str(
            payload.get("file_format") or payload.get("fileFormat") or base.file_format
        )
        save_all = bool(
            payload.get("save_all")
            if "save_all" in payload
            else payload.get("saveAll", base.save_all)
        )

        return SaveToFilesConfig(
            source_databank=src,
            output_directory=out_dir,
            file_format=fmt,
            save_all=save_all,
        )

    @staticmethod
    def write(target: dict[str, Any], config: SaveToFilesConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["sourceDatabank"] = config.source_databank
        target["outputDirectory"] = config.output_directory
        target["fileFormat"] = config.file_format
        target["saveAll"] = config.save_all

    @staticmethod
    def to_dict(config: SaveToFilesConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
