"""Retester service integration with actual saved strategies and shared jobs."""

from __future__ import annotations

from typing import Any

import pytest
from app.core.lib.errors import DomainError
from app.workspace.retester.app_retester import AppRetesterService
from tests.workspace.builder.test_app_builder import (
    native_environment as native_environment,  # noqa: PLC0414
)


def test_actual_two_strategy_retest(native_environment: Any, caplog: Any) -> None:
    home, jobs = native_environment
    config = home.load_project("acceptance-retester")["tasks"]["task"]["settings"][
        "execution"
    ]
    home.save_project_settings(
        "acceptance-retester",
        "task",
        {"execution": {**config, "strategy_result_ids": ["source", "seed-run-0"]}},
        1,
    )
    service = AppRetesterService(home)
    with caplog.at_level("INFO"):
        started = service.start(
            "acceptance-retester", task_id="task", expected_revision=2
        ).data
    final = jobs.wait_for_job(started["job_id"], timeout=10)
    assert final.status == "COMPLETED"
    state = service.get_state("acceptance-retester").data
    assert state["processed_count"] == 2
    assert state["accepted_count"] == 2
    assert state["status"] == "COMPLETED"
    assert "FR-retester-lifecycle" in caplog.text


def test_unbound_lifecycle_cannot_claim_success() -> None:
    service = AppRetesterService()
    assert service.get_state("draft").data["status"] == "IDLE"
    for action in (service.start, service.pause, service.resume, service.stop):
        with pytest.raises(DomainError) as caught:
            action("draft")
        assert caught.value.code == "EXECUTION_CONTEXT_REQUIRED"
