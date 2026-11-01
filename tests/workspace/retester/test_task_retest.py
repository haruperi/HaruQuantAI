"""Retester compatibility runner uses actual snapshot inputs and preserves results."""

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from app.core.lib.errors import DomainError
from app.workspace.retester.settings_auto_retest_data import AutoRetestDataSettings
from app.workspace.retester.settings_cross_checks import CrossChecksSettingsSnapshot
from app.workspace.retester.settings_what_to_retest import WhatToRetestSettings
from app.workspace.retester.task_retest import TaskRetestRunner
from tests.workspace.home.test_execution_acceptance import context, project
from tests.workspace.home.test_execution_acceptance import execution as execution  # noqa: PLC0414


def test_no_implicit_strategies_or_fabricated_success() -> None:
    with pytest.raises(DomainError) as caught:
        TaskRetestRunner.execute(
            "draft",
            WhatToRetestSettings(),
            AutoRetestDataSettings(),
            CrossChecksSettingsSnapshot(),
        )
    assert caught.value.code == "EXECUTION_CONTEXT_REQUIRED"


def test_actual_retest_preserves_prior_records(execution: Any, tmp_path: Path) -> None:
    executor, _, results = execution
    results.save_result(
        "bank", replace(results.get_result("source"), result_id="source-two")
    )
    before = results.get_result("source").to_dict()
    snapshot = executor.prepare(
        project(strategy_result_ids=["source", "source-two"]), "task", 1
    )
    summary = TaskRetestRunner.execute(
        "project",
        WhatToRetestSettings(source_databank="bank", target_databank="bank"),
        AutoRetestDataSettings(),
        CrossChecksSettingsSnapshot(enabled=False),
        execution=executor,
        snapshot=snapshot,
        context=context(tmp_path, "retester-compat"),
    )
    assert summary.processed == summary.passed == 2
    assert results.get_result("source").to_dict() == before
    assert len(results.list_results("bank")) == 4
