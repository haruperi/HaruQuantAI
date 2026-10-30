"""Delete file settings serialization and parsing.

Description:
    Provides serialization and deserialization helpers for task "Delete File"
    automation settings. Configures file path and missing-file policies.

Purpose:
    FEAT-TASK-MANAGER: Support DeleteFile task configuration workflows.

Key Capabilities:
    - FR-settings-delete-file: Read and write DeleteFile configuration
      dictionaries with default fallback and non-destructive target updates.

Python API Usage:
    ```python
    from app.workspace.task_manager.settings.delete_file import (
        DeleteFileConfig,
        DeleteFileSettings,
    )

    config = DeleteFileSettings.load({"filePath": "/tmp/test.csv"})
    target = {}
    DeleteFileSettings.write(target, config)
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

__all__ = ["DeleteFileConfig", "DeleteFileSettings"]


@dataclass(frozen=True, slots=True)
class DeleteFileConfig:
    """Immutable configuration for Delete File task."""

    file_path: str = ""
    fail_if_missing: bool = False


class DeleteFileSettings:
    """Serialization and deserialization helper for DeleteFile configuration."""

    @staticmethod
    def load(
        payload: Mapping[str, Any] | None,
        current: DeleteFileConfig | None = None,
    ) -> DeleteFileConfig:
        """Load configuration from a payload mapping."""
        if payload is None:
            return current if current is not None else DeleteFileConfig()

        base = current or DeleteFileConfig()
        path = str(
            payload.get("file_path")
            or payload.get("filePath")
            or payload.get("file")
            or base.file_path
        )
        fail = bool(
            payload.get("fail_if_missing")
            if "fail_if_missing" in payload
            else payload.get("failIfMissing", base.fail_if_missing)
        )

        return DeleteFileConfig(file_path=path, fail_if_missing=fail)

    @staticmethod
    def write(target: dict[str, Any], config: DeleteFileConfig) -> None:
        """Write configuration to target dictionary, preserving other keys."""
        target["filePath"] = config.file_path
        target["failIfMissing"] = config.fail_if_missing

    @staticmethod
    def to_dict(config: DeleteFileConfig) -> dict[str, Any]:
        """Convert configuration to dictionary representation."""
        return asdict(config)
