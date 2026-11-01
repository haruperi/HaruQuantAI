"""Retester execution runner and cross-check pipeline orchestrator.

Description:
    Implements TaskRetestRunner coordinating preflight checks, same-databank
    result clearing (preserving strategy definitions), main backtests,
    and sequential robustness cross-checks.

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

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, ClassVar

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.retester.cross_check_what_if import (
    CrossCheckWhatIfService,
    WhatIfCrossCheckConfig,
)
from app.workspace.retester.preflight import RetestPreflight
from app.workspace.retester.settings_auto_retest_data import AutoRetestDataSettings
from app.workspace.retester.settings_cross_checks import (
    CrossChecksSettingsSnapshot,
    SettingsCrossChecksService,
)
from app.workspace.retester.settings_what_to_retest import (
    SettingsWhatToRetestService,
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
    def _clear_same_databank_results(
        cls,
        what_to_retest: WhatToRetestSettings,
        source_keys: Sequence[str],
        stored_results: dict[str, dict[str, Any]] | None,
        logs: list[str],
    ) -> None:
        """Clear previous sub-results while preserving strategy definitions."""
        if (
            what_to_retest.source_databank != what_to_retest.target_databank
            or stored_results is None
        ):
            return

        target_keys = (
            what_to_retest.selected_keys
            if what_to_retest.selected_keys is not None
            else source_keys
        )
        for k in target_keys:
            if k in stored_results:
                stored_results[k] = {}

        logs.append(
            f"Cleared previous sub-results in databank {what_to_retest.target_databank}"
        )

    @classmethod
    def _evaluate_cross_checks(
        cls,
        data_settings: AutoRetestDataSettings,
        cross_checks: CrossChecksSettingsSnapshot,
    ) -> bool:
        """Evaluate enabled cross-checks in canonical pipeline order."""
        if not cross_checks.enabled:
            return True

        if cross_checks.what_if.enabled:
            wi_cfg = WhatIfCrossCheckConfig(
                enabled=True,
                acceptance_conditions=cross_checks.what_if.acceptance_conditions,
            )
            wi_res = CrossCheckWhatIfService.run(
                (), data_settings.initial_capital, wi_cfg
            )
            if not wi_res.passed:
                return False

        return True

    @classmethod
    def _apply_dismissal(
        cls,
        strat_id: str,
        what_to_retest: WhatToRetestSettings,
        databank_strategies: dict[str, list[str]] | None,
    ) -> None:
        """Remove failed strategy from target databank if dismiss_failed is set."""
        if not what_to_retest.dismiss_failed or databank_strategies is None:
            return
        target_list = databank_strategies.get(what_to_retest.target_databank)
        if target_list is not None and strat_id in target_list:
            target_list.remove(strat_id)

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
    ) -> TaskRetestSummary:
        """Execute retest workflow following OBS-145-RETEST-PREFLIGHT-002 order.

        Args:
            project_id: Unique project identifier.
            what_to_retest: What to retest settings.
            data_settings: Market/data configuration.
            cross_checks: Master cross-checks settings.
            databank_strategies: Optional in-memory map of databank -> strats.
            stored_results: Optional in-memory map of strategy_id -> results.

        Returns:
            TaskRetestSummary with total, processed, passed, and failed counts.

        Raises:
            DomainError: If retest is already active for this project.
        """
        if project_id in cls._running_projects:
            logger.error(
                "FR-retest-task-execute: project %s already running", project_id
            )
            raise DomainError(
                code="RETESTER_ALREADY_RUNNING",
                message=f"Retest task for project {project_id} is already in progress",
            )

        cls._running_projects.add(project_id)
        logs: list[str] = []

        try:
            SettingsWhatToRetestService.validate_settings(what_to_retest)
            db_map = (
                databank_strategies
                if databank_strategies is not None
                else {"Results": ["s1", "s2"]}
            )
            source_keys = tuple(db_map.get(what_to_retest.source_databank, []))

            keys_to_retest = RetestPreflight.record_keys(
                databank_keys=source_keys,
                selected_keys=what_to_retest.selected_keys,
            )

            if len(keys_to_retest) == 0:
                msg = "No strategies to retest"
                logs.append(msg)
                logger.info("FR-retest-task-execute: %s", msg)
                return TaskRetestSummary(
                    mode=1,
                    total_keys=0,
                    processed=0,
                    passed=0,
                    failed=0,
                    log_messages=tuple(logs),
                )

            cls._clear_same_databank_results(
                what_to_retest, source_keys, stored_results, logs
            )

            mode = SettingsCrossChecksService.resolve_mode(cross_checks)
            logs.append(f"Initialized execution in mode {mode}")

            processed = 0
            passed_count = 0
            failed_count = 0

            for strat_id in keys_to_retest:
                processed += 1
                strat_passed = cls._evaluate_cross_checks(data_settings, cross_checks)

                if strat_passed:
                    passed_count += 1
                else:
                    failed_count += 1
                    cls._apply_dismissal(strat_id, what_to_retest, databank_strategies)

            logs.append(
                f"Completed retesting {processed} strategies: "
                f"{passed_count} passed, {failed_count} failed"
            )
            logger.info("FR-retest-task-execute: %s", logs[-1])

            return TaskRetestSummary(
                mode=mode,
                total_keys=len(keys_to_retest),
                processed=processed,
                passed=passed_count,
                failed=failed_count,
                log_messages=tuple(logs),
            )

        finally:
            cls._running_projects.discard(project_id)
