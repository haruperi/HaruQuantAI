"""Optimizer service integration with real grid backtests and shared stores."""

from __future__ import annotations

from typing import Any

import pytest
from app.core.lib.errors import DomainError
from app.workspace.optimizer.app_optimizer import AppOptimizerService
from tests.workspace.builder.test_app_builder import (
    native_environment as native_environment,  # noqa: PLC0414
)


def test_actual_grid_evaluation(native_environment: Any, caplog: Any) -> None:
    home, jobs = native_environment
    service = AppOptimizerService(home)
    with caplog.at_level("INFO"):
        started = service.start(
            "acceptance-optimizer", task_id="task", expected_revision=1
        ).data
    record = jobs.wait_for_job(started.job_id, timeout=10)
    assert record.status == "COMPLETED"
    state = service.get_state("acceptance-optimizer").data
    assert state.evaluations_completed == 3
    assert state.best_fitness == 0
    assert state.status == "COMPLETED"
    assert service.profile_service.get_available_params(
        record.result["result_ids"][0]
    ) == ("threshold",)
    assert "FR-optimizer-lifecycle" in caplog.text


def test_unknown_authority_cannot_transition() -> None:
    service = AppOptimizerService()
    assert service.get_state("draft").data.status == "IDLE"
    for action in (service.start, service.pause, service.resume, service.stop):
        with pytest.raises(DomainError) as caught:
            action("draft")
        assert caught.value.code == "EXECUTION_CONTEXT_REQUIRED"


def test_invalid_saved_revision_prevents_submission(native_environment: Any) -> None:
    home, jobs = native_environment
    service = AppOptimizerService(home)
    with pytest.raises(DomainError) as caught:
        service.start("acceptance-optimizer", task_id="task", expected_revision=99)
    assert caught.value.code == "CONFLICT"
    assert jobs.list_jobs() == []
