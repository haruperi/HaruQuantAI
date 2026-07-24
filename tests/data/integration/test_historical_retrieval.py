"""Integration evidence for WF-DATA-007 recoverable historical backfill."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from app.services.data import (
    DatasetSaveRequest,
    DataSettings,
    JobDefinition,
    JobStatusRequest,
    create_data_update_job,
    data_settings_context,
    get_data_update_job_status,
    run_data_migrations,
    run_data_update_job_once,
    save_dataset,
)
from app.utils import generate_id

from tests.data.helpers import END, START, make_dataset, register_local_test_source


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset process-local source composition state around the workflow."""
    for target in (
        "app.services.data.sources.registry._registry",
        "app.services.data.sources.registry._instances",
        "app.services.data.sources.registry._identities",
        "app.services.data.sources.policy._policy_configs",
    ):
        monkeypatch.setattr(target, {})


def test_wf_data_007_commits_data_and_resumable_checkpoint(tmp_path: Path) -> None:
    """Run retrieval through a real local source into a durable job checkpoint."""
    raw_root = tmp_path / "data" / "raw"
    raw_root.mkdir(parents=True)
    settings = DataSettings(
        database_url="sqlite:///workflow.sqlite3",
        data_dir=tmp_path,
        approved_storage_roots=(Path("data/raw"),),
    )
    request_id = generate_id("req")

    with data_settings_context(settings):
        run_data_migrations(request_id)
        save_dataset(
            DatasetSaveRequest(
                dataset=make_dataset().model_copy(update={"request_id": request_id}),
                relative_path=Path("data/raw/ABC_1m.csv"),
                format="csv",
                overwrite=False,
                request_id=request_id,
            )
        )
        register_local_test_source(raw_root, ("ABC",), source_id="local_csv")
        created = create_data_update_job(
            JobDefinition(
                job_id="wf-data-007",
                source_id="local_csv",
                symbols=("ABC",),
                timeframes=("1m",),
                data_kinds=("ohlcv",),
                start=START,
                end=END,
                interval_seconds=60,
                enabled=True,
                created_at=START - timedelta(minutes=1),
                request_id=request_id,
            ),
            request_id=request_id,
        )
        result = run_data_update_job_once("wf-data-007", request_id=request_id)
        status = get_data_update_job_status(
            JobStatusRequest(job_id="wf-data-007", request_id=request_id)
        )

    assert created.state == "created"
    assert result.state == "succeeded"
    assert result.committed_chunks == 1
    assert result.record_count == 1
    assert result.last_checkpoint is not None
    assert (tmp_path / result.last_checkpoint).is_file()
    assert (
        (tmp_path / result.last_checkpoint)
        .with_suffix(".parquet.manifest.json")
        .is_file()
    )
    assert status.last_run_status == "succeeded"
    assert status.last_checkpoint == result.last_checkpoint
