"""Integration evidence for WF-DATA-007 recoverable historical backfill."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from app.services.data import (
    build_data_settings,
    build_dataset_save_request,
    build_job_definition,
    build_job_status_request,
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
    root = tmp_path.resolve()
    raw_root = root / "data" / "raw"
    raw_root.mkdir(parents=True)
    settings = build_data_settings(
        database_url="sqlite:///workflow.sqlite3",
        data_dir=root,
        sqlite_busy_timeout_seconds=1.5,
        write_lock_lease_seconds=30.0,
        approved_storage_roots=(Path("data/raw"),),
    )
    request_id = generate_id("req")

    with data_settings_context(settings):
        mig_res = run_data_migrations(request_id)
        assert mig_res.status == "success"
        save_res = save_dataset(
            build_dataset_save_request(
                dataset=make_dataset().model_copy(update={"request_id": request_id}),
                relative_path=Path("data/raw/ABC_1m.csv"),
                format="csv",
                overwrite=False,
                request_id=request_id,
            )
        )
        assert save_res.status == "success", f"save_dataset failed: {save_res.error}"
        register_local_test_source(raw_root, ("ABC",), source_id="local_csv")
        created = create_data_update_job(
            build_job_definition(
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
            build_job_status_request(job_id="wf-data-007", request_id=request_id)
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
