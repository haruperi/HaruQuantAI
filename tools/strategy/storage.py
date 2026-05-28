"""Storage helpers and official AI tools for versioned strategy source files.

This module intentionally does not dynamically import user code. Dynamic code
loading should be handled only by a sandboxed and approval-gated workflow.

Exported AI Tools:
    - save_strategy_source_file

Classes:
    - StoredStrategyRecord
    - StrategyStorage
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.utils import logger
from tools.utils.standard import TOOL_RISK_LEVEL_MEDIUM, execute_tool_boundary

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "strategy"
TOOL_RISK_LEVEL = "medium"
REQUIRES_APPROVAL = False
READ_ONLY = False
WRITES_FILE = True
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


@dataclass(frozen=True)
class StoredStrategyRecord:
    """Metadata describing a saved strategy source snapshot."""

    strategy_name: str
    version: str
    path: str
    metadata_path: str
    created_at: str
    parameters: dict[str, Any]


class StrategyStorage:
    """Manage safe local file snapshots for strategy source code."""

    def __init__(self, base_dir: str | Path) -> None:
        """Initialize storage with an explicit base directory."""
        self.base_dir = Path(base_dir).expanduser().resolve()

    def save_strategy_source(
        self,
        *,
        strategy_name: str,
        version: str,
        source_code: str,
        parameters: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> StoredStrategyRecord:
        """Save strategy source and metadata without importing or executing it."""
        safe_name = self._safe_part(strategy_name, "strategy_name")
        safe_version = self._safe_part(version, "version")
        if not source_code.strip():
            raise ValueError("source_code cannot be empty.")
        target_dir = self.base_dir / safe_name / safe_version
        source_path = target_dir / "strategy.py"
        metadata_path = target_dir / "metadata.json"
        if source_path.exists() and not overwrite:
            raise FileExistsError(
                "strategy source already exists; set overwrite=True to replace it."
            )
        target_dir.mkdir(parents=True, exist_ok=True)
        created_at = datetime.now(tz=UTC).isoformat()
        source_path.write_text(source_code, encoding="utf-8")
        record = StoredStrategyRecord(
            strategy_name=safe_name,
            version=safe_version,
            path=str(source_path),
            metadata_path=str(metadata_path),
            created_at=created_at,
            parameters=dict(parameters or {}),
        )
        metadata_path.write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")
        logger.info(
            "strategy source saved | strategy=%s | version=%s", safe_name, safe_version
        )
        return record

    def list_strategy_versions(self, strategy_name: str) -> list[str]:
        """List saved versions for a strategy name."""
        safe_name = self._safe_part(strategy_name, "strategy_name")
        target = self.base_dir / safe_name
        if not target.exists():
            return []
        return sorted(path.name for path in target.iterdir() if path.is_dir())

    @staticmethod
    def _safe_part(value: str, field_name: str) -> str:
        """Return a safe single path component for strategy storage paths."""
        part = str(value or "").strip()
        if not part:
            raise ValueError(f"{field_name} is required.")
        if any(char in part for char in ("/", "\\", "..")):
            raise ValueError(f"{field_name} contains unsafe path characters.")
        return part


def save_strategy_source_file(
    *,
    base_dir: str,
    strategy_name: str,
    version: str,
    source_code: str,
    parameters: dict[str, Any] | None = None,
    overwrite: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Save strategy source code as a versioned local snapshot.

    Use this AI tool only for local artifact persistence. It writes files, so it
    is classified as medium risk. It never imports, executes, deletes, or zips
    strategy code.

    Args:
        base_dir: Base directory where strategy snapshots should be written.
        strategy_name: Strategy name used as a safe path component.
        version: Version string used as a safe path component.
        source_code: Strategy source code to write to ``strategy.py``.
        parameters: Optional metadata parameters to store with the snapshot.
        overwrite: Whether an existing snapshot can be replaced.
        request_id: Optional workflow/request ID for tracing.

    Returns:
        Standard HaruQuant tool response containing saved artifact metadata.
    """

    def operation() -> dict[str, Any]:
        if not base_dir:
            raise ValueError("base_dir is required.")
        storage = StrategyStorage(Path(base_dir))
        record = storage.save_strategy_source(
            strategy_name=strategy_name,
            version=version,
            source_code=source_code,
            parameters=parameters,
            overwrite=overwrite,
        )
        return record.__dict__

    return execute_tool_boundary(
        tool_name="save_strategy_source_file",
        request_id=request_id,
        operation=operation,
        success_message="Strategy source file saved.",
        tool_risk_level=TOOL_RISK_LEVEL_MEDIUM,
        read_only=False,
        writes_file=True,
    )
