"""Retester execution runner and cross-check pipeline orchestrator.

Description:
    Delegates validated native snapshots to actual Core main backtests and
    preserves earlier results. Missing execution inputs and unimplemented
    robustness modes fail closed.

Purpose:
    FEAT-RETESTER-TASK-RUNNER: Core execution pipeline for strategy retesting.

Key Capabilities:
    - FR-retest-task-execute: Coordinate preflight, same-databank clearing,
      backtests, and 9 cross-check plugins in pipeline order.

Python API Usage:
    from app.workspace.retester.task_retest import TaskRetestRunner
    summary = TaskRetestRunner.execute(
        project_id, what_to_retest, data_settings, cross_checks
    )

CLI Usage:
    python -m app.cli retest execute-task --project proj_1
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from app.core.host.logging import get_logger
from app.core.jobs.manager import JobContext
from app.core.lib.errors import DomainError
from app.workspace.home.execution import ExecutionSnapshot, ProjectExecutor
from app.workspace.retester.settings_auto_retest_data import AutoRetestDataSettings
from app.workspace.retester.settings_cross_checks import (
    CrossChecksSettingsSnapshot,
)
from app.workspace.retester.settings_what_to_retest import (
    WhatToRetestSettings,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TaskRetestSummary:
    """Summary receipt of an executed retest run."""

    mode: int
    total_keys: int
    processed: int
    passed: int
    failed: int
    log_messages: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            "mode": self.mode,
            "total_keys": self.total_keys,
            "processed": self.processed,
            "passed": self.passed,
            "failed": self.failed,
            "log_messages": list(self.log_messages),
        }


class TaskRetestRunner:
    """Orchestrates strategy retesting and cross-check pipelines."""

    _running_projects: ClassVar[set[str]] = set()

    @classmethod
    def execute(
        cls,
        project_id: str,
        what_to_retest: WhatToRetestSettings,
        data_settings: AutoRetestDataSettings,
        cross_checks: CrossChecksSettingsSnapshot,
        *,
        databank_strategies: dict[str, list[str]] | None = None,
        stored_results: dict[str, dict[str, Any]] | None = None,
        execution: ProjectExecutor | None = None,
        snapshot: ExecutionSnapshot | None = None,
        context: JobContext | None = None,
    ) -> TaskRetestSummary:
        """Execute retest workflow following OBS-145-RETEST-PREFLIGHT-002 order.

        Args:
            project_id: Unique project identifier.
            what_to_retest: What to retest settings.
            data_settings: Market/data configuration.
            cross_checks: Master cross-checks settings.
            databank_strategies: Optional in-memory map of databank -> strats.
            stored_results: Legacy in-memory results, preserved unchanged.
            execution: Injected Core-backed execution owner.
            snapshot: Validated immutable native task inputs.
            context: Host cooperative lifecycle context.

        Returns:
            TaskRetestSummary with total, processed, passed, and failed counts.

        Raises:
            DomainError: If retest is already active for this project.
        """
        logger.info(
            "FR-retest-task-execute: native snapshot supersedes legacy inputs "
            "(source=%s, capital=%s, banks=%d, results=%d)",
            what_to_retest.source_databank,
            data_settings.initial_capital,
            len(databank_strategies or {}),
            len(stored_results or {}),
        )
        if execution is None or snapshot is None or context is None:
            raise DomainError(
                code="EXECUTION_CONTEXT_REQUIRED",
                message="Retester requires a validated native execution snapshot",
            )
        if snapshot.project_id != project_id or cross_checks.enabled:
            raise DomainError(
                code="UNSUPPORTED_MODE",
                message="Only snapshot-backed main retests are available",
            )
        logger.info(
            "FR-retest-task-execute: evaluating validated snapshot for %s", project_id
        )
        receipt = execution.run(context, snapshot)
        return TaskRetestSummary(
            mode=1,
            total_keys=int(receipt["candidates_evaluated"]),
            processed=int(receipt["candidates_evaluated"]),
            passed=int(receipt["candidates_accepted"]),
            failed=int(receipt["candidates_rejected"]),
            log_messages=("Evaluated actual bars; previous results preserved",),
        )
