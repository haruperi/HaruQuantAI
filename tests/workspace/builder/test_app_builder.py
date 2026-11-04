"""Builder service integration with isolated shared project/job authority."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from app.core.host.resources import ResourceMonitor
from app.core.jobs.manager import JobManager
from app.core.lib.errors import DomainError
from app.workspace.builder.app_builder import AppBuilderService
from app.workspace.builder.genetic_defaults import GeneticOptionsDefaults
from app.workspace.builder.settings_what_to_build import WhatToBuildSettings
from app.workspace.home.service import HomeService
from tests.support.home_acceptance_server import seed_environment


@pytest.fixture
def native_environment(tmp_path: Path) -> Generator[tuple[HomeService, JobManager]]:
    """Supply the same temporary gateway/catalog/result/settings/job authority."""
    gateway = seed_environment(tmp_path)
    jobs = JobManager(
        persistence=gateway,
        min_available_ram_pct=0,
        resource_mgr=ResourceMonitor(scratch_root=tmp_path / "jobs"),
    )
    home = HomeService(
        persistence=gateway, job_manager=jobs, projects_dir=tmp_path / "projects"
    )
    try:
        yield home, jobs
    finally:
        jobs.shutdown(wait=True, cancel_futures=True)


def test_actual_shared_lifecycle(native_environment: Any, caplog: Any) -> None:
    """State and cancellation come from the real manager, never a local clock."""
    home, jobs = native_environment
    config = home.load_project("acceptance-builder")["tasks"]["task"]["settings"][
        "execution"
    ]
    home.save_project_settings(
        "acceptance-builder", "task", {"execution": {**config, "candidates": 10}}, 1
    )
    service = AppBuilderService(home)
    with caplog.at_level("INFO"):
        started = service.start(
            "acceptance-builder", task_id="task", expected_revision=2
        ).data
    assert started.job_id is not None
    assert (
        service.pause("acceptance-builder", job_id=started.job_id).data.status
        == "PAUSED"
    )
    assert (
        service.resume("acceptance-builder", job_id=started.job_id).data.status
        == "RUNNING"
    )
    service.stop("acceptance-builder", job_id=started.job_id)
    assert jobs.wait_for_job(started.job_id, timeout=10).status == "CANCELLED"
    assert service.get_state("acceptance-builder").data.status == "CANCELLED"
    assert "FR-builder-lifecycle" in caplog.text


def test_missing_authority_fails_closed() -> None:
    service = AppBuilderService()
    assert service.get_state("unpersisted-draft").data.status == "IDLE"
    for action in (service.start, service.pause, service.resume, service.stop):
        with pytest.raises(DomainError) as caught:
            action("unpersisted-draft")
        assert caught.value.code == "EXECUTION_CONTEXT_REQUIRED"


def test_save_settings_draft_and_native_revision(native_environment: Any) -> None:
    home, _ = native_environment
    service = AppBuilderService(home)
    custom = WhatToBuildSettings(build_mode="RANDOM", min_entry_conditions=2)
    draft = service.save_settings(
        "acceptance-builder",
        what_to_build=custom,
        genetic_options=GeneticOptionsDefaults(population_size=20),
    )
    assert draft.data.what_to_build == custom
    saved = service.save_native_settings(
        "acceptance-builder", "task", {"description": "saved"}, 1
    )
    assert saved["revision"] == 2
    assert (
        home.load_project("acceptance-builder")["tasks"]["task"]["settings"][
            "description"
        ]
        == "saved"
    )
