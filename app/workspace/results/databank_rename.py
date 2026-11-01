"""Batch strategy rename service for databank results.

Description:
    Implements DatabankRenameService executing sequential strategy display
    name renaming over selected databank rows via ServletRenameTool while
    avoiding naming collisions.

Purpose:
    FEAT-RESULTS-DATABANK-RENAME: Batch strategy rename service.

Key Capabilities:
    - FR-results-databank-rename: Format and apply batch strategy renames.

Python API Usage:
    from app.workspace.results.databank_rename import (
        DatabankRenameRequest,
        DatabankRenameService,
    )
    service = DatabankRenameService()
    req = DatabankRenameRequest("p1", "Results", ("s1", "s2"))
    resp = service.rename_strategies(req)

CLI Usage:
    python -m app.cli results databank-rename --project-id p1 --databank Results
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.responses import StandardResponse
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore
from app.workspace.results.app_results import wrap_response
from app.workspace.results.servlet_rename_tool import (
    RenamePatternSpec,
    ServletRenameTool,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class DatabankRenameRequest:
    """Request specification for renaming strategies in a databank."""

    project_id: str
    databank_name: str
    strategy_ids: tuple[str, ...]
    prefix: str = "Strategy "
    start_number: int = 1
    digits: int = 1
    suffix: str = ""
    separator: str = "."

    def to_dict(self) -> dict[str, Any]:
        """Convert rename request to dictionary."""
        return {
            "project_id": self.project_id,
            "databank_name": self.databank_name,
            "strategy_ids": list(self.strategy_ids),
            "prefix": self.prefix,
            "start_number": self.start_number,
            "digits": self.digits,
            "suffix": self.suffix,
            "separator": self.separator,
        }


@dataclass(frozen=True, slots=True)
class DatabankRenameReceipt:
    """Receipt detailing results of batch strategy rename."""

    renamed: tuple[tuple[str, str], ...]
    skipped: tuple[tuple[str, str], ...]
    revision: int

    def to_dict(self) -> dict[str, Any]:
        """Convert rename receipt to dictionary."""
        return {
            "renamed": [list(item) for item in self.renamed],
            "skipped": [list(item) for item in self.skipped],
            "revision": self.revision,
        }


class DatabankRenameService:
    """Batch strategy renaming service."""

    def __init__(self, store: ResultStore | None = None) -> None:
        """Initialize service with optional ResultStore."""
        self.store = store
        self._in_memory_results: dict[str, RunResult] = {}
        self._revision = 1

    def register_in_memory_result(self, result: RunResult) -> None:
        """Register in-memory test result."""
        self._in_memory_results[result.strategy_id] = result

    def rename_strategies(
        self, request: DatabankRenameRequest
    ) -> StandardResponse[DatabankRenameReceipt]:
        """Execute deterministic batch rename of strategies in target databank."""
        logger.info(
            "FR-results-databank-rename: renaming %d strategies in databank %s",
            len(request.strategy_ids),
            request.databank_name,
        )

        spec = RenamePatternSpec(
            prefix=request.prefix,
            start_number=request.start_number,
            digits=request.digits,
            suffix=request.suffix,
            separator=request.separator,
        )

        valid_ids: list[str] = []
        skipped: list[tuple[str, str]] = []
        existing_names: set[str] = set()

        # Collect existing unselected names and partition candidates
        if self._in_memory_results:
            for sid, r in self._in_memory_results.items():
                if sid not in request.strategy_ids:
                    existing_names.add(r.strategy_name)

            for sid in request.strategy_ids:
                if sid in self._in_memory_results:
                    valid_ids.append(sid)
                else:
                    skipped.append((sid, "NOT_FOUND"))
        else:
            # When working with abstract IDs
            valid_ids = list(request.strategy_ids)

        formatted_pairs = ServletRenameTool.format_names(
            valid_ids, spec, existing_names=existing_names
        )

        # Apply renames to in-memory store
        for sid, new_name in formatted_pairs:
            if sid in self._in_memory_results:
                curr = self._in_memory_results[sid]
                updated = replace(curr, strategy_name=new_name)
                self._in_memory_results[sid] = updated
                if self.store is not None:
                    self.store.save_result(request.databank_name, updated)

        self._revision += 1
        receipt = DatabankRenameReceipt(
            renamed=formatted_pairs,
            skipped=tuple(skipped),
            revision=self._revision,
        )

        logger.info(
            "FR-results-databank-rename: renamed %d strategies, skipped %d (rev=%d)",
            len(formatted_pairs),
            len(skipped),
            self._revision,
        )

        return wrap_response(
            request_id="req_databank_rename",
            data=receipt,
            json_payload=receipt.to_dict(),
            revision=self._revision,
        )
